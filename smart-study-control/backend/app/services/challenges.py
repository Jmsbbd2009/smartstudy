import hmac
import hashlib
import secrets
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import select, update
from app.models.entities import AuthChallenge, now
from app.security.auth import digest
from app.core.config import settings


def issue(db, user, kind, payload=None):
    state, verifier = secrets.token_urlsafe(24), secrets.token_urlsafe(32)
    row = AuthChallenge(
        user_id=user.id,
        kind=kind,
        state_hash=digest(state),
        verifier_hash=digest(verifier),
        expires_at=now() + timedelta(minutes=5),
        payload=payload or {},
    )
    db.add(row)
    db.flush()
    return row, state, verifier


def lock_challenge(db, ident):
    db.execute(update(AuthChallenge).where(AuthChallenge.id == ident).values(updated_at=now()))
    return db.scalar(
        select(AuthChallenge).where(AuthChallenge.id == ident).execution_options(populate_existing=True)
    )


def validate(row, verifier, kind):
    if (
        not row
        or row.kind != kind
        or row.consumed
        or row.expires_at <= now()
        or row.attempts >= 5
        or not hmac.compare_digest(row.verifier_hash, digest(verifier))
    ):
        raise HTTPException(401, "Tasdiqlash muddati tugagan yoki noto‘g‘ri")


def otp_hash(row, code):
    return hmac.new(settings.secret.encode(), (row.id + ":" + code).encode(), hashlib.sha256).hexdigest()


def failed(db, row):
    row.attempts = min(5, row.attempts + 1)
    db.commit()  # Persist brute-force limits even though an error response follows.
    raise HTTPException(401, "Tasdiqlash kodi yoki kalit noto‘g‘ri")
