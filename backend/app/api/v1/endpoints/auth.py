from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_refresh_token
from app.core.config import settings
from app.core.exceptions import LMSException
from app.core.security import ALGORITHM, create_access_token, get_password_hash
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
)
from app.schemas.common import MessageResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> User:
    return await AuthService(db).register(payload)


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, response: Response, db: Annotated[AsyncSession, Depends(get_db)]) -> TokenResponse:
    user, access, refresh = await AuthService(db).login(payload)
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=settings.refresh_token_expire_days * 86400,
    )
    return TokenResponse(access_token=access, user=UserRead.model_validate(user).model_dump())


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    payload: RefreshRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    refresh_cookie: Annotated[str, Depends(get_refresh_token)],
) -> TokenResponse:
    token = payload.refresh_token or refresh_cookie
    try:
        decoded = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
    except JWTError as exc:
        raise LMSException(status_code=401, detail="Invalid refresh token") from exc
    if decoded.get("type") != "refresh":
        raise LMSException(status_code=401, detail="Invalid token type")
    user = await db.scalar(select(User).where(User.id == int(decoded["sub"])))
    if not user:
        raise LMSException(status_code=404, detail="User not found")
    access = create_access_token(str(user.id), {"role": user.role.value, "email": user.email})
    return TokenResponse(access_token=access, user=UserRead.model_validate(user).model_dump())


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    response.delete_cookie("refresh_token")
    return MessageResponse(detail="Logged out successfully")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> MessageResponse:
    AuthService(db).generate_reset_token(payload.email)
    return MessageResponse(detail="Password reset instructions queued")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, db: Annotated[AsyncSession, Depends(get_db)]) -> MessageResponse:
    service = AuthService(db)
    email = service.verify_reset_token(payload.token)
    user = await db.scalar(select(User).where(User.email == email))
    if not user:
        raise LMSException(status_code=404, detail="User not found")
    user.password_hash = get_password_hash(payload.new_password)
    await db.commit()
    return MessageResponse(detail="Password updated successfully")


@router.get("/me", response_model=UserRead)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]) -> User:
    return current_user

