# ═══════════════════════════════════════════════════════════════════════════════
# ARIRAS API — Dockerfile
# ═══════════════════════════════════════════════════════════════════════════════
#
# Multi-stage build strategy:
#   Stage 1 (builder) — install all dependencies into a clean venv
#   Stage 2 (runtime) — copy only the venv + app code; no build tools in prod
#
# This keeps the final image lean (~400 MB vs ~900 MB for a single-stage build)
# and means no pip / gcc in production — smaller attack surface.
#
# Build:  docker build -t ariras-api .
# Run:    docker run -p 10000:10000 --env-file .env ariras-api
#
# Render / Railway:
#   Both platforms auto-detect the Dockerfile.
#   Set your environment variables in the platform dashboard instead of .env.
# ═══════════════════════════════════════════════════════════════════════════════

# ── Stage 1: dependency builder ───────────────────────────────────────────────
# cache-bust: 1
FROM python:3.11-slim AS builder

# Don't write .pyc files; don't buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install system build dependencies needed for some Python packages
# (chromadb needs sqlite3; some ML libs need gcc)
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libsqlite3-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first — Docker layer cache means this only re-runs
# when requirements.txt changes, not on every code change.
COPY requirements.txt .

# Create a virtual environment and install all dependencies into it
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ── Stage 2: production runtime ───────────────────────────────────────────────
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    # Point Python at the venv from Stage 1
    PATH="/opt/venv/bin:$PATH" \
    # Default port — override with PORT env var on Render/Railway
    PORT=10000

WORKDIR /app

# Runtime system dependencies only (no build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libsqlite3-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the virtual environment from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application source code
# .dockerignore excludes: .env, __pycache__, data/, *.pyc, .git, etc.
COPY app/       ./app/
COPY agents/    ./agents/
COPY core/      ./core/

# Create persistent data directories
# These will be overridden by volume mounts or cloud storage in production

# Non-root user — security best practice
RUN useradd --no-create-home --shell /bin/false ariras && \
    mkdir -p data/uploads data/chroma_db && \
    chown -R ariras:ariras /app
USER ariras
# Document which port the container listens on
EXPOSE 10000

# Health check — Docker / Render / Railway will poll this
# Starts checking after 30s, retries 3 times before marking unhealthy
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:10000/health || exit 1

# Production server command:
#   --host 0.0.0.0      → accept external connections (required in Docker)
#   --port $PORT        → use env var (Render/Railway inject PORT automatically)
#   --workers 1         → single worker (ChromaDB is not multi-process safe)
#   --loop uvloop       → faster async event loop (auto-installed)
#   --access-log        → log requests (our middleware also logs, belt+suspenders)
#   --no-server-header  → don't expose uvicorn version in response headers
CMD uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT:-10000} \
        --workers 1 \
        --loop uvloop \
        --access-log \
        --no-server-header
