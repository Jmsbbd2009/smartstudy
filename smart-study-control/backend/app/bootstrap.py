"""Idempotent attended bootstrap. Never ships or prints a privileged password."""

import os
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.entities import User, Role, UserRole
from app.security.auth import hasher


def bootstrap(db, login, password):
    login = "".join(login.lower().split())
    if not login or len(password) < 10:
        raise ValueError("Bootstrap needs a login and temporary password of at least 10 characters")
    existing = db.scalar(select(User).where(User.login == login))
    if existing:
        if existing.role != "SUPER_ADMIN":
            raise ValueError("Login belongs to another role")
        return False
    # A legacy email-based super admin must be handled explicitly, never duplicated silently.
    if db.scalar(select(User.id).where(User.role == "SUPER_ADMIN")):
        raise ValueError("A super admin exists; use attended account recovery")
    user = User(
        login=login,
        email=login + "@bootstrap.invalid",
        name="Super admin",
        role="SUPER_ADMIN",
        password_hash=hasher.hash(password),
        must_change_password=True,
    )
    db.add(user)
    db.flush()
    role = db.scalar(select(Role).where(Role.name == "SUPER_ADMIN"))
    if not role:
        raise ValueError("Run migrations before bootstrap")
    db.add(UserRole(user_id=user.id, role_id=role.id))
    return True


def main():
    login = os.getenv("BOOTSTRAP_SUPERADMIN_LOGIN", "")
    password = os.getenv("BOOTSTRAP_SUPERADMIN_PASSWORD", "")
    if not login or not password:
        raise SystemExit("Set server-only BOOTSTRAP_SUPERADMIN_LOGIN/PASSWORD")
    with SessionLocal.begin() as db:
        created = bootstrap(db, login, password)
    print(
        "Super admin created; password change is required"
        if created
        else "Existing super admin left unchanged"
    )


if __name__ == "__main__":
    main()
