"""
routes/gap_analysis.py — Gap Analysis Endpoints
================================================
  POST /gap-analysis         →  JSON gap report      [AUTH REQUIRED]
  POST /gap-analysis/export  →  Excel download        [AUTH REQUIRED]

Async note:
  detect_gaps() reads a PDF (disk I/O) and calls the LLM (network I/O).
  Both benefit from async treatment:
    • File read  → await file.read()
    • LLM call   → asyncio.to_thread(detect_gaps, ...)
  This means while one gap analysis is running, the server can handle
  health checks and other lightweight requests concurrently.
"""

import asyncio
import io

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from app.config import settings
from app.middleware.rate_limiter import limiter
from app.utils.auth import get_current_user
from app.utils.helpers import FileAdapter, require_vectorstore

# ── Import your existing pipeline — UNCHANGED ─────────────────────────────────
from agents.gap_detector import build_gap_excel, detect_gaps

router = APIRouter(tags=["Compliance Analysis"])

# ── Reusable file validation ───────────────────────────────────────────────────
_ALLOWED_EXTENSIONS = (".pdf", ".txt")


def _validate_policy_file(filename: str) -> None:
    if not any(filename.lower().endswith(ext) for ext in _ALLOWED_EXTENSIONS):
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF or TXT policy files are supported. Got: {filename!r}",
        )


async def _save_and_adapt(file: UploadFile) -> FileAdapter:
    """Save an uploaded file to disk and return a FileAdapter for the pipeline."""
    from pathlib import Path

    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    save_path = upload_dir / f"policy_{file.filename}"

    content = await file.read()
    save_path.write_bytes(content)
    return FileAdapter(save_path)


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT — Gap Analysis (JSON)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/gap-analysis",
    summary="Run gap analysis — returns JSON report",
    responses={
        200: {"description": "Gap analysis completed."},
        400: {"description": "No regulation indexed or unsupported file type."},
        401: {"description": "Missing or invalid JWT token."},
        429: {"description": "Rate limit exceeded."},
        500: {"description": "Gap analysis pipeline error."},
    },
)
@limiter.limit(settings.RATE_LIMIT_QUERY)
async def gap_analysis(
    request: Request,
    file: UploadFile = File(...),
    regulation_name: str = Form(default=""),
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Upload your company policy and compare it against the indexed regulation.

    - Accepts a **PDF** or **TXT** policy document.
    - Compares it against the indexed regulation in ChromaDB.
    - Returns a compliance score + detailed gap list.

    **Requires:** A regulation must be indexed first via `POST /regulation/upload`.

    🔒 **Requires Bearer token** from `POST /auth/token`.

    **Form fields:**
    - `file` — Your company policy document (PDF or TXT).
    - `regulation_name` — Optional label for the regulation being checked against.

    **Response fields:**
    - `compliance_score` — 0–100 overall score.
    - `gaps` — Obligations not met, with severity + recommended actions.
    - `met` — Obligations your policy already satisfies.
    - `preflight` — Pre-analysis quality checks.
    - `blocked` — True if analysis was blocked by a pre-flight guard.
    """
    require_vectorstore(settings.CHROMA_PERSIST_DIR)
    _validate_policy_file(file.filename)

    adapter = await _save_and_adapt(file)

    try:
        result = await asyncio.to_thread(
            detect_gaps,
            policy_file=adapter,
            regulation_name=regulation_name,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Gap analysis error: {exc}")

    return {
        "policy_file": file.filename,
        "regulation_name": result.get("regulation_name", regulation_name),
        "compliance_score": result.get("compliance_score", 0),
        "gaps": result.get("gaps", []),
        "met": result.get("met", []),
        "preflight": result.get("_preflight", {}),
        "blocked": result.get("_edge_case", {}).get("blocked", False),
        "block_reason": result.get("_edge_case", {}).get("reason", ""),
        "analyzed_by": current_user,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT — Gap Analysis (Excel Export)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/gap-analysis/export",
    summary="Run gap analysis — returns Excel (.xlsx) download",
    responses={
        200: {"description": "Excel report generated.", "content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}},
        400: {"description": "No regulation indexed or unsupported file type."},
        401: {"description": "Missing or invalid JWT token."},
        429: {"description": "Rate limit exceeded."},
        500: {"description": "Excel export error."},
    },
)
@limiter.limit(settings.RATE_LIMIT_QUERY)
async def gap_analysis_export(
    request: Request,
    file: UploadFile = File(...),
    regulation_name: str = Form(default=""),
    current_user: str = Depends(get_current_user),
) -> StreamingResponse:
    """
    Run gap analysis and return the result as a downloadable **Excel** report.

    Same analysis as `POST /gap-analysis` but returns `.xlsx` instead of JSON.
    Ideal for direct download by a frontend or automation pipeline.

    🔒 **Requires Bearer token** from `POST /auth/token`.
    """
    require_vectorstore(settings.CHROMA_PERSIST_DIR)
    _validate_policy_file(file.filename)

    adapter = await _save_and_adapt(file)

    try:
        result = await asyncio.to_thread(
            detect_gaps,
            policy_file=adapter,
            regulation_name=regulation_name,
        )
        excel_bytes = build_gap_excel(
            result=result,
            regulation_name=regulation_name,
            policy_name=file.filename,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Excel export error: {exc}")

    safe_name = file.filename.replace(".", "_")
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": (
                f"attachment; filename=ARIRAS_Gap_Analysis_{safe_name}.xlsx"
            )
        },
    )
