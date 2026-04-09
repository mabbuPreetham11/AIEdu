from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, Submission
from app.models.grade import Grade
from app.schemas.grade import GradeUpdate
from app.services.ai_service import AIService


class GradeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()

    async def auto_grade_submission(self, submission: Submission, assignment: Assignment) -> Grade:
        result = self.ai_service.grade_submission(
            assignment_type=assignment.type,
            description=assignment.description,
            text=submission.submission_text or "",
            rubric=assignment.topics_covered or [],
            max_score=float(assignment.max_score),
        )
        grade = Grade(
            submission_id=submission.id,
            student_id=submission.student_id,
            course_id=assignment.course_id,
            grade_type=assignment.type,
            score=result["score"],
            max_score=float(assignment.max_score),
            ai_graded=True,
            ai_feedback=result,
            improvement_suggestions=", ".join(result.get("suggestions", [])),
            focus_areas=result.get("focus_areas", []),
            is_final=False,
        )
        self.db.add(grade)
        await self.db.commit()
        await self.db.refresh(grade)
        return grade

    async def update_grade(self, grade_id: int, payload: GradeUpdate) -> Grade | None:
        grade = await self.db.scalar(select(Grade).where(Grade.id == grade_id))
        if not grade:
            return None
        for field, value in payload.model_dump(exclude_none=True).items():
            setattr(grade, field, value)
        await self.db.commit()
        await self.db.refresh(grade)
        return grade
