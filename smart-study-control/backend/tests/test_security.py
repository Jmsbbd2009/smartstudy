from app.models.entities import RefreshToken
from sqlalchemy import select


def test_public_registration_rejects_privileged_role(context):
    c, _ = context
    r = c.post(
        "/api/v1/auth/register",
        json={"email": "x@example.test", "name": "X", "password": "long-password-123", "role": "SUPER_ADMIN"},
    )
    assert r.status_code == 422
    assert "long-password-123" not in r.text


def test_register_login_logout_and_rotation(context):
    c, _ = context
    data = {"email": "s@example.test", "name": "Ali", "password": "long-password-123", "role": "STUDENT"}
    r = c.post("/api/v1/auth/register", json=data)
    assert r.status_code == 201
    initial = r.json()
    rotated = c.post("/api/v1/auth/refresh", json={"refresh_token": initial["refresh_token"]})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != initial["refresh_token"]
    assert c.post("/api/v1/auth/refresh", json={"refresh_token": initial["refresh_token"]}).status_code == 401
    assert (
        c.post("/api/v1/auth/refresh", json={"refresh_token": rotated.json()["refresh_token"]}).status_code
        == 401
    )
    assert (
        c.post("/api/v1/auth/login", json={"email": data["email"], "password": "wrong-password"}).status_code
        == 401
    )


def test_unlinked_parent_and_teacher_cannot_see_household(homework):
    c, _, p, a, s = homework
    for name in ["parent2", "teacher3", "super_admin5"]:
        assert c.get("/api/v1/assignments/" + a["id"], headers=p[name]["headers"]).status_code == 403
        assert (
            c.get(
                "/api/v1/rewards/wallet", params={"child_id": p["student0"]["id"]}, headers=p[name]["headers"]
            ).status_code
            == 403
        )
        assert (
            c.post("/api/v1/submissions/" + s["id"] + "/approve", headers=p[name]["headers"]).status_code
            == 403
        )
    assert (
        c.post("/api/v1/submissions/" + s["id"] + "/approve", headers=p["student0"]["headers"]).status_code
        == 403
    )


def test_link_invite_single_use_and_multiple_guardians(people):
    c, _, p = people
    student = p["student0"]
    code = c.post("/api/v1/families/invite", headers=student["headers"]).json()["code"]
    body = {"code": code, "guardian_consent": True}
    assert (
        c.post("/api/v1/families/link-child", json=body, headers=p["parent2"]["headers"]).status_code == 200
    )
    assert (
        c.post("/api/v1/families/link-child", json=body, headers=p["parent1"]["headers"]).status_code == 400
    )
    for name in ["parent1", "parent2"]:
        assert c.get("/api/v1/families/children", headers=p[name]["headers"]).json()[0]["id"] == student["id"]


def test_teacher_academic_scope_excludes_device_and_wallet(people):
    c, _, p = people
    t = p["teacher3"]["headers"]
    s = p["student0"]["headers"]
    room = c.post("/api/v1/classrooms", headers=t, json={"name": "8A"}).json()
    code = c.post("/api/v1/classrooms/" + room["id"] + "/invite", headers=t).json()["code"]
    assert c.post("/api/v1/classrooms/join", headers=s, json={"code": code}).status_code == 200
    a = c.post(
        "/api/v1/assignments",
        headers=t,
        json={
            "student_id": p["student0"]["id"],
            "classroom_id": room["id"],
            "title": "Quiz",
            "subject": "IT",
            "reward_minutes": 0,
        },
    )
    assert a.status_code == 201, a.text
    report = c.get("/api/v1/reports/weekly", params={"child_id": p["student0"]["id"]}, headers=t).json()
    assert report["assigned"] == 1
    assert "access_minutes_reserved" not in report and "focus_seconds" not in report
    device = c.post("/api/v1/devices", headers=s, json={"name": "Test"}).json()
    assert c.get("/api/v1/devices/" + device["id"] + "/policies", headers=t).status_code == 403
    assert c.post("/api/v1/devices/" + device["id"] + "/authorize", headers=t).status_code == 403


def test_draft_is_private_and_guardian_controls_teacher_reward(people):
    c, _, p = people
    ph = p["parent1"]["headers"]
    sh = p["student0"]["headers"]
    row = c.post(
        "/api/v1/assignments",
        headers=ph,
        json={"student_id": p["student0"]["id"], "title": "Draft", "subject": "IT", "status": "DRAFT"},
    ).json()
    assert c.get("/api/v1/assignments", headers=sh).json() == []
    assert c.get("/api/v1/assignments/" + row["id"], headers=sh).status_code == 403
    assert c.post("/api/v1/assignments/" + row["id"] + "/publish", headers=ph).json()["status"] == "ASSIGNED"
    assert c.post("/api/v1/assignments/" + row["id"] + "/start", headers=sh).json()["status"] == "IN_PROGRESS"
    assert (
        c.put(
            "/api/v1/assignments/" + row["id"] + "/reward-policy",
            headers=p["teacher3"]["headers"],
            json={"reward_minutes": 30},
        ).status_code
        == 403
    )
    assert (
        c.put(
            "/api/v1/assignments/" + row["id"] + "/reward-policy", headers=ph, json={"reward_minutes": 30}
        ).json()["reward_minutes"]
        == 30
    )


def test_large_declared_or_chunked_bodies_are_rejected_before_processing(context):
    c, _ = context
    r = c.post(
        "/api/v1/auth/login",
        content=b"{}",
        headers={
            "Content-Length": str(13 * 1024 * 1024),
            "Content-Type": "application/json",
            "Origin": "http://localhost:5173",
        },
    )
    assert r.status_code == 413
    assert r.headers["access-control-allow-origin"] == "http://localhost:5173"

    def chunks():
        yield b'{"email":"x@x.test","password":"'
        for _ in range(13):
            yield b"x" * (1024 * 1024)
        yield b'"}'

    r = c.post("/api/v1/auth/login", content=chunks(), headers={"Content-Type": "application/json"})
    assert r.status_code == 413
