from collections.abc import Callable
from typing import Annotated

from fastapi import Cookie, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import LMSException
from app.core.security import ALGORITHM
from app.db.session import get_db
from app.models.user import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login")


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Annotated[AsyncSession, Depends(get_db)]) -> User:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise LMSException(status_code=401, detail="Could not validate credentials") from exc
    if payload.get("type") != "access":
        raise LMSException(status_code=401, detail="Invalid token type")
    user = await db.scalar(select(User).where(User.id == int(payload["sub"])))
    if not user:
        raise LMSException(status_code=404, detail="User not found")
    return user


async def get_refresh_token(refresh_token: str | None = Cookie(default=None)) -> str:
    if not refresh_token:
        raise LMSException(status_code=401, detail="Missing refresh token")
    return refresh_token


def require_role(*roles: UserRole) -> Callable:
    async def role_dependency(user: Annotated[User, Depends(get_current_user)]) -> User:
        if user.role not in roles:
            raise LMSException(status_code=403, detail="Insufficient permissions")
        return user

    return role_dependency

