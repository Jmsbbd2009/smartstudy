from datetime import datetime, timezone
import pytest
from app.services.policy import decision, window_active
from test_learning_rewards import device


def test_priority_and_midnight_window():
    instant = datetime(2026, 10, 30, 17, tzinfo=timezone.utc)  # Friday 22:00 Tashkent
    policy = {
        "blocked_packages": ["com.game.app"],
        "essential_packages": ["com.phone.app"],
        "safety_packages": ["com.game.app"],
        "timezone": "Asia/Tashkent",
        "default_blocked": True,
        "sleep": [{"days": [5], "start_minute": 1260, "end_minute": 420}],
    }
    assert decision(policy, "com.phone.app", instant) == "ESSENTIAL"
    assert decision(policy, "com.game.app", instant, True) == "SAFETY"
    policy["override_until"] = "2026-10-31T00:00:00Z"
    assert decision(policy, "com.game.app", instant, True) == "SAFETY"
    policy["safety_packages"] = []
    assert decision(policy, "com.game.app", instant, True) == "OVERRIDE"
    policy.pop("override_until")
    assert decision(policy, "com.game.app", instant, True) == "SLEEP"
    assert decision(policy, "com.game.app", datetime(2026, 10, 30, 23, tzinfo=timezone.utc), True) == "SLEEP"
    assert decision(policy, "com.game.app", datetime(2026, 10, 31, 4, tzinfo=timezone.utc), True) == "EARNED"
    policy["sleep"] = []
    policy["study"] = [{"days": [5], "start_minute": 1200, "end_minute": 1400}]
    assert decision(policy, "com.game.app", instant, True) == "STUDY"
    policy["study"] = []
    assert decision(policy, "com.game.app", instant) == "DEFAULT_BLOCK"


def test_policy_versions_and_deprovision(people):
    c, _, p = people
    d = device(c, p)
    ph = p["parent1"]["headers"]
    sh = p["student0"]["headers"]
    path = "/api/v1/devices/" + d["id"]
    assert c.put(path + "/policies", headers=ph, json={"expected_version": 0}).status_code == 409
    assert c.post(path + "/sync", headers=sh, json={"applied_version": 2}).status_code == 409
    assert (
        c.post(path + "/sync", headers=sh, json={"applied_version": 1, "device_owner": False}).status_code
        == 200
    )
    assert c.post(path + "/deprovision", headers=ph).status_code == 200
    r = c.post(
        path + "/sync",
        headers=sh,
        json={"applied_version": 1, "cleanup_complete": True, "failures": ["com.game.app"]},
    )
    assert not r.json()["retired"]
    r = c.post(path + "/sync", headers=sh, json={"applied_version": 1, "cleanup_complete": True})
    assert r.json()["retired"]


def test_quiz_answers_hidden_until_completed(homework):
    c, _, p, a, s = homework
    ph = p["parent1"]["headers"]
    sh = p["student0"]["headers"]
    q = c.post(
        "/api/v1/quizzes",
        headers=ph,
        json={
            "assignment_id": a["id"],
            "title": "2+2",
            "validated": True,
            "questions": [
                {"prompt": "2+2?", "options": ["3", "4"], "answer": "4", "explanation": "2 va 2 yig‘indisi 4"}
            ],
        },
    ).json()
    detail = c.get("/api/v1/quizzes/" + q["id"], headers=sh).json()
    question = detail["questions"][0]
    assert "answer" not in question and "explanation" not in question
    assert c.post("/api/v1/quizzes/" + q["id"] + "/start", headers=sh).status_code == 200
    for _ in range(2):
        result = c.post(
            "/api/v1/quizzes/" + q["id"] + "/finish", headers=sh, json={"answers": {question["id"]: "4"}}
        )
        assert result.status_code == 200, result.text
        assert result.json()["score"] == 1 and result.json()["explanations"][0]["answer"] == "4"


def test_app_inventory_requires_guardian_authorization_and_stays_private(people):
    c, _, p = people
    sh = p["student0"]["headers"]
    ph = p["parent1"]["headers"]
    d = c.post("/api/v1/devices", headers=sh, json={"name": "Tablet"}).json()
    path = "/api/v1/devices/" + d["id"]
    body = {
        "applied_version": 0,
        "eligible_apps": [{"package": "com.instagram.android", "label": "Instagram"}],
    }
    assert c.post(path + "/sync", headers=sh, json=body).status_code == 403
    assert c.post(path + "/authorize", headers=ph).status_code == 200
    assert c.post(path + "/sync", headers=sh, json=body).json()["management_authorized"]
    devices = c.get("/api/v1/devices", headers=ph, params={"child_id": p["student0"]["id"]}).json()
    assert devices[0]["compliance"]["eligible_apps"][0]["label"] == "Instagram"
    assert (
        c.get(
            "/api/v1/devices", headers=p["teacher3"]["headers"], params={"child_id": p["student0"]["id"]}
        ).status_code
        == 403
    )
