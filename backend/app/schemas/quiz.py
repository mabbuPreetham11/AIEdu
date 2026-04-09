from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from app.schemas.common import ORMModel, TimestampedSchema

QuestionType = Literal["mcq", "true_false"]


class GeneratedQuizQuestion(BaseModel):
    question: str
    type: QuestionType
    options: list[str] = Field(default_factory=list)
    correct_answer: str
    explanation: str

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: list[str]) -> list[str]:
        cleaned = [item.strip() for item in value if item and item.strip()]
        return cleaned


class QuizGenerateRequest(BaseModel):
    topic: str | None = None
    material_id: int | None = None


class QuizGenerateResponse(BaseModel):
    questions: list[GeneratedQuizQuestion]


class QuizPublishRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    deadline: datetime
    randomise_order: bool = False
    is_published: bool = True
    questions: list[GeneratedQuizQuestion]


class QuizQuestionRead(ORMModel):
    id: int
    quiz_id: int
    question: str
    type: str
    options: list[str] | None
    correct_answer: str
    explanation: str
    order_number: int


class QuizQuestionPublicRead(ORMModel):
    id: int
    quiz_id: int
    question: str
    type: str
    options: list[str] | None
    order_number: int


class QuizRead(TimestampedSchema):
    id: int
    classroom_id: int
    title: str
    deadline: datetime
    is_published: bool
    randomise_order: bool
    questions: list[QuizQuestionRead]


class QuizAttemptSubmitRequest(BaseModel):
    answers: dict[str, str] = Field(default_factory=dict)


class QuizAttemptQuestionResult(BaseModel):
    question_id: int
    question: str
    selected_answer: str
    correct_answer: str
    is_correct: bool
    explanation: str


class QuizAttemptSubmitResponse(BaseModel):
    attempt_id: int
    quiz_id: int
    score: float
    total_questions: int
    correct_count: int
    submitted_at: datetime
    results: list[QuizAttemptQuestionResult]


class QuizAttemptRead(ORMModel):
    id: int
    quiz_id: int
    student_id: int
    score: float
    answers: dict[str, str]
    submitted_at: datetime


class QuizAnalyticsItem(BaseModel):
    student_id: int
    student_name: str
    student_email: str
    score: float
    submitted_at: datetime


class QuizWithAttemptRead(QuizRead):
    id: int
    classroom_id: int
    title: str
    deadline: datetime
    is_published: bool
    randomise_order: bool
    questions: list[QuizQuestionPublicRead]
    my_attempt: QuizAttemptRead | None = None


class QuizAnalyticsResponse(BaseModel):
    quiz_id: int
    title: str
    deadline: datetime
    attempts: list[QuizAnalyticsItem]
