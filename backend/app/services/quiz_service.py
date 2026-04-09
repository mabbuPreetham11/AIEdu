from __future__ import annotations

import json
import random
import re
from datetime import datetime, timezone
from pathlib import Path

import httpx
from PyPDF2 import PdfReader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import LMSException
from app.models.classroom import Classroom, ClassroomMember
from app.models.material import Material, MaterialType
from app.models.quiz import ClassroomQuizQuestion, Quiz, QuizAttempt
from app.models.user import User, UserRole
from app.services.groq_rate_limit import acquire_groq_slot
from app.schemas.quiz import GeneratedQuizQuestion, QuizPublishRequest


class QuizService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_questions(self, classroom_id: int, teacher: User, topic: str | None, material_id: int | None) -> list[GeneratedQuizQuestion]:
        classroom = await self._teacher_classroom_or_403(classroom_id, teacher)
        del classroom

        content_text = ""
        if material_id is not None:
            material = await self.db.scalar(select(Material).where(Material.id == material_id, Material.classroom_id == classroom_id))
            if not material:
                raise LMSException(status_code=404, detail="Selected material not found in this classroom")
            content_text = await self._material_text(material)

        topic_text = topic.strip() if topic else ""
        if not content_text and not topic_text:
            raise LMSException(status_code=400, detail="Provide a topic or select an uploaded material")

        prompt = (
            "Generate 10 quiz questions from this content. Mix MCQ (4 options, 1 correct) and True/False. "
            "Return as JSON array with fields: question, type, options, correct_answer, explanation."
        )
        source_text = f"Topic: {topic_text}\n\nMaterial:\n{content_text}" if topic_text else content_text
        generated = await self._groq_generate(prompt=prompt, content=source_text)
        return generated

    async def publish_quiz(self, classroom_id: int, teacher: User, payload: QuizPublishRequest) -> Quiz:
        await self._teacher_classroom_or_403(classroom_id, teacher)
        if len(payload.questions) == 0:
            raise LMSException(status_code=400, detail="At least one question is required")

        quiz = Quiz(
            classroom_id=classroom_id,
            title=payload.title.strip(),
            deadline=payload.deadline,
            is_published=payload.is_published,
            randomise_order=payload.randomise_order,
        )
        self.db.add(quiz)
        await self.db.flush()

        questions = payload.questions[:]
        if payload.randomise_order:
            random.shuffle(questions)

        for index, question in enumerate(questions, start=1):
            options = question.options
            if question.type == "mcq":
                if len(options) != 4:
                    raise LMSException(status_code=400, detail="MCQ questions must have exactly 4 options")
            else:
                options = ["True", "False"]

            self.db.add(
                ClassroomQuizQuestion(
                    quiz_id=quiz.id,
                    question=question.question.strip(),
                    type=question.type,
                    options=options,
                    correct_answer=question.correct_answer.strip(),
                    explanation=question.explanation.strip(),
                    order_number=index,
                )
            )

        await self.db.commit()
        loaded = await self.db.scalar(select(Quiz).options(selectinload(Quiz.questions)).where(Quiz.id == quiz.id))
        if not loaded:
            raise LMSException(status_code=500, detail="Failed to load created quiz")
        return loaded

    async def list_quizzes(self, classroom_id: int, user: User) -> list[Quiz]:
        if user.role == UserRole.teacher:
            await self._teacher_classroom_or_403(classroom_id, user)
            where_clause = Quiz.classroom_id == classroom_id
        elif user.role == UserRole.student:
            await self._student_classroom_or_403(classroom_id, user)
            where_clause = (Quiz.classroom_id == classroom_id) & (Quiz.is_published.is_(True))
        else:
            raise LMSException(status_code=403, detail="Not allowed")

        result = await self.db.scalars(
            select(Quiz)
            .options(selectinload(Quiz.questions), selectinload(Quiz.attempts))
            .where(where_clause)
            .order_by(Quiz.created_at.desc())
        )
        return list(result.all())

    async def submit_attempt(self, classroom_id: int, quiz_id: int, student: User, answers: dict[str, str]) -> QuizAttempt:
        if student.role != UserRole.student:
            raise LMSException(status_code=403, detail="Only students can submit quiz attempts")
        await self._student_classroom_or_403(classroom_id, student)

        quiz = await self.db.scalar(
            select(Quiz)
            .options(selectinload(Quiz.questions))
            .where(Quiz.id == quiz_id, Quiz.classroom_id == classroom_id, Quiz.is_published.is_(True))
        )
        if not quiz:
            raise LMSException(status_code=404, detail="Quiz not found")

        now_utc = datetime.now(timezone.utc)
        if quiz.deadline and quiz.deadline < now_utc:
            raise LMSException(status_code=400, detail="Quiz deadline has passed")

        existing = await self.db.scalar(
            select(QuizAttempt).where(QuizAttempt.quiz_id == quiz_id, QuizAttempt.student_id == student.id)
        )
        if existing:
            raise LMSException(status_code=400, detail="Quiz already submitted")

        total = len(quiz.questions)
        if total == 0:
            raise LMSException(status_code=400, detail="Quiz has no questions")

        normalized_answers: dict[str, str] = {}
        correct_count = 0
        for question in quiz.questions:
            selected = str(answers.get(str(question.id), "")).strip()
            normalized_answers[str(question.id)] = selected
            if self._answers_match(selected, question.correct_answer, question.type):
                correct_count += 1

        score = round((correct_count / total) * 100, 2)
        attempt = QuizAttempt(
            quiz_id=quiz_id,
            student_id=student.id,
            score=score,
            answers=normalized_answers,
        )
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def get_quiz(self, classroom_id: int, quiz_id: int, user: User) -> Quiz:
        if user.role == UserRole.teacher:
            await self._teacher_classroom_or_403(classroom_id, user)
        elif user.role == UserRole.student:
            await self._student_classroom_or_403(classroom_id, user)
        else:
            raise LMSException(status_code=403, detail="Not allowed")

        quiz = await self.db.scalar(
            select(Quiz)
            .options(selectinload(Quiz.questions), selectinload(Quiz.attempts))
            .where(Quiz.id == quiz_id, Quiz.classroom_id == classroom_id)
        )
        if not quiz:
            raise LMSException(status_code=404, detail="Quiz not found")
        if user.role == UserRole.student and not quiz.is_published:
            raise LMSException(status_code=404, detail="Quiz not found")
        return quiz

    async def get_quiz_analytics(self, classroom_id: int, quiz_id: int, teacher: User) -> tuple[Quiz, list[QuizAttempt]]:
        await self._teacher_classroom_or_403(classroom_id, teacher)
        quiz = await self.db.scalar(
            select(Quiz).where(Quiz.id == quiz_id, Quiz.classroom_id == classroom_id)
        )
        if not quiz:
            raise LMSException(status_code=404, detail="Quiz not found")

        attempts = await self.db.scalars(
            select(QuizAttempt)
            .options(selectinload(QuizAttempt.student))
            .where(QuizAttempt.quiz_id == quiz_id)
            .order_by(QuizAttempt.submitted_at.desc())
        )
        return quiz, list(attempts.all())

    async def _teacher_classroom_or_403(self, classroom_id: int, teacher: User) -> Classroom:
        if teacher.role != UserRole.teacher:
            raise LMSException(status_code=403, detail="Only teachers can manage quizzes")
        classroom = await self.db.scalar(select(Classroom).where(Classroom.id == classroom_id))
        if not classroom:
            raise LMSException(status_code=404, detail="Classroom not found")
        if classroom.teacher_id != teacher.id:
            raise LMSException(status_code=403, detail="Only classroom teacher can manage quizzes")
        return classroom

    async def _student_classroom_or_403(self, classroom_id: int, student: User) -> None:
        if student.role != UserRole.student:
            raise LMSException(status_code=403, detail="Only students can access this")
        membership = await self.db.scalar(
            select(ClassroomMember).where(
                ClassroomMember.classroom_id == classroom_id,
                ClassroomMember.student_id == student.id,
            )
        )
        if not membership:
            raise LMSException(status_code=403, detail="Student is not in this classroom")

    def _answers_match(self, selected: str, correct: str, question_type: str) -> bool:
        left = selected.strip().lower()
        right = correct.strip().lower()
        if question_type == "true_false":
            true_values = {"true", "t", "1", "yes"}
            false_values = {"false", "f", "0", "no"}
            if left in true_values:
                left = "true"
            elif left in false_values:
                left = "false"
            if right in true_values:
                right = "true"
            elif right in false_values:
                right = "false"
        return left == right

    async def _material_text(self, material: Material) -> str:
        if material.type in {MaterialType.pdf, MaterialType.slide} and material.file_path:
            pdf_path = Path(settings.local_storage_path) / material.file_path
            if not pdf_path.exists():
                raise LMSException(status_code=404, detail="Material file not found on server")
            reader = PdfReader(str(pdf_path))
            pages = []
            for page in reader.pages:
                text = (page.extract_text() or "").strip()
                if text:
                    pages.append(text)
            return "\n\n".join(pages)

        if material.type in {MaterialType.video, MaterialType.link} and material.url:
            return f"Reference URL: {material.url}\nTitle: {material.title}"
        return material.title

    async def _groq_generate(self, prompt: str, content: str) -> list[GeneratedQuizQuestion]:
        if not settings.groq_api_key:
            raise LMSException(status_code=500, detail="GROQ_API_KEY is required for quiz generation")
        acquire_groq_slot()
        prepared_content = self._prepare_content_for_model(content)

        payload = {
            "model": settings.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You generate classroom quizzes from provided content. "
                        "Output must be valid JSON only."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"{prompt}\n\n"
                        "Allowed values for type: mcq, true_false.\n"
                        "For true_false, options must be [\"True\", \"False\"].\n"
                        f"Content:\n{prepared_content}\n\n"
                        "Return only JSON. No markdown fences. No extra text."
                    ),
                },
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        with httpx.Client(timeout=90.0) as client:
            response = client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        if response.status_code >= 400:
            raise LMSException(status_code=500, detail=f"Groq API error: {response.text}")

        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise LMSException(status_code=500, detail=f"Unexpected Groq response: {json.dumps(data)}")
        raw = str(choices[0].get("message", {}).get("content", "")).strip()
        if not raw:
            raise LMSException(status_code=500, detail="Groq returned empty quiz output")

        parsed = self._extract_json_array(raw)
        if not isinstance(parsed, list):
            parsed = []

        questions: list[GeneratedQuizQuestion] = []
        for item in parsed:
            normalized_question = self._normalize_question_item(item)
            if normalized_question:
                questions.append(normalized_question)

        if len(questions) == 0:
            questions = self._build_local_fallback_questions(prepared_content)
        if len(questions) == 0:
            raise LMSException(status_code=500, detail="No valid quiz questions were generated")
        return questions[:10]

    def _prepare_content_for_model(self, content: str, max_chars: int = 120000) -> str:
        text = (content or "").strip()
        if len(text) <= max_chars:
            return text
        slice_size = max_chars // 3
        first = text[:slice_size]
        middle_start = max((len(text) // 2) - (slice_size // 2), 0)
        middle = text[middle_start : middle_start + slice_size]
        last = text[-slice_size:]
        return (
            "[START EXCERPT]\n"
            f"{first}\n\n"
            "[MIDDLE EXCERPT]\n"
            f"{middle}\n\n"
            "[END EXCERPT]\n"
            f"{last}"
        )

    def _extract_json_array(self, raw: str) -> list[dict] | list:
        normalized = raw.strip()
        if "```" in normalized:
            normalized = normalized.replace("```json", "").replace("```", "").strip()

        try:
            parsed = json.loads(normalized)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                if isinstance(parsed.get("questions"), list):
                    return parsed["questions"]
                if isinstance(parsed.get("data"), list):
                    return parsed["data"]
        except json.JSONDecodeError:
            pass

        match = re.search(r"\[[\s\S]*\]", normalized)
        if not match:
            return []
        candidate = match.group(0).strip()
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, list) else []
        except json.JSONDecodeError:
            return []

    def _normalize_question_item(self, item: object) -> GeneratedQuizQuestion | None:
        if not isinstance(item, dict):
            return None

        question_text = str(item.get("question") or item.get("question_text") or "").strip()
        if not question_text:
            return None

        raw_type = str(item.get("type") or "").strip().lower().replace("-", "_")
        if raw_type in {"tf", "truefalse", "true_false", "true/false"}:
            question_type = "true_false"
        else:
            question_type = "mcq"

        options_value = item.get("options", [])
        options: list[str] = []
        if isinstance(options_value, dict):
            for key in ("A", "B", "C", "D", "a", "b", "c", "d"):
                value = options_value.get(key)
                if value is not None:
                    options.append(str(value).strip())
        elif isinstance(options_value, list):
            options = [str(v).strip() for v in options_value if str(v).strip()]

        correct_answer = str(item.get("correct_answer") or item.get("answer") or "").strip()
        if question_type == "mcq":
            if len(options) < 4:
                while len(options) < 4:
                    options.append(f"Option {len(options) + 1}")
            options = options[:4]
            if correct_answer.isdigit():
                idx = int(correct_answer)
                if 1 <= idx <= len(options):
                    correct_answer = options[idx - 1]
            if not correct_answer:
                correct_answer = options[0]
        else:
            options = ["True", "False"]
            lowered = correct_answer.lower()
            correct_answer = "True" if lowered in {"true", "t", "1", "yes"} else "False"

        explanation = str(item.get("explanation") or "Based on the provided course content.").strip()
        try:
            return GeneratedQuizQuestion(
                question=question_text,
                type=question_type,  # type: ignore[arg-type]
                options=options,
                correct_answer=correct_answer,
                explanation=explanation,
            )
        except Exception:
            return None

    def _build_local_fallback_questions(self, content: str) -> list[GeneratedQuizQuestion]:
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", content) if len(s.strip()) > 40]
        if not sentences:
            return []
        base = sentences[:10]
        questions: list[GeneratedQuizQuestion] = []
        for idx, sentence in enumerate(base, start=1):
            if idx % 3 == 0:
                questions.append(
                    GeneratedQuizQuestion(
                        question=f"True or False: {sentence[:180]}",
                        type="true_false",
                        options=["True", "False"],
                        correct_answer="True",
                        explanation="This statement is taken from the provided material excerpt.",
                    )
                )
            else:
                questions.append(
                    GeneratedQuizQuestion(
                        question=f"Which option best matches this statement from the material? \"{sentence[:140]}\"",
                        type="mcq",
                        options=[
                            sentence[:80],
                            "An unrelated statement",
                            "A contradictory statement",
                            "None of the above",
                        ],
                        correct_answer=sentence[:80],
                        explanation="The first option is directly extracted from the provided content.",
                    )
                )
        return questions[:10]
