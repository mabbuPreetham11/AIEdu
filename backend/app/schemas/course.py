from datetime import date

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedSchema


class CourseCreate(BaseModel):
    course_code: str = Field(min_length=2, max_length=50)
    title: str = Field(min_length=3, max_length=255)
    semester: str = Field(min_length=2, max_length=30)
    year: int = Field(ge=2020, le=2100)


class CourseUpdate(BaseModel):
    title: str | None = None
    semester: str | None = None
    year: int | None = None
    is_archived: bool | None = None


class CourseRead(TimestampedSchema):
    id: int
    course_code: str
    title: str
    teacher_id: int
    class_code: str
    course_info_url: str | None
    syllabus: dict | None
    grading_weights: dict | None
    semester: str
    year: int
    is_archived: bool


class EnrollmentRequest(BaseModel):
    class_code: str = Field(min_length=4, max_length=16)


class SessionCreate(BaseModel):
    course_id: int
    session_number: int
    topics_covered: str
    session_date: date


class SessionRead(TimestampedSchema):
    id: int
    course_id: int
    session_number: int
    topics_covered: str
    session_date: date


class SessionNoteUpdate(BaseModel):
    content: str


class SessionNoteRead(TimestampedSchema):
    id: int
    session_id: int
    student_id: int | None
    content: str
    is_template: bool

