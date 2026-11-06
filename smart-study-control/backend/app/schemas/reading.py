from datetime import datetime
from typing import ClassVar, Literal
from pydantic import Field, model_validator
from app.schemas.contracts import Strict
from app.schemas.responses import UtcModel
from app.ai.provider import AIResult


class Concept(Strict):
    id: str = Field(pattern=r"^[a-z0-9_]{1,30}$")
    title: str = Field(min_length=1, max_length=70)
    explanation: str = Field(min_length=1, max_length=800)
    source_page: int = Field(ge=1, le=300)
    source_quote: str = Field(min_length=8, max_length=600)


class Connection(Strict):
    from_id: str = Field(max_length=30)
    to_id: str = Field(max_length=30)
    label: str = Field(min_length=1, max_length=50)


class ReadingQuestion(Strict):
    prompt: str = Field(min_length=1, max_length=600)
    options: list[str] = Field(min_length=2, max_length=5)
    correct_index: int = Field(ge=0, le=4)
    explanation: str = Field(min_length=1, max_length=800)
    source_page: int = Field(ge=1, le=300)
    source_quote: str = Field(min_length=8, max_length=600)

    @model_validator(mode="after")
    def valid_key(self):
        if (
            self.correct_index >= len(self.options)
            or len(set(self.options)) != len(self.options)
            or any(not 1 <= len(x) <= 250 for x in self.options)
        ):
            raise ValueError("Distinct options and valid correct_index are required")
        return self


class LessonContent(Strict, AIResult):
    max_output_tokens: ClassVar[int] = 5000
    title: str = Field(min_length=1, max_length=150)
    summary: str = Field(min_length=1, max_length=2000)
    concepts: list[Concept] = Field(min_length=1, max_length=8)
    connections: list[Connection] = Field(max_length=12)
    questions: list[ReadingQuestion] = Field(min_length=3, max_length=10)

    @model_validator(mode="after")
    def known_concepts(self):
        keys = {c.id for c in self.concepts}
        if len(keys) != len(self.concepts) or any(
            e.from_id not in keys or e.to_id not in keys or e.from_id == e.to_id for e in self.connections
        ):
            raise ValueError("Concept connections must refer to distinct existing IDs")
        return self


class LessonIn(Strict):
    start_page: int = Field(ge=1, le=300)
    end_page: int = Field(ge=1, le=300)
    content: LessonContent


class GenerateLesson(Strict):
    start_page: int = Field(ge=1, le=300)
    end_page: int = Field(ge=1, le=300)


class PublishLesson(Strict):
    expected_version: int = Field(ge=1)
    answer_key_validated: Literal[True]


class PlanIn(Strict):
    student_id: str
    classroom_id: str | None = None
    start_page: int = Field(ge=1, le=300)
    end_page: int = Field(ge=1, le=300)
    reward_minutes: int = Field(default=0, ge=0, le=30)
    pass_percent: int = Field(default=80, ge=50, le=100)
    auto_reward: bool = False


class PlanReward(Strict):
    reward_minutes: int = Field(ge=0, le=30)
    pass_percent: int = Field(ge=50, le=100)
    auto_reward: bool


class PageProgress(Strict):
    page_number: int = Field(ge=1, le=300)
    reported_seconds: int = Field(ge=0, le=86400)


class FinishReading(Strict):
    answers: dict[str, int] = Field(min_length=1, max_length=10)


class AutomationIn(Strict):
    enabled: bool
    auto_practice: bool
    daily_reward_limit: int = Field(ge=0, le=120)
    max_tasks_per_day: int = Field(ge=0, le=3)


class PracticeTask(Strict):
    title: str = Field(min_length=1, max_length=150)
    subject: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=3000)
    estimated_minutes: int = Field(ge=5, le=45)


class PracticePlan(Strict, AIResult):
    max_output_tokens: ClassVar[int] = 3000
    summary: str = Field(min_length=1, max_length=1000)
    tasks: list[PracticeTask] = Field(max_length=3)


class PracticeRequest(Strict):
    message: str = Field(min_length=1, max_length=2000)


class BookOut(UtcModel):
    id: str
    title: str
    owner_id: str
    filename: str
    page_count: int
    status: str
    created_at: datetime


class PlanOut(UtcModel):
    id: str
    book_id: str
    book_title: str
    student_id: str
    student_name: str
    assigned_by: str
    start_page: int
    end_page: int
    reward_minutes: int
    pass_percent: int
    auto_reward: bool
    active: bool
    created_at: datetime
