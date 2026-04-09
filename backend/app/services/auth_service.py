from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import LMSException
from app.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.serializer = URLSafeTimedSerializer(settings.secret_key)

    async def register(self, payload: RegisterRequest) -> User:
        existing = await self.db.scalar(select(User).where(User.email == payload.email.lower()))
        if existing:
            raise LMSException(status_code=400, detail="User already exists")

        user = User(
            email=payload.email.lower(),
            password_hash=get_password_hash(payload.password),
            role=payload.role,
            first_name=payload.first_name,
            last_name=payload.last_name,
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def login(self, payload: LoginRequest) -> tuple[User, str, str]:
        user = await self.db.scalar(select(User).where(User.email == payload.email.lower()))
        if not user or not verify_password(payload.password, user.password_hash):
            raise LMSException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise LMSException(status_code=403, detail="User is inactive")
        access = create_access_token(str(user.id), {"role": user.role.value, "email": user.email})
        refresh = create_refresh_token(str(user.id), {"role": user.role.value})
        return user, access, refresh

    def generate_verification_token(self, email: str) -> str:
        return self.serializer.dumps(email, salt="verify-email")

    def generate_reset_token(self, email: str) -> str:
        return self.serializer.dumps(email, salt="reset-password")

    def verify_reset_token(self, token: str) -> str:
        return self.serializer.loads(token, salt="reset-password", max_age=3600)

