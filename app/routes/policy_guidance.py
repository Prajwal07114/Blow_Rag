"""
routes/policy_guidance.py — Policy Guidance Endpoints
=======================================================
  POST /policy-guidance         →  JSON guidance     [AUTH REQUIRED]
  POST /policy-guidance/export  →  Excel download     [AUTH REQUIRED]

Async note:
  generate_policy_guidance() calls:
    • load_vectorstore() — disk I/O (ChromaDB read)   → can benefit from async
    • retriever.invoke()  — in-process vector search  → CPU, minor I/O
    • Groq LLM API call   — network I/O               → big benefit from async

  We use asyncio.to_thread() to run the entire guidance generation off the
  main event loop thread so other requests aren't blocked during the
  (typically 3-8 second) LLM call.
"""

import asyncio
import io

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

from app.config import settings
from app.middleware.rate_limiter import limiter
from app.models.schemas import PolicyGuidanceRequest
from app.utils.auth import get_current_user
from app.utils.helpers import chroma_is_ready

# ── Import your existing pipeline — UNCHANGED ─────────────────────────────────
from agents.policy_builder import build_excel, generate_policy_guidance
from core.vectorstore import load_vectorstore

router = APIRouter(tags=["Policy Builder"])


# ── Helper: load regulation context from vectorstore (if indexed) ─────────────
def _load_regulation_context() -> str:
    """
    Pull the top-6 regulation chunks most relevant to compliance obligations.
    Returns empty string if no regulation is indexed or if load fails.

    This mirrors exactly what the original Streamlit app did — preserved unchanged.
    """
    if not chroma_is_ready(settings.CHROMA_PERSIST_DIR):
        return ""
    try:
        vs = load_vectorstore()
        retriever = vs.as_retriever(search_kwargs={"k": 6})
        docs = retriever.invoke(
            "obligations requirements compliance reporting disclosure penalties"
        )
        return "\n\n".join([d.page_content for d in docs])[:3500]
    except Exception:
        return ""


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT — Policy Guidance (JSON)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/policy-guidance",
    summary="Generate company-specific compliance policy guidance",
    responses={
        200: {"description": "Policy guidance generated successfully."},
        401: {"description": "Missing or invalid JWT token."},
        429: {"description": "Rate limit exceeded."},
        500: {"description": "Policy guidance pipeline error."},
    },
)
@limiter.limit(settings.RATE_LIMIT_QUERY)
async def policy_guidance(
    request: Request,
    body: PolicyGuidanceRequest,
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Generate tailored compliance policy guidance for a company.

    - Pulls regulation context from the indexed vectorstore (if available).
    - Calls Groq LLM to generate guidance sections, sample clauses, and actions.
    - **Works without a regulation indexed** — falls back to general best practices.

    🔒 **Requires Bearer token** from `POST /auth/token`.

    **Response fields:**
    - `readiness_score` — 0–100 compliance readiness estimate.
    - `regulation_used` — Regulation identified from the indexed content.
    - `summary` — Plain-English compliance situation overview.
    - `sections` — Guidance sections with sample clauses + regulation references.
    - `priority_actions` — Concrete immediate steps for the company.
    - `risk_areas` — Key compliance risk areas identified.
    """
    # Load context synchronously (could be empty if no regulation indexed)
    regulation_context = await asyncio.to_thread(_load_regulation_context)

    try:
        guidance = await asyncio.to_thread(
            generate_policy_guidance,
            company_name=body.company_name,
            company_description=body.company_description,
            information_flows=body.information_flows,
            key_stakeholders=body.key_stakeholders,
            compliance_concerns=body.compliance_concerns,
            existing_policies=body.existing_policies,
            regulation_context=regulation_context,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Policy guidance error: {exc}")

    return {**guidance, "generated_by": current_user}


# ═══════════════════════════════════════════════════════════════════════════════
# ENDPOINT — Policy Guidance (Excel Export)
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/policy-guidance/export",
    summary="Generate policy guidance — returns Excel (.xlsx) download",
    responses={
        200: {"description": "Excel report generated.", "content": {"application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": {}}},
        401: {"description": "Missing or invalid JWT token."},
        429: {"description": "Rate limit exceeded."},
        500: {"description": "Excel export error."},
    },
)
@limiter.limit(settings.RATE_LIMIT_QUERY)
async def policy_guidance_export(
    request: Request,
    body: PolicyGuidanceRequest,
    current_user: str = Depends(get_current_user),
) -> StreamingResponse:
    """
    Generate policy guidance and return it as a downloadable **Excel** report.

    Same as `POST /policy-guidance` but returns `.xlsx`.
    The workbook contains two sheets:
    - **Policy Guidance** — sections with sample clauses and references.
    - **Summary & Score** — readiness score and priority actions.

    🔒 **Requires Bearer token** from `POST /auth/token`.
    """
    regulation_context = await asyncio.to_thread(_load_regulation_context)

    try:
        guidance = await asyncio.to_thread(
            generate_policy_guidance,
            company_name=body.company_name,
            company_description=body.company_description,
            information_flows=body.information_flows,
            key_stakeholders=body.key_stakeholders,
            compliance_concerns=body.compliance_concerns,
            existing_policies=body.existing_policies,
            regulation_context=regulation_context,
        )
        excel_bytes = build_excel(guidance)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Excel export error: {exc}")

    safe_name = body.company_name.replace(" ", "_")
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": (
                f"attachment; filename=ARIRAS_Policy_{safe_name}.xlsx"
            )
        },
    )
