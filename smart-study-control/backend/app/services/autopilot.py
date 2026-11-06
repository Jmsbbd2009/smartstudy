import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import HTTPException
from sqlalchemy import select
from app.models.entities import (
    AutomationSetting,
    AutomationRun,
    Assignment,
    User,
    Notification,
    AuditEvent,
    now,
)
from app.security.scope import guardian
from app.services.rewards import locked_wallet
from app.schemas.reading import PracticePlan
from app.ai.provider import provider


def valid_guardian(db, user, child):
    if not user or not user.active or not guardian(db, user, child):
        raise HTTPException(403, "Active guardian authority required")


def run_daily(db, user, child, message="Create a balanced short revision plan from current school progress"):
    valid_guardian(db, user, child)
    locked_wallet(db, child)
    setting = db.scalar(
        select(AutomationSetting)
        .where(AutomationSetting.child_id == child)
        .execution_options(populate_existing=True)
    )
    if not setting or not setting.enabled or not setting.auto_practice:
        raise HTTPException(409, "Ota-ona avtopilot mashqlarini avval yoqishi kerak")
    day = datetime.now(ZoneInfo("Asia/Tashkent")).date().isoformat()
    row = db.scalar(
        select(AutomationRun)
        .where(AutomationRun.child_id == child, AutomationRun.day == day)
        .execution_options(populate_existing=True)
    )
    if row and row.status == "COMPLETED":
        return row
    if row and row.attempts >= 3:
        raise HTTPException(409, "Bugungi AI urinishlari chegarasi tugadi; keyingi kuni qayta uriniladi")
    if row and row.status == "RUNNING" and row.updated_at > now() - timedelta(minutes=5):
        raise HTTPException(409, "Bugungi reja allaqachon yaratilmoqda")
    if not row:
        row = AutomationRun(child_id=child, guardian_id=user.id, day=day, status="RUNNING")
        db.add(row)
        db.flush()
    row.status = "RUNNING"
    row.attempts = (row.attempts or 0) + 1
    row.updated_at = now()
    row.guardian_id = user.id
    db.commit()
    # AI cannot grant itself permissions, alter package policies, mint rewards or run code.
    try:
        tasks = list(
            db.scalars(
                select(Assignment)
                .where(Assignment.student_id == child, Assignment.status != "DRAFT")
                .order_by(Assignment.created_at.desc())
                .limit(30)
            )
        )
        summary = [{"subject": a.subject, "status": a.status, "title": a.title[:150]} for a in tasks]
        plan = provider.structured(
            json.dumps({"request": message, "recent_academic_progress": summary}, ensure_ascii=False),
            PracticePlan,
            "You are an Uzbek Latin educational planning assistant. Suggest at most 3 short optional school practice tasks, with breaks and supportive wording. Use only academic context. Never punish, threaten, infer private traits, change device restrictions, grant rewards, request credentials, execute commands, or instruct children to disable management. Tasks are low-stakes practice, with no answer keys and no entertainment credit.",
        )
        locked_wallet(db, child)
        db.refresh(setting)
        db.refresh(user)
        valid_guardian(db, user, child)
        if not setting.enabled or not setting.auto_practice:
            raise HTTPException(409, "Avtopilot o‘chirildi; hech qanday vazifa yaratilmadi")
        ids = []
        for task in plan.tasks[: setting.max_tasks_per_day]:
            assignment = Assignment(
                owner_id=user.id,
                student_id=child,
                title=task.title,
                subject=task.subject,
                description=task.description,
                estimated_minutes=task.estimated_minutes,
                reward_minutes=0,
            )
            db.add(assignment)
            db.flush()
            ids.append(assignment.id)
        row.status = "COMPLETED"
        row.result = {
            "summary": plan.summary,
            "assignment_ids": ids,
            "model": getattr(plan, "_provider_model", "") or "configured-provider",
            "scope": "academic_practice_only",
            "reward_minutes": 0,
        }
        db.add(
            AuditEvent(
                actor_id=user.id,
                action="automation.daily_practice",
                resource_id=row.id,
                details={"tasks": len(ids)},
            )
        )
        if ids:
            db.add(Notification(user_id=child, title="AI o‘qish rejasi tayyor", body=plan.summary))
        db.commit()
        return row
    except Exception as exc:
        db.rollback()
        row = db.get(AutomationRun, row.id)
        if row:
            row.status = "FAILED"
            row.result = {"error_code": "AI_UNAVAILABLE_OR_REVIEW_REQUIRED", "no_tasks_created": True}
            db.commit()
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(503, "AI rejani ishonchli yarata olmadi. Mavjud vazifalar o‘zgartirilmadi.")
