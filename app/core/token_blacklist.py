import time

from app.db.redis_client import get_redis_client


def _revoked_key(jti: str) -> str:
    return f"auth:revoked:{jti}"


async def revoke_token(jti: str, expires_at: int) -> None:
    """Keep a token id revoked until it would have expired."""
    ttl = int(expires_at) - int(time.time())
    if ttl <= 0:
        return
    client = get_redis_client()
    await client.set(_revoked_key(jti), "1", ex=ttl)


async def is_token_revoked(jti: str) -> bool:
    client = get_redis_client()
    return bool(await client.exists(_revoked_key(jti)))
