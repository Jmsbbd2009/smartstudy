from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.db.session import get_db
from app.models.entities import AutomationSetting, AutomationRun, AuditEvent
from app.security.auth import current_user
from app.security.scope import guardian
from app.security.rate_limit import limit
from app.schemas.reading import AutomationIn, PracticeRequest
from app.services.rewards import locked_wallet
from app.services.autopilot import run_daily

router = APIRouter(prefix="/api/v1/automation", tags=["automation"])


def authorized(db, user, child):
    if not guardian(db, user, child):
        raise HTTPException(403, "Guardian automation authority required")


def output(row):
    return {
        "id": row.id,
        "day": row.day,
        "status": row.status,
        "attempts": row.attempts,
        "result": row.result,
    }


def config(row):
    if not row:
        return {
            "configured": False,
            "enabled": False,
            "auto_practice": False,
            "daily_reward_limit": 60,
            "max_tasks_per_day": 2,
        }
    return {
        "configured": True,
        "enabled": row.enabled,
        "auto_practice": row.auto_practice,
        "daily_reward_limit": row.daily_reward_limit,
        "max_tasks_per_day": row.max_tasks_per_day,
    }


@router.get("/children/{child_id}")
def get_settings(child_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    authorized(db, user, child_id)
    return config(db.scalar(select(AutomationSetting).where(AutomationSetting.child_id == child_id)))


@router.put("/children/{child_id}")
def save_settings(
    child_id: str, body: AutomationIn, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    authorized(db, user, child_id)
    locked_wallet(db, child_id)
    row = db.scalar(select(AutomationSetting).where(AutomationSetting.child_id == child_id))
    if not row:
        row = AutomationSetting(child_id=child_id, guardian_id=user.id)
        db.add(row)
    for key, value in body.model_dump().items():
        setattr(row, key, value)
    row.guardian_id = user.id
    db.add(
        AuditEvent(
            actor_id=user.id, action="automation.configure", resource_id=child_id, details=body.model_dump()
        )
    )
    return config(row)


@router.post("/children/{child_id}/run")
def run(
    child_id: str, body: PracticeRequest, user=Depends(current_user), db=Depends(get_db, scope="function")
):
    authorized(db, user, child_id)
    limit("autopilot:" + user.id, 5, 3600)
    return output(run_daily(db, user, child_id, body.message))


@router.get("/children/{child_id}/runs")
def runs(child_id: str, user=Depends(current_user), db=Depends(get_db, scope="function")):
    authorized(db, user, child_id)
    return [
        output(row)
        for row in db.scalars(
            select(AutomationRun)
            .where(AutomationRun.child_id == child_id)
            .order_by(AutomationRun.created_at.desc())
            .limit(30)
        )
    ]
