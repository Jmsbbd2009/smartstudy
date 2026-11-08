"""Own-account session controls. No private device/location metadata is inferred."""
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, update
from app.db.session import get_db
from app.models.entities import RefreshToken, AuditEvent, now
from app.security.auth import current_user

router = APIRouter(prefix="/api/v1/profile", tags=["profile"])


@router.get("/sessions")
def sessions(request: Request, user=Depends(current_user), db=Depends(get_db, scope="function")):
    rows = db.scalars(select(RefreshToken).where(
        RefreshToken.user_id == user.id, RefreshToken.revoked.is_(False),
        RefreshToken.expires_at > now(),
    ).order_by(RefreshToken.created_at.desc()).limit(100))
    return [{"id": r.family, "current": r.family == request.state.session_id,
             "renewed_at": r.created_at.isoformat() + "Z"} for r in rows]


@router.post("/sessions/terminate-others")
def terminate_others(request: Request, user=Depends(current_user), db=Depends(get_db, scope="function")):
    if not request.state.session_id:
        raise HTTPException(409, "Seansni aniqlash uchun qayta kiring")
    db.execute(update(RefreshToken).where(
        RefreshToken.user_id == user.id,
        RefreshToken.family != request.state.session_id,
    ).values(revoked=True))
    db.add(AuditEvent(actor_id=user.id, action="session.terminate_others", resource_id=user.id, details={}))
    return {"ok": True}


@router.delete("/sessions/{session_id}")
def terminate(session_id: str, request: Request, user=Depends(current_user), db=Depends(get_db, scope="function")):
    row = db.scalar(select(RefreshToken.id).where(
        RefreshToken.user_id == user.id, RefreshToken.family == session_id,
    ).limit(1))
    if not row:
        raise HTTPException(404, "Seans topilmadi")
    if session_id == request.state.session_id:
        raise HTTPException(409, "Joriy seans uchun hisobdan chiqish tugmasini ishlating")
    db.execute(update(RefreshToken).where(
        RefreshToken.user_id == user.id, RefreshToken.family == session_id,
    ).values(revoked=True))
    db.add(AuditEvent(actor_id=user.id, action="session.terminate", resource_id=session_id, details={}))
    return {"ok": True}


@router.get("/assessment")
def assessment(user=Depends(current_user), db=Depends(get_db, scope="function")):
    from app.security.assessment import assessment_active

    return {"active": assessment_active(db, user.id)}
