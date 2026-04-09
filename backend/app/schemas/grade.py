from pydantic import BaseModel

from app.schemas.common import TimestampedSchema


class GradeRead(TimestampedSchema):
    id: int
    submission_id: int
    student_id: int
    course_id: int
    grade_type: str
    score: float
    max_score: float
    ai_graded: bool
    ai_feedback: dict | None
    improvement_suggestions: str | None
    focus_areas: list[str] | None
    graded_by: int | None
    is_final: bool


class GradeUpdate(BaseModel):
    score: float | None = None
    ai_feedback: dict | None = None
    improvement_suggestions: str | None = None
    focus_areas: list[str] | None = None
    is_final: bool | None = None

