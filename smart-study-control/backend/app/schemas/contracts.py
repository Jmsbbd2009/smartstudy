from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Register(Strict):
    email: str | None = Field(default=None, min_length=5, max_length=254, pattern=r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
    phone: str | None = Field(default=None, min_length=7, max_length=24, pattern=r"^\+?[0-9 ()-]+$")
    password: str = Field(min_length=12, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    role: Literal["STUDENT", "PARENT"]

    @model_validator(mode="after")
    def has_login_method(self):
        if not self.phone and not self.email:
            raise ValueError("phone or email is required")
        if self.role == "PARENT" and not self.email:
            raise ValueError("parent accounts require an email")
        return self


class Login(Strict):
    email: str = Field(max_length=254)
    password: str = Field(max_length=128)


class Refresh(Strict):
    refresh_token: str = Field(min_length=20, max_length=200)


class Link(Strict):
    code: str = Field(min_length=10, max_length=100)
    guardian_consent: Literal[True]


class Named(Strict):
    name: str = Field(min_length=1, max_length=100)


class Join(Strict):
    code: str = Field(min_length=10, max_length=100)


class AssignmentIn(Strict):
    student_id: str
    classroom_id: str | None = None
    title: str = Field(min_length=1, max_length=150)
    subject: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=20000)
    due_at: datetime | None = None
    estimated_minutes: int = Field(default=25, ge=1, le=480)
    difficulty: Literal["EASY", "NORMAL", "HARD"] = "NORMAL"
    reward_minutes: int = Field(default=15, ge=0, le=120)
    answer_key: dict[str, str] = Field(default_factory=dict, max_length=100)
    status: Literal["DRAFT", "ASSIGNED"] = "ASSIGNED"

    @field_validator("due_at")
    @classmethod
    def utc_due(cls, v):
        if v and v.tzinfo is None:
            raise ValueError("due_at must include a timezone")
        if v:
            from datetime import timezone

            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


class RewardPolicyIn(Strict):
    reward_minutes: int = Field(ge=0, le=120)


class SubmissionIn(Strict):
    text: str = Field(default="", max_length=20000)
    answers: dict[str, str] = Field(default_factory=dict, max_length=100)


class ReviewIn(Strict):
    decision: Literal["APPROVED", "REJECTED", "REVISION_REQUESTED"]
    feedback: str = Field(default="", max_length=5000)


class DeviceIn(Named):
    pass


class Window(Strict):
    days: list[int] = Field(min_length=1, max_length=7)
    start_minute: int = Field(ge=0, lt=1440)
    end_minute: int = Field(ge=0, lt=1440)

    @field_validator("days")
    @classmethod
    def weekdays(cls, v):
        if any(x < 1 or x > 7 for x in v):
            raise ValueError("ISO weekdays 1..7 required")
        return sorted(set(v))

    @model_validator(mode="after")
    def nonempty(self):
        if self.start_minute == self.end_minute:
            raise ValueError("Window cannot be empty or all-day")
        return self


class PolicyIn(Strict):
    expected_version: int = Field(ge=0)
    blocked_packages: list[str] = Field(default_factory=list, max_length=100)
    essential_packages: list[str] = Field(default_factory=list, max_length=100)
    safety_packages: list[str] = Field(default_factory=list, max_length=100)
    study: list[Window] = Field(default_factory=list, max_length=30)
    sleep: list[Window] = Field(default_factory=list, max_length=30)
    timezone: str = "Asia/Tashkent"
    default_blocked: bool = False
    uninstall_protection: bool = False
    override_until: datetime | None = None

    @field_validator("timezone")
    @classmethod
    def valid_tz(cls, v):
        try:
            ZoneInfo(v)
        except ZoneInfoNotFoundError:
            raise ValueError("Unknown timezone")
        return v

    @field_validator("blocked_packages", "essential_packages", "safety_packages")
    @classmethod
    def packages(cls, v):
        import re

        if any(not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+", p) for p in v):
            raise ValueError("Invalid package name")
        if any(len(p) > 200 for p in v):
            raise ValueError("Package name too long")
        return sorted(set(v))


class EligibleApp(Strict):
    package: str = Field(min_length=3, max_length=200, pattern=r"^[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z0-9_]+)+$")
    label: str = Field(min_length=1, max_length=120)


class SyncIn(Strict):
    applied_version: int = Field(ge=0)
    device_owner: bool = False
    uninstall_blocked: bool = False
    failures: list[str] = Field(default_factory=list, max_length=100)
    cleanup_complete: bool = False
    eligible_apps: list[EligibleApp] | None = Field(default=None, max_length=100)


class Redeem(Strict):
    device_id: str
    package: str = Field(max_length=200)
    minutes: int = Field(ge=1, le=120)


class Ack(Strict):
    applied: bool


class Budget(Strict):
    daily_max: int = Field(ge=0, le=240)
    weekly_max: int = Field(ge=0, le=1680)


class FocusIn(Strict):
    subject: str = Field(min_length=1, max_length=100)
    duration_seconds: int = Field(default=1500, ge=60, le=10800)


class AlarmIn(Strict):
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    weekdays: list[int] = Field(min_length=1, max_length=7)
    label: str = Field(default="Study", max_length=100)
    enabled: bool = True

    @field_validator("weekdays")
    @classmethod
    def days(cls, v):
        if any(d < 1 or d > 7 for d in v):
            raise ValueError("Weekday must be 1..7")
        return sorted(set(v))


class TutorIn(Strict):
    message: str = Field(min_length=1, max_length=2000)
    subject: str = Field(default="General", max_length=100)


class QuestionIn(Strict):
    prompt: str = Field(min_length=1, max_length=2000)
    options: list[str] = Field(min_length=2, max_length=8)
    answer: str = Field(min_length=1, max_length=500)
    explanation: str = Field(min_length=1, max_length=2000)

    @model_validator(mode="after")
    def key_in_options(self):
        if self.answer not in self.options or len(set(self.options)) != len(self.options):
            raise ValueError("Answer must be one of distinct options")
        return self


class QuizIn(Strict):
    assignment_id: str
    title: str = Field(min_length=1, max_length=150)
    time_limit_seconds: int = Field(default=600, ge=30, le=7200)
    questions: list[QuestionIn] = Field(min_length=1, max_length=100)
    validated: Literal[True]


class QuizAnswers(Strict):
    answers: dict[str, str] = Field(max_length=100)
