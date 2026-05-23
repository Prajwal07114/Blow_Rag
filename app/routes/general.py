"""
routes/general.py — General / Utility Endpoints
=================================================
  GET /        → Welcome message
  GET /health  → System health check
"""

from pathlib import Path

from fastapi import APIRouter

from app.config import settings
from app.models.schemas import HealthResponse
from app.utils.helpers import chroma_is_ready

router = APIRouter(tags=["General"])


@router.get("/", summary="Welcome")
async def root() -> dict:
    """
    Confirms the API is running. No auth required.
    Returns basic API metadata and navigation links.
    """
    return {
        "message": f"{settings.APP_NAME} is running.",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "docs": "/docs",
        "health": "/health",
        "auth": "POST /auth/token  →  get your JWT",
    }


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System health check",
)
async def health_check() -> HealthResponse:
    """
    Returns system health status. No auth required.

    - **vectorstore_ready**: True if a regulation has been indexed.
    - **chroma_dir**: Path to the persisted ChromaDB on disk.
    - **uploaded_files**: Regulation PDFs found in the uploads folder.
    - **environment**: `development` or `production`.
    """
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    uploaded_files = [f.name for f in upload_dir.glob("*.pdf")]

    return HealthResponse(
        status="ok",
        vectorstore_ready=chroma_is_ready(settings.CHROMA_PERSIST_DIR),
        chroma_dir=settings.CHROMA_PERSIST_DIR,
        uploaded_files=uploaded_files,
        environment=settings.ENVIRONMENT,
    )
