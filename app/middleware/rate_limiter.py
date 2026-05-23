"""
middleware/rate_limiter.py — Rate Limiting with SlowAPI
========================================================
Prevents API abuse and protects expensive LLM endpoints.

Why rate limiting matters for AI backends:
  • Each /query call hits a paid LLM API (Groq/OpenAI) — abuse = real cost
  • ChromaDB is single-threaded by default — floods can freeze the server
  • Demonstrates production awareness to interviewers

Implementation: SlowAPI (the FastAPI port of Flask-Limiter)
  • Uses in-memory storage — fine for single-instance deployments
  • Easy to swap to Redis storage for multi-instance (just change the key_func)

Limits applied:
  • /query, /gap-analysis, /policy-guidance  → 5 req/min  (LLM-backed, expensive)
  • /upload                                  → 10 req/min (disk + embed, moderate)
  • Everything else                          → 30 req/min (cheap reads)

Usage in routes:
    from app.middleware.rate_limiter import limiter
    from slowapi.errors import RateLimitExceeded

    @router.post("/query")
    @limiter.limit("5/minute")
    async def query(request: Request, ...):   # `request` param REQUIRED by slowapi
        ...
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Identify clients by their IP address.
# In production behind a reverse proxy, swap get_remote_address for a function
# that reads the X-Forwarded-For header instead.
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["30/minute"],   # fallback limit for any un-decorated route
)
