"""
routes/regulation.py — Regulation Management Endpoints
=======================================================
  POST /regulation/upload  →  Upload & index a regulation PDF  [AUTH REQUIRED]

Async note:
  build_vectorstore() involves:
    • disk I/O  (reading the PDF)          → benefits from async
    • CPU-heavy embedding computation      → does NOT benefit from async
      (Python GIL means CPU work blocks the event loop anyway)

  We use `async def` here because the file-read part (await file.read())
  IS async I/O.  The CPU-bound embedding step is fine for a
  single-instance deployment.  At scale, move build_vectorstore() to a
  Celery/background task worker.
"""

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.config import settings
from app.middleware.rate_limiter import limiter
from app.utils.auth import get_current_user

# ── Import your existing pipeline — UNCHANGED ─────────────────────────────────
from core.vectorstore import build_vectorstore

router = APIRouter(prefix="/regulation", tags=["Regulation Management"])


@router.post(
    "/upload",
    summary="Upload & index a regulation PDF",
    responses={
        200: {"description": "PDF uploaded and indexed successfully."},
        400: {"description": "File is not a PDF."},
        401: {"description": "Missing or invalid JWT token."},
        429: {"description": "Rate limit exceeded — max 10 uploads/minute."},
        500: {"description": "Failed to save or index the file."},
    },
)
@limiter.limit(settings.RATE_LIMIT_UPLOAD)
async def upload_regulation(
    request: Request,                             # required by slowapi
    file: UploadFile = File(...),
    current_user: str = Depends(get_current_user),  # JWT guard
) -> dict:
    """
    Upload a regulation PDF and index it into ChromaDB.

    - Accepts a single **PDF** file.
    - Saves it to `data/uploads/`.
    - Calls `build_vectorstore()` to chunk + embed it.
    - Returns the filename and chunk count.

    **Must be called before** `/query`, `/gap-analysis`, or `/conflict-check`.

    🔒 **Requires Bearer token** from `POST /auth/token`.
    """
    # ── Validate file type ────────────────────────────────────────────────────
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files are supported. Received: {file.filename!r}",
        )

    # ── Save to disk (async read = non-blocking) ──────────────────────────────
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    save_path = upload_dir / file.filename

    try:
        content = await file.read()          # async — releases event loop during I/O
        save_path.write_bytes(content)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {exc}",
        )

    # ── Index into ChromaDB (sync — CPU-bound embedding) ─────────────────────
    # Note: build_vectorstore() is CPU-bound (embedding model), so there's
    # no benefit to making it awaitable.  For production at scale, move this
    # to a background task / Celery worker.
    try:
        vectorstore = build_vectorstore(str(save_path))
        chunk_count = vectorstore._collection.count()
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index regulation: {exc}",
        )

    return {
        "message": "Regulation indexed successfully.",
        "filename": file.filename,
        "saved_to": str(save_path),
        "chunk_count": chunk_count,
        "indexed_by": current_user,
        "next_step": "Use POST /query to ask questions about this regulation.",
    }
