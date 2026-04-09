from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.grade import Grade
from app.models.user import User, UserRole
from app.schemas.grade import GradeRead, GradeUpdate
from app.services.export_service import ExportService
from app.services.grade_service import GradeService
from app.services.storage_service import StorageService

router = APIRouter()


@router.get("/", response_model=list[GradeRead])
async def list_grades(db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]) -> list[Grade]:
    result = await db.scalars(select(Grade))
    return list(result.all())


@router.patch("/{grade_id}", response_model=GradeRead)
async def update_grade(
    grade_id: int,
    payload: GradeUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> Grade:
    return await GradeService(db).update_grade(grade_id, payload)


@router.get("/export/{course_id}")
async def export_grades(
    course_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> Response:
    grades = await db.scalars(select(Grade).where(Grade.course_id == course_id))
    rows = [
        {
            "Student Name": f"Student {grade.student_id}",
            "Quizzes": grade.score if grade.grade_type == "quiz" else "",
            "Assignments": grade.score if grade.grade_type in {"essay", "report"} else "",
            "Projects": grade.score if grade.grade_type in {"project", "code"} else "",
            "Midsem": "",
            "Endsem": "",
            "Final Score": grade.score,
        }
        for grade in grades
    ]
    content = ExportService().build_gradebook_xlsx(rows)
    StorageService().upload_bytes(
        f"exports/{course_id}/gradebook.xlsx",
        content,
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="gradebook.xlsx"'},
    )
