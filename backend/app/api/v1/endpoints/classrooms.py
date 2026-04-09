from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, require_role
from app.core.config import settings
from app.core.exceptions import LMSException
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.chat import ChatMessage
from app.models.material import MaterialType
from app.models.quiz import Quiz
from app.models.user import User, UserRole
from app.schemas.chat import ChatMessageRead, CitationRead, ClassroomQuestionRequest
from app.schemas.classroom import ClassroomCreate, JoinClassroomRequest, StudentClassroomRead, TeacherClassroomRead
from app.schemas.material import MaterialRead
from app.schemas.quiz import QuizGenerateRequest, QuizGenerateResponse, QuizPublishRequest, QuizRead
from app.services.chat_service import ChatService
from app.services.classroom_service import ClassroomService, classroom_qr_code_data_url
from app.services.material_service import MaterialService
from app.services.quiz_service import QuizService

router = APIRouter()


def _chat_message_read(message: ChatMessage) -> ChatMessageRead:
    return ChatMessageRead(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at,
        updated_at=message.updated_at,
        citations=[CitationRead(doc_name=item.doc_name, page_number=item.page_number) for item in message.citations],
    )


@router.post("/", response_model=TeacherClassroomRead, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    payload: ClassroomCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    teacher: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> TeacherClassroomRead:
    classroom = await ClassroomService(db).create_classroom(teacher, payload.name)
    return TeacherClassroomRead(
        id=classroom.id,
        name=classroom.name,
        teacher_id=classroom.teacher_id,
        invite_code=classroom.invite_code,
        created_at=classroom.created_at,
        updated_at=classroom.updated_at,
        qr_code_data_url=classroom_qr_code_data_url(classroom.invite_code),
    )


@router.get("/teacher", response_model=list[TeacherClassroomRead])
async def list_teacher_classrooms(
    db: Annotated[AsyncSession, Depends(get_db)],
    teacher: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> list[TeacherClassroomRead]:
    classrooms = await ClassroomService(db).list_teacher_classrooms(teacher)
    return [
        TeacherClassroomRead(
            id=classroom.id,
            name=classroom.name,
            teacher_id=classroom.teacher_id,
            invite_code=classroom.invite_code,
            created_at=classroom.created_at,
            updated_at=classroom.updated_at,
            qr_code_data_url=classroom_qr_code_data_url(classroom.invite_code),
        )
        for classroom in classrooms
    ]


@router.post("/join", response_model=StudentClassroomRead)
async def join_classroom(
    payload: JoinClassroomRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role(UserRole.student))],
) -> StudentClassroomRead:
    classroom, membership = await ClassroomService(db).join_by_invite_code(student, payload.invite_code)
    return StudentClassroomRead(
        id=classroom.id,
        name=classroom.name,
        teacher_id=classroom.teacher_id,
        invite_code=classroom.invite_code,
        joined_at=membership.joined_at,
    )


@router.get("/student", response_model=list[StudentClassroomRead])
async def list_student_classrooms(
    db: Annotated[AsyncSession, Depends(get_db)],
    student: Annotated[User, Depends(require_role(UserRole.student))],
) -> list[StudentClassroomRead]:
    rows = await ClassroomService(db).list_student_classrooms(student)
    return [
        StudentClassroomRead(
            id=classroom.id,
            name=classroom.name,
            teacher_id=classroom.teacher_id,
            invite_code=classroom.invite_code,
            joined_at=membership.joined_at,
        )
        for classroom, membership in rows
    ]


@router.post("/{classroom_id}/materials", response_model=MaterialRead, status_code=status.HTTP_201_CREATED)
async def upload_classroom_material(
    classroom_id: int,
    title: str = Form(...),
    type: str = Form(...),
    url: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_role(UserRole.teacher)),
) -> MaterialRead:
    material = await MaterialService(db).create_material(
        classroom_id=classroom_id,
        teacher=teacher,
        title=title,
        material_type=type,
        url=url,
        file=file,
    )
    file_url = f"/uploads/{material.file_path}" if material.file_path else None
    return MaterialRead(
        id=material.id,
        classroom_id=material.classroom_id,
        uploader_id=material.uploader_id,
        title=material.title,
        type=material.type.value,
        file_path=material.file_path,
        url=material.url,
        uploaded_at=material.uploaded_at,
        file_url=file_url,
    )


@router.get("/{classroom_id}/materials", response_model=list[MaterialRead])
async def list_classroom_materials(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[MaterialRead]:
    materials = await MaterialService(db).list_for_classroom(classroom_id, user)
    return [
        MaterialRead(
            id=material.id,
            classroom_id=material.classroom_id,
            uploader_id=material.uploader_id,
            title=material.title,
            type=material.type.value,
            file_path=material.file_path,
            url=material.url,
            uploaded_at=material.uploaded_at,
            file_url=f"/uploads/{material.file_path}" if material.file_path else None,
        )
        for material in materials
    ]


@router.get("/{classroom_id}/materials/{material_id}/download")
async def download_classroom_material(
    classroom_id: int,
    material_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> FileResponse:
    material = await MaterialService(db).get_material_for_download(classroom_id, material_id, user)
    if not material.file_path:
        raise LMSException(status_code=404, detail="File not found")

    file_path = str((Path(settings.local_storage_path) / material.file_path).resolve())
    filename = f"{material.title}.pdf" if material.type in {MaterialType.pdf, MaterialType.slide} else material.title
    return FileResponse(path=file_path, media_type="application/pdf", filename=filename)


@router.get("/{classroom_id}/chat/messages", response_model=list[ChatMessageRead])
async def list_classroom_chat_messages(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[ChatMessageRead]:
    messages = await ChatService(db).list_classroom_messages(classroom_id, user)
    return [_chat_message_read(item) for item in messages]


@router.post("/{classroom_id}/chat/messages", response_model=ChatMessageRead)
@limiter.limit("12/minute")
async def ask_classroom_chat_question(
    request: Request,
    classroom_id: int,
    payload: ClassroomQuestionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ChatMessageRead:
    del request
    message = await ChatService(db).ask_classroom_question(classroom_id, user, payload.question.strip())
    return _chat_message_read(message)


@router.post("/{classroom_id}/quizzes/generate", response_model=QuizGenerateResponse)
async def generate_classroom_quiz_questions(
    classroom_id: int,
    payload: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_role(UserRole.teacher)),
) -> QuizGenerateResponse:
    questions = await QuizService(db).generate_questions(
        classroom_id=classroom_id,
        teacher=teacher,
        topic=payload.topic,
        material_id=payload.material_id,
    )
    return QuizGenerateResponse(questions=questions)


@router.post("/{classroom_id}/quizzes", response_model=QuizRead, status_code=status.HTTP_201_CREATED)
async def publish_classroom_quiz(
    classroom_id: int,
    payload: QuizPublishRequest,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_role(UserRole.teacher)),
) -> Quiz:
    return await QuizService(db).publish_quiz(classroom_id=classroom_id, teacher=teacher, payload=payload)


@router.get("/{classroom_id}/quizzes", response_model=list[QuizRead])
async def list_classroom_quizzes(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[Quiz]:
    return await QuizService(db).list_quizzes(classroom_id=classroom_id, user=user)
