# app/api/v1/routers/user.py
import structlog
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.api.schemas.user import (
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    RefreshResponse,
    UserRegisterRequest,
    UserResponse,
)
from app.db.database import get_db
from app.services.auth_service import (
    login_user,
    logout_user,
    refresh_token,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])
logger = structlog.get_logger()


@router.post(
    "/register",
    response_model=UserResponse,
    summary="Register a new user",
    description="Register a new user with the given email and password",
)
async def register(
    user: UserRegisterRequest, db: AsyncSession = Depends(get_db)
) -> UserResponse:
    """
    Register a new user with the given email and password
    """
    return await register_user(user=user, db=db)


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Login a user",
    description="Login a user with the given email and password",
)
async def login(
    user: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Login a user with the given email and password
    """
    return await login_user(user=user, ip_address=request.client.host, db=db)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    summary="Logout a user",
    description="Logout a user from the system",
)
async def logout(
    request: Request, db: AsyncSession = Depends(get_db)
) -> LogoutResponse:
    """
    Logout a user from the system
    """
    return await logout_user(request=request, db=db)


@router.post(
    "/refresh",
    response_model=RefreshResponse,
    summary="Refresh a user's token",
    description="Refresh a user's token",
)
async def refresh(
    request: Request, db: AsyncSession = Depends(get_db)
) -> RefreshResponse:
    """
    Refresh a user's token
    """
    return await refresh_token(request=request, db=db)
