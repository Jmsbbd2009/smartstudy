import argparse
import getpass
from sqlalchemy import select
from app.db.session import SessionLocal
from app.models.entities import User, Wallet, Role, UserRole
from app.security.auth import hasher


def main():
    parser = argparse.ArgumentParser(description="Attended platform account provisioning")
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create-user")
    create.add_argument("--email", required=True)
    create.add_argument("--name", required=True)
    create.add_argument("--role", choices=["TEACHER", "SCHOOL_ADMIN", "SUPER_ADMIN"], required=True)
    args = parser.parse_args()
    password = getpass.getpass("New password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Password too short")
    with SessionLocal.begin() as db:
        if db.scalar(select(User.id).where(User.email == args.email.lower())):
            raise SystemExit("Account exists")
        user = User(
            email=args.email.lower(), name=args.name, role=args.role, password_hash=hasher.hash(password)
        )
        db.add(user)
        db.flush()
        role = db.scalar(select(Role).where(Role.name == args.role))
        db.add(UserRole(user_id=user.id, role_id=role.id))
    print("Authorized account created")


if __name__ == "__main__":
    main()
