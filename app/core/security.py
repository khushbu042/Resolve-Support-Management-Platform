import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.core.settings import get_settings

settings = get_settings()


def create_access_token(*, user_id: int, role: str) -> str:
    """Build a signed access token for the given user."""
    payload = {
        "user_id": user_id,
        "role": role,
        "jti": str(uuid.uuid4()),
        "exp": datetime.now(UTC)
        + timedelta(minutes=settings.access_token_expire_minutes),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def decode_access_token(token: str) -> dict:
    """Verify a token and return its payload. Raises jwt.InvalidTokenError."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
