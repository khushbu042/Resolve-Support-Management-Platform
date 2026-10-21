import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import Permission, ROLE_PERMISSIONS
from app.core.security import decode_access_token
from app.core.token_blacklist import is_token_revoked
from app.db.database import get_db
from app.models.user_model import User


security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = decode_access_token(token)
        jti = payload.get("jti")
        if jti and await is_token_revoked(str(jti)):
            raise HTTPException(status_code=401, detail="Token has been revoked")

        user_id = payload.get("user_id")

        select_user = select(User).where(User.id == user_id)
        result = await db.execute(select_user)
        current_user = result.scalar_one_or_none()

        if not current_user:
            raise HTTPException(status_code=401, detail="User not found")
        return current_user

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def require_permission(*required: Permission):
    def checker(current_user: User = Depends(get_current_user)):
        user_permissions = ROLE_PERMISSIONS.get(current_user.role.value, set())
        if not set(required).issubset(user_permissions):
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permission(s): {required}"
            )
        return current_user
    return checker