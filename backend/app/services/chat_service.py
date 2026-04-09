from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import LMSException
from app.models.chat import ChatConversation, ChatMessage, ChatMessageCitation
from app.models.classroom import Classroom, ClassroomMember
from app.models.user import User, UserRole
from app.schemas.chat import CitationRead, ConversationCreate
from app.services.ai_service import AIService
from app.services.rag_service import RAGService


class ChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ai_service = AIService()
        self.rag_service = RAGService()

    async def create_conversation(self, user_id: int, payload: ConversationCreate) -> ChatConversation:
        conversation = ChatConversation(user_id=user_id, **payload.model_dump())
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def add_message(self, conversation: ChatConversation, content: str) -> ChatMessage:
        user_message = ChatMessage(conversation_id=conversation.id, role="user", content=content)
        self.db.add(user_message)
        await self.db.flush()
        ai_response = self.ai_service.answer_course_question(content=content, context_type=conversation.context_type)
        assistant_message = ChatMessage(conversation_id=conversation.id, role="assistant", content=ai_response)
        self.db.add(assistant_message)
        await self.db.commit()
        await self.db.refresh(assistant_message)
        return assistant_message

    async def get_or_create_classroom_conversation(self, classroom_id: int, student_id: int) -> ChatConversation:
        context_key = f"classroom:{classroom_id}"
        conversation = await self.db.scalar(
            select(ChatConversation).where(ChatConversation.user_id == student_id, ChatConversation.context_type == context_key)
        )
        if conversation:
            return conversation
        conversation = ChatConversation(
            user_id=student_id,
            context_type=context_key,
            title=f"Classroom {classroom_id} Q&A",
        )
        self.db.add(conversation)
        await self.db.commit()
        await self.db.refresh(conversation)
        return conversation

    async def list_classroom_messages(self, classroom_id: int, student: User) -> list[ChatMessage]:
        await self._ensure_classroom_student_access(classroom_id, student)
        conversation = await self.get_or_create_classroom_conversation(classroom_id, student.id)
        result = await self.db.scalars(
            select(ChatMessage)
            .options(selectinload(ChatMessage.citations))
            .where(ChatMessage.conversation_id == conversation.id)
            .order_by(ChatMessage.created_at.asc())
        )
        return list(result.all())

    async def ask_classroom_question(self, classroom_id: int, student: User, question: str) -> ChatMessage:
        await self._ensure_classroom_student_access(classroom_id, student)
        conversation = await self.get_or_create_classroom_conversation(classroom_id, student.id)

        user_message = ChatMessage(conversation_id=conversation.id, role="user", content=question)
        self.db.add(user_message)
        await self.db.flush()

        chunks = self.rag_service.retrieve(classroom_id=classroom_id, question=question, k=8)
        if not chunks:
            answer = "I could not find relevant content in the uploaded course material for this classroom."
            assistant = ChatMessage(conversation_id=conversation.id, role="assistant", content=answer)
            self.db.add(assistant)
            await self.db.commit()
            loaded = await self.db.scalar(
                select(ChatMessage).options(selectinload(ChatMessage.citations)).where(ChatMessage.id == assistant.id)
            )
            if not loaded:
                raise LMSException(status_code=500, detail="Failed to load assistant chat response")
            return loaded

        answer = self.rag_service.answer_with_llm(question=question, chunks=chunks)
        assistant = ChatMessage(conversation_id=conversation.id, role="assistant", content=answer)
        self.db.add(assistant)
        await self.db.flush()

        for chunk in chunks:
            citation = ChatMessageCitation(
                message_id=assistant.id,
                doc_name=chunk.doc_name,
                page_number=chunk.page_number,
            )
            self.db.add(citation)

        await self.db.commit()
        loaded = await self.db.scalar(
            select(ChatMessage).options(selectinload(ChatMessage.citations)).where(ChatMessage.id == assistant.id)
        )
        if not loaded:
            raise LMSException(status_code=500, detail="Failed to load assistant chat response")
        return loaded

    async def _ensure_classroom_student_access(self, classroom_id: int, user: User) -> None:
        classroom = await self.db.scalar(select(Classroom).where(Classroom.id == classroom_id))
        if not classroom:
            raise LMSException(status_code=404, detail="Classroom not found")
        if user.role == UserRole.teacher and classroom.teacher_id == user.id:
            return
        if user.role == UserRole.student:
            membership = await self.db.scalar(
                select(ClassroomMember).where(
                    ClassroomMember.classroom_id == classroom_id,
                    ClassroomMember.student_id == user.id,
                )
            )
            if membership:
                return
        raise LMSException(status_code=403, detail="Not allowed to access classroom chat")
