from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.course import Course
from app.models.user import User, UserRole
from app.schemas.common import MessageResponse
from app.schemas.course import CourseCreate, CourseRead, CourseUpdate, EnrollmentRequest
from app.services.course_service import CourseService
from app.services.storage_service import StorageService

router = APIRouter()


@router.get("/", response_model=list[CourseRead])
async def list_courses(
    db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]
) -> list[Course]:
    result = await db.scalars(select(Course))
    return list(result.all())


@router.post("/", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    teacher: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> Course:
    return await CourseService(db).create_course(teacher, payload)


@router.patch("/{course_id}", response_model=CourseRead)
async def update_course(
    course_id: int,
    payload: CourseUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> Course:
    course = await db.scalar(select(Course).where(Course.id == course_id))
    return await CourseService(db).update_course(course, payload)


@router.post("/enroll", response_model=MessageResponse)
async def enroll(
    payload: EnrollmentRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role(UserRole.student))],
) -> MessageResponse:
    await CourseService(db).enroll(student, payload.class_code)
    return MessageResponse(detail="Enrollment successful")


@router.post("/{course_id}/upload-info", response_model=MessageResponse)
async def upload_course_info(
    course_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.teacher)),
) -> MessageResponse:
    course = await db.scalar(select(Course).where(Course.id == course_id))
    storage = StorageService()
    content = await file.read()
    url = storage.upload_bytes(f"course-info/{course_id}/{file.filename}", content, file.content_type or "application/octet-stream")
    course.course_info_url = url
    course.syllabus = {"status": "queued", "source_file": file.filename}
    course.grading_weights = {"quizzes": 10, "assignments": 20, "projects": 20, "midsem": 20, "endsem": 30}
    await db.commit()
    return MessageResponse(detail="Course info uploaded and AI extraction queued")
