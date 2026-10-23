# app/core/settings.py

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central configuration for the application.
    All values come from environment variables or the .env file.
    """

    # ── Pydantic Settings Configuration ──────────────────────
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ───────────────────────────────────────────
    app_name: str = "Resolve Support Management"
    app_version: str = "1.0.0"
    app_description: str = (
        "Support Management is a platform for managing support tickets and resolving issues."
    )
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False

    # ── PostgreSQL ────────────────────────────────────────────
    database_url: str = Field(
        default="",
        alias="DATABASE_URL",
    )

    # ── Security ──────────────────────────────────────────────
    secret_key: str = Field(
        default="",
        alias="SECRET_KEY",
    )
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # ── Redis ────────────────────────────────────────────────
    redis_url: str = Field(
        default="redis://localhost:6379",
        alias="REDIS_URL",
    )
    user_limit: int = Field(
        default=5,
        alias="USER_LIMIT",
    )
    user_window: int = Field(
        default=2 * 60,
        alias="USER_WINDOW",
    )

    ip_limit: int = Field(
        default=10,
        alias="IP_LIMIT",
    )
    ip_window: int = Field(
        default=60,
        alias="IP_WINDOW",
    )

    # ── RabbitMQ ─────────────────────────────────────────────
    rabbitmq_url: str = Field(
        default="amqp://guest:guest@localhost:5672/",
        alias="RABBITMQ_URL",
    )

    # ── SMTP Configuration ───────────────────────────────────
    smtp_host: str = Field(
        default="",
        alias="SMTP_HOST",
    )

    smtp_port: int = Field(
        default=1025,
        alias="SMTP_PORT",
    )

    smtp_from: str = Field(
        default="noreply@localhost",
        alias="SMTP_FROM",
    )

    smtp_user: str = Field(
        default="",
        alias="SMTP_USER",
    )

    smtp_password: str = Field(
        default="",
        alias="SMTP_PASSWORD",
    )

    smtp_use_tls: bool = Field(
        default=False,
        alias="SMTP_USE_TLS",
    )

    # ── Notifications ────────────────────────────────────────
    notification_max_retries: int = Field(
        default=3,
        alias="NOTIFICATION_MAX_RETRIES",
    )

    # ── S3 ───────────────────────────────────────────────────
    s3_bucket_name: str = Field(
        default="",
        alias="S3_BUCKET_NAME",
    )
    s3_region: str = Field(
        default="",
        alias="S3_REGION",
    )
    allowed_files: dict[str, str] = Field(
        default={
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".xls": "application/vnd.ms-excel",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".ppt": "application/vnd.ms-powerpoint",
            ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        },
        alias="ALLOWED_FILES",
    )
    max_file_size: int = Field(
        default=5 * 1024 * 1024,
        alias="MAX_FILE_SIZE",
    )
    chunk_size: int = Field(
        default=1024 * 1024,
        alias="CHUNK_SIZE",
    )

    # ── Database URL Normalization ───────────────────────────
    def model_post_init(self, __context) -> None:
        """
        Normalize PostgreSQL URLs for Psycopg 3 compatibility.
        """
        if self.database_url.startswith("postgresql://"):
            self.database_url = self.database_url.replace(
                "postgresql://",
                "postgresql+psycopg://",
            )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.
    Created only once for the application lifetime.
    """
    return Settings()
