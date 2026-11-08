import hashlib
import json
import os
import secrets
import subprocess
import sys
from datetime import timedelta
from pathlib import Path
from fastapi import HTTPException
from sqlalchemy import select, func, update
from app.models.entities import (
    StudyBook,
    BookPage,
    BookLesson,
    ReadingPlan,
    ReadingProgress,
    ReadingAttempt,
    User,
    ParentLink,
    Classroom,
    ClassroomMember,
    AutomationSetting,
    RewardTransaction,
    AuditEvent,
    Notification,
    now,
    uid,
)
from app.security.scope import guardian
from app.services.rewards import locked_wallet, credit
from app.schemas.reading import LessonContent


def log(db, user, action, resource, details=None):
    db.add(AuditEvent(actor_id=user.id, action=action, resource_id=resource, details=details or {}))


def parse_pdf(path, mode="extract", start=1, end=1):
    if os.name != "posix":
        raise HTTPException(503, "PDF processing requires the Linux worker")
    script = Path(__file__).resolve().parents[1] / "workers" / "pdf_extract.py"
    try:
        result = subprocess.run(
            [sys.executable, str(script), str(path), mode, str(start), str(end)],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            timeout=65 if mode == "ocr" else 22,
            check=True,
            env={
                "PATH": "/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "OCR_LANG": os.getenv("OCR_LANG", "eng"),
                "OMP_THREAD_LIMIT": "1",
            },
        )
        if len(result.stdout) > 7 * 1024 * 1024:
            raise ValueError("Worker output limit")
        data = json.loads(result.stdout)
        if not 1 <= data["page_count"] <= 300:
            raise ValueError("Page limit")
        return data
    except (subprocess.SubprocessError, ValueError, KeyError, OSError):
        raise HTTPException(
            422,
            "PDFni o‘qib bo‘lmadi. Shifrlanmagan, 10 MB va 300 sahifadan kichik PDF yuklang. OCR uchun Poppler va Tesseract kerak.",
        )


def plan_scope(db, user, ident, student_only=False):
    plan = db.get(ReadingPlan, ident)
    if not plan or not plan.active:
        raise HTTPException(404, "Reading plan not found")
    if student_only:
        allowed = user.role == "STUDENT" and user.id == plan.student_id
    else:
        allowed = user.id == plan.student_id or guardian(db, user, plan.student_id)
        if not allowed and user.role == "TEACHER" and plan.assigned_by == user.id and plan.classroom_id:
            allowed = bool(
                db.scalar(
                    select(ClassroomMember.id)
                    .join(Classroom, Classroom.id == ClassroomMember.classroom_id)
                    .where(
                        Classroom.id == plan.classroom_id,
                        Classroom.teacher_id == user.id,
                        ClassroomMember.student_id == plan.student_id,
                    )
                )
            )
    if not allowed:
        raise HTTPException(403, "Reading plan access denied")
    return plan


def visible_plans(db, user):
    if user.role == "STUDENT":
        return select(ReadingPlan).where(ReadingPlan.student_id == user.id, ReadingPlan.active.is_(True))
    if user.role == "PARENT":
        children = select(ParentLink.child_id).where(
            ParentLink.parent_id == user.id, ParentLink.consent.is_(True)
        )
        return select(ReadingPlan).where(ReadingPlan.student_id.in_(children), ReadingPlan.active.is_(True))
    if user.role == "TEACHER":
        return (
            select(ReadingPlan)
            .join(Classroom, Classroom.id == ReadingPlan.classroom_id)
            .join(
                ClassroomMember,
                (ClassroomMember.classroom_id == Classroom.id)
                & (ClassroomMember.student_id == ReadingPlan.student_id),
            )
            .where(
                ReadingPlan.assigned_by == user.id,
                Classroom.teacher_id == user.id,
                ReadingPlan.active.is_(True),
            )
        )
    return select(ReadingPlan).where(ReadingPlan.id.is_(None))


def book_scope(db, user, ident, owner=False):
    book = db.get(StudyBook, ident)
    if not book:
        raise HTTPException(404, "Book not found")
    if book.owner_id == user.id:
        return book
    if not owner and db.scalar(
        visible_plans(db, user).where(ReadingPlan.book_id == book.id).with_only_columns(ReadingPlan.id)
    ):
        return book
    raise HTTPException(403, "Book access denied")


def lock_book(db, book):
    # Serialize source changes, lesson edits and publication on both PostgreSQL
    # and the SQLite developer fallback. Refresh objects read before the lock.
    db.execute(update(StudyBook).where(StudyBook.id == book.id).values(updated_at=now()))
    db.refresh(book)


def source_pages(db, book, start, end, for_ai=False):
    if not 1 <= start <= end <= book.page_count or end - start > 4:
        raise HTTPException(422, "Select 1 to 5 existing pages")
    pages = list(
        db.scalars(
            select(BookPage)
            .where(BookPage.book_id == book.id, BookPage.page_number >= start, BookPage.page_number <= end)
            .order_by(BookPage.page_number)
        )
    )
    if len(pages) != end - start + 1 or any(len(p.text.strip()) < 8 for p in pages):
        raise HTTPException(422, "Bu sahifada matn yo‘q. Avval OCR bajaring yoki boshqa sahifani tanlang.")
    if for_ai and sum(len(p.text) for p in pages) > 20000:
        raise HTTPException(422, "AI uchun kichikroq bo‘lim tanlang (20 000 belgigacha)")
    return pages


def source_digest(pages):
    return hashlib.sha256(
        json.dumps([(p.page_number, p.text) for p in pages], ensure_ascii=False).encode()
    ).hexdigest()


def normalized(text):
    return " ".join(text.casefold().split())


def validate_grounding(content, pages):
    by_page = {p.page_number: p.text for p in pages}
    for item in [*content.concepts, *content.questions]:
        if item.source_page not in by_page or normalized(item.source_quote) not in normalized(
            by_page[item.source_page]
        ):
            raise HTTPException(
                422, "Manba iqtibosi tanlangan sahifada topilmadi. Dars va javob kalitini tuzating."
            )


def lesson_scope(db, user, ident):
    lesson = db.get(BookLesson, ident)
    if not lesson:
        raise HTTPException(404, "Lesson not found")
    book = book_scope(db, user, lesson.book_id)
    if book.owner_id != user.id:
        scope = visible_plans(db, user).where(
            ReadingPlan.book_id == book.id,
            ReadingPlan.start_page <= lesson.start_page,
            ReadingPlan.end_page >= lesson.end_page,
        )
        if lesson.status != "PUBLISHED" or not db.scalar(scope.with_only_columns(ReadingPlan.id)):
            raise HTTPException(403, "Published assigned lesson required")
    return lesson, book


def book_output(book):
    return {
        k: getattr(book, k)
        for k in ["id", "owner_id", "title", "filename", "page_count", "status", "created_at"]
    }


def plan_output(db, plan):
    return {
        **{
            k: getattr(plan, k)
            for k in [
                "id",
                "book_id",
                "student_id",
                "assigned_by",
                "start_page",
                "end_page",
                "reward_minutes",
                "pass_percent",
                "auto_reward",
                "active",
                "created_at",
            ]
        },
        "book_title": db.get(StudyBook, plan.book_id).title,
        "student_name": db.get(User, plan.student_id).name,
    }


def lesson_output(lesson, book, user):
    content = dict(lesson.content)
    if book.owner_id != user.id:
        content.pop("questions", None)
    return {
        "id": lesson.id,
        "book_id": book.id,
        "title": lesson.title,
        "start_page": lesson.start_page,
        "end_page": lesson.end_page,
        "status": lesson.status,
        "version": lesson.version,
        "provider_model": lesson.provider_model,
        "question_count": len(lesson.content["questions"]),
        "content": content,
        "can_edit": book.owner_id == user.id,
    }


def assign_plan(db, user, book, body):
    student = db.get(User, body.student_id)
    if not student or student.role != "STUDENT":
        raise HTTPException(404, "Student not found")
    if not 1 <= body.start_page <= body.end_page <= book.page_count:
        raise HTTPException(422, "Invalid page range")
    if user.role == "PARENT":
        if not guardian(db, user, student.id) or body.classroom_id:
            raise HTTPException(403, "Guardian link required")
    elif user.role == "TEACHER":
        classroom = db.get(Classroom, body.classroom_id) if body.classroom_id else None
        membership = db.scalar(
            select(ClassroomMember.id).where(
                ClassroomMember.classroom_id == body.classroom_id, ClassroomMember.student_id == student.id
            )
        )
        if not classroom or classroom.teacher_id != user.id or not membership:
            raise HTTPException(403, "Own classroom membership required")
        if body.reward_minutes or body.auto_reward:
            raise HTTPException(403, "A guardian configures device-related rewards")
    else:
        raise HTTPException(403, "Adult assignment role required")
    locked_wallet(db, student.id)
    plan = ReadingPlan(
        book_id=book.id,
        student_id=student.id,
        assigned_by=user.id,
        classroom_id=body.classroom_id,
        start_page=body.start_page,
        end_page=body.end_page,
        reward_minutes=body.reward_minutes,
        pass_percent=body.pass_percent,
        auto_reward=body.auto_reward,
        reward_guardian_id=user.id if user.role == "PARENT" else None,
    )
    db.add(plan)
    db.flush()
    db.add(Notification(user_id=student.id, title="Yangi kitob topshirig‘i", body=book.title))
    log(db, user, "reading.assign", plan.id)
    return plan


def award(db, attempt, plan, force=False):
    locked_wallet(db, plan.student_id)
    origin = f"reading:{plan.student_id}:{attempt.lesson_id}"
    existing = db.scalar(select(RewardTransaction).where(RewardTransaction.origin == origin))
    if existing:
        return (
            {"state": "GRANTED", "minutes": existing.delta}
            if existing.reference == attempt.id
            else {"state": "ALREADY_GRANTED", "minutes": 0}
        )
    if not attempt.result.get("passed"):
        return {"state": "NOT_PASSED", "minutes": 0}
    if plan.reward_minutes <= 0:
        return {"state": "NOT_CONFIGURED", "minutes": 0}
    author = db.get(User, plan.reward_guardian_id) if plan.reward_guardian_id else None
    setting = db.scalar(select(AutomationSetting).where(AutomationSetting.child_id == plan.student_id))
    if not force and (
        not plan.auto_reward
        or not author
        or not author.active
        or not guardian(db, author, plan.student_id)
        or not setting
        or not setting.enabled
    ):
        return {"state": "HUMAN_REQUIRED", "minutes": 0}
    # Parent authority is checked again by the manual approval endpoint when force=True.
    daily_limit = setting.daily_reward_limit if setting else 60
    start = now().replace(hour=0, minute=0, second=0, microsecond=0)
    used = db.scalar(
        select(func.coalesce(func.sum(RewardTransaction.delta), 0)).where(
            RewardTransaction.student_id == plan.student_id,
            RewardTransaction.kind == "EARN",
            RewardTransaction.origin.like("reading:%"),
            RewardTransaction.created_at >= start,
        )
    )
    if used + plan.reward_minutes > daily_limit:
        return {"state": "BUDGET_REACHED", "minutes": 0}
    transaction = credit(db, plan.student_id, origin, plan.reward_minutes, attempt.id)
    return {"state": "GRANTED", "minutes": transaction.delta}


def attempt_output(attempt):
    result = {
        "id": attempt.id,
        "finished_at": attempt.finished_at.isoformat() + "Z" if attempt.finished_at else None,
        "plan_id": attempt.plan_id,
        "lesson_id": attempt.lesson_id,
        "status": attempt.status,
        "expires_at": attempt.expires_at.isoformat() + "Z",
        "questions": attempt.questions,
        "result": attempt.result,
    }
    if attempt.finished_at:
        result["review"] = [
            {
                "id": q["id"],
                "correct_index": attempt.answer_key[q["id"]]["correct_index"],
                "explanation": attempt.answer_key[q["id"]]["explanation"],
                "source_page": attempt.answer_key[q["id"]]["source_page"],
            }
            for q in attempt.questions
        ]
    return result


def start_attempt(db, user, plan, lesson, key):
    locked_wallet(db, user.id)
    existing = db.scalar(
        select(ReadingAttempt).where(ReadingAttempt.student_id == user.id, ReadingAttempt.start_key == key)
    )
    if existing:
        if existing.plan_id != plan.id or existing.lesson_id != lesson.id:
            raise HTTPException(409, "Idempotency key conflict")
        return existing
    if (
        lesson.book_id != plan.book_id
        or lesson.status != "PUBLISHED"
        or lesson.start_page < plan.start_page
        or lesson.end_page > plan.end_page
    ):
        raise HTTPException(403, "Published lesson must be within assigned pages")
    required_pages = set(range(lesson.start_page, lesson.end_page + 1))
    reported_pages = set(
        db.scalars(
            select(ReadingProgress.page_number).where(
                ReadingProgress.plan_id == plan.id,
                ReadingProgress.page_number >= lesson.start_page,
                ReadingProgress.page_number <= lesson.end_page,
            )
        )
    )
    if not required_pages.issubset(reported_pages):
        raise HTTPException(409, "Read and mark every page in this lesson before starting its test")
    active = db.scalar(
        select(ReadingAttempt).where(
            ReadingAttempt.plan_id == plan.id,
            ReadingAttempt.lesson_id == lesson.id,
            ReadingAttempt.status == "ACTIVE",
        )
    )
    if active and active.expires_at > now() and active.lesson_version == lesson.version:
        return active
    if active:
        active.status = "SUPERSEDED" if active.lesson_version != lesson.version else "EXPIRED"
    questions = []
    answers = {}
    pool = list(lesson.content["questions"])
    secrets.SystemRandom().shuffle(pool)
    for source in pool:
        ident = uid()
        options = list(enumerate(source["options"]))
        secrets.SystemRandom().shuffle(options)
        correct = next(i for i, (index, _) in enumerate(options) if index == source["correct_index"])
        questions.append(
            {"id": ident, "prompt": source["prompt"], "options": [value for _, value in options]}
        )
        answers[ident] = {
            "correct_index": correct,
            "explanation": source["explanation"],
            "source_page": source["source_page"],
        }
    attempt = ReadingAttempt(
        plan_id=plan.id,
        lesson_id=lesson.id,
        student_id=user.id,
        lesson_version=lesson.version,
        questions=questions,
        answer_key=answers,
        expires_at=now() + timedelta(minutes=30),
        start_key=key,
    )
    db.add(attempt)
    db.flush()
    return attempt


def finish_attempt(db, user, attempt, body):
    plan = plan_scope(db, user, attempt.plan_id, True)
    locked_wallet(db, user.id)
    db.refresh(attempt)
    if attempt.finished_at:
        if attempt.answers != body.answers:
            raise HTTPException(409, "Completed answers are immutable")
        return attempt
    lesson = db.get(BookLesson, attempt.lesson_id)
    if not lesson or lesson.status != "PUBLISHED" or lesson.version != attempt.lesson_version:
        raise HTTPException(409, "Lesson changed; start a new validated test")
    if attempt.expires_at <= now() or attempt.status != "ACTIVE":
        raise HTTPException(409, "Test time expired")
    if set(body.answers) != set(attempt.answer_key):
        raise HTTPException(422, "Answer every question once")
    if any(
        type(value) is not int
        or not 0 <= value < len(next(q["options"] for q in attempt.questions if q["id"] == ident))
        for ident, value in body.answers.items()
    ):
        raise HTTPException(422, "Invalid option")
    correct = [
        key for key, value in body.answers.items() if value == attempt.answer_key[key]["correct_index"]
    ]
    percent = round(100 * len(correct) / len(attempt.questions), 2)
    attempt.answers = body.answers
    attempt.status = "FINISHED"
    attempt.finished_at = now()
    attempt.result = {
        "correct": len(correct),
        "total": len(attempt.questions),
        "percent": percent,
        "passed": percent >= plan.pass_percent,
        "assessed_pages": sorted({attempt.answer_key[key]["source_page"] for key in correct}),
        "evidence": "objective_answer_key_not_proof_of_reading",
    }
    attempt.result = {**attempt.result, "reward": award(db, attempt, plan)}
    log(db, user, "reading.test_finished", attempt.id, {"passed": attempt.result["passed"]})
    db.add(Notification(user_id=plan.assigned_by, title="Kitob testi yakunlandi", body=f"{percent}%"))
    return attempt


def progress_output(db, plan):
    reported = list(db.scalars(select(ReadingProgress).where(ReadingProgress.plan_id == plan.id)))
    attempts = list(
        db.scalars(
            select(ReadingAttempt).where(
                ReadingAttempt.plan_id == plan.id, ReadingAttempt.status == "FINISHED"
            )
        )
    )
    assessed = sorted({page for attempt in attempts for page in attempt.result.get("assessed_pages", [])})
    total = plan.end_page - plan.start_page + 1
    return {
        "plan_id": plan.id,
        "assigned_pages": total,
        "reported_pages": sorted(p.page_number for p in reported),
        "self_reported_percent": round(100 * len(reported) / total, 2),
        "assessed_pages": assessed,
        "checked_percent": round(100 * len(assessed) / total, 2),
        "passed_lessons": len({a.lesson_id for a in attempts if a.result.get("passed")}),
        "attempt_count": len(attempts),
        "notice": "Sahifa belgilash — o‘quvchi hisoboti. Testdagi to‘g‘ri javoblar tushunish dalili, butun kitobni o‘qiganlik isboti emas.",
    }
