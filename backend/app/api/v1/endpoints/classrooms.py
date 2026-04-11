from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

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
from app.schemas.chat import ChatMessageRead, CitationRead, ClassroomQuestionRequest, ClassroomVoiceChatResponse
from app.schemas.classroom import ClassroomCreate, JoinClassroomRequest, StudentClassroomRead, TeacherClassroomRead
from app.schemas.material import MaterialRead
from app.schemas.quiz import (
    QuizAnalyticsItem,
    QuizAnalyticsResponse,
    QuizAttemptQuestionResult,
    QuizAttemptRead,
    QuizAttemptSubmitRequest,
    QuizAttemptSubmitResponse,
    QuizGenerateRequest,
    QuizGenerateResponse,
    QuizPublishRequest,
    QuizRead,
    QuizWithAttemptRead,
)
from app.services.chat_service import ChatService
from app.services.classroom_service import ClassroomService, classroom_qr_code_data_url
from app.services.material_service import MaterialService
from app.services.quiz_service import QuizService
from app.services.voice_chat_service import VoiceChatService

router = APIRouter()


def _frontend_base_url_from_request(request: Request) -> str:
    forwarded_host = request.headers.get("x-forwarded-host")
    if forwarded_host:
        forwarded_proto = request.headers.get("x-forwarded-proto", "https").split(",")[0].strip()
        host = forwarded_host.split(",")[0].strip()
        if host:
            return f"{forwarded_proto}://{host}"

    origin = request.headers.get("origin")
    if origin:
        parsed = urlparse(origin)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"

    referer = request.headers.get("referer")
    if referer:
        parsed = urlparse(referer)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"

    return settings.frontend_url


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


def _quiz_with_attempt_read(quiz: Quiz, user: User) -> QuizWithAttemptRead:
    my_attempt = None
    if user.role == UserRole.student:
        match = next((item for item in quiz.attempts if item.student_id == user.id), None)
        if match:
            my_attempt = QuizAttemptRead.model_validate(match)
    return QuizWithAttemptRead(
        id=quiz.id,
        classroom_id=quiz.classroom_id,
        title=quiz.title,
        deadline=quiz.deadline,
        is_published=quiz.is_published,
        randomise_order=quiz.randomise_order,
        questions=sorted(quiz.questions, key=lambda item: item.order_number),
        created_at=quiz.created_at,
        updated_at=quiz.updated_at,
        my_attempt=my_attempt,
    )


@router.post("/", response_model=TeacherClassroomRead, status_code=status.HTTP_201_CREATED)
async def create_classroom(
    request: Request,
    payload: ClassroomCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    teacher: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> TeacherClassroomRead:
    classroom = await ClassroomService(db).create_classroom(teacher, payload.name)
    frontend_base_url = _frontend_base_url_from_request(request)
    return TeacherClassroomRead(
        id=classroom.id,
        name=classroom.name,
        teacher_id=classroom.teacher_id,
        invite_code=classroom.invite_code,
        created_at=classroom.created_at,
        updated_at=classroom.updated_at,
        qr_code_data_url=classroom_qr_code_data_url(classroom.invite_code, frontend_base_url),
    )


@router.get("/teacher", response_model=list[TeacherClassroomRead])
async def list_teacher_classrooms(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    teacher: Annotated[User, Depends(require_role(UserRole.teacher))],
) -> list[TeacherClassroomRead]:
    classrooms = await ClassroomService(db).list_teacher_classrooms(teacher)
    frontend_base_url = _frontend_base_url_from_request(request)
    return [
        TeacherClassroomRead(
            id=classroom.id,
            name=classroom.name,
            teacher_id=classroom.teacher_id,
            invite_code=classroom.invite_code,
            created_at=classroom.created_at,
            updated_at=classroom.updated_at,
            qr_code_data_url=classroom_qr_code_data_url(classroom.invite_code, frontend_base_url),
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


@router.post("/{classroom_id}/chat/voice", response_model=ClassroomVoiceChatResponse)
@limiter.limit("8/minute")
async def ask_classroom_chat_voice_question(
    request: Request,
    classroom_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_role(UserRole.student)),
) -> ClassroomVoiceChatResponse:
    del request
    result = await VoiceChatService(db).ask_voice_question(classroom_id=classroom_id, student=student, file=file)
    assistant = result["assistant_message"]
    return ClassroomVoiceChatResponse(
        transcript_original=result["transcript_original"],
        transcript_english=result["transcript_english"],
        detected_language_code=result["detected_language_code"],
        answer_text=result["answer_text"],
        answer_language_code=result["answer_language_code"],
        answer_audio_base64=result["answer_audio_base64"],
        answer_audio_mime_type=result["answer_audio_mime_type"],
        assistant_message=_chat_message_read(assistant),
    )


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


@router.get("/{classroom_id}/quizzes", response_model=list[QuizWithAttemptRead])
async def list_classroom_quizzes(
    classroom_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[QuizWithAttemptRead]:
    quizzes = await QuizService(db).list_quizzes(classroom_id=classroom_id, user=user)
    return [_quiz_with_attempt_read(item, user) for item in quizzes]


@router.post("/{classroom_id}/quizzes/{quiz_id}/attempt", response_model=QuizAttemptSubmitResponse)
async def submit_quiz_attempt(
    classroom_id: int,
    quiz_id: int,
    payload: QuizAttemptSubmitRequest,
    db: AsyncSession = Depends(get_db),
    student: User = Depends(require_role(UserRole.student)),
) -> QuizAttemptSubmitResponse:
    service = QuizService(db)
    attempt = await service.submit_attempt(classroom_id=classroom_id, quiz_id=quiz_id, student=student, answers=payload.answers)
    quiz = await service.get_quiz(classroom_id=classroom_id, quiz_id=quiz_id, user=student)

    results: list[QuizAttemptQuestionResult] = []
    correct_count = 0
    for question in sorted(quiz.questions, key=lambda item: item.order_number):
        selected = str(attempt.answers.get(str(question.id), "")).strip()
        is_correct = selected.strip().lower() == question.correct_answer.strip().lower()
        if question.type == "true_false":
            yes_vals = {"true", "t", "1", "yes"}
            no_vals = {"false", "f", "0", "no"}
            left = "true" if selected.lower() in yes_vals else "false" if selected.lower() in no_vals else selected.lower()
            right = "true" if question.correct_answer.lower() in yes_vals else "false" if question.correct_answer.lower() in no_vals else question.correct_answer.lower()
            is_correct = left == right
        if is_correct:
            correct_count += 1
        results.append(
            QuizAttemptQuestionResult(
                question_id=question.id,
                question=question.question,
                selected_answer=selected,
                correct_answer=question.correct_answer,
                is_correct=is_correct,
                explanation=question.explanation,
            )
        )

    return QuizAttemptSubmitResponse(
        attempt_id=attempt.id,
        quiz_id=quiz.id,
        score=attempt.score,
        total_questions=len(quiz.questions),
        correct_count=correct_count,
        submitted_at=attempt.submitted_at,
        results=results,
    )


@router.get("/{classroom_id}/quizzes/{quiz_id}/analytics", response_model=QuizAnalyticsResponse)
async def get_quiz_analytics(
    classroom_id: int,
    quiz_id: int,
    db: AsyncSession = Depends(get_db),
    teacher: User = Depends(require_role(UserRole.teacher)),
) -> QuizAnalyticsResponse:
    quiz, attempts = await QuizService(db).get_quiz_analytics(classroom_id=classroom_id, quiz_id=quiz_id, teacher=teacher)
    items = [
        QuizAnalyticsItem(
            student_id=item.student_id,
            student_name=f"{item.student.first_name} {item.student.last_name}".strip(),
            student_email=item.student.email,
            score=item.score,
            submitted_at=item.submitted_at,
        )
        for item in attempts
    ]
    return QuizAnalyticsResponse(
        quiz_id=quiz.id,
        title=quiz.title,
        deadline=quiz.deadline,
        attempts=items,
    )
