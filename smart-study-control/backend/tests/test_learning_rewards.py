from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from sqlalchemy import select
from app.models.entities import Wallet, RewardTransaction, UnlockSession, now, FocusSession


def approve(c, p, s):
    r = c.post("/api/v1/submissions/" + s["id"] + "/approve", headers=p["parent1"]["headers"])
    assert r.status_code == 200, r.text


def device(c, p):
    sh = p["student0"]["headers"]
    ph = p["parent1"]["headers"]
    d = c.post("/api/v1/devices", json={"name": "Tablet"}, headers=sh).json()
    assert c.post("/api/v1/devices/" + d["id"] + "/authorize", headers=ph).status_code == 200
    r = c.put(
        "/api/v1/devices/" + d["id"] + "/policies",
        headers=ph,
        json={"expected_version": 0, "blocked_packages": ["com.instagram.android"], "default_blocked": True},
    )
    assert r.status_code == 200, r.text
    return d


def test_duplicate_submission_and_approval_only_credit_once(homework):
    c, db, p, a, s = homework
    headers = {**p["student0"]["headers"], "Idempotency-Key": "submission-test-0001"}
    duplicate = c.post(
        "/api/v1/assignments/" + a["id"] + "/submit",
        headers=headers,
        json={"text": "2+2=4", "answers": {"1": "4"}},
    )
    assert duplicate.json()["id"] == s["id"]
    conflict = c.post("/api/v1/assignments/" + a["id"] + "/submit", headers=headers, json={"text": "changed"})
    assert conflict.status_code == 409
    approve(c, p, s)
    approve(c, p, s)
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 30
    with db() as session:
        assert len(list(session.scalars(select(RewardTransaction)))) == 1


def test_approval_revocation_and_reapproval_cannot_mint(homework):
    c, db, p, a, s = homework
    approve(c, p, s)
    assert (
        c.post(
            "/api/v1/submissions/" + s["id"] + "/review",
            headers=p["parent1"]["headers"],
            json={"decision": "REVISION_REQUESTED"},
        ).status_code
        == 200
    )
    approve(c, p, s)
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 0


def test_two_simultaneous_redemptions_cannot_double_spend(homework):
    c, db, p, a, s = homework
    approve(c, p, s)
    d = device(c, p)
    body = {"device_id": d["id"], "package": "com.instagram.android", "minutes": 20}

    def redeem(i):
        return c.post(
            "/api/v1/rewards/redeem",
            headers={**p["student0"]["headers"], "Idempotency-Key": f"concurrent-request-{i}"},
            json=body,
        )

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(redeem, [1, 2]))
    assert sorted(r.status_code for r in results) == [200, 409], [r.text for r in results]
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 10


def test_failed_unlock_refunds_once_and_expired_pending_refunds(homework):
    c, db, p, a, s = homework
    approve(c, p, s)
    d = device(c, p)
    headers = {**p["student0"]["headers"], "Idempotency-Key": "redeem-test-0001"}
    body = {"device_id": d["id"], "package": "com.instagram.android", "minutes": 20}
    lease = c.post("/api/v1/rewards/redeem", headers=headers, json=body).json()
    assert c.post("/api/v1/rewards/redeem", headers=headers, json=body).json()["id"] == lease["id"]
    for _ in range(2):
        assert (
            c.post(
                "/api/v1/rewards/sessions/" + lease["id"] + "/ack",
                headers=p["student0"]["headers"],
                json={"applied": False},
            ).status_code
            == 200
        )
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 30
    lease = c.post(
        "/api/v1/rewards/redeem", headers={**headers, "Idempotency-Key": "redeem-test-0002"}, json=body
    ).json()
    with db.begin() as session:
        session.get(UnlockSession, lease["id"]).expires_at = now() - timedelta(seconds=1)
    assert (
        c.post(
            "/api/v1/rewards/sessions/" + lease["id"] + "/ack",
            headers=p["student0"]["headers"],
            json={"applied": True},
        ).json()["status"]
        == "FAILED"
    )
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 30


def test_budget_prevents_redemption(homework):
    c, _, p, a, s = homework
    approve(c, p, s)
    d = device(c, p)
    assert (
        c.put(
            "/api/v1/rewards/budget/" + p["student0"]["id"],
            headers=p["parent1"]["headers"],
            json={"daily_max": 5, "weekly_max": 20},
        ).status_code
        == 200
    )
    r = c.post(
        "/api/v1/rewards/redeem",
        headers={**p["student0"]["headers"], "Idempotency-Key": "budget-test-0001"},
        json={"device_id": d["id"], "package": "com.instagram.android", "minutes": 10},
    )
    assert r.status_code == 409


def test_objective_review_is_assistance_and_no_auto_credit(homework):
    c, _, p, a, s = homework
    r = c.post(
        "/api/v1/ai/evaluate-homework", params={"submission_id": s["id"]}, headers=p["student0"]["headers"]
    )
    assert r.status_code == 200, r.text
    assert r.json()["correct"] == 1 and r.json()["human_required"]
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 0


def test_unconfigured_ai_returns_real_error(people):
    c, _, p = people
    r = c.post("/api/v1/ai/tutor", json={"message": "Kasrlarni tushuntir"}, headers=p["student0"]["headers"])
    assert r.status_code == 503


def test_focus_cannot_complete_early_or_duplicate(homework):
    c, db, p, a, s = homework
    headers = p["student0"]["headers"]
    row = c.post(
        "/api/v1/focus", headers=headers, json={"subject": "Matematika", "duration_seconds": 60}
    ).json()
    assert (
        c.post("/api/v1/focus", headers=headers, json={"subject": "IT", "duration_seconds": 60}).status_code
        == 409
    )
    assert c.post("/api/v1/focus/" + row["id"] + "/complete", headers=headers).status_code == 409
    with db.begin() as session:
        session.get(FocusSession, row["id"]).created_at = now() - timedelta(seconds=65)
    for _ in range(2):
        assert (
            c.post("/api/v1/focus/" + row["id"] + "/complete", headers=headers).json()["status"]
            == "COMPLETED"
        )
    assert c.get("/api/v1/rewards/wallet", headers=headers).json()["available"] == 0


def test_private_upload_type_size_and_scope(homework):
    c, _, p, a, s = homework
    r = c.post(
        "/api/v1/assignments/" + a["id"] + "/attachments",
        headers=p["student0"]["headers"],
        files={"file": ("bad.png", b"not a png", "image/png")},
    )
    assert r.status_code == 415
    r = c.post(
        "/api/v1/assignments/" + a["id"] + "/attachments",
        headers=p["student0"]["headers"],
        files={"file": ("work.pdf", b"%PDF-1.7 test", "application/pdf")},
    )
    assert r.status_code == 201, r.text
    path = "/api/v1/attachments/" + r.json()["id"]
    assert c.get(path, headers=p["parent2"]["headers"]).status_code == 403
    assert c.get(path, headers=p["parent1"]["headers"]).content.startswith(b"%PDF")
