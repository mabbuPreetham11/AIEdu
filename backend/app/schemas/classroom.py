from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import TimestampedSchema


class ClassroomCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class JoinClassroomRequest(BaseModel):
    invite_code: str = Field(min_length=6, max_length=6)


class TeacherClassroomRead(TimestampedSchema):
    id: int
    name: str
    teacher_id: int
    invite_code: str
    qr_code_data_url: str


class StudentClassroomRead(BaseModel):
    id: int
    name: str
    teacher_id: int
    invite_code: str
    joined_at: datetime
