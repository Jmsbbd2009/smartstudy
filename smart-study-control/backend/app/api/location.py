"""Visible, student-initiated, time-bounded location sharing. Never a teacher/admin feed."""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.db.session import get_db
from app.models.entities import LocationConsent, LocationShare, AuditEvent, Consent, now
from app.security.auth import current_user, require
from app.security.scope import academic, guardian
from app.security.rate_limit import limit
from app.services.rewards import locked_wallet
from app.schemas.access import LocationPolicy, LocationStart, LocationPoint

router = APIRouter(prefix="/api/v1/location", tags=["location"])


def erase(row, state):
    row.status = state
    row.latitude = row.longitude = row.accuracy_m = row.received_at = None


def current(db, child):
    rows = list(
        db.scalars(
            select(LocationShare)
            .where(LocationShare.child_id == child, LocationShare.status == "ACTIVE")
            .order_by(LocationShare.created_at.desc())
        )
    )
    active = None
    policy = db.scalar(select(LocationConsent).where(LocationConsent.child_id == child))
    for row in rows:
        from app.models.entities import User

        adult = db.get(User, row.consent_guardian_id)
        if (
            row.expires_at <= now()
            or not policy
            or not policy.enabled
            or not adult
            or not adult.active
            or not (guardian(db, adult, child) or (adult.role == "TEACHER" and academic(db, adult, child)))
        ):
            erase(row, "EXPIRED" if row.expires_at <= now() else "REVOKED")
        elif active is None:
            active = row
        else:
            erase(row, "SUPERSEDED")
    return active


def visible(row):
    fresh = bool(row.received_at and (now() - row.received_at).total_seconds() <= 90)
    return {
        "id": row.id,
        "active": True,
        "expires_at": row.expires_at.isoformat() + "Z",
        "latitude": row.latitude if fresh else None,
        "longitude": row.longitude if fresh else None,
        "accuracy_m": row.accuracy_m if fresh else None,
        "received_at": row.received_at.isoformat() + "Z" if row.received_at else None,
        "stale": not row.received_at or (now() - row.received_at).total_seconds() > 90,
        "notice": "Telefon bildirgan oxirgi joylashuv; GPS aniqligi va aloqa holatiga bog‘liq. Bu jonli kuzatilayotganlik kafolati emas.",
    }


@router.get("/children/{child}/consent")
def get_policy(child: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    if not guardian(db, user, child) and not (user.role == "TEACHER" and academic(db, user, child)) and not (user.role == "STUDENT" and user.id == child):
        raise HTTPException(403, "Faqat o‘quvchi, vakolatli oila yoki shu sinf o‘qituvchisi uchun")
    row = db.scalar(select(LocationConsent).where(LocationConsent.child_id == child))
    return {"enabled": bool(row and row.enabled), "max_minutes": row.max_minutes if row else 60}


@router.put("/children/{child}/consent")
def set_policy(
    child: str, body: LocationPolicy, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    if not guardian(db, user, child) and not (user.role == "TEACHER" and academic(db, user, child)):
        raise HTTPException(403, "Vakolatli oila yoki o‘quvchining sinf o‘qituvchisi bo‘lishi kerak")
    locked_wallet(db, child)
    row = db.scalar(select(LocationConsent).where(LocationConsent.child_id == child))
    if not row:
        row = LocationConsent(child_id=child, guardian_id=user.id)
        db.add(row)
    row.guardian_id = user.id
    row.enabled = body.enabled
    row.max_minutes = body.max_minutes
    db.add(
        Consent(actor_id=user.id, child_id=child, purpose="visible_location_sharing", granted=body.enabled)
    )
    db.add(
        AuditEvent(
            actor_id=user.id,
            action="location.consent_changed",
            resource_id=child,
            details={"enabled": body.enabled},
        )
    )
    if not body.enabled:
        for share in db.scalars(
            select(LocationShare).where(LocationShare.child_id == child, LocationShare.status == "ACTIVE")
        ):
            erase(share, "REVOKED")
    return {"enabled": row.enabled, "max_minutes": row.max_minutes}


@router.post("/shares", status_code=201)
def start(body: LocationStart, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    limit("location-start:" + user.id, 10, 3600)
    locked_wallet(db, user.id)
    policy = db.scalar(select(LocationConsent).where(LocationConsent.child_id == user.id))
    from app.models.entities import User

    adult = db.get(User, policy.guardian_id) if policy else None
    if not policy or not policy.enabled or not adult or not adult.active or not (guardian(db, adult, user.id) or (adult.role == "TEACHER" and academic(db, adult, user.id))):
        raise HTTPException(403, "Avval vakolatli oila yoki sinf o‘qituvchisi muddatli ulashishni yoqishi kerak")
    if body.minutes > policy.max_minutes:
        raise HTTPException(422, "Ota-ona belgilagan muddatdan oshdi")
    if current(db, user.id):
        raise HTTPException(409, "Ulashish allaqachon faol")
    row = LocationShare(
        child_id=user.id, consent_guardian_id=adult.id, expires_at=now() + timedelta(minutes=body.minutes)
    )
    db.add(row)
    db.flush()
    db.add(
        AuditEvent(
            actor_id=user.id, action="location.started", resource_id=row.id, details={"minutes": body.minutes}
        )
    )
    return visible(row)


@router.post("/shares/{ident}/point")
def point(ident: str, body: LocationPoint, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    limit("location-point:" + user.id, 12, 60)
    locked_wallet(db, user.id)
    row = current(db, user.id)
    if not row or row.id != ident:
        db.commit()
        raise HTTPException(409, "Ulashish tugagan yoki bekor qilingan")
    row.latitude, row.longitude, row.accuracy_m = body.latitude, body.longitude, body.accuracy_m
    row.received_at = now()
    return {"accepted": True, "expires_at": row.expires_at.isoformat() + "Z"}


@router.post("/shares/{ident}/stop")
def stop(ident: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    require(user, "STUDENT")
    locked_wallet(db, user.id)
    row = db.get(LocationShare, ident)
    if not row or row.child_id != user.id:
        raise HTTPException(403, "Boshqa foydalanuvchi ulashishi")
    erase(row, "STOPPED")
    db.add(AuditEvent(actor_id=user.id, action="location.stopped", resource_id=row.id, details={}))
    return {"stopped": True}


@router.get("/children/{child}/latest")
def latest(child: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    teacher_access = user.role == "TEACHER" and academic(db, user, child)
    if not guardian(db, user, child) and not teacher_access and not (user.role == "STUDENT" and child == user.id):
        raise HTTPException(403, "Joylashuv shu o‘quvchi, vakolatli oila va uning sinf o‘qituvchisigagina ochiq")
    row = current(db, child)
    if teacher_access:
        db.add(AuditEvent(actor_id=user.id, action="location.teacher_viewed", resource_id=child, details={"active": bool(row)}))
    return visible(row) if row else {"active": False, "latitude": None, "longitude": None}
