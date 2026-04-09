from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_role
from app.db.session import get_db
from app.models.course import ClassSession, SessionNote
from app.models.user import User, UserRole
from app.schemas.course import SessionCreate, SessionNoteRead, SessionNoteUpdate, SessionRead
from app.services.course_service import CourseService

router = APIRouter()


@router.post("/", response_model=SessionRead)
async def create_session(
    payload: SessionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> ClassSession:
    session, _ = await CourseService(db).create_session(payload)
    return session


@router.get("/", response_model=list[SessionRead])
async def list_sessions(db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]) -> list[ClassSession]:
    result = await db.scalars(select(ClassSession))
    return list(result.all())


@router.get("/{session_id}/notes", response_model=list[SessionNoteRead])
async def list_notes(
    session_id: int, db: Annotated[AsyncSession, Depends(get_db)], _: Annotated[User, Depends(get_current_user)]
) -> list[SessionNote]:
    result = await db.scalars(select(SessionNote).where(SessionNote.session_id == session_id))
    return list(result.all())


@router.patch("/notes/{note_id}", response_model=SessionNoteRead)
async def update_note(
    note_id: int,
    payload: SessionNoteUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> SessionNote:
    note = await db.scalar(select(SessionNote).where(SessionNote.id == note_id))
    note.content = payload.content
    await db.commit()
    await db.refresh(note)
    return note

