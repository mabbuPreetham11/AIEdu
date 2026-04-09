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
