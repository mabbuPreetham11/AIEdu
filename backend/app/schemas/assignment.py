from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from app.schemas.common import ORMModel, TimestampedSchema

AssignmentType = Literal["quiz", "essay", "report", "project", "code"]


class AssignmentGenerateRequest(BaseModel):
    course_id: int
    type: AssignmentType
    title: str
    topics_covered: list[str]
    assigned_date: datetime
    due_date: datetime
    weightage: float
    max_score: float = 100
    num_questions: int | None = None


class AssignmentCreate(BaseModel):
    course_id: int
    title: str
    description: str
    type: AssignmentType
    topics_covered: list[str]
    assigned_date: datetime
    due_date: datetime
    weightage: float
    max_score: float = 100
    ai_generated: bool = False


class AssignmentRead(TimestampedSchema):
    id: int
    course_id: int
    title: str
    description: str
    type: str
    topics_covered: list[str] | None
    assigned_date: datetime
    due_date: datetime
    weightage: float
    max_score: float
    ai_generated: bool


class QuizQuestionRead(ORMModel):
    id: int
    assignment_id: int
    question_text: str
    options: list[str]
    points: float
    order_number: int


class SubmissionCreate(BaseModel):
    assignment_id: int
    submission_text: str | None = None
    quiz_answers: dict | None = None


class SubmissionRead(TimestampedSchema):
    id: int
    assignment_id: int
    student_id: int
    submission_url: str | None
    submission_text: str | None
    quiz_answers: dict | None
    plagiarism_score: float | None
    plagiarism_report: dict | None

