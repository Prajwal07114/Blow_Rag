"""
config.py — Centralised settings loaded from environment variables / .env
=========================================================================
All secrets and configuration live here.  Import `settings` anywhere in the
app — never hard-code secrets or paths.

Usage:
    from app.config import settings
    print(settings.JWT_SECRET_KEY)
"""
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── App identity ──────────────────────────────────────────────────────────
    APP_NAME: str = "ARIRAS API"
    APP_VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"          # development | production

    # ── JWT ───────────────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── Demo credentials (replace with a real user DB in production) ──────────
    DEMO_USERNAME: str = "ariras_user"
    DEMO_PASSWORD: str = "ariras_pass"

    # ── LLM / External API keys ───────────────────────────────────────────────
    GROQ_API_KEY: str = ""
    OPENAI_API_KEY: str = ""                  # optional fallback

    # ── ChromaDB ─────────────────────────────────────────────────────────────
    CHROMA_PERSIST_DIR: str = "/app/data/chroma_db"

    # ── File storage ──────────────────────────────────────────────────────────
    UPLOAD_DIR: str = "/app/data/uploads"

    # ── Rate limiting ─────────────────────────────────────────────────────────
    RATE_LIMIT_QUERY: str = "5/minute"        # LLM-backed endpoints
    RATE_LIMIT_UPLOAD: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "30/minute"

    # ── Server ────────────────────────────────────────────────────────────────
    HOST: str = "0.0.0.0"
    PORT: int = 10000

    # Reads from .env automatically
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


@lru_cache()          # singleton — loaded once, cached for the process lifetime
def get_settings() -> Settings:
    return Settings()


# Convenient module-level alias used across the codebase
settings: Settings = get_settings()
