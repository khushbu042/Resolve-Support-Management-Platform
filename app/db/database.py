# app/db/database.py
"""
PostgreSQL database connection using SQLAlchemy async engine.

We use async SQLAlchemy so database queries never block the event loop.
This is critical for a FastAPI application that needs to handle
many concurrent requests.
"""
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
import structlog

from app.core.settings import get_settings

logger = structlog.get_logger()

# ── Base class for all database models ───────────────────────
class Base(DeclarativeBase):
    """
    All SQLAlchemy models inherit from this.
    Gives us .metadata for creating/dropping tables.
    """
    pass


# ── Module-level engine and session factory ───────────────────
# These are created once and reused for all requests
_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker | None = None
_connection: AsyncConnection | None = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            # Connection pool settings
            pool_size=5,          # Keep 5 connections ready
            max_overflow=10,      # Allow 10 more if needed
            pool_timeout=30,      # Wait max 30s for a connection
            pool_recycle=1800,    # Recycle connections every 30 min
            echo=settings.debug,  # Log SQL in debug mode
        )
        logger.info("Database engine created")
    return _engine


def get_session_factory() -> async_sessionmaker:
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,  # Don't expire objects after commit
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


async def connect_database() -> None:
    """
    Create the engine and session factory, then open one connection.
    Called once from the application lifespan.
    """
    global _connection
    engine = get_engine()
    get_session_factory()
    connection = await engine.connect()
    try:
        await connection.execute(text("SELECT 1"))
        await connection.rollback()
    except Exception:
        await connection.close()
        logger.exception("Database connection failed")
        await close_database()
        raise
    _connection = connection
    logger.info("Database connected")


async def check_database_connection() -> tuple[bool, str]:
    """
    Test database connectivity.
    Returns (is_healthy, detail_message)
    Used by the readiness check endpoint.
    """
    if _connection is None or _connection.closed:
        return False, "Database is not connected"

    try:
        await _connection.execute(text("SELECT 1"))
        await _connection.rollback()
        return True, "Connected successfully"
    except Exception as e:
        logger.error("Database health check failed", error=str(e))
        return False, str(e)


async def close_database() -> None:
    """
    Close database connections gracefully.
    Called at application shutdown.
    """
    global _engine, _session_factory, _connection
    if _connection is not None and not _connection.closed:
        await _connection.close()
    _connection = None
    if _engine is not None:
        await _engine.dispose()
        logger.info("Database connections closed")
    _engine = None
    _session_factory = None

async def get_db() -> AsyncSession:
    """Get a database session."""
    session = _session_factory()
    try:
        yield session
    finally:
        await session.aclose()