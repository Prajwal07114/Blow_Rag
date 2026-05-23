"""
routes/conflict_check.py — Regulation Conflict Check Endpoint
==============================================================
  POST /conflict-check  →  Detect conflicts between regulations  [AUTH REQUIRED]
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.middleware.rate_limiter import limiter
from app.models.schemas import ConflictCheckRequest
from app.utils.auth import get_current_user

# ── Import your existing pipeline — UNCHANGED ─────────────────────────────────
from core.edge_handler import detect_reg_conflicts

router = APIRouter(tags=["Compliance Analysis"])


@router.post(
    "/conflict-check",
    summary="Detect conflicts between two or more regulations",
    responses={
        200: {"description": "Conflict analysis completed."},
        400: {"description": "Fewer than 2 regulation names provided."},
        401: {"description": "Missing or invalid JWT token."},
        429: {"description": "Rate limit exceeded."},
        500: {"description": "Conflict detection error."},
    },
)
@limiter.limit(settings.RATE_LIMIT_QUERY)
async def conflict_check(
    request: Request,
    body: ConflictCheckRequest,
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Detect conflicts between two or more loaded regulations.

    Pass a list of 2+ regulation names.
    Returns detected cross-regulation conflicts with severity ratings.

    **Example:** GDPR + DPDP Act may conflict on data retention vs erasure rights.

    🔒 **Requires Bearer token** from `POST /auth/token`.
    """
    if len(body.regulation_names) < 2:
        raise HTTPException(
            status_code=400,
            detail="Provide at least 2 regulation names to check for conflicts.",
        )

    try:
        result = await asyncio.to_thread(detect_reg_conflicts, body.regulation_names)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Conflict check error: {exc}")

    return {**result, "checked_by": current_user}
