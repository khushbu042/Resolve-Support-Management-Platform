import aio_pika
import structlog
from aio_pika.abc import AbstractRobustConnection

from app.core.settings import get_settings


settings = get_settings()
logger = structlog.get_logger()
_connection: AbstractRobustConnection | None = None


async def get_connection() -> AbstractRobustConnection:
    global _connection
    if _connection is None or _connection.is_closed:
        _connection = await aio_pika.connect_robust(settings.rabbitmq_url)
    return _connection

async def check_rabbitmq_connection() -> bool:
    try:
        connection = await get_connection()
        return True, "Connected successfully"
    except Exception as e:
        logger.error(f"Error checking RabbitMQ connection: {e}")
        return False

async def close_rabbitmq() -> None:
    global _connection
    if _connection is not None and not _connection.is_closed:
        await _connection.close()
    _connection = None
