"""
middleware/logging_middleware.py — Request / Response Logging
==============================================================
Logs every inbound request and outbound response in a clean,
recruiter-readable format:

    INFO  - 2024-01-15 14:32:01 - POST /query          - 200 -  1.42s
    INFO  - 2024-01-15 14:32:03 - POST /upload         - 200 -  3.87s
    ERROR - 2024-01-15 14:32:05 - POST /gap-analysis   - 500 -  0.12s

Why a middleware (not decorators on each route)?
  • DRY — one place to add/modify logging for ALL endpoints
  • Catches errors that happen before your route code even runs
    (e.g. 422 validation errors, 404s)
  • Timing wraps the full request cycle including FastAPI overhead
"""

import logging
import time

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

# ── Logger setup ──────────────────────────────────────────────────────────────
# Use Python's standard logging so logs integrate with any log aggregator
# (CloudWatch, Datadog, Railway logs, etc.) without extra dependencies.
logger = logging.getLogger("ariras.access")


def configure_logging() -> None:
    """
    Call once at startup to configure root + ariras loggers.
    Format mirrors common production log formats — easy to grep.
    """
    log_format = "%(levelname)-5s - %(asctime)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        datefmt=date_format,
    )

    # Quieten noisy third-party loggers in production
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("langchain").setLevel(logging.WARNING)


# ── Middleware class ───────────────────────────────────────────────────────────

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    ASGI middleware that wraps every request/response cycle.

    Logs:
      • Method + path
      • Response status code
      • Total elapsed time in seconds
      • Client IP (useful for debugging rate limit issues)
      • Errors at ERROR level so they stand out in log streams
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()

        # ── Log the incoming request ───────────────────────────────────────
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            "→ %s %s  [client=%s]",
            request.method,
            request.url.path,
            client_ip,
        )

        # ── Call the actual route handler ──────────────────────────────────
        try:
            response: Response = await call_next(request)
        except Exception as exc:
            # Unhandled exceptions — log at ERROR level and re-raise so
            # FastAPI's default exception handler still returns a 500
            elapsed = time.perf_counter() - start_time
            logger.error(
                "✗ %s %s  - 500 - %.2fs  [UNHANDLED: %s]",
                request.method,
                request.url.path,
                elapsed,
                str(exc),
            )
            raise

        # ── Log the response ───────────────────────────────────────────────
        elapsed = time.perf_counter() - start_time
        status_code = response.status_code

        # Choose log level based on status: errors stand out
        if status_code >= 500:
            log_fn = logger.error
            icon = "✗"
        elif status_code >= 400:
            log_fn = logger.warning
            icon = "⚠"
        else:
            log_fn = logger.info
            icon = "✓"

        log_fn(
            "%s %s %s  - %d - %.2fs",
            icon,
            request.method,
            request.url.path,
            status_code,
            elapsed,
        )

        # Inject timing header — handy for frontend/API consumers
        response.headers["X-Response-Time"] = f"{elapsed:.3f}s"
        return response
