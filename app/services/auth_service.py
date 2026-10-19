import jwt
from fastapi import HTTPException
from pwdlib import PasswordHash
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import (
    AsyncSession
)

from app.core.security import create_access_token, decode_access_token
from app.core.settings import get_settings
from app.core.token_blacklist import is_token_revoked, revoke_token
from app.api.schemas.user import (
    LoginRequest, 
    UserRegisterRequest, 
    LoginResponse,
    LoginResponseData,
    LogoutResponse,
    UserResponse,
)
from app.services.rate_limit.login import check_login_rate_limit, record_failed_login, check_ip_rate_limit
from app.db.redis_client import get_redis_client as redis_client
from app.database_model.user_model import User, UserRole

password_hash = PasswordHash.recommended()
settings = get_settings()


def _bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization")
    if not header or not header.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return token


def _verified_payload(token: str) -> dict:
    try:
        return decode_access_token(token)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


async def _active_payload(token: str) -> dict:
    payload = _verified_payload(token)
    jti = payload.get("jti")
    if not jti:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    if await is_token_revoked(str(jti)):
        raise HTTPException(status_code=401, detail="Token has been revoked")
    return payload

async def register_user(user: UserRegisterRequest, db: AsyncSession):

    """
    Register a new user with the given email and password
    """
    # 1. Check for existing user
    select_user = select(User).where(User.email == user.email)
    result = await db.execute(select_user)
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = password_hash.hash(user.password)

    new_user = User(
        name=user.name,
        email=user.email,
        password=hashed_password,
        role=UserRole.agent,
    )


    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return userResponse(
        id=new_user.id,
        name=new_user.name,
        email=new_user.email,
        role=new_user.role,
    )

async def login_user(user: LoginRequest, db: AsyncSession, ip_address: str):
    """
    Login a user with the given email and password
    """
    # 1. Check for existing user
    select_user = select(User).where(User.email == user.email)
    result = await db.execute(select_user)
    existing_user = result.scalar_one_or_none()

    if not existing_user:

        rate_limit = await check_ip_rate_limit(ip_address)
        if not rate_limit["allowed"]:
            raise HTTPException(
                status_code=429,
                detail="Too many failed login attempts. Please try again later.",
            )

        await record_failed_login(
            user_id=None,
            ip_address=ip_address,
        )

        raise HTTPException(
            status_code=400, detail="User email does not exist. Please register."
        )

    rate_limit = await check_login_rate_limit(
        user_id=existing_user.id,
        ip_address=ip_address
    )

    if not rate_limit["allowed"]:
        raise HTTPException(
            status_code=429,
            detail="Too many Failed login attempts. Please try again with correct Credentials",
        )

    if not password_hash.verify(user.password, existing_user.password):
        await record_failed_login(
            user_id=existing_user.id,
            ip_address=ip_address
        )
        raise HTTPException(status_code=401, detail="Password is incorrect")

    token = create_access_token(
        user_id=existing_user.id,
        role=existing_user.role.value,
    )

    return LoginResponse(
        success=True,
        message="Login successful",
        data=LoginResponseData(
            access_token=token,
            token_type="Bearer",
        ),
    )

async def logout_user(request: Request, db: AsyncSession):
    payload = await _active_payload(_bearer_token(request))
    await revoke_token(str(payload["jti"]), int(payload["exp"]))
    return LogoutResponse(
        success=True,
        message="Logout successful",
    )


async def refresh_token(request: Request, db: AsyncSession):
    payload = await _active_payload(_bearer_token(request))
    result = await db.execute(select(User).where(User.id == payload.get("user_id")))
    current_user = result.scalar_one_or_none()
    if current_user is None:
        raise HTTPException(status_code=401, detail="User not found")

    await revoke_token(str(payload["jti"]), int(payload["exp"]))
    token = create_access_token(
        user_id=current_user.id,
        role=current_user.role.value,
    )
    return {
        "success": True,
        "message": "Refresh successful",
        "data": {
            "access_token": token,
            "token_type": "Bearer",
            "expires_in": settings.access_token_expire_minutes * 60,
        },
    }