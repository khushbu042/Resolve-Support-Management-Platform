# app/api/v1/routers/health.py
from datetime import datetime, timezone

import structlog
from fastapi import APIRouter

from app.api.schemas.health import ComponentStatus, HealthResponse, ReadinessResponse
from app.core.settings import get_settings
from app.db.database import check_database_connection
from app.db.redis_client import check_redis_connection
from app.infrastructure.rabbitmq.rabbitmq_client import check_rabbitmq_connection

router = APIRouter(prefix="/health", tags=["Health"])
logger = structlog.get_logger()


@router.get(
    "",
    response_model=HealthResponse,
    summary="Liveness Check",
    description="Basic check that the application process is alive.",
)
async def health_check() -> HealthResponse:
    """
    Liveness endpoint - just confirms the app is running.
    No dependency checks here - those belong in /ready.
    """
    settings = get_settings()

    return HealthResponse(
        status="healthy",
        app_name=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        timestamp=datetime.now(timezone.utc),
    )


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Check",
    description="Checks all dependencies. Returns 200 only when fully ready.",
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness endpoint - checks every dependency the app needs.
    """
    settings = get_settings()
    components = []
    all_ready = True

    # ── Check 1: Configuration ────────────────────────────────
    app_name_ok = bool(settings.app_name)
    components.append(
        ComponentStatus(
            name="configuration",
            status="healthy" if app_name_ok else "unhealthy",
            details=(
                f"App Name: {settings.app_name} | "
                f"Environment: {settings.environment}"
            ),
        )
    )
    if not app_name_ok:
        all_ready = False

    # ── Check 2: PostgreSQL ───────────────────────────────────
    db_ok, db_detail = await check_database_connection()
    components.append(
        ComponentStatus(
            name="postgresql",
            status="healthy" if db_ok else "unhealthy",
            details=db_detail,
        )
    )
    if not db_ok:
        all_ready = False

    # ── Check 3: Redis ────────────────────────────────────────
    redis_ok, redis_detail = await check_redis_connection()
    components.append(
        ComponentStatus(
            name="redis",
            status="healthy" if redis_ok else "unhealthy",
            details=redis_detail,
        )
    )
    if not redis_ok:
        all_ready = False

    # # ── Check 4: RabbitMQ ───────────────────────────────────────
    rabbitmq_ok, rabbitmq_detail = await check_rabbitmq_connection()
    components.append(
        ComponentStatus(
            name="rabbitmq",
            status="healthy" if rabbitmq_ok else "unhealthy",
            details=rabbitmq_detail,
        )
    )
    if not rabbitmq_ok:
        all_ready = False

    logger.info(
        "Readiness check completed",
        status="ready" if all_ready else "not_ready",
    )

    return ReadinessResponse(
        status="ready" if all_ready else "not_ready",
        components=components,
        timestamp=datetime.now(timezone.utc),
    )
