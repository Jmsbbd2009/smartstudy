import hashlib
import secrets
from datetime import timedelta
import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerificationError, InvalidHashError
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from app.core.config import settings
from app.db.session import get_db
from app.models.entities import User, RefreshToken, now, uid

hasher = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
bearer = HTTPBearer(auto_error=False)


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def verify_password(raw, hashed):
    try:
        return hasher.verify(hashed, raw)
    except (VerificationError, InvalidHashError):
        return False


def tokens(db, user, family=None):
    raw = secrets.token_urlsafe(48)
    db.add(
        RefreshToken(
            user_id=user.id, digest=digest(raw), family=family or uid(), expires_at=now() + timedelta(days=30)
        )
    )
    access = jwt.encode(
        {
            "sub": user.id,
            "ver": user.auth_epoch,
            "type": "access",
            "iat": now(),
            "exp": now() + timedelta(minutes=15),
            "jti": uid(),
            "iss": "smart-study-control",
            "aud": "study-clients",
        },
        settings.secret,
        algorithm="HS256",
    )
    return {
        "access_token": access,
        "refresh_token": raw,
        "token_type": "bearer",
        "expires_in": 900,
        "user": {
            "id": user.id,
            "name": user.name,
            "role": user.role,
            "email": user.email,
            "login": user.login,
            "must_change_password": user.must_change_password,
        },
    }


def current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db=Depends(get_db, scope="function"),
):
    if not credentials:
        raise HTTPException(401, "Authentication required")
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.secret,
            algorithms=["HS256"],
            audience="study-clients",
            issuer="smart-study-control",
        )
        if payload.get("type") != "access":
            raise jwt.InvalidTokenError()
        user = db.get(User, payload["sub"])
    except (jwt.InvalidTokenError, KeyError):
        raise HTTPException(401, "Invalid or expired token")
    if not user or not user.active or payload.get("ver", 0) != user.auth_epoch:
        raise HTTPException(401, "Account unavailable")
    if user.must_change_password and request.url.path not in {
        "/api/v1/auth/password",
        "/api/v1/auth/logout",
        "/api/v1/users/me",
    }:
        raise HTTPException(403, "Avval vaqtinchalik parolni yangilang")
    return user


def require(user, *roles):
    if user.role not in roles:
        raise HTTPException(403, "Role not permitted")
