from pydantic import BaseModel

from app.models.user import UserRole


class UserCreateByAdmin(BaseModel):
    email: str
    first_name: str
    last_name: str
    role: UserRole
    password: str


class SystemSettingUpdate(BaseModel):
    email_provider: str | None = None
    llm_provider: str | None = None
    storage_provider: str | None = None
