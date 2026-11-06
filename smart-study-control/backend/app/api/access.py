import json
import hmac
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy import select, update, or_
from webauthn import (
    generate_registration_options,
    verify_registration_response,
    generate_authentication_options,
    verify_authentication_response,
    options_to_json,
    base64url_to_bytes,
)
from webauthn.helpers import bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    AuthenticatorAttachment,
    UserVerificationRequirement,
    PublicKeyCredentialDescriptor,
)
from app.db.session import get_db
from app.core.config import settings
from app.models.entities import (
    User,
    Role,
    UserRole,
    School,
    StaffProfile,
    Notification,
    AuditEvent,
    RefreshToken,
    TelegramIdentity,
    AuthChallenge,
    Passkey,
    now,
)
from app.security.auth import current_user, require, tokens, digest, hasher, verify_password
from app.security.rate_limit import auth_limit, limit
from app.schemas.responses import TokenOut
from app.schemas.access import *
from app.services.challenges import issue, lock_challenge, validate, failed, otp_hash
from app.integrations.telegram import process_update

router = APIRouter(prefix="/api/v1", tags=["access"])
STAFF = ("TEACHER", "SCHOOL_ADMIN", "SUPER_ADMIN")


def staff(user):
    require(user, *STAFF)


def find_login(db, login):
    normalized = "".join(login.lower().split())
    return db.scalar(select(User).where(or_(User.email == login.lower().strip(), User.login == normalized)))


def event(db, user, action, resource):
    db.add(AuditEvent(actor_id=user.id, action=action, resource_id=resource, details={}))


def staff_output(db, user):
    profile = db.scalar(select(StaffProfile).where(StaffProfile.user_id == user.id))
    return {
        "id": user.id,
        "login": user.login,
        "email": user.email,
        "name": user.name,
        "role": user.role,
        "active": user.active,
        "must_change_password": user.must_change_password,
        "school_id": profile.school_id if profile else None,
    }


@router.get("/auth/capabilities")
def capabilities():
    return {
        "telegram": bool(settings.telegram_token),
        "bot_username": settings.telegram_username,
        "passkeys": bool(settings.passkey_rp_id and settings.passkey_origin),
        "face_storage": "none",
    }


@router.post("/auth/password", response_model=TokenOut)
def password(body: PasswordChange, user=Depends(current_user), db=Depends(get_db, scope="function")):
    if (
        not verify_password(body.current_password, user.password_hash)
        or body.current_password == body.new_password
    ):
        raise HTTPException(400, "Eski parolni tekshiring va yangi parol tanlang")
    db.execute(update(User).where(User.id == user.id).values(updated_at=now()))
    db.refresh(user)
    user.password_hash = hasher.hash(body.new_password)
    user.must_change_password = False
    user.auth_epoch += 1
    db.execute(update(AuthChallenge).where(AuthChallenge.user_id == user.id).values(consumed=True))
    db.execute(update(RefreshToken).where(RefreshToken.user_id == user.id).values(revoked=True))
    event(db, user, "account.password_changed", user.id)
    return tokens(db, user)


@router.get("/staff")
def list_staff(user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "SUPER_ADMIN", "SCHOOL_ADMIN")
    query = select(User).where(User.role.in_(["TEACHER", "SCHOOL_ADMIN"]))
    if user.role == "SCHOOL_ADMIN":
        schools = select(School.id).where(School.owner_id == user.id)
        query = query.join(StaffProfile, StaffProfile.user_id == User.id).where(
            StaffProfile.school_id.in_(schools)
        )
    return [staff_output(db, row) for row in db.scalars(query.order_by(User.created_at.desc()).limit(100))]


@router.get("/staff/schools")
def schools(user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "SUPER_ADMIN", "SCHOOL_ADMIN")
    query = select(School)
    if user.role != "SUPER_ADMIN":
        query = query.where(School.owner_id == user.id)
    return [{"id": s.id, "name": s.name} for s in db.scalars(query.limit(100))]


@router.post("/staff", status_code=201)
def create_staff(body: StaffIn, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "SUPER_ADMIN")
    limit("staff-create:" + user.id, 30, 3600)
    if db.scalar(
        select(User.id).where(or_(User.login == body.login.lower(), User.email == body.email.lower()))
    ):
        raise HTTPException(409, "Bunday login yoki email mavjud")
    school = db.get(School, body.school_id) if body.school_id else None
    if body.role == "TEACHER" and not school:
        raise HTTPException(422, "O‘qituvchi uchun maktab tanlang")
    if body.role == "SCHOOL_ADMIN" and (school or not body.school_name):
        raise HTTPException(422, "Yangi admin uchun maktab nomini kiriting")
    target = User(
        login=body.login.lower(),
        email=body.email.lower(),
        name=body.name,
        password_hash=hasher.hash(body.password),
        role=body.role,
        must_change_password=True,
    )
    db.add(target)
    db.flush()
    if body.role == "SCHOOL_ADMIN":
        school = School(name=body.school_name, owner_id=target.id)
        db.add(school)
        db.flush()
    db.add(StaffProfile(user_id=target.id, school_id=school.id, created_by=user.id))
    role = db.scalar(select(Role).where(Role.name == body.role))
    db.add(UserRole(user_id=target.id, role_id=role.id))
    db.add(
        Notification(
            user_id=target.id,
            title="Hisobingiz yaratildi",
            body="Avval vaqtinchalik parolni yangilang. Keyin Telegram yoki qurilma passkey orqali kirishni sozlang.",
        )
    )
    db.add(
        Notification(user_id=user.id, title="Xodim hisobi yaratildi", body=target.name + " — " + body.role)
    )
    event(db, user, "staff.created", target.id)
    db.flush()
    return staff_output(db, target)


@router.put("/staff/{ident}/state")
def staff_state(
    ident: str, body: StaffState, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    require(user, "SUPER_ADMIN")
    target = db.get(User, ident)
    if not target or target.role not in ("TEACHER", "SCHOOL_ADMIN"):
        raise HTTPException(404, "Xodim topilmadi")
    target.active = body.active
    target.auth_epoch += 1
    db.execute(update(RefreshToken).where(RefreshToken.user_id == target.id).values(revoked=True))
    event(db, user, "staff.state_changed", target.id)
    return staff_output(db, target)


@router.post("/staff/announcements", status_code=201)
def announce(body: Announcement, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "SUPER_ADMIN", "SCHOOL_ADMIN")
    allowed = {row["id"] for row in list_staff(user, db)}
    if any(ident not in allowed for ident in body.recipient_ids):
        raise HTTPException(403, "Qabul qiluvchi sizning vakolatingizdan tashqarida")
    for ident in set(body.recipient_ids):
        db.add(Notification(user_id=ident, title=body.title, body=body.body))
    event(db, user, "staff.announcement", user.id)
    return {"sent": len(set(body.recipient_ids)), "channel": "in_app"}


@router.post("/auth/telegram/link/start")
def link_start(body: PasswordProof, user=Depends(current_user), db=Depends(get_db, scope="function")):
    staff(user)
    limit("credential-enroll:" + user.id, 10, 3600)
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Parol noto‘g‘ri")
    if not settings.telegram_token:
        raise HTTPException(503, "Telegram bot serverda sozlanmagan")
    limit("tg-link:" + user.id, 5, 3600)
    row, state, verifier = issue(db, user, "TG_LINK")
    return {
        "challenge_id": row.id,
        "verifier": verifier,
        "deep_link": f"https://t.me/{settings.telegram_username}?start=link_{state}",
        "expires_in": 300,
    }


@router.post("/auth/telegram/login/start", dependencies=[Depends(auth_limit)])
def login_start(body: LoginName, db=Depends(get_db, scope="function")):
    if not settings.telegram_token:
        raise HTTPException(503, "Telegram bot serverda sozlanmagan")
    user = find_login(db, body.login)
    identity = (
        db.scalar(select(TelegramIdentity).where(TelegramIdentity.user_id == user.id)) if user else None
    )
    if not user or not user.active or user.role not in STAFF or not identity:
        raise HTTPException(401, "Telegram orqali kirish mavjud emas. Avval hisob va Telegramni bog‘lang.")
    limit("tg-login:" + user.id, 5, 300)
    row, state, verifier = issue(db, user, "TG_LOGIN")
    return {
        "challenge_id": row.id,
        "verifier": verifier,
        "deep_link": f"https://t.me/{settings.telegram_username}?start=login_{state}",
        "expires_in": 300,
    }


@router.post("/auth/telegram/status", dependencies=[Depends(auth_limit)])
def status(body: ChallengeProof, db=Depends(get_db, scope="function")):
    row = db.get(AuthChallenge, body.challenge_id)
    if not row or row.kind not in ("TG_LOGIN", "TG_LINK"):
        raise HTTPException(401, "So‘rov topilmadi")
    validate(row, body.verifier, row.kind)
    return {"delivered": row.delivered, "expires_in": max(0, int((row.expires_at - now()).total_seconds()))}


@router.post("/auth/telegram/link/finish")
def link_finish(body: LinkProof, user=Depends(current_user), db=Depends(get_db, scope="function")):
    staff(user)
    row = lock_challenge(db, body.challenge_id)
    validate(row, body.verifier, "TG_LINK")
    if row.user_id != user.id or not verify_password(body.password, user.password_hash):
        failed(db, row)
    if not row.delivered:
        raise HTTPException(409, "Avval botdagi Start tugmasini bosing")
    tg_id = row.payload["telegram_user_id"]
    existing = db.scalar(select(TelegramIdentity).where(TelegramIdentity.telegram_user_id == tg_id))
    if existing and existing.user_id != user.id:
        raise HTTPException(409, "Bu Telegram boshqa hisobga bog‘langan")
    identity = db.scalar(select(TelegramIdentity).where(TelegramIdentity.user_id == user.id))
    if not identity:
        identity = TelegramIdentity(user_id=user.id, telegram_user_id=tg_id, chat_id=row.payload["chat_id"])
        db.add(identity)
    identity.telegram_user_id, identity.chat_id = tg_id, row.payload["chat_id"]
    db.execute(
        update(AuthChallenge)
        .where(AuthChallenge.user_id == user.id, AuthChallenge.id != row.id)
        .values(consumed=True)
    )
    row.consumed = True
    event(db, user, "auth.telegram_linked", user.id)
    return {"linked": True}


@router.post("/auth/telegram/login/finish", response_model=TokenOut, dependencies=[Depends(auth_limit)])
def login_finish(body: OtpProof, db=Depends(get_db, scope="function")):
    row = lock_challenge(db, body.challenge_id)
    validate(row, body.verifier, "TG_LOGIN")
    if (
        not row.delivered
        or not row.code_hash
        or not hmac.compare_digest(row.code_hash, otp_hash(row, body.code))
    ):
        failed(db, row)
    user = db.get(User, row.user_id)
    if not user.active or user.role not in STAFF:
        raise HTTPException(401, "Hisob yopilgan")
    row.consumed = True
    event(db, user, "auth.telegram_login", user.id)
    return tokens(db, user)


@router.post("/telegram/webhook")
def webhook(
    update_body: dict,
    x_telegram_bot_api_secret_token: str = Header(default=""),
    db=Depends(get_db, scope="function"),
):
    if not settings.telegram_webhook_secret or not hmac.compare_digest(
        settings.telegram_webhook_secret, x_telegram_bot_api_secret_token
    ):
        raise HTTPException(403, "Webhook tasdiqlanmadi")
    process_update(db, update_body)
    return {"ok": True}


@router.get("/auth/telegram/me")
def telegram_me(user=Depends(current_user), db=Depends(get_db, scope="function")):
    staff(user)
    row = db.scalar(select(TelegramIdentity).where(TelegramIdentity.user_id == user.id))
    return {"linked": bool(row), "notifications_enabled": bool(row and row.notifications_enabled)}


@router.put("/auth/telegram/notifications")
def telegram_notifications(
    body: TelegramPreference, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    staff(user)
    row = db.scalar(select(TelegramIdentity).where(TelegramIdentity.user_id == user.id))
    if not row:
        raise HTTPException(409, "Avval Telegramni bog‘lang")
    row.notifications_enabled = body.enabled
    return {"enabled": row.notifications_enabled}


@router.post("/auth/passkeys/register/options")
def registration_options(
    body: PasswordProof, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    staff(user)
    limit("credential-enroll:" + user.id, 10, 3600)
    if not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Parol noto‘g‘ri")
    if len(list(db.scalars(select(Passkey.id).where(Passkey.user_id == user.id)))) >= 10:
        raise HTTPException(409, "Hisobda ko‘pi bilan 10 qurilma kaliti bo‘lishi mumkin")
    options = generate_registration_options(
        rp_id=settings.passkey_rp_id,
        rp_name="SMART STUDY CONTROL",
        user_id=user.id.encode(),
        user_name=user.login or user.email,
        user_display_name=user.name,
        authenticator_selection=AuthenticatorSelectionCriteria(
            authenticator_attachment=AuthenticatorAttachment.PLATFORM,
            user_verification=UserVerificationRequirement.REQUIRED,
        ),
        exclude_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(k.credential_id))
            for k in db.scalars(select(Passkey).where(Passkey.user_id == user.id))
        ],
    )
    row, _, verifier = issue(db, user, "PASSKEY_REG", {"challenge": bytes_to_base64url(options.challenge)})
    return {"challenge_id": row.id, "verifier": verifier, "options": json.loads(options_to_json(options))}


@router.post("/auth/passkeys/register/verify")
def registration_verify(body: PasskeyProof, user=Depends(current_user), db=Depends(get_db, scope="function")):
    staff(user)
    row = lock_challenge(db, body.challenge_id)
    validate(row, body.verifier, "PASSKEY_REG")
    if row.user_id != user.id:
        failed(db, row)
    try:
        result = verify_registration_response(
            credential=body.credential,
            expected_challenge=base64url_to_bytes(row.payload["challenge"]),
            expected_rp_id=settings.passkey_rp_id,
            expected_origin=settings.passkey_origin,
            require_user_verification=True,
        )
    except Exception:
        failed(db, row)
    db.add(
        Passkey(
            user_id=user.id,
            credential_id=bytes_to_base64url(result.credential_id),
            public_key=bytes_to_base64url(result.credential_public_key),
            sign_count=result.sign_count,
            label=body.label,
        )
    )
    row.consumed = True
    event(db, user, "auth.passkey_registered", user.id)
    return {"registered": True, "verification": "platform_user_verification", "face_images_stored": False}


@router.post("/auth/passkeys/login/options", dependencies=[Depends(auth_limit)])
def authentication_options(body: LoginName, db=Depends(get_db, scope="function")):
    user = find_login(db, body.login)
    keys = list(db.scalars(select(Passkey).where(Passkey.user_id == user.id))) if user else []
    if not user or not user.active or user.role not in STAFF or not keys:
        raise HTTPException(401, "Bu hisobda qurilma kaliti yo‘q")
    options = generate_authentication_options(
        rp_id=settings.passkey_rp_id,
        user_verification=UserVerificationRequirement.REQUIRED,
        allow_credentials=[
            PublicKeyCredentialDescriptor(id=base64url_to_bytes(k.credential_id)) for k in keys
        ],
    )
    row, _, verifier = issue(db, user, "PASSKEY_LOGIN", {"challenge": bytes_to_base64url(options.challenge)})
    return {"challenge_id": row.id, "verifier": verifier, "options": json.loads(options_to_json(options))}


@router.post("/auth/passkeys/login/verify", response_model=TokenOut, dependencies=[Depends(auth_limit)])
def authentication_verify(body: PasskeyProof, db=Depends(get_db, scope="function")):
    row = lock_challenge(db, body.challenge_id)
    validate(row, body.verifier, "PASSKEY_LOGIN")
    key = db.scalar(
        select(Passkey).where(
            Passkey.credential_id == body.credential.get("id"), Passkey.user_id == row.user_id
        )
    )
    if not key:
        failed(db, row)
    db.execute(update(Passkey).where(Passkey.id == key.id).values(updated_at=now()))
    db.refresh(key)
    try:
        result = verify_authentication_response(
            credential=body.credential,
            expected_challenge=base64url_to_bytes(row.payload["challenge"]),
            expected_rp_id=settings.passkey_rp_id,
            expected_origin=settings.passkey_origin,
            credential_public_key=base64url_to_bytes(key.public_key),
            credential_current_sign_count=key.sign_count,
            require_user_verification=True,
        )
    except Exception:
        failed(db, row)
    user = db.get(User, row.user_id)
    if not user.active or user.role not in STAFF:
        raise HTTPException(401, "Hisob yopilgan")
    key.sign_count = result.new_sign_count
    row.consumed = True
    event(db, user, "auth.passkey_login", user.id)
    return tokens(db, user)


@router.get("/auth/passkeys")
def passkeys(user=Depends(current_user), db=Depends(get_db, scope="function")):
    staff(user)
    return [
        {"id": k.id, "label": k.label} for k in db.scalars(select(Passkey).where(Passkey.user_id == user.id))
    ]


@router.delete("/auth/passkeys/{ident}")
def remove_passkey(
    ident: str, body: PasswordProof, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    staff(user)
    key = db.get(Passkey, ident)
    if not key or key.user_id != user.id or not verify_password(body.password, user.password_hash):
        raise HTTPException(403, "Ruxsat yo‘q yoki parol noto‘g‘ri")
    db.delete(key)
    event(db, user, "auth.passkey_removed", ident)
    return {"removed": True}


@router.get("/operations/integrations")
def integrations(user=Depends(current_user)):
    require(user, "SUPER_ADMIN")
    return {
        "telegram_configured": bool(settings.telegram_token),
        "telegram_username": settings.telegram_username,
        "ai_provider": settings.ai_provider,
        "huggingface_configured": bool(settings.hf_token),
        "hf_model": settings.hf_model,
        "hf_guard_model": settings.hf_guard_model,
        "groq_configured": bool(settings.groq_key),
        "groq_model": settings.groq_model,
        "deepseek_configured": bool(settings.deepseek_key),
        "deepseek_model": settings.deepseek_model,
        "passkey_origin": settings.passkey_origin,
        "passkey_rp_id": settings.passkey_rp_id,
    }


@router.post("/operations/integrations/check")
def integration_check(user=Depends(current_user)):
    import httpx

    require(user, "SUPER_ADMIN")
    limit("integration-check:" + user.id, 5, 300)
    targets = [
        ("groq", "https://api.groq.com/openai/v1/models", settings.groq_key),
        ("deepseek", "https://api.deepseek.com/models", settings.deepseek_key),
        ("huggingface", "https://huggingface.co/api/whoami-v2", settings.hf_token),
    ]
    results = {}
    with httpx.Client(timeout=8) as client:
        for name, url, key in targets:
            if not key:
                results[name] = {"configured": False}
                continue
            try:
                response = client.get(url, headers={"Authorization": "Bearer " + key})
                results[name] = {
                    "configured": True,
                    "http_status": response.status_code,
                    "accepted": response.status_code == 200,
                    "inference_checked": False,
                }
            except httpx.HTTPError:
                results[name] = {"configured": True, "accepted": False, "error": "transport_unavailable"}
    return results
