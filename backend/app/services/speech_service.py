from __future__ import annotations

import json
from typing import Any

import httpx
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import LMSException


class SpeechService:
    async def transcribe_with_sarvam(
        self,
        *,
        file: UploadFile,
        model: str | None = None,
        mode: str | None = None,
        language_code: str | None = None,
    ) -> tuple[str, str | None]:
        if not settings.sarvam_api_key:
            raise LMSException(status_code=500, detail="SARVAM_API_KEY is not configured")

        content = await file.read()
        if not content:
            raise LMSException(status_code=400, detail="Uploaded audio file is empty")

        selected_model = (model or settings.sarvam_stt_model).strip()
        selected_mode = (mode or settings.sarvam_stt_mode or "").strip()
        selected_language = (language_code or settings.sarvam_stt_language_code).strip() or "unknown"

        data: dict[str, str] = {
            "model": selected_model,
            "language_code": selected_language,
        }
        if selected_mode:
            data["mode"] = selected_mode

        file_name = file.filename or "recording.webm"
        raw_content_type = file.content_type or "audio/webm"
        content_type = raw_content_type.split(";")[0].strip().lower()
        if not content_type:
            content_type = "audio/webm"
        files = {"file": (file_name, content, content_type)}
        headers = {"api-subscription-key": settings.sarvam_api_key}

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.sarvam.ai/speech-to-text",
                headers=headers,
                data=data,
                files=files,
            )
        if response.status_code >= 400:
            raise LMSException(status_code=500, detail=f"Sarvam STT error: {response.text}")

        payload = response.json()
        transcript = str(payload.get("transcript", "")).strip()
        if not transcript:
            raise LMSException(status_code=500, detail=f"Sarvam STT returned empty transcript: {json.dumps(payload)}")
        detected_language = payload.get("language_code")
        return transcript, str(detected_language) if detected_language else None

    async def text_to_speech_with_sarvam(
        self,
        *,
        text: str,
        target_language_code: str,
        speaker: str | None = None,
        model: str | None = None,
        output_audio_codec: str | None = None,
    ) -> tuple[str, str]:
        if not settings.sarvam_api_key:
            raise LMSException(status_code=500, detail="SARVAM_API_KEY is not configured")
        clean_text = text.strip()
        if not clean_text:
            raise LMSException(status_code=400, detail="Text is empty for speech synthesis")

        payload: dict[str, Any] = {
            "text": clean_text[:2500],
            "target_language_code": target_language_code,
            "model": model or settings.sarvam_tts_model,
            "speaker": speaker or settings.sarvam_tts_speaker,
            "output_audio_codec": output_audio_codec or settings.sarvam_tts_output_codec,
        }
        headers = {
            "api-subscription-key": settings.sarvam_api_key,
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                "https://api.sarvam.ai/text-to-speech",
                headers=headers,
                json=payload,
            )
        if response.status_code >= 400:
            raise LMSException(status_code=500, detail=f"Sarvam TTS error: {response.text}")

        data = response.json()
        audios = data.get("audios", [])
        if not isinstance(audios, list) or len(audios) == 0:
            raise LMSException(status_code=500, detail=f"Sarvam TTS returned no audio: {json.dumps(data)}")
        base64_audio = str(audios[0]).strip()
        if not base64_audio:
            raise LMSException(status_code=500, detail=f"Sarvam TTS returned empty audio: {json.dumps(data)}")
        codec = str(payload["output_audio_codec"]).lower()
        mime = "audio/wav" if codec == "wav" else f"audio/{codec}"
        return base64_audio, mime
