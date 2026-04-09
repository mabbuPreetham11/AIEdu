from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assignment import Assignment, QuizQuestion, Submission
from app.schemas.assignment import AssignmentCreate, AssignmentGenerateRequest, SubmissionCreate
from app.services.ai_service import AIService
from app.services.plagiarism_service import PlagiarismService


class AssignmentService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()
        self.plagiarism = PlagiarismService()

    async def create_assignment(self, payload: AssignmentCreate) -> Assignment:
        assignment = Assignment(**payload.model_dump())
        self.db.add(assignment)
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def generate_assignment(self, payload: AssignmentGenerateRequest) -> Assignment:
        description, questions = self.ai_service.generate_assignment(payload)
        assignment = Assignment(
            course_id=payload.course_id,
            title=payload.title,
            description=description,
            type=payload.type,
            topics_covered=payload.topics_covered,
            assigned_date=payload.assigned_date,
            due_date=payload.due_date,
            weightage=payload.weightage,
            max_score=payload.max_score,
            ai_generated=True,
        )
        self.db.add(assignment)
        await self.db.flush()
        for index, question in enumerate(questions, start=1):
            self.db.add(
                QuizQuestion(
                    assignment_id=assignment.id,
                    question_text=question["question_text"],
                    options=question.get("options", []),
                    correct_answer=question.get("correct_answer", ""),
                    points=question.get("points", 1),
                    order_number=index,
                )
            )
        await self.db.commit()
        await self.db.refresh(assignment)
        return assignment

    async def create_submission(self, student_id: int, payload: SubmissionCreate) -> Submission:
        submission = Submission(student_id=student_id, **payload.model_dump())
        self.db.add(submission)
        await self.db.flush()
        if payload.submission_text:
            plagiarism_result = self.plagiarism.scan_text(payload.submission_text)
            submission.plagiarism_score = plagiarism_result["score"]
            submission.plagiarism_report = plagiarism_result
        await self.db.commit()
        await self.db.refresh(submission)
        return submission

