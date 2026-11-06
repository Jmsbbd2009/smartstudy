import os

os.environ["JWT_SECRET"] = "unit-test-only-secret-0123456789abcdef0123456789"
os.environ["APP_ENV"] = "test"
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.db.session import Base, get_db
from app.main import app
from app.security import rate_limit
from app.models.entities import User, Role, UserRole, Wallet
from app.security.auth import hasher


@pytest.fixture
def context(tmp_path, monkeypatch):
    url = os.getenv("TEST_DATABASE_URL", "sqlite:///" + str(tmp_path / "test.db"))
    engine = create_engine(
        url, connect_args={"check_same_thread": False, "timeout": 30} if url.startswith("sqlite") else {}
    )

    @event.listens_for(engine, "connect")
    def pragma(c, _):
        if url.startswith("sqlite"):
            c.execute("PRAGMA foreign_keys=ON")
            c.execute("PRAGMA journal_mode=WAL")

    if not url.startswith("sqlite"):
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)

    def db_dep():
        with factory() as db:
            try:
                yield db
                db.commit()
            except Exception:
                db.rollback()
                raise

    app.dependency_overrides[get_db] = db_dep
    monkeypatch.setattr(rate_limit, "limit", lambda *a, **kw: None)
    with factory.begin() as db:
        for name in ["STUDENT", "PARENT", "TEACHER", "SCHOOL_ADMIN", "SUPER_ADMIN"]:
            db.add(Role(name=name))
    with TestClient(app) as client:
        yield client, factory
    app.dependency_overrides.clear()
    engine.dispose()


@pytest.fixture
def people(context):
    client, factory = context
    result = {}
    for role in ["STUDENT", "PARENT", "PARENT", "TEACHER", "TEACHER", "SUPER_ADMIN"]:
        name = role.lower() + str(len(result))
        with factory.begin() as db:
            u = User(
                email=name + "@example.test",
                name=name,
                role=role,
                password_hash=hasher.hash("Strong-password-123"),
            )
            db.add(u)
            db.flush()
            ident = u.id
            if role == "STUDENT":
                db.add(Wallet(student_id=u.id))
        login = client.post(
            "/api/v1/auth/login", json={"email": name + "@example.test", "password": "Strong-password-123"}
        ).json()
        result[name] = {
            "id": ident,
            "headers": {"Authorization": "Bearer " + login["access_token"]},
            "tokens": login,
        }
    student = result["student0"]
    parent = result["parent1"]
    code = client.post("/api/v1/families/invite", headers=student["headers"]).json()["code"]
    assert (
        client.post(
            "/api/v1/families/link-child",
            headers=parent["headers"],
            json={"code": code, "guardian_consent": True},
        ).status_code
        == 200
    )
    return client, factory, result


@pytest.fixture
def homework(people):
    client, factory, p = people
    body = {
        "student_id": p["student0"]["id"],
        "title": "Kasrlar",
        "subject": "Matematika",
        "reward_minutes": 30,
        "answer_key": {"1": "4"},
    }
    a = client.post("/api/v1/assignments", headers=p["parent1"]["headers"], json=body)
    assert a.status_code == 201, a.text
    sub = client.post(
        "/api/v1/assignments/" + a.json()["id"] + "/submit",
        headers={**p["student0"]["headers"], "Idempotency-Key": "submission-test-0001"},
        json={"text": "2+2=4", "answers": {"1": "4"}},
    )
    assert sub.status_code == 201, sub.text
    return client, factory, p, a.json(), sub.json()
