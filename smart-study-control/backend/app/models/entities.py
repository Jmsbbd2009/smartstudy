from sqlalchemy import Float
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
    UniqueConstraint,
    CheckConstraint,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from app.db.session import Base


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Entity:
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=uid)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now, onupdate=now)


class User(Entity, Base):
    __tablename__ = "users"
    login: Mapped[str | None] = mapped_column(String(80), nullable=True, unique=True, index=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False, server_default="0")
    auth_epoch: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    email: Mapped[str] = mapped_column(String(254), unique=True)
    name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(24), index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (CheckConstraint("role IN ('STUDENT','PARENT','TEACHER','SCHOOL_ADMIN','SUPER_ADMIN')"),)


class Role(Entity, Base):
    __tablename__ = "roles"
    name: Mapped[str] = mapped_column(String(24), unique=True)


class UserRole(Entity, Base):
    __tablename__ = "user_roles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    role_id: Mapped[str] = mapped_column(ForeignKey("roles.id"))
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)


class RefreshToken(Entity, Base):
    __tablename__ = "refresh_tokens"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    family: Mapped[str] = mapped_column(String(36), index=True)
    digest: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    revoked: Mapped[bool] = mapped_column(Boolean, default=False)


class Family(Entity, Base):
    __tablename__ = "families"
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))


class FamilyMember(Entity, Base):
    __tablename__ = "family_members"
    family_id: Mapped[str] = mapped_column(ForeignKey("families.id"), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    __table_args__ = (UniqueConstraint("family_id", "user_id"),)


class ParentLink(Entity, Base):
    __tablename__ = "parent_child_links"
    parent_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    child_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    consent: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("parent_id", "child_id"),)


class Invite(Entity, Base):
    __tablename__ = "invites"
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    resource_id: Mapped[str] = mapped_column(String(36))
    code_hash: Mapped[str] = mapped_column(String(64), unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    used: Mapped[bool] = mapped_column(Boolean, default=False)


class School(Entity, Base):
    __tablename__ = "schools"
    name: Mapped[str] = mapped_column(String(120))
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)


class Classroom(Entity, Base):
    __tablename__ = "classrooms"
    name: Mapped[str] = mapped_column(String(100))
    teacher_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    school_id: Mapped[str | None] = mapped_column(ForeignKey("schools.id"), nullable=True)


class ClassroomMember(Entity, Base):
    __tablename__ = "classroom_members"
    classroom_id: Mapped[str] = mapped_column(ForeignKey("classrooms.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    __table_args__ = (UniqueConstraint("classroom_id", "student_id"),)


class Consent(Entity, Base):
    __tablename__ = "consent_records"
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    child_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(100))
    version: Mapped[str] = mapped_column(String(20), default="1")
    granted: Mapped[bool] = mapped_column(Boolean)


class Device(Entity, Base):
    __tablename__ = "devices"
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    mode: Mapped[str] = mapped_column(String(24), default="STANDARD")
    version: Mapped[int] = mapped_column(Integer, default=0)
    deprovision_requested: Mapped[bool] = mapped_column(Boolean, default=False)
    retired: Mapped[bool] = mapped_column(Boolean, default=False)
    compliance: Mapped[dict] = mapped_column(JSON, default=dict)


class Enrollment(Entity, Base):
    __tablename__ = "device_enrollments"
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), index=True)
    authorized_by: Mapped[str] = mapped_column(ForeignKey("users.id"))
    consent_id: Mapped[str] = mapped_column(ForeignKey("consent_records.id"))


class DevicePolicy(Entity, Base):
    __tablename__ = "device_policies"
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    document: Mapped[dict] = mapped_column(JSON)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("device_id", "version"),)


class BlockedAppRule(Entity, Base):
    __tablename__ = "blocked_app_rules"
    policy_id: Mapped[str] = mapped_column(ForeignKey("device_policies.id"), index=True)
    package: Mapped[str] = mapped_column(String(200))
    __table_args__ = (UniqueConstraint("policy_id", "package"),)


class PolicyVersion(Entity, Base):
    __tablename__ = "policy_versions"
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), index=True)
    version: Mapped[int] = mapped_column(Integer)
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    __table_args__ = (UniqueConstraint("device_id", "version"),)


class Assignment(Entity, Base):
    __tablename__ = "assignments"
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    classroom_id: Mapped[str | None] = mapped_column(ForeignKey("classrooms.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(150))
    subject: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(Text, default="")
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    estimated_minutes: Mapped[int] = mapped_column(Integer, default=25)
    difficulty: Mapped[str] = mapped_column(String(12), default="NORMAL")
    reward_minutes: Mapped[int] = mapped_column(Integer, default=15)
    status: Mapped[str] = mapped_column(String(30), default="ASSIGNED", index=True)
    answer_key: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (CheckConstraint("reward_minutes >= 0 AND reward_minutes <= 120"),)


class Attachment(Entity, Base):
    __tablename__ = "assignment_attachments"
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"), index=True)
    uploader_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    submission_id: Mapped[str | None] = mapped_column(ForeignKey("submissions.id"), nullable=True, index=True)
    filename: Mapped[str] = mapped_column(String(180))
    storage_key: Mapped[str] = mapped_column(String(36), unique=True)
    media_type: Mapped[str] = mapped_column(String(80))
    size: Mapped[int] = mapped_column(Integer)


class Submission(Entity, Base):
    __tablename__ = "submissions"
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(30), default="SUBMITTED")
    idempotency_key: Mapped[str] = mapped_column(String(100))
    __table_args__ = (UniqueConstraint("student_id", "idempotency_key"),)


class SubmissionReview(Entity, Base):
    __tablename__ = "submission_reviews"
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), index=True)
    reviewer_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    decision: Mapped[str] = mapped_column(String(30))
    feedback: Mapped[str] = mapped_column(Text, default="")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class Quiz(Entity, Base):
    __tablename__ = "quizzes"
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    assignment_id: Mapped[str] = mapped_column(ForeignKey("assignments.id"), unique=True)
    title: Mapped[str] = mapped_column(String(150))
    time_limit_seconds: Mapped[int] = mapped_column(Integer, default=600)
    validated: Mapped[bool] = mapped_column(Boolean, default=False)


class QuizQuestion(Entity, Base):
    __tablename__ = "quiz_questions"
    quiz_id: Mapped[str] = mapped_column(ForeignKey("quizzes.id"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON)
    answer: Mapped[str] = mapped_column(String(500))
    explanation: Mapped[str] = mapped_column(Text)
    __table_args__ = (UniqueConstraint("quiz_id", "position"),)


class QuizAttempt(Entity, Base):
    __tablename__ = "quiz_attempts"
    quiz_id: Mapped[str] = mapped_column(ForeignKey("quizzes.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    __table_args__ = (UniqueConstraint("quiz_id", "student_id"),)


class Wallet(Entity, Base):
    __tablename__ = "reward_wallets"
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    available: Mapped[int] = mapped_column(Integer, default=0)
    debt: Mapped[int] = mapped_column(Integer, default=0)
    daily_max: Mapped[int] = mapped_column(Integer, default=60)
    weekly_max: Mapped[int] = mapped_column(Integer, default=300)
    __table_args__ = (CheckConstraint("available >= 0 AND debt >= 0 AND daily_max >= 0 AND weekly_max >= 0"),)


class RewardTransaction(Entity, Base):
    __tablename__ = "reward_transactions"
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    origin: Mapped[str] = mapped_column(String(150), unique=True)
    delta: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(24))
    reference: Mapped[str] = mapped_column(String(100))


class UnlockSession(Entity, Base):
    __tablename__ = "app_unlock_sessions"
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    device_id: Mapped[str] = mapped_column(ForeignKey("devices.id"), index=True)
    package: Mapped[str] = mapped_column(String(200))
    minutes: Mapped[int] = mapped_column(Integer)
    idempotency_key: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    __table_args__ = (
        UniqueConstraint("student_id", "idempotency_key"),
        CheckConstraint("minutes > 0 AND minutes <= 120"),
    )


class FocusSession(Entity, Base):
    __tablename__ = "focus_sessions"
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    subject: Mapped[str] = mapped_column(String(100))
    duration_seconds: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Alarm(Entity, Base):
    __tablename__ = "alarms"
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    hour: Mapped[int] = mapped_column(Integer)
    minute: Mapped[int] = mapped_column(Integer)
    weekdays: Mapped[list] = mapped_column(JSON)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    label: Mapped[str] = mapped_column(String(100), default="Study")
    __table_args__ = (CheckConstraint("hour >= 0 AND hour < 24 AND minute >= 0 AND minute < 60"),)


class SleepSchedule(Entity, Base):
    __tablename__ = "sleep_schedules"
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    start_minute: Mapped[int] = mapped_column(Integer)
    end_minute: Mapped[int] = mapped_column(Integer)
    timezone: Mapped[str] = mapped_column(String(64), default="Asia/Tashkent")
    __table_args__ = (
        CheckConstraint(
            "start_minute >= 0 AND start_minute < 1440 AND end_minute >= 0 AND end_minute < 1440"
        ),
    )


class Notification(Entity, Base):
    __tablename__ = "notifications"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)


class AuditEvent(Entity, Base):
    __tablename__ = "audit_events"
    actor_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    action: Mapped[str] = mapped_column(String(100), index=True)
    resource_id: Mapped[str] = mapped_column(String(100), index=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)


class OutboxRecord(Entity, Base):
    __tablename__ = "sync_outbox_records"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    event_type: Mapped[str] = mapped_column(String(50))
    payload: Mapped[dict] = mapped_column(JSON)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DeletionRequest(Entity, Base):
    __tablename__ = "deletion_requests"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")


class StudyBook(Entity, Base):
    __tablename__ = "study_books"
    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    filename: Mapped[str] = mapped_column(String(180))
    storage_key: Mapped[str] = mapped_column(String(36), unique=True)
    sha256: Mapped[str] = mapped_column(String(64))
    size: Mapped[int] = mapped_column(Integer)
    page_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="READY")
    __table_args__ = (
        CheckConstraint("size > 0 AND page_count > 0 AND page_count <= 300"),
        UniqueConstraint("owner_id", "sha256"),
    )


class BookPage(Entity, Base):
    __tablename__ = "book_pages"
    book_id: Mapped[str] = mapped_column(ForeignKey("study_books.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)
    method: Mapped[str] = mapped_column(String(20), default="TEXT")
    __table_args__ = (UniqueConstraint("book_id", "page_number"), CheckConstraint("page_number > 0"))


class BookLesson(Entity, Base):
    __tablename__ = "book_lessons"
    book_id: Mapped[str] = mapped_column(ForeignKey("study_books.id"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    start_page: Mapped[int] = mapped_column(Integer)
    end_page: Mapped[int] = mapped_column(Integer)
    content: Mapped[dict] = mapped_column(JSON)
    source_digest: Mapped[str] = mapped_column(String(64))
    provider_model: Mapped[str] = mapped_column(String(200), default="adult-authored")
    status: Mapped[str] = mapped_column(String(20), default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, default=1)
    published_by: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    __table_args__ = (
        CheckConstraint("start_page > 0 AND end_page >= start_page AND end_page - start_page < 5"),
    )


class ReadingPlan(Entity, Base):
    __tablename__ = "reading_plans"
    book_id: Mapped[str] = mapped_column(ForeignKey("study_books.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    assigned_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    classroom_id: Mapped[str | None] = mapped_column(ForeignKey("classrooms.id"), nullable=True)
    start_page: Mapped[int] = mapped_column(Integer)
    end_page: Mapped[int] = mapped_column(Integer)
    reward_minutes: Mapped[int] = mapped_column(Integer, default=0)
    pass_percent: Mapped[int] = mapped_column(Integer, default=80)
    auto_reward: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_guardian_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (
        CheckConstraint("start_page > 0 AND end_page >= start_page"),
        CheckConstraint(
            "reward_minutes >= 0 AND reward_minutes <= 30 AND pass_percent >= 50 AND pass_percent <= 100"
        ),
    )


class ReadingProgress(Entity, Base):
    __tablename__ = "reading_progress"
    plan_id: Mapped[str] = mapped_column(ForeignKey("reading_plans.id"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    reported_seconds: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (
        UniqueConstraint("plan_id", "page_number"),
        CheckConstraint("reported_seconds >= 0 AND reported_seconds <= 86400"),
    )


class ReadingAttempt(Entity, Base):
    __tablename__ = "reading_attempts"
    plan_id: Mapped[str] = mapped_column(ForeignKey("reading_plans.id"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("book_lessons.id"), index=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    lesson_version: Mapped[int] = mapped_column(Integer)
    questions: Mapped[list] = mapped_column(JSON)
    answer_key: Mapped[dict] = mapped_column(JSON)
    answers: Mapped[dict] = mapped_column(JSON, default=dict)
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    start_key: Mapped[str] = mapped_column(String(100))
    __table_args__ = (UniqueConstraint("student_id", "start_key"),)


class AutomationSetting(Entity, Base):
    __tablename__ = "automation_settings"
    child_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    guardian_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    auto_practice: Mapped[bool] = mapped_column(Boolean, default=False)
    daily_reward_limit: Mapped[int] = mapped_column(Integer, default=60)
    max_tasks_per_day: Mapped[int] = mapped_column(Integer, default=2)
    __table_args__ = (
        CheckConstraint(
            "daily_reward_limit >= 0 AND daily_reward_limit <= 120 AND max_tasks_per_day >= 0 AND max_tasks_per_day <= 3"
        ),
    )


class AutomationRun(Entity, Base):
    __tablename__ = "automation_runs"
    child_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    guardian_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    day: Mapped[str] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    __table_args__ = (UniqueConstraint("child_id", "day"), CheckConstraint("attempts >= 0 AND attempts <= 3"))


class StaffProfile(Entity, Base):
    __tablename__ = "staff_profiles"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    school_id: Mapped[str] = mapped_column(ForeignKey("schools.id"), index=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)


class AuthChallenge(Entity, Base):
    __tablename__ = "auth_challenges"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(30))
    state_hash: Mapped[str] = mapped_column(String(64), unique=True)
    verifier_hash: Mapped[str] = mapped_column(String(64))
    code_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    consumed: Mapped[bool] = mapped_column(Boolean, default=False)
    delivered: Mapped[bool] = mapped_column(Boolean, default=False)
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    __table_args__ = (CheckConstraint("attempts >= 0 AND attempts <= 5"),)


class TelegramIdentity(Entity, Base):
    __tablename__ = "telegram_identities"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    telegram_user_id: Mapped[str] = mapped_column(String(30), unique=True)
    chat_id: Mapped[str] = mapped_column(String(30))
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False)


class TelegramUpdate(Entity, Base):
    __tablename__ = "telegram_updates"
    update_id: Mapped[str] = mapped_column(String(30), unique=True)


class Passkey(Entity, Base):
    __tablename__ = "passkeys"
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    credential_id: Mapped[str] = mapped_column(String(1500), unique=True)
    public_key: Mapped[str] = mapped_column(Text)
    sign_count: Mapped[int] = mapped_column(Integer, default=0)
    label: Mapped[str] = mapped_column(String(100), default="Qurilma")
    __table_args__ = (CheckConstraint("sign_count >= 0"),)


class LocationConsent(Entity, Base):
    __tablename__ = "location_consents"
    child_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)
    guardian_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    max_minutes: Mapped[int] = mapped_column(Integer, default=60)
    __table_args__ = (CheckConstraint("max_minutes >= 1 AND max_minutes <= 240"),)


class LocationShare(Entity, Base):
    __tablename__ = "location_shares"
    child_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    consent_guardian_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE")
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    accuracy_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    __table_args__ = (
        CheckConstraint("latitude IS NULL OR (latitude >= -90 AND latitude <= 90)"),
        CheckConstraint("longitude IS NULL OR (longitude >= -180 AND longitude <= 180)"),
        CheckConstraint("accuracy_m IS NULL OR (accuracy_m >= 0 AND accuracy_m <= 100000)"),
    )


class TelegramDelivery(Entity, Base):
    __tablename__ = "telegram_deliveries"
    notification_id: Mapped[str] = mapped_column(ForeignKey("notifications.id"), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    __table_args__ = (CheckConstraint("attempts >= 0 AND attempts <= 3"),)
