from datetime import datetime, timezone
from pydantic import BaseModel, Field, model_serializer
from app.schemas.contracts import PolicyIn


class UtcModel(BaseModel):
    @model_serializer(mode="wrap")
    def explicit_utc(self, handler):
        data = handler(self)
        for key in type(self).model_fields:
            value = getattr(self, key)
            if isinstance(value, datetime):
                if value.tzinfo is None:
                    value = value.replace(tzinfo=timezone.utc)
                data[key] = value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        return data


class UserOut(UtcModel):
    email: str
    name: str
    role: str
    active: bool
    id: str
    created_at: datetime
    updated_at: datetime


class AssignmentOut(UtcModel):
    owner_id: str
    student_id: str
    classroom_id: str | None = None
    title: str
    subject: str
    description: str
    due_at: datetime | None = None
    estimated_minutes: int
    difficulty: str
    reward_minutes: int
    status: str
    id: str
    created_at: datetime
    updated_at: datetime


class SubmissionOut(UtcModel):
    assignment_id: str
    student_id: str
    text: str
    answers: dict
    status: str
    idempotency_key: str
    id: str
    created_at: datetime
    updated_at: datetime


class SubmissionReviewOut(UtcModel):
    submission_id: str
    reviewer_id: str | None = None
    decision: str
    feedback: str
    metadata_json: dict
    id: str
    created_at: datetime
    updated_at: datetime


class AttachmentOut(UtcModel):
    assignment_id: str
    uploader_id: str
    submission_id: str | None = None
    filename: str
    media_type: str
    size: int
    id: str
    created_at: datetime
    updated_at: datetime


class DeviceOut(UtcModel):
    student_id: str
    name: str
    mode: str
    version: int
    deprovision_requested: bool
    retired: bool
    compliance: dict
    id: str
    created_at: datetime
    updated_at: datetime


class WalletOut(UtcModel):
    student_id: str
    available: int
    debt: int
    daily_max: int
    weekly_max: int
    id: str
    created_at: datetime
    updated_at: datetime


class RewardOut(UtcModel):
    student_id: str
    origin: str
    delta: int
    kind: str
    reference: str
    id: str
    created_at: datetime
    updated_at: datetime


class UnlockOut(UtcModel):
    student_id: str
    device_id: str
    package: str
    minutes: int
    idempotency_key: str
    status: str
    expires_at: datetime
    id: str
    created_at: datetime
    updated_at: datetime


class ClassroomOut(UtcModel):
    name: str
    teacher_id: str
    school_id: str | None = None
    id: str
    created_at: datetime
    updated_at: datetime


class FocusOut(UtcModel):
    student_id: str
    subject: str
    duration_seconds: int
    status: str
    completed_at: datetime | None = None
    id: str
    created_at: datetime
    updated_at: datetime


class AlarmOut(UtcModel):
    student_id: str
    hour: int
    minute: int
    weekdays: list
    enabled: bool
    label: str
    id: str
    created_at: datetime
    updated_at: datetime


class NotificationOut(UtcModel):
    user_id: str
    title: str
    body: str
    read: bool
    id: str
    created_at: datetime
    updated_at: datetime


class AuditOut(UtcModel):
    actor_id: str
    action: str
    resource_id: str
    details: dict
    id: str
    created_at: datetime
    updated_at: datetime


class QuizOut(UtcModel):
    owner_id: str
    assignment_id: str
    title: str
    time_limit_seconds: int
    validated: bool
    id: str
    created_at: datetime
    updated_at: datetime


class QuestionOut(UtcModel):
    quiz_id: str
    position: int
    prompt: str
    options: list
    id: str
    created_at: datetime
    updated_at: datetime


class AttemptOut(UtcModel):
    quiz_id: str
    student_id: str
    answers: dict
    score: int | None = None
    completed_at: datetime | None = None
    id: str
    created_at: datetime
    updated_at: datetime


class TokenUser(UtcModel):
    login: str | None = None
    must_change_password: bool = False
    id: str
    name: str
    email: str
    role: str


class TokenOut(UtcModel):
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int
    user: TokenUser


class PolicyDocument(PolicyIn):
    expected_version: int = Field(default=0, exclude=True)


class PolicyOut(UtcModel):
    device_id: str
    version: int
    document: PolicyDocument
    deprovision_requested: bool
    retired: bool
    management_authorized: bool = False


class AssignmentDetailOut(AssignmentOut):
    attachments: list[AttachmentOut]
    submissions: list[SubmissionOut]


class QuizDetailOut(QuizOut):
    questions: list[QuestionOut]


class ExplanationOut(UtcModel):
    question_id: str
    answer: str
    explanation: str


class FinishedQuizOut(AttemptOut):
    explanations: list[ExplanationOut]


class InviteOut(UtcModel):
    code: str
    expires_in: int


class ReportOut(UtcModel):
    assigned: int
    approved: int
    completion_rate: float
    subjects: list[str]
    focus_seconds: int | None = None
    reward_minutes_earned: int | None = None
    access_minutes_reserved: int | None = None


class DashboardOut(UtcModel):
    name: str
    assigned: int
    approved: int
    wallet: WalletOut
