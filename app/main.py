"""
app/main.py — ARIRAS FastAPI Backend  (Day 2: Production Upgrade)
=================================================================
What changed from Day 1:
  ✓ JWT authentication middleware on all sensitive endpoints
  ✓ Request/response logging middleware (timing + status codes)
  ✓ Rate limiting via SlowAPI (protects LLM spend)
  ✓ All heavy endpoints converted to async (LLM + DB I/O)
  ✓ Modular router architecture (routes/, services/, middleware/)
  ✓ Centralised config via pydantic-settings + .env
  ✓ Docker-ready (uvicorn on 0.0.0.0:10000)

What stayed the same (Day 1 preserved):
  ✓ All 9 original endpoints work identically
  ✓ RAG pipeline code untouched (core/, agents/)
  ✓ Swagger docs at /docs
  ✓ Same request/response shapes

Run locally:
    uvicorn app.main:app --reload --port 10000

Swagger UI:
    http://localhost:10000/docs

Auth flow:
    1. POST /auth/token  { username, password }  →  { access_token }
    2. Click "Authorize 🔒" in Swagger, paste the token
    3. All protected endpoints now work
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import settings
from app.middleware import LoggingMiddleware, configure_logging, limiter
from app.routes import (
    auth_router,
    conflict_router,
    gap_router,
    general_router,
    policy_router,
    query_router,
    regulation_router,
)

# ── Logging — configure before anything else ──────────────────────────────────
configure_logging()


# ── Lifespan — startup / shutdown tasks ──────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once at startup and once at shutdown.
    Good place for: DB connection pools, model pre-loading, cache warming.
    """
    import logging
    logger = logging.getLogger("ariras.startup")

    # Ensure required directories exist
    Path(settings.UPLOAD_DIR).mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

    logger.info("=" * 60)
    logger.info("  %s v%s  [%s]", settings.APP_NAME, settings.APP_VERSION, settings.ENVIRONMENT)
    logger.info("  Upload dir  : %s", settings.UPLOAD_DIR)
    logger.info("  Chroma dir  : %s", settings.CHROMA_PERSIST_DIR)
    logger.info("  Docs        : http://0.0.0.0:%d/docs", settings.PORT)
    logger.info("=" * 60)

    yield  # server runs here

    logger.info("ARIRAS API shutting down.")


# ── FastAPI app ────────────────────────────────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    description="""
## AI Regulatory Intelligence & Reporting Assurance System

Production-grade FastAPI backend exposing a RAG pipeline as REST endpoints.

### Authentication
All sensitive endpoints require a **Bearer JWT token**.

1. Call **`POST /auth/token`** with your credentials.
2. Click the **Authorize 🔒** button above and paste the token.
3. Protected endpoints will now work.

### Demo Credentials
| Field    | Value         |
|----------|---------------|
| username | `ariras_user` |
| password | `ariras_pass` |

### Endpoint Groups
| Tag                    | Purpose                                      |
|------------------------|----------------------------------------------|
| Authentication         | Login → get JWT token                        |
| General                | Health check, welcome                        |
| Regulation Management  | Upload & index regulation PDFs               |
| RAG Q&A                | Ask questions against indexed regulations    |
| Compliance Analysis    | Gap analysis, conflict detection             |
| Policy Builder         | AI-generated company policy guidance         |

### Rate Limits
| Endpoint group          | Limit         |
|-------------------------|---------------|
| LLM-backed endpoints    | 5 req / min   |
| Upload endpoints        | 10 req / min  |
| Read endpoints          | 30 req / min  |
    """,
    version=settings.APP_VERSION,
    contact={"name": "Team Token Burners", "email": "team@ariras.ai"},
    lifespan=lifespan,
    # Swagger UI customisation
    swagger_ui_parameters={
        "persistAuthorization": True,    # keeps your token across page refreshes
        "displayRequestDuration": True,  # shows response time in Swagger
    },
)

# ── Rate limiter state ────────────────────────────────────────────────────────
# Attach limiter to the app so SlowAPI can read/write request counts
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware stack ──────────────────────────────────────────────────────────
# Order matters: middleware runs top-to-bottom on request, bottom-to-top on response.
app.add_middleware(SlowAPIMiddleware)     # rate limiting
app.add_middleware(LoggingMiddleware)    # request/response logging + timing

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(general_router)
app.include_router(auth_router)
app.include_router(regulation_router)
app.include_router(query_router)
app.include_router(gap_router)
app.include_router(policy_router)
app.include_router(conflict_router)


# ── Global exception handler ──────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for any unhandled exception.
    Returns a clean 500 JSON response instead of a raw Python traceback.
    In production, also log to an error tracker (Sentry, Datadog, etc.).
    """
    import logging
    logging.getLogger("ariras.error").exception(
        "Unhandled exception on %s %s", request.method, request.url.path
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred. Please try again later.",
            "path": str(request.url.path),
        },
    )
