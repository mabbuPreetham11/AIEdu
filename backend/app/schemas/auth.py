from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.user import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    role: UserRole

    @field_validator("email")
    @classmethod
    def validate_email_domain(cls, value: str) -> str:
        normalized_email = value.strip().lower()
        if not normalized_email.endswith("@iiitdwd.ac.in"):
            raise ValueError("Only @iiitdwd.ac.in emails are allowed")
        return normalized_email


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict
