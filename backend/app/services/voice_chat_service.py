from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import LMSException
from app.models.user import User
from app.services.chat_service import ChatService
from app.services.groq_rate_limit import acquire_groq_slot
from app.services.speech_service import SpeechService

_SUPPORTED_TTS_CODES = {
    "hi-IN",
    "bn-IN",
    "kn-IN",
    "ml-IN",
    "mr-IN",
    "od-IN",
    "pa-IN",
    "ta-IN",
    "te-IN",
    "en-IN",
    "gu-IN",
}

_LANGUAGE_NAME_BY_CODE = {
    "hi-IN": "Hindi",
    "bn-IN": "Bengali",
    "kn-IN": "Kannada",
    "ml-IN": "Malayalam",
    "mr-IN": "Marathi",
    "od-IN": "Odia",
    "pa-IN": "Punjabi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "en-IN": "English",
    "gu-IN": "Gujarati",
    "as-IN": "Assamese",
    "ur-IN": "Urdu",
    "ne-IN": "Nepali",
}


class VoiceChatService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.speech_service = SpeechService()
        self.chat_service = ChatService(db)

    async def ask_voice_question(self, *, classroom_id: int, student: User, file: UploadFile) -> dict[str, Any]:
        transcript_original, detected_language = await self.speech_service.transcribe_with_sarvam(
            file=file,
            model="saarika:v2.5",
            mode=None,
            language_code="unknown",
        )

        # Reset file pointer for second STT call on same uploaded file
        await file.seek(0)
        transcript_english, _ = await self.speech_service.transcribe_with_sarvam(
            file=file,
            model="saaras:v3",
            mode="translate",
            language_code="unknown",
        )

        assistant_message = await self.chat_service.ask_classroom_question(
            classroom_id=classroom_id,
            student=student,
            question=transcript_english,
        )

        answer_language = self._normalize_tts_language_code(detected_language)
        answer_text = assistant_message.content
        if answer_language != "en-IN":
            answer_text = await self._translate_with_groq(answer_text, answer_language)

        audio_base64, audio_mime = await self.speech_service.text_to_speech_with_sarvam(
            text=answer_text,
            target_language_code=answer_language,
        )

        return {
            "transcript_original": transcript_original,
            "transcript_english": transcript_english,
            "detected_language_code": detected_language,
            "answer_text": answer_text,
            "answer_language_code": answer_language,
            "answer_audio_base64": audio_base64,
            "answer_audio_mime_type": audio_mime,
            "assistant_message": assistant_message,
        }

    def _normalize_tts_language_code(self, code: str | None) -> str:
        if not code:
            return "en-IN"
        normalized = code.strip()
        if normalized in _SUPPORTED_TTS_CODES:
            return normalized
        base = normalized.split("-")[0].lower()
        for item in _SUPPORTED_TTS_CODES:
            if item.split("-")[0].lower() == base:
                return item
        return "en-IN"

    async def _translate_with_groq(self, text: str, target_language_code: str) -> str:
        if not settings.groq_api_key:
            return text
        acquire_groq_slot()
        target_name = _LANGUAGE_NAME_BY_CODE.get(target_language_code, target_language_code)
        payload: dict[str, Any] = {
            "model": settings.groq_model,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Translate the user-provided text accurately. "
                        "Return only translated text, preserve meaning, no extra commentary."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Translate this text to {target_name} ({target_language_code}):\n\n{text}",
                },
            ],
            "temperature": 0.2,
        }
        headers = {
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
        if response.status_code >= 400:
            raise LMSException(status_code=500, detail=f"Groq translation error: {response.text}")
        data = response.json()
        choices = data.get("choices", [])
        if not choices:
            raise LMSException(status_code=500, detail=f"Unexpected Groq translation response: {json.dumps(data)}")
        content = str(choices[0].get("message", {}).get("content", "")).strip()
        return content or text
