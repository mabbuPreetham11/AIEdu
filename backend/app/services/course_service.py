import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LMSException
from app.models.course import Course, CourseEnrollment, SessionNote
from app.models.user import User
from app.schemas.course import CourseCreate, CourseUpdate, SessionCreate
from app.services.ai_service import AIService


class CourseService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    async def create_course(self, teacher: User, payload: CourseCreate) -> Course:
        course = Course(
            course_code=payload.course_code,
            title=payload.title,
            teacher_id=teacher.id,
            class_code=secrets.token_hex(3).upper(),
            semester=payload.semester,
            year=payload.year,
        )
        self.db.add(course)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def update_course(self, course: Course | None, payload: CourseUpdate) -> Course:
        if not course:
            raise LMSException(status_code=404, detail="Course not found")
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(course, field, value)
        await self.db.commit()
        await self.db.refresh(course)
        return course

    async def enroll(self, student: User, class_code: str) -> CourseEnrollment:
        course = await self.db.scalar(select(Course).where(Course.class_code == class_code))
        if not course:
            raise LMSException(status_code=404, detail="Class code not found")
        enrollment = CourseEnrollment(course_id=course.id, student_id=student.id)
        self.db.add(enrollment)
        await self.db.commit()
        await self.db.refresh(enrollment)
        return enrollment

    async def create_session(self, payload: SessionCreate) -> tuple[object, str]:
        from app.models.course import ClassSession

        session = ClassSession(**payload.model_dump())
        self.db.add(session)
        await self.db.flush()
        notes_markdown = self.ai_service.generate_notes(topics_covered=payload.topics_covered, course_name=f"Course {payload.course_id}")
        note = SessionNote(session=session, content=notes_markdown, is_template=True)
        self.db.add(note)
        await self.db.commit()
        await self.db.refresh(session)
        return session, notes_markdown

