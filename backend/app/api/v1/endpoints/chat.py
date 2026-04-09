from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user
from app.db.session import get_db
from app.models.chat import ChatConversation, ChatMessage
from app.models.user import User
from app.schemas.chat import ChatMessageRead, ConversationCreate, ConversationRead, MessageCreate, SpeechTranscriptionResponse
from app.schemas.common import MessageResponse
from app.services.chat_service import ChatService
from app.services.speech_service import SpeechService
from app.services.storage_service import StorageService

router = APIRouter()


@router.get("/conversations", response_model=list[ConversationRead])
async def list_conversations(
    db: Annotated[AsyncSession, Depends(get_db)], user: Annotated[User, Depends(get_current_user)]
) -> list[ChatConversation]:
    result = await db.scalars(select(ChatConversation).where(ChatConversation.user_id == user.id))
    return list(result.all())


@router.post("/conversations", response_model=ConversationRead)
async def create_conversation(
    payload: ConversationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> ChatConversation:
    return await ChatService(db).create_conversation(user.id, payload)


@router.get("/conversations/{conversation_id}/messages", response_model=list[ChatMessageRead])
async def list_messages(conversation_id: int, db: Annotated[AsyncSession, Depends(get_db)]) -> list[ChatMessage]:
    result = await db.scalars(select(ChatMessage).where(ChatMessage.conversation_id == conversation_id))
    return list(result.all())


@router.post("/conversations/{conversation_id}/messages", response_model=ChatMessageRead)
async def send_message(
    conversation_id: int,
    payload: MessageCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    _: Annotated[User, Depends(get_current_user)],
) -> ChatMessage:
    conversation = await db.scalar(select(ChatConversation).where(ChatConversation.id == conversation_id))
    return await ChatService(db).add_message(conversation, payload.content)


@router.post("/upload-pdf", response_model=MessageResponse)
async def upload_pdf(
    conversation_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> MessageResponse:
    storage = StorageService()
    content = await file.read()
    url = storage.upload_bytes(
        f"chat-uploads/{user.id}/{conversation_id}/{file.filename}",
        content,
        file.content_type or "application/pdf",
    )
    conversation = await db.scalar(select(ChatConversation).where(ChatConversation.id == conversation_id))
    conversation.pdf_url = url
    await db.commit()
    return MessageResponse(detail="PDF uploaded successfully")


@router.post("/speech-to-text", response_model=SpeechTranscriptionResponse)
async def speech_to_text(
    file: UploadFile = File(...),
    model: str | None = Form(default=None),
    mode: str | None = Form(default=None),
    language_code: str | None = Form(default=None),
    _: User = Depends(get_current_user),
) -> SpeechTranscriptionResponse:
    transcript, detected_language = await SpeechService().transcribe_with_sarvam(
        file=file,
        model=model,
        mode=mode,
        language_code=language_code,
    )
    return SpeechTranscriptionResponse(transcript=transcript, language_code=detected_language)
