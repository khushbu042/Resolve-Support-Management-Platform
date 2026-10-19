import asyncio
import logging

from app.infrastructure.rabbitmq.rabbitmq_client import close_rabbitmq
from app.workers.notifications.consumer import consume_ticket_notifications

logging.basicConfig(level=logging.INFO)


async def _run() -> None:
    try:
        await consume_ticket_notifications()
    finally:
        await close_rabbitmq()


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
