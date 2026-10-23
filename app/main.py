import time
import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# from app.api.v1.routers import user
# ── Routers imports ───────────────────────────────────────────────
from app.api.v1.routers import auth, health, ticket, ticket_attachments
from app.core.logging import setup_logging
from app.core.settings import get_settings
from app.db.database import close_database, connect_database
from app.db.redis_client import check_redis_connection, close_redis
from app.infrastructure.rabbitmq.rabbitmq_client import (
    check_rabbitmq_connection,
    close_rabbitmq,
)

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown.
    Infrastructure connections are checked and released here.
    """

    logger.info("Application starting")

    # ── Startup: Connect infrastructure services ────────────────────────────────
    # ── Step 1: Database connection ───────────────────────────────
    logger.info("Connecting to PostgreSQL")
    await connect_database()
    logger.info("PostgreSQL connected successfully")

    # ── Step 2: Redis connection ───────────────────────────────
    logger.info("Connecting to Redis")
    redis_ok, redis_detail = await check_redis_connection()
    if not redis_ok:
        logger.error("Redis connection failed", error=redis_detail)
        raise Exception(f"Redis connection failed: {redis_detail}")
    logger.info("Redis connected successfully")

    # ── Step 3: RabbitMQ connection ───────────────────────────────
    logger.info("Connecting to RabbitMQ")
    rabbitmq_ok, rabbitmq_detail = await check_rabbitmq_connection()
    if not rabbitmq_ok:
        logger.error("RabbitMQ connection failed", error=rabbitmq_detail)
        raise Exception(f"RabbitMQ connection failed: {rabbitmq_detail}")
    logger.info("RabbitMQ connected successfully")

    logger.info("All infrastructure connections established")
    yield

    # ── Shutdown: Release infrastructure connections ────────────────────────────────
    await close_database()
    await close_redis()
    await close_rabbitmq()

    logger.info("All infrastructure connections closed")


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=settings.app_description,
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-Correlation-ID",
            "X-Process-Time-Ms",
        ],
    )

    # ── Routers ───────────────────────────────────────────────
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    # app.include_router(user.router, prefix="/api/v1")
    app.include_router(ticket.router, prefix="/api/v1")
    app.include_router(ticket_attachments.router, prefix="/api/v1")

    return app


app = create_app()
