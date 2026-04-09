from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.assignment import Assignment, Submission
from app.models.user import User, UserRole
from app.schemas.assignment import (
    AssignmentCreate,
    AssignmentGenerateRequest,
    AssignmentRead,
    SubmissionCreate,
    SubmissionRead,
)
from app.services.assignment_service import AssignmentService
from app.services.grade_service import GradeService

router = APIRouter()


@router.get("/", response_model=list[AssignmentRead])
async def list_assignments(
    db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]
) -> list[Assignment]:
    result = await db.scalars(select(Assignment))
    return list(result.all())


@router.post("/", response_model=AssignmentRead)
async def create_assignment(
    payload: AssignmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> Assignment:
    return await AssignmentService(db).create_assignment(payload)


@router.post("/generate", response_model=AssignmentRead)
async def generate_assignment(
    payload: AssignmentGenerateRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> Assignment:
    return await AssignmentService(db).generate_assignment(payload)


@router.post("/submit", response_model=SubmissionRead)
async def submit_assignment(
    payload: SubmissionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role(UserRole.student))],
) -> Submission:
    service = AssignmentService(db)
    submission = await service.create_submission(student.id, payload)
    assignment = await db.scalar(select(Assignment).where(Assignment.id == submission.assignment_id))
    if assignment and assignment.type != "quiz":
        await GradeService(db).auto_grade_submission(submission, assignment)
    return submission
