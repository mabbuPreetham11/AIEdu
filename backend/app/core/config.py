from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "IIIT Dharwad AI LMS"
    api_v1_prefix: str = "/api/v1"
    secret_key: str = Field(min_length=16)
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    allowed_email_domain: str = "iiitdwd.ac.in"
    frontend_url: str = "http://localhost:3000"
    database_url: str = "sqlite+aiosqlite:///./lms.db"
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    storage_backend: Literal["local", "s3"] = "local"
    local_storage_path: str = "./uploads"
    s3_endpoint_url: str | None = None
    s3_bucket: str = "iiitdwd-lms"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    s3_region: str = "ap-south-1"
    smtp_from_email: str = "no-reply@iiitdwd.ac.in"
    sendgrid_api_key: str | None = None
    aws_ses_region: str | None = None
    openai_api_key: str | None = None
    groq_api_key: str | None = None
    groq_model: str = "llama-3.3-70b-versatile"
    groq_max_requests_per_minute: int = 25
    sarvam_api_key: str | None = None
    sarvam_stt_model: str = "saarika:v2.5"
    sarvam_stt_mode: str | None = None
    sarvam_stt_language_code: str = "unknown"
    sarvam_tts_model: str = "bulbul:v3"
    sarvam_tts_speaker: str = "shubh"
    sarvam_tts_output_codec: str = "wav"
    default_llm_provider: Literal["openai", "groq", "local"] = "groq"
    plagiarism_provider: Literal["copyleaks", "turnitin"] = "copyleaks"
    plagiarism_api_key: str | None = None
    rate_limit: str = "20/minute"
    cookie_secure: bool = False
    seed_demo_data: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()


def ensure_local_directories() -> None:
    Path(settings.local_storage_path).mkdir(parents=True, exist_ok=True)
