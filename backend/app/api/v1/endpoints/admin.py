import csv
from io import StringIO
from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import require_role
from app.core.security import get_password_hash
from app.db.session import get_db
from app.models.course import Course
from app.models.user import User, UserRole
from app.schemas.admin import UserCreateByAdmin
from app.schemas.common import MessageResponse
from app.schemas.course import CourseRead
from app.schemas.user import UserRead

router = APIRouter(dependencies=[Depends(require_role(UserRole.admin))])


@router.get("/users", response_model=list[UserRead])
async def list_users(db: Annotated[AsyncSession, Depends(get_db)]) -> list[User]:
    result = await db.scalars(select(User))
    return list(result.all())


@router.post("/users", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreateByAdmin, db: Annotated[AsyncSession, Depends(get_db)]) -> User:
    user = User(
        email=payload.email.lower(),
        first_name=payload.first_name,
        last_name=payload.last_name,
        role=payload.role,
        password_hash=get_password_hash(payload.password),
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/bulk-import", response_model=MessageResponse)
async def bulk_import_users(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)) -> MessageResponse:
    content = (await file.read()).decode("utf-8")
    reader = csv.DictReader(StringIO(content))
    for row in reader:
        db.add(
            User(
                email=row["email"].lower(),
                first_name=row["first_name"],
                last_name=row["last_name"],
                role=UserRole(row["role"]),
                password_hash=get_password_hash(row.get("password", "ChangeMe123!")),
                is_verified=True,
            )
        )
    await db.commit()
    return MessageResponse(detail="Bulk import completed")


@router.get("/courses", response_model=list[CourseRead])
async def list_all_courses(db: Annotated[AsyncSession, Depends(get_db)]) -> list[Course]:
    result = await db.scalars(select(Course))
    return list(result.all())


@router.get("/analytics")
async def analytics(db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    total_users = await db.scalar(select(func.count()).select_from(User))
    total_courses = await db.scalar(select(func.count()).select_from(Course))
    return {"total_users": total_users, "total_courses": total_courses}
