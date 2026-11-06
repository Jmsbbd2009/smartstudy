from sqlalchemy import select
from app.models.entities import Assignment, AutomationRun
from app.schemas.reading import PracticePlan


def settings(c, p):
    child = p["student0"]["id"]
    return c.put(
        f"/api/v1/automation/children/{child}",
        headers=p["parent1"]["headers"],
        json={"enabled": True, "auto_practice": True, "daily_reward_limit": 60, "max_tasks_per_day": 1},
    )


def test_daily_ai_run_is_bounded_idempotent_and_cannot_mint_rewards(people, monkeypatch):
    from app.services import autopilot

    c, factory, p = people
    assert settings(c, p).status_code == 200

    class Provider:
        def structured(self, *args):
            return PracticePlan(
                summary="Qisqa takrorlash",
                tasks=[
                    {
                        "title": "Kasrlar mashqi",
                        "subject": "Matematika",
                        "description": "Ikki misolni yeching, keyin dam oling.",
                        "estimated_minutes": 10,
                    },
                    {
                        "title": "Lug‘at",
                        "subject": "Ingliz tili",
                        "description": "Besh so‘zni takrorlang.",
                        "estimated_minutes": 5,
                    },
                ],
            )

    monkeypatch.setattr(autopilot, "provider", Provider())
    path = f"/api/v1/automation/children/{p['student0']['id']}/run"
    for _ in range(2):
        r = c.post(path, headers=p["parent1"]["headers"], json={"message": "Bugungi reja"})
        assert r.status_code == 200, r.text
        assert len(r.json()["result"]["assignment_ids"]) == 1
    with factory() as db:
        tasks = list(db.scalars(select(Assignment)))
        assert len(tasks) == 1 and tasks[0].reward_minutes == 0
        assert len(list(db.scalars(select(AutomationRun)))) == 1
    assert c.get("/api/v1/rewards/wallet", headers=p["student0"]["headers"]).json()["available"] == 0


def test_automation_is_guardian_scoped_and_off_by_default(people):
    c, _, p = people
    path = f"/api/v1/automation/children/{p['student0']['id']}"
    assert c.get(path, headers=p["parent1"]["headers"]).json()["enabled"] is False
    assert (
        c.post(path + "/run", headers=p["parent1"]["headers"], json={"message": "Daily plan"}).status_code
        == 409
    )
    for name in ["student0", "parent2", "teacher3", "super_admin5"]:
        assert c.get(path, headers=p[name]["headers"]).status_code == 403
        assert (
            c.post(path + "/run", headers=p[name]["headers"], json={"message": "Daily plan"}).status_code
            == 403
        )


def test_unavailable_ai_creates_no_practice_and_records_failure(people):
    c, factory, p = people
    settings(c, p)
    r = c.post(
        f"/api/v1/automation/children/{p['student0']['id']}/run",
        headers=p["parent1"]["headers"],
        json={"message": "Daily plan"},
    )
    assert r.status_code == 503
    with factory() as db:
        assert list(db.scalars(select(Assignment))) == []
        row = db.scalar(select(AutomationRun))
        assert row.status == "FAILED" and row.result["no_tasks_created"]


def test_failed_ai_retries_are_capped_and_do_not_charge_rewards(people, monkeypatch):
    from app.services import autopilot
    from fastapi import HTTPException

    c, _, p = people
    settings(c, p)
    calls = []

    class Provider:
        def structured(self, *args):
            calls.append(1)
            raise HTTPException(503, "Unavailable")

    monkeypatch.setattr(autopilot, "provider", Provider())
    path = f"/api/v1/automation/children/{p['student0']['id']}/run"
    result = [
        c.post(path, headers=p["parent1"]["headers"], json={"message": "Daily plan"}).status_code
        for _ in range(4)
    ]
    assert result == [503, 503, 503, 409]
    assert len(calls) == 3
