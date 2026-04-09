from pydantic import BaseModel

from app.schemas.common import ORMModel, TimestampedSchema


class ConversationCreate(BaseModel):
    course_id: int | None = None
    context_type: str
    title: str


class MessageCreate(BaseModel):
    content: str


class CitationRead(ORMModel):
    doc_name: str
    page_number: int


class ChatMessageRead(TimestampedSchema):
    id: int
    conversation_id: int
    role: str
    content: str
    citations: list[CitationRead] = []


class ConversationRead(TimestampedSchema):
    id: int
    user_id: int
    course_id: int | None
    context_type: str
    title: str
    pdf_url: str | None


class ClassroomQuestionRequest(BaseModel):
    question: str


class SpeechTranscriptionResponse(BaseModel):
    transcript: str
    language_code: str | None = None


class ClassroomVoiceChatResponse(BaseModel):
    transcript_original: str
    transcript_english: str
    detected_language_code: str | None = None
    answer_text: str
    answer_language_code: str
    answer_audio_base64: str
    answer_audio_mime_type: str
    assistant_message: ChatMessageRead
