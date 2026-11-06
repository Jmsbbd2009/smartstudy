from datetime import timedelta, timezone
from pathlib import Path
import secrets
from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select, update, func, or_, inspect
from app.db.session import get_db
from app.models.entities import *
from app.schemas.contracts import *
from app.schemas.responses import *
from app.security.auth import current_user, require, hasher, verify_password, tokens, digest
from app.security.scope import guardian, academic, assignment_access, device_access
from app.security.rate_limit import auth_limit, limit
from app.services.rewards import credit, revoke, reserve, refund, locked_wallet, settle_stale
from app.services.policy import decision
from app.core.config import settings
from app.ai.provider import provider, TutorAnswer, Evaluation

router = APIRouter(prefix="/api/v1")


def output(row, exclude=()):
    return {c.key: getattr(row, c.key) for c in inspect(type(row)).columns if c.key not in exclude}


def audit(db, user, action, resource, details=None):
    db.add(AuditEvent(actor_id=user.id, action=action, resource_id=resource, details=details or {}))


def idempotency(idempotency_key: str = Header(min_length=8, max_length=100)):
    return idempotency_key


def assignments_query(db, user):
    if user.role == "STUDENT":
        return select(Assignment).where(Assignment.student_id == user.id, Assignment.status != "DRAFT")
    if user.role == "PARENT":
        children = select(ParentLink.child_id).where(
            ParentLink.parent_id == user.id, ParentLink.consent.is_(True)
        )
        return select(Assignment).where(
            Assignment.student_id.in_(children),
            or_(Assignment.status != "DRAFT", Assignment.owner_id == user.id),
        )
    return select(Assignment).where(Assignment.owner_id == user.id)


def latest_policy(db, device):
    row = db.scalar(
        select(DevicePolicy).where(
            DevicePolicy.device_id == device.id, DevicePolicy.version == device.version
        )
    )
    return row.document if row else {}


@router.post("/auth/register", response_model=TokenOut, status_code=201, dependencies=[Depends(auth_limit)])
def register(body: Register, db=Depends(get_db, scope="function")):
    email = body.email.lower()
    if db.scalar(select(User.id).where(User.email == email)):
        raise HTTPException(409, "Email already registered")
    user = User(email=email, name=body.name, role=body.role, password_hash=hasher.hash(body.password))
    db.add(user)
    db.flush()
    role = db.scalar(select(Role).where(Role.name == body.role))
    if role:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    if user.role == "STUDENT":
        db.add(Wallet(student_id=user.id))
    audit(db, user, "account.register", user.id)
    return tokens(db, user)


@router.post("/auth/login", response_model=TokenOut, dependencies=[Depends(auth_limit)])
def login(body: Login, db=Depends(get_db, scope="function")):
    user = db.scalar(
        select(User).where(
            or_(User.email == body.email.lower(), User.login == "".join(body.email.lower().split()))
        )
    )
    # Always perform password work, including unknown accounts.
    fallback = (
        "$argon2id$v=19$m=65536,t=3,p=2$U21hcnRTdHVkeUNvbnRyb2w$ZaDE3xwRglTbYm+8oB2ViCkZCmgKaIOXen4DXQLWFK0"
    )
    valid = verify_password(body.password, user.password_hash if user else fallback)
    if not user or not valid or not user.active:
        raise HTTPException(401, "Invalid credentials")
    return tokens(db, user)


@router.post("/auth/refresh", response_model=TokenOut, dependencies=[Depends(auth_limit)])
def refresh(body: Refresh, db=Depends(get_db, scope="function")):
    row = db.scalar(
        select(RefreshToken).where(RefreshToken.digest == digest(body.refresh_token)).with_for_update()
    )
    if not row or row.expires_at < now():
        raise HTTPException(401, "Refresh token expired")
    if row.revoked:
        db.execute(update(RefreshToken).where(RefreshToken.family == row.family).values(revoked=True))
        db.commit()  # Reuse revocation must persist even though the response is an error.
        raise HTTPException(401, "Refresh token reuse detected; sign in again")
    # Conditional consume protects even databases without SELECT FOR UPDATE.
    claimed = db.execute(
        update(RefreshToken)
        .where(RefreshToken.id == row.id, RefreshToken.revoked.is_(False))
        .values(revoked=True)
    )
    if claimed.rowcount != 1:
        raise HTTPException(401, "Refresh token already consumed")
    user = db.get(User, row.user_id)
    if not user or not user.active:
        raise HTTPException(401, "Account unavailable")
    return tokens(db, user, row.family)


@router.post("/auth/logout")
def logout(body: Refresh, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.scalar(
        select(RefreshToken).where(
            RefreshToken.digest == digest(body.refresh_token), RefreshToken.user_id == user.id
        )
    )
    if row:
        db.execute(update(RefreshToken).where(RefreshToken.family == row.family).values(revoked=True))
    return {"ok": True}


@router.get("/users/me", response_model=UserOut)
def me(user=Depends(current_user)):
    return output(user, ("password_hash",))


@router.post("/families/invite", response_model=InviteOut)
def family_invite(user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    raw = secrets.token_urlsafe(24)
    db.add(
        Invite(
            owner_id=user.id,
            kind="FAMILY",
            resource_id=user.id,
            code_hash=digest(raw),
            expires_at=now() + timedelta(minutes=15),
        )
    )
    return {"code": raw, "expires_in": 900}


@router.post("/families/link-child")
def link(body: Link, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "PARENT")
    limit("link:" + user.id, 10)
    invite = db.scalar(
        select(Invite).where(Invite.code_hash == digest(body.code), Invite.kind == "FAMILY").with_for_update()
    )
    if not invite or invite.used or invite.expires_at < now():
        raise HTTPException(400, "Invalid or expired invite")
    claimed = db.execute(
        update(Invite).where(Invite.id == invite.id, Invite.used.is_(False)).values(used=True)
    )
    if claimed.rowcount != 1:
        raise HTTPException(409, "Invite already consumed")
    existing = db.scalar(
        select(ParentLink).where(ParentLink.parent_id == user.id, ParentLink.child_id == invite.owner_id)
    )
    if existing:
        existing.consent = True
    else:
        db.add(ParentLink(parent_id=user.id, child_id=invite.owner_id))
    db.add(Consent(actor_id=user.id, child_id=invite.owner_id, purpose="guardian_supervision", granted=True))
    audit(db, user, "family.link", invite.owner_id)
    return {"child_id": invite.owner_id}


@router.get("/families/children", response_model=list[UserOut])
def children(user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "PARENT")
    return [
        output(u, ("password_hash",))
        for u in db.scalars(
            select(User)
            .join(ParentLink, ParentLink.child_id == User.id)
            .where(ParentLink.parent_id == user.id, ParentLink.consent.is_(True))
        )
    ]


@router.delete("/families/children/{child_id}")
def unlink(child_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.scalar(
        select(ParentLink).where(ParentLink.parent_id == user.id, ParentLink.child_id == child_id)
    )
    if not row or not guardian(db, user, child_id):
        raise HTTPException(403, "Guardian access required")
    row.consent = False
    db.add(Consent(actor_id=user.id, child_id=child_id, purpose="guardian_supervision", granted=False))
    audit(db, user, "family.unlink", child_id)
    return {"ok": True}


@router.post("/classrooms", response_model=ClassroomOut, status_code=201)
def create_class(body: Named, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "TEACHER")
    row = Classroom(name=body.name, teacher_id=user.id)
    db.add(row)
    db.flush()
    return output(row)


@router.get("/classrooms", response_model=list[ClassroomOut])
def classrooms(user=Depends(current_user), db=Depends(get_db, scope="function")):
    if user.role == "TEACHER":
        query = select(Classroom).where(Classroom.teacher_id == user.id)
    elif user.role == "STUDENT":
        query = (
            select(Classroom)
            .join(ClassroomMember, ClassroomMember.classroom_id == Classroom.id)
            .where(ClassroomMember.student_id == user.id)
        )
    else:
        raise HTTPException(403, "Academic role required")
    return [output(c) for c in db.scalars(query)]


@router.post("/classrooms/{class_id}/invite", response_model=InviteOut)
def class_invite(class_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.get(Classroom, class_id)
    if not row or row.teacher_id != user.id:
        raise HTTPException(403, "Classroom ownership required")
    raw = secrets.token_urlsafe(24)
    db.add(
        Invite(
            owner_id=user.id,
            kind="CLASS",
            resource_id=class_id,
            code_hash=digest(raw),
            expires_at=now() + timedelta(days=1),
        )
    )
    return {"code": raw, "expires_in": 86400}


@router.post("/classrooms/join")
def class_join(body: Join, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    limit("join:" + user.id, 10)
    row = db.scalar(
        select(Invite).where(
            Invite.kind == "CLASS",
            Invite.code_hash == digest(body.code),
            Invite.used.is_(False),
            Invite.expires_at > now(),
        )
    )
    if not row:
        raise HTTPException(400, "Invalid classroom invite")
    if not db.scalar(
        select(ClassroomMember.id).where(
            ClassroomMember.classroom_id == row.resource_id, ClassroomMember.student_id == user.id
        )
    ):
        db.add(ClassroomMember(classroom_id=row.resource_id, student_id=user.id))
    return {"classroom_id": row.resource_id}


@router.get("/classrooms/{class_id}/students")
def roster(class_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.get(Classroom, class_id)
    if not row or row.teacher_id != user.id:
        raise HTTPException(403, "Classroom ownership required")
    return [
        {"id": u.id, "name": u.name}
        for u in db.scalars(
            select(User)
            .join(ClassroomMember, ClassroomMember.student_id == User.id)
            .where(ClassroomMember.classroom_id == class_id)
        )
    ]


@router.get("/assignments", response_model=list[AssignmentOut])
def assignments(
    limit_count: int = 50, offset: int = 0, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    if not 1 <= limit_count <= 100 or offset < 0:
        raise HTTPException(422, "Invalid pagination")
    return [
        output(a, ("answer_key",))
        for a in db.scalars(
            assignments_query(db, user)
            .order_by(Assignment.created_at.desc())
            .offset(offset)
            .limit(limit_count)
        )
    ]


@router.post("/assignments", response_model=AssignmentOut, status_code=201)
def create_assignment(body: AssignmentIn, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "PARENT", "TEACHER")
    student = db.get(User, body.student_id)
    if not student or student.role != "STUDENT":
        raise HTTPException(404, "Student not found")
    if user.role == "PARENT":
        if not guardian(db, user, body.student_id) or body.classroom_id:
            raise HTTPException(403, "Linked household assignment required")
    else:
        room = db.get(Classroom, body.classroom_id) if body.classroom_id else None
        member = db.scalar(
            select(ClassroomMember.id).where(
                ClassroomMember.classroom_id == body.classroom_id,
                ClassroomMember.student_id == body.student_id,
            )
        )
        if not room or room.teacher_id != user.id or not member:
            raise HTTPException(403, "Student must be in your classroom")
        # Teacher cannot set a household entertainment budget or promise screen time.
        if body.reward_minutes != 0:
            raise HTTPException(
                422, "Teacher assignments require guardian-configured rewards; set reward_minutes=0"
            )
    row = Assignment(owner_id=user.id, **body.model_dump())
    db.add(row)
    db.flush()
    audit(db, user, "assignment.create", row.id)
    db.add(Notification(user_id=body.student_id, title=body.title, body="Yangi vazifa berildi"))
    return output(row, ("answer_key",))


@router.get("/assignments/{assignment_id}", response_model=AssignmentDetailOut)
def detail(assignment_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = assignment_access(db, user, assignment_id)
    result = output(row, ("answer_key",))
    result["attachments"] = [
        output(a, ("storage_key",))
        for a in db.scalars(select(Attachment).where(Attachment.assignment_id == row.id))
    ]
    result["submissions"] = [
        output(s)
        for s in db.scalars(
            select(Submission).where(Submission.assignment_id == row.id).order_by(Submission.created_at)
        )
    ]
    return result


@router.post("/assignments/{assignment_id}/submit", response_model=SubmissionOut, status_code=201)
def submit(
    assignment_id: str,
    body: SubmissionIn,
    key=Depends(idempotency),
    user=Depends(current_user),
    db=Depends(get_db, scope="function"),
):
    require(user, "STUDENT")
    row = assignment_access(db, user, assignment_id)
    db.execute(update(Assignment).where(Assignment.id == row.id).values(updated_at=now()))
    old = db.scalar(
        select(Submission).where(Submission.student_id == user.id, Submission.idempotency_key == key)
    )
    if old:
        if (old.assignment_id, old.text, old.answers) != (assignment_id, body.text, body.answers):
            raise HTTPException(409, "Idempotency key conflict")
        return output(old)
    if row.status == "APPROVED":
        raise HTTPException(409, "Assignment already approved")
    result = Submission(
        assignment_id=row.id, student_id=user.id, text=body.text, answers=body.answers, idempotency_key=key
    )
    db.add(result)
    row.status = "SUBMITTED"
    db.flush()
    return output(result)


@router.post("/submissions/{submission_id}/review", response_model=SubmissionOut)
def review(
    submission_id: str, body: ReviewIn, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(404, "Submission not found")
    row = assignment_access(db, user, sub.assignment_id, review=True)
    locked_wallet(db, row.student_id)
    latest = db.scalar(
        select(Submission.id)
        .where(Submission.assignment_id == row.id)
        .order_by(Submission.created_at.desc(), Submission.id.desc())
    )
    if latest != sub.id:
        raise HTTPException(409, "Review the newest submission")
    if sub.status == body.decision:
        return output(sub)
    if body.decision == "APPROVED":
        credit(db, row.student_id, "assignment:" + row.id, row.reward_minutes, row.id)
    elif row.status == "APPROVED":
        revoke(db, row.student_id, row.id)
    row.status = body.decision
    sub.status = body.decision
    db.add(
        SubmissionReview(
            submission_id=sub.id, reviewer_id=user.id, decision=body.decision, feedback=body.feedback
        )
    )
    audit(db, user, "submission." + body.decision.lower(), sub.id)
    db.add(
        Notification(user_id=sub.student_id, title="Vazifa tekshirildi", body=body.feedback or body.decision)
    )
    return output(sub)


@router.post("/submissions/{submission_id}/approve", response_model=SubmissionOut)
def approve(submission_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    return review(submission_id, ReviewIn(decision="APPROVED"), user, db)


@router.get("/submissions/{submission_id}/reviews", response_model=list[SubmissionReviewOut])
def reviews(submission_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(404, "Submission not found")
    assignment_access(db, user, sub.assignment_id)
    return [
        output(x)
        for x in db.scalars(
            select(SubmissionReview)
            .where(SubmissionReview.submission_id == submission_id)
            .order_by(SubmissionReview.created_at)
        )
    ]


@router.post("/assignments/{assignment_id}/attachments", response_model=AttachmentOut, status_code=201)
def upload(
    assignment_id: str,
    file: UploadFile = File(...),
    user=Depends(current_user),
    db=Depends(get_db, scope="function"),
):
    assignment_access(db, user, assignment_id)
    key = uid()
    root = Path(settings.upload_dir)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = root / key
    size = 0
    head = b""
    try:
        with path.open("xb") as target:
            path.chmod(0o600)
            while chunk := file.file.read(65536):
                if not head:
                    head = chunk[:16]
                size += len(chunk)
                if size > 10 * 1024 * 1024:
                    raise HTTPException(413, "Attachment exceeds 10 MiB")
                target.write(chunk)
        types = [
            (b"%PDF-", "application/pdf"),
            (b"\x89PNG\r\n\x1a\n", "image/png"),
            (b"\xff\xd8\xff", "image/jpeg"),
        ]
        media = next((m for prefix, m in types if head.startswith(prefix)), None)
        if not media or file.content_type != media:
            raise HTTPException(415, "Only matching PDF/PNG/JPEG files are accepted")
        filename = Path(file.filename or "attachment").name.replace("\r", "").replace("\n", "")[:180]
        row = Attachment(
            assignment_id=assignment_id,
            uploader_id=user.id,
            filename=filename,
            storage_key=key,
            media_type=media,
            size=size,
        )
        db.add(row)
        db.flush()
        db.commit()
        return output(row, ("storage_key",))
    except Exception:
        path.unlink(missing_ok=True)
        raise


@router.get("/attachments/{attachment_id}")
def download(attachment_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.get(Attachment, attachment_id)
    if not row:
        raise HTTPException(404, "Attachment not found")
    assignment_access(db, user, row.assignment_id)
    return FileResponse(
        Path(settings.upload_dir) / row.storage_key,
        filename=row.filename,
        media_type="application/octet-stream",
        headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "no-store"},
    )


@router.post("/devices", response_model=DeviceOut, status_code=201)
def enroll(body: DeviceIn, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    row = Device(student_id=user.id, name=body.name)
    db.add(row)
    db.flush()
    audit(db, user, "device.register", row.id)
    return output(row)


@router.get("/devices", response_model=list[DeviceOut])
def devices(child_id: str | None = None, user=Depends(current_user), db=Depends(get_db, scope="function")):
    child = child_id or user.id
    if user.id != child and not guardian(db, user, child):
        raise HTTPException(403, "Household access required")
    return [
        output(d)
        for d in db.scalars(select(Device).where(Device.student_id == child, Device.retired.is_(False)))
    ]


@router.post("/devices/{device_id}/authorize")
def authorize_device(device_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    device = device_access(db, user, device_id, True)
    c = Consent(
        actor_id=user.id, child_id=device.student_id, purpose="device_management:" + device_id, granted=True
    )
    db.add(c)
    db.flush()
    db.add(Enrollment(device_id=device.id, authorized_by=user.id, consent_id=c.id))
    audit(db, user, "device.authorize", device.id)
    return {"ok": True}


@router.get("/devices/{device_id}/policies", response_model=PolicyOut)
def get_policy(device_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    device = device_access(db, user, device_id)
    return {
        "device_id": device.id,
        "version": device.version,
        "document": latest_policy(db, device),
        "deprovision_requested": device.deprovision_requested,
        "retired": device.retired,
        "management_authorized": not device.retired
        and not device.deprovision_requested
        and db.scalar(select(Enrollment.id).where(Enrollment.device_id == device.id)) is not None,
    }


@router.put("/devices/{device_id}/policies", response_model=PolicyOut)
def put_policy(
    device_id: str, body: PolicyIn, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    device = device_access(db, user, device_id, True)
    if device.retired or device.deprovision_requested:
        raise HTTPException(409, "Device is being removed")
    if not db.scalar(select(Enrollment.id).where(Enrollment.device_id == device.id)):
        raise HTTPException(409, "Explicit device authorization required")
    if "uz.smartstudy.control" in body.blocked_packages or "com.android.settings" in body.blocked_packages:
        raise HTTPException(422, "Protected package")
    if body.override_until:
        if body.override_until.tzinfo is None:
            raise HTTPException(422, "Override requires timezone")
        delta = body.override_until.astimezone(timezone.utc).replace(tzinfo=None) - now()
        if not timedelta(0) < delta <= timedelta(hours=24):
            raise HTTPException(422, "Override must expire within 24 hours")
    changed = db.execute(
        update(Device)
        .where(Device.id == device.id, Device.version == body.expected_version)
        .values(version=Device.version + 1)
    )
    if changed.rowcount != 1:
        raise HTTPException(409, "Stale policy version; reload before editing")
    version = body.expected_version + 1
    document = body.model_dump(mode="json", exclude={"expected_version"})
    policy = DevicePolicy(device_id=device.id, version=version, document=document, actor_id=user.id)
    db.add(policy)
    db.flush()
    for package in body.blocked_packages:
        db.add(BlockedAppRule(policy_id=policy.id, package=package))
    db.add(PolicyVersion(device_id=device.id, version=version, actor_id=user.id))
    audit(db, user, "policy.publish", device.id, {"version": version})
    return {
        "device_id": device.id,
        "version": version,
        "document": document,
        "deprovision_requested": False,
        "retired": False,
        "management_authorized": True,
    }


@router.post("/devices/{device_id}/sync", response_model=PolicyOut)
def sync(device_id: str, body: SyncIn, user=Depends(current_user), db=Depends(get_db, scope="function")):
    device = device_access(db, user, device_id)
    if user.id != device.student_id:
        raise HTTPException(403, "Device student must acknowledge")
    if body.applied_version > device.version:
        raise HTTPException(409, "Unknown future policy version")
    authorized = (
        not device.retired
        and not device.deprovision_requested
        and db.scalar(select(Enrollment.id).where(Enrollment.device_id == device.id)) is not None
    )
    if body.eligible_apps and not authorized:
        raise HTTPException(403, "Guardian device authorization is required before sharing app names")
    inventory = (
        [app.model_dump() for app in body.eligible_apps]
        if body.eligible_apps is not None
        else device.compliance.get("eligible_apps", [])
    )
    if not authorized:
        inventory = []
    device.mode = "MANAGED_REPORTED" if body.device_owner else "STANDARD"
    device.compliance = {
        "eligible_apps": inventory,
        "device_owner_reported": body.device_owner,
        "uninstall_blocked": body.device_owner and body.uninstall_blocked,
        "applied_version": body.applied_version,
        "failures": body.failures,
        "reported_at": now().isoformat(),
        "self_reported": True,
    }
    if (
        device.deprovision_requested
        and body.cleanup_complete
        and not body.failures
        and body.applied_version == device.version
    ):
        device.retired = True
        device.compliance = {**device.compliance, "eligible_apps": []}
        audit(db, user, "device.cleanup_acknowledged", device.id)
    return get_policy(device_id, user, db)


@router.post("/devices/{device_id}/deprovision")
def deprovision(device_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    device = device_access(db, user, device_id, True)
    device.deprovision_requested = True
    audit(db, user, "device.deprovision_request", device.id)
    return {"pending_cleanup": True}


@router.get("/rewards/wallet", response_model=WalletOut)
def wallet(child_id: str | None = None, user=Depends(current_user), db=Depends(get_db, scope="function")):
    child = child_id or user.id
    if child != user.id and not guardian(db, user, child):
        raise HTTPException(403, "Household access required")
    settle_stale(db, child)
    row = db.scalar(select(Wallet).where(Wallet.student_id == child))
    if not row:
        raise HTTPException(404, "Wallet not found")
    return output(row)


@router.put("/rewards/budget/{child_id}", response_model=WalletOut)
def budget(child_id: str, body: Budget, user=Depends(current_user), db=Depends(get_db, scope="function")):
    if not guardian(db, user, child_id):
        raise HTTPException(403, "Guardian required")
    row = locked_wallet(db, child_id)
    row.daily_max = body.daily_max
    row.weekly_max = body.weekly_max
    audit(db, user, "reward.budget", child_id)
    return output(row)


@router.get("/rewards/ledger", response_model=list[RewardOut])
def ledger(child_id: str | None = None, user=Depends(current_user), db=Depends(get_db, scope="function")):
    child = child_id or user.id
    if child != user.id and not guardian(db, user, child):
        raise HTTPException(403, "Household access required")
    return [
        output(x)
        for x in db.scalars(
            select(RewardTransaction)
            .where(RewardTransaction.student_id == child)
            .order_by(RewardTransaction.created_at.desc())
            .limit(100)
        )
    ]


@router.post("/rewards/redeem", response_model=UnlockOut)
def redeem(
    body: Redeem, key=Depends(idempotency), user=Depends(current_user), db=Depends(get_db, scope="function")
):
    require(user, "STUDENT")
    device = device_access(db, user, body.device_id)
    if device.student_id != user.id or device.retired or device.deprovision_requested:
        raise HTTPException(409, "Device unavailable")
    policy = latest_policy(db, device)
    if body.package not in policy.get("blocked_packages", []):
        raise HTTPException(422, "Select a configured entertainment package")
    if decision(policy, body.package, now().replace(tzinfo=timezone.utc), earned=True) not in (
        "EARNED",
        "ALLOW",
        "OVERRIDE",
        "ESSENTIAL",
    ):
        raise HTTPException(409, "Study, sleep or safety policy currently takes priority")
    row = reserve(db, user.id, body, key)
    return output(row)


@router.post("/rewards/sessions/{session_id}/ack", response_model=UnlockOut)
def acknowledge(session_id: str, body: Ack, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.get(UnlockSession, session_id)
    if not row or row.student_id != user.id:
        raise HTTPException(403, "Session access denied")
    locked_wallet(db, user.id)
    db.refresh(row)
    if row.status != "PENDING":
        return output(row)
    if row.expires_at <= now() or not body.applied:
        refund(db, row)
    else:
        row.status = "ACTIVE"
        row.expires_at = now() + timedelta(minutes=row.minutes)
    return output(row)


@router.get("/rewards/sessions", response_model=list[UnlockOut])
def unlocks(user=Depends(current_user), db=Depends(get_db, scope="function")):
    settle_stale(db, user.id)
    return [
        output(x)
        for x in db.scalars(
            select(UnlockSession).where(
                UnlockSession.student_id == user.id, UnlockSession.status.in_(["PENDING", "ACTIVE"])
            )
        )
    ]


@router.post("/focus", response_model=FocusOut, status_code=201)
def start_focus(body: FocusIn, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    locked_wallet(db, user.id)
    if db.scalar(
        select(FocusSession.id).where(FocusSession.student_id == user.id, FocusSession.status == "ACTIVE")
    ):
        raise HTTPException(409, "A focus session is active")
    row = FocusSession(student_id=user.id, **body.model_dump())
    db.add(row)
    db.flush()
    return output(row)


@router.get("/focus", response_model=list[FocusOut])
def focus_history(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return [
        output(f)
        for f in db.scalars(
            select(FocusSession)
            .where(FocusSession.student_id == user.id)
            .order_by(FocusSession.created_at.desc())
            .limit(100)
        )
    ]


@router.post("/focus/{session_id}/complete", response_model=FocusOut)
def complete_focus(session_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.get(FocusSession, session_id)
    if not row or row.student_id != user.id:
        raise HTTPException(403, "Focus access denied")
    locked_wallet(db, user.id)
    if row.status == "COMPLETED":
        return output(row)
    if row.status != "ACTIVE" or (now() - row.created_at).total_seconds() < row.duration_seconds:
        raise HTTPException(409, "Session has not finished")
    row.status = "COMPLETED"
    row.completed_at = now()
    # Study time is recorded, never treated as proof of academic work. No unapproved credits.
    return output(row)


@router.post("/focus/{session_id}/cancel", response_model=FocusOut)
def cancel_focus(session_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.get(FocusSession, session_id)
    if not row or row.student_id != user.id:
        raise HTTPException(403, "Focus access denied")
    if row.status == "ACTIVE":
        row.status = "CANCELLED"
    return output(row)


@router.get("/alarms", response_model=list[AlarmOut])
def alarms(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return [output(a) for a in db.scalars(select(Alarm).where(Alarm.student_id == user.id))]


@router.post("/alarms", response_model=AlarmOut, status_code=201)
def add_alarm(body: AlarmIn, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    row = Alarm(student_id=user.id, **body.model_dump())
    db.add(row)
    db.flush()
    return output(row)


@router.delete("/alarms/{alarm_id}")
def remove_alarm(alarm_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.get(Alarm, alarm_id)
    if not row or row.student_id != user.id:
        raise HTTPException(403, "Alarm access denied")
    db.delete(row)
    return {"ok": True}


@router.get("/students/me/dashboard", response_model=DashboardOut)
def dashboard(user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    tasks = list(
        db.scalars(select(Assignment).where(Assignment.student_id == user.id, Assignment.status != "DRAFT"))
    )
    return {
        "name": user.name,
        "assigned": len(tasks),
        "approved": sum(t.status == "APPROVED" for t in tasks),
        "wallet": wallet(None, user, db),
    }


@router.get("/reports/weekly", response_model=ReportOut, response_model_exclude_none=True)
def reports(child_id: str | None = None, user=Depends(current_user), db=Depends(get_db, scope="function")):
    child = child_id or user.id
    if not academic(db, user, child):
        raise HTTPException(403, "Academic access denied")
    query = select(Assignment).where(Assignment.student_id == child)
    if user.role == "TEACHER":
        query = query.where(Assignment.owner_id == user.id)
    tasks = list(db.scalars(query))
    total = len(tasks)
    approved = sum(a.status == "APPROVED" for a in tasks)
    # Teachers see only their own academic performance, never household wallet or app history.
    report = {
        "assigned": total,
        "approved": approved,
        "completion_rate": approved / total if total else 0,
        "subjects": sorted({a.subject for a in tasks}),
    }
    if user.id == child or guardian(db, user, child):
        since = now() - timedelta(days=7)
        report["focus_seconds"] = db.scalar(
            select(func.coalesce(func.sum(FocusSession.duration_seconds), 0)).where(
                FocusSession.student_id == child,
                FocusSession.status == "COMPLETED",
                FocusSession.completed_at >= since,
            )
        )
        report["reward_minutes_earned"] = db.scalar(
            select(func.coalesce(func.sum(RewardTransaction.delta), 0)).where(
                RewardTransaction.student_id == child,
                RewardTransaction.kind == "EARN",
                RewardTransaction.created_at >= since,
            )
        )
        report["access_minutes_reserved"] = db.scalar(
            select(func.coalesce(func.sum(UnlockSession.minutes), 0)).where(
                UnlockSession.student_id == child,
                UnlockSession.status.in_(["ACTIVE", "EXPIRED"]),
                UnlockSession.created_at >= since,
            )
        )
    return report


@router.get("/notifications", response_model=list[NotificationOut])
def notifications(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return [
        output(n)
        for n in db.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
            .limit(100)
        )
    ]


@router.post("/notifications/{notification_id}/read")
def mark_read(notification_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.get(Notification, notification_id)
    if not row or row.user_id != user.id:
        raise HTTPException(403, "Notification access denied")
    row.read = True
    return {"ok": True}


@router.get("/audit", response_model=list[AuditOut])
def audit_list(user=Depends(current_user), db=Depends(get_db, scope="function")):
    return [
        output(e)
        for e in db.scalars(
            select(AuditEvent)
            .where(AuditEvent.actor_id == user.id)
            .order_by(AuditEvent.created_at.desc())
            .limit(100)
        )
    ]


@router.post("/ai/tutor", response_model=TutorAnswer)
def tutor(body: TutorIn, user=Depends(current_user)):
    require(user, "STUDENT")
    limit("ai:" + user.id, 10)
    return provider.structured(
        body.subject + ": " + body.message,
        TutorAnswer,
        "You are a school tutor. Use simple Uzbek Latin. Give hints, explain reasoning, then practice. Do not provide personal advice, collect personal data or solve graded exams. Encourage an adult for unsafe personal situations.",
    )


@router.post("/ai/evaluate-homework")
def evaluate_homework(submission_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    sub = db.get(Submission, submission_id)
    if not sub:
        raise HTTPException(404, "Submission not found")
    row = assignment_access(db, user, sub.assignment_id)
    limit("evaluation:" + user.id, 10)
    if row.answer_key:
        correct = sum(
            sub.answers.get(k, "").strip().casefold() == v.strip().casefold()
            for k, v in row.answer_key.items()
        )
        data = {
            "correct": correct,
            "total": len(row.answer_key),
            "confidence": 1.0,
            "feedback": "Xatolarni o‘qituvchi bilan ko‘rib chiqing.",
            "human_required": True,
            "model": "validated-answer-key-v1",
        }
    else:
        result = provider.structured(
            sub.text,
            Evaluation,
            "Assist an adult reviewing school homework. Explain uncertainty. Never grant rewards. Subjective writing requires a human. Use Uzbek Latin.",
        )
        if result.correct > result.total:
            raise HTTPException(503, "AI scoring schema is inconsistent")
        data = result.model_dump()
        data["human_required"] = True
        data["model"] = result._provider_model or settings.ai_model
        data["review_version"] = "1"
    db.add(
        SubmissionReview(
            submission_id=sub.id, decision="NEEDS_HUMAN_REVIEW", feedback=data["feedback"], metadata_json=data
        )
    )
    if sub.status not in ("APPROVED", "REJECTED", "REVISION_REQUESTED"):
        sub.status = "NEEDS_HUMAN_REVIEW"
        if row.status not in ("APPROVED", "REJECTED", "REVISION_REQUESTED"):
            row.status = "NEEDS_HUMAN_REVIEW"
    return data


@router.post("/quizzes", response_model=QuizOut, status_code=201)
def create_quiz(body: QuizIn, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = assignment_access(db, user, body.assignment_id, True)
    if row.owner_id != user.id:
        raise HTTPException(403, "Assignment owner must validate quiz keys")
    if db.scalar(select(Quiz.id).where(Quiz.assignment_id == row.id)):
        raise HTTPException(409, "Assignment already has a quiz")
    quiz = Quiz(
        owner_id=user.id,
        assignment_id=row.id,
        title=body.title,
        time_limit_seconds=body.time_limit_seconds,
        validated=True,
    )
    db.add(quiz)
    db.flush()
    for i, q in enumerate(body.questions):
        db.add(QuizQuestion(quiz_id=quiz.id, position=i, **q.model_dump()))
    return output(quiz)


@router.get("/quizzes", response_model=list[QuizOut])
def quiz_list(user=Depends(current_user), db=Depends(get_db, scope="function")):
    ids = assignments_query(db, user).with_only_columns(Assignment.id)
    return [output(q) for q in db.scalars(select(Quiz).where(Quiz.assignment_id.in_(ids)))]


@router.get("/quizzes/{quiz_id}", response_model=QuizDetailOut)
def quiz_detail(quiz_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    assignment_access(db, user, quiz.assignment_id)
    return {
        **output(quiz),
        "questions": [
            output(q, ("answer", "explanation"))
            for q in db.scalars(
                select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id).order_by(QuizQuestion.position)
            )
        ],
    }


@router.post("/quizzes/{quiz_id}/start", response_model=AttemptOut)
def quiz_start(quiz_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    assignment_access(db, user, quiz.assignment_id)
    locked_wallet(db, user.id)
    attempt = db.scalar(
        select(QuizAttempt).where(QuizAttempt.quiz_id == quiz.id, QuizAttempt.student_id == user.id)
    )
    if not attempt:
        attempt = QuizAttempt(quiz_id=quiz.id, student_id=user.id)
        db.add(attempt)
        db.flush()
    return output(attempt)


@router.post("/quizzes/{quiz_id}/finish", response_model=FinishedQuizOut)
def quiz_finish(
    quiz_id: str, body: QuizAnswers, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    require(user, "STUDENT")
    quiz = db.get(Quiz, quiz_id)
    if not quiz:
        raise HTTPException(404, "Quiz not found")
    assignment_access(db, user, quiz.assignment_id)
    locked_wallet(db, user.id)
    attempt = db.scalar(
        select(QuizAttempt).where(QuizAttempt.quiz_id == quiz.id, QuizAttempt.student_id == user.id)
    )
    if not attempt:
        raise HTTPException(409, "Start quiz first")
    if not attempt.completed_at:
        if (now() - attempt.created_at).total_seconds() > quiz.time_limit_seconds + 15:
            raise HTTPException(409, "Quiz time limit exceeded")
        questions = list(db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id)))
        if any(k not in {q.id for q in questions} for k in body.answers):
            raise HTTPException(422, "Unknown quiz question")
        attempt.answers = body.answers
        attempt.score = sum(body.answers.get(q.id) == q.answer for q in questions)
        attempt.completed_at = now()
    return {
        **output(attempt),
        "explanations": [
            {"question_id": q.id, "answer": q.answer, "explanation": q.explanation}
            for q in db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id))
        ],
    }


@router.post("/privacy/deletion-request", status_code=202)
def deletion(user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = DeletionRequest(user_id=user.id)
    db.add(row)
    db.flush()
    audit(db, user, "privacy.deletion_requested", row.id)
    return {
        "id": row.id,
        "status": row.status,
        "message": "Request recorded for verified administrative processing",
    }


@router.post("/assignments/{assignment_id}/publish", response_model=AssignmentOut)
def publish_assignment(assignment_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = assignment_access(db, user, assignment_id, True)
    if row.owner_id != user.id:
        raise HTTPException(403, "Assignment owner required")
    if row.status == "DRAFT":
        row.status = "ASSIGNED"
    audit(db, user, "assignment.publish", row.id)
    return output(row, ("answer_key",))


@router.post("/assignments/{assignment_id}/start", response_model=AssignmentOut)
def begin_assignment(assignment_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    row = assignment_access(db, user, assignment_id)
    if row.status in ("ASSIGNED", "REVISION_REQUESTED"):
        row.status = "IN_PROGRESS"
    return output(row, ("answer_key",))


@router.put("/assignments/{assignment_id}/reward-policy", response_model=AssignmentOut)
def assignment_reward(
    assignment_id: str, body: RewardPolicyIn, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    row = assignment_access(db, user, assignment_id, True)
    if not guardian(db, user, row.student_id):
        raise HTTPException(403, "Guardian must configure household reward")
    locked_wallet(db, row.student_id)
    if db.scalar(select(RewardTransaction.id).where(RewardTransaction.origin == "assignment:" + row.id)):
        raise HTTPException(409, "Reward origin already credited; it cannot be changed")
    row.reward_minutes = body.reward_minutes
    audit(db, user, "assignment.reward_policy", row.id, {"minutes": body.reward_minutes})
    return output(row, ("answer_key",))
