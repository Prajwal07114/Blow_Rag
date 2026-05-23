"""
routes/query.py — RAG Q&A Endpoint
=====================================
  POST /query  →  Ask a question against the indexed regulation  [AUTH REQUIRED]

Async discussion:
  ask_regulation() makes a network call to the Groq LLM API.
  Network I/O is exactly where `async def` helps:
    • While waiting for Groq to respond the event loop is free to handle
      other incoming requests — better throughput under concurrent load.
    • We can't use `await` on the raw LangChain call (it's sync internally)
      so we use asyncio.to_thread() to run it in a thread pool without
      blocking the event loop.  This is the correct pattern for wrapping
      synchronous I/O-bound code in an async FastAPI handler.
"""

import asyncio

from fastapi import APIRouter, Depends, HTTPException, Request

from app.config import settings
from app.middleware.rate_limiter import limiter
from app.models.schemas import QueryRequest
from app.utils.auth import get_current_user
from app.utils.helpers import require_vectorstore

# ── Import your existing pipeline — UNCHANGED ─────────────────────────────────
from agents.rag_agent import ask_regulation

router = APIRouter(tags=["RAG Q&A"])


@router.post(
    "/query",
    summary="Ask a question against the indexed regulation (RAG)",
    responses={
        200: {"description": "Answer generated successfully."},
        400: {"description": "No regulation indexed or empty question."},
        401: {"description": "Missing or invalid JWT token."},
        429: {"description": "Rate limit exceeded — max 5 requests/minute."},
        500: {"description": "RAG pipeline error."},
    },
)
@limiter.limit(settings.RATE_LIMIT_QUERY)    # 5/minute — protects Groq API spend
async def query_rag(
    request: Request,                         # required by slowapi
    body: QueryRequest,
    current_user: str = Depends(get_current_user),
) -> dict:
    """
    Ask a natural-language question against the indexed regulation.

    - Retrieves relevant chunks from ChromaDB (semantic search).
    - Generates a grounded answer via Groq LLM.
    - Returns confidence score + source clause references.

    **Requires:** A regulation must be indexed first via `POST /regulation/upload`.

    🔒 **Requires Bearer token** from `POST /auth/token`.

    **Response fields:**
    - `answer` — LLM-generated answer with clause references.
    - `sources` — Regulation excerpts used as grounding context.
    - `confidence` — `HIGH` / `MEDIUM` / `LOW` / `INSUFFICIENT`.
    - `confidence_score` — Composite 0–100 score (semantic + faithfulness).
    - `warnings` — Hallucination or grounding warnings.
    - `answer_safe` — Whether the answer passed safety checks.
    """
    # ── Pre-flight guards ─────────────────────────────────────────────────────
    require_vectorstore(settings.CHROMA_PERSIST_DIR)

    if not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # ── Call RAG pipeline in a thread pool ────────────────────────────────────
    # ask_regulation() is synchronous (LangChain / Groq network call).
    # asyncio.to_thread() runs it in a thread pool without blocking the
    # event loop — other requests can be handled concurrently while we wait.
    try:
        result = await asyncio.to_thread(ask_regulation, body.question)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {exc}")

    # ── Flatten edge metadata to top level ───────────────────────────────────
    edge = result.get("_edge", {})

    return {
        "question": body.question,
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "confidence": edge.get("confidence", "UNKNOWN"),
        "confidence_score": edge.get("confidence_score", 0),
        "warnings": edge.get("warnings", []),
        "answer_safe": edge.get("answer_safe", False),
        "_edge": edge,
        "queried_by": current_user,
    }
