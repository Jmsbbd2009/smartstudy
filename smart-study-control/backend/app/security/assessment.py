from datetime import timedelta
from sqlalchemy import select
from app.models.entities import ReadingAttempt, QuizAttempt, Quiz, now


def assessment_active(db, user_id):
    instant = now()
    if db.scalar(select(ReadingAttempt.id).where(
        ReadingAttempt.student_id == user_id, ReadingAttempt.status == "ACTIVE",
        ReadingAttempt.expires_at > instant,
    ).limit(1)):
        return True
    rows = db.execute(select(QuizAttempt.created_at, Quiz.time_limit_seconds).join(
        Quiz, Quiz.id == QuizAttempt.quiz_id,
    ).where(QuizAttempt.student_id == user_id, QuizAttempt.completed_at.is_(None)))
    return any(start + timedelta(seconds=duration) > instant for start, duration in rows)
