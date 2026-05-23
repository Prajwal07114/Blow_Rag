# ARIRAS API — Day 2: Production Upgrade

> **AI Regulatory Intelligence & Reporting Assurance System**  
> FastAPI + LangChain + ChromaDB — Production-Ready RAG Backend

[![Python](https://img.shields.io/badge/Python-3.11-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-ready-blue)](https://docker.com)

---

## What's New in Day 2

| Feature | Status |
|---|---|
| JWT Authentication (Bearer token) | ✅ |
| Request/Response Logging Middleware | ✅ |
| Rate Limiting (SlowAPI) | ✅ |
| Async endpoints (LLM + DB calls) | ✅ |
| Dockerized + Render/Railway ready | ✅ |
| Centralised config (.env / pydantic-settings) | ✅ |
| Modular router architecture | ✅ |
| All Day 1 endpoints preserved | ✅ |

---

## Project Structure

```
project/
├── app/
│   ├── main.py              ← FastAPI app, middleware setup, router registration
│   ├── config.py            ← All settings from .env (pydantic-settings)
│   │
│   ├── routes/
│   │   ├── auth.py          ← POST /auth/token
│   │   ├── general.py       ← GET /, GET /health
│   │   ├── regulation.py    ← POST /regulation/upload
│   │   ├── query.py         ← POST /query
│   │   ├── gap_analysis.py  ← POST /gap-analysis, /gap-analysis/export
│   │   ├── policy_guidance.py ← POST /policy-guidance, /policy-guidance/export
│   │   └── conflict_check.py ← POST /conflict-check
│   │
│   ├── middleware/
│   │   ├── logging_middleware.py  ← request/response timing + status logs
│   │   └── rate_limiter.py        ← SlowAPI limiter instance
│   │
│   ├── models/
│   │   └── schemas.py       ← All Pydantic request/response models
│   │
│   └── utils/
│       ├── auth.py          ← JWT create / verify / FastAPI dependency
│       └── helpers.py       ← chroma_is_ready(), require_vectorstore(), FileAdapter
│
├── agents/                  ← Your existing RAG agents (UNTOUCHED)
├── core/                    ← Your existing vectorstore + edge handler (UNTOUCHED)
│
├── Dockerfile
├── .dockerignore
├── requirements.txt
├── .env.example
└── README.md
```

---

## Quick Start

### 1. Local Development

```bash
# Clone & set up
cp .env.example .env
# Fill in your GROQ_API_KEY in .env

pip install -r requirements.txt

# Run
uvicorn app.main:app --reload --port 10000
```

Open **http://localhost:10000/docs** for Swagger UI.

### 2. Docker

```bash
# Build
docker build -t ariras-api .

# Run (reads .env for secrets)
docker run -p 10000:10000 --env-file .env ariras-api

# With persistent data volumes (recommended)
docker run -p 10000:10000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  ariras-api
```

---

## Authentication Flow

All endpoints except `/`, `/health`, and `POST /auth/token` require a JWT.

```
POST /auth/token
  Body: { "username": "ariras_user", "password": "ariras_pass" }
  Returns: { "access_token": "eyJ...", "token_type": "bearer", "expires_in": 3600 }
```

**In Swagger UI:**
1. Call `POST /auth/token`
2. Copy the `access_token` value
3. Click **Authorize 🔒** (top of page)
4. Paste the token → click Authorize

**In curl / Postman:**
```bash
# Get token
TOKEN=$(curl -s -X POST http://localhost:10000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username":"ariras_user","password":"ariras_pass"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Use token
curl -X POST http://localhost:10000/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the breach notification obligations?"}'
```

---

## Endpoints

| Method | Path | Auth | Rate Limit | Description |
|--------|------|------|------------|-------------|
| GET | `/` | ❌ | 30/min | Welcome + API info |
| GET | `/health` | ❌ | 30/min | System health check |
| POST | `/auth/token` | ❌ | 30/min | Login → get JWT |
| POST | `/regulation/upload` | ✅ | 10/min | Upload & index regulation PDF |
| POST | `/query` | ✅ | 5/min | RAG Q&A against regulation |
| POST | `/gap-analysis` | ✅ | 5/min | Gap analysis (JSON) |
| POST | `/gap-analysis/export` | ✅ | 5/min | Gap analysis (Excel) |
| POST | `/policy-guidance` | ✅ | 5/min | Policy guidance (JSON) |
| POST | `/policy-guidance/export` | ✅ | 5/min | Policy guidance (Excel) |
| POST | `/conflict-check` | ✅ | 5/min | Regulation conflict detection |

---

## Logging

Every request logs in a clean, structured format:

```
INFO  - 2024-01-15 14:32:01 - → POST /query  [client=127.0.0.1]
INFO  - 2024-01-15 14:32:03 - ✓ POST /query  - 200 - 1.42s
INFO  - 2024-01-15 14:32:05 - → POST /regulation/upload  [client=127.0.0.1]
INFO  - 2024-01-15 14:32:08 - ✓ POST /regulation/upload  - 200 - 3.87s
WARN  - 2024-01-15 14:32:10 - ⚠ POST /query  - 429 - 0.01s
ERROR - 2024-01-15 14:32:12 - ✗ POST /gap-analysis  - 500 - 0.12s
```

Logs are also available via the `X-Response-Time` header on every response.

---

## Rate Limiting

Responses include standard rate-limit headers:

```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1705330323
```

When exceeded, returns HTTP 429:
```json
{ "error": "Rate limit exceeded: 5 per 1 minute" }
```

---

## Architecture — Request Lifecycle

```
Client Request
      │
      ▼
SlowAPIMiddleware          ← Check rate limit (reject with 429 if exceeded)
      │
      ▼
LoggingMiddleware          ← Log "→ POST /query [client=x.x.x.x]"
      │                       Start timer
      ▼
FastAPI Router             ← Route matching
      │
      ▼
Depends(get_current_user)  ← Decode JWT → extract username
      │                       Raise 401 if invalid/missing
      ▼
Route Handler (async)      ← Business logic
      │
      │  asyncio.to_thread()
      ├──────────────────→  LLM call (Groq API)     ← in thread pool
      │                     ChromaDB query           ← in thread pool
      │◄─────────────────── results
      │
      ▼
LoggingMiddleware          ← Log "✓ POST /query - 200 - 1.42s"
      │                       Add X-Response-Time header
      ▼
Client Response
```

---

## Async Strategy

| Call type | Async? | Method | Reason |
|-----------|--------|--------|--------|
| `await file.read()` | ✅ Yes | Native async | FastAPI UploadFile is awaitable |
| `ask_regulation()` | ✅ Yes | `asyncio.to_thread()` | Network I/O (LLM API) — sync wrapper |
| `detect_gaps()` | ✅ Yes | `asyncio.to_thread()` | Disk I/O + Network I/O |
| `build_vectorstore()` | ❌ No (in thread) | `asyncio.to_thread()` | CPU-bound (embedding) — thread pool |
| `build_excel()` | ❌ Sync is fine | Sync | Pure in-memory, <10ms |

**Rule of thumb:**
- **Network I/O** (LLM APIs, HTTP calls) → always async
- **Disk I/O** (file reads/writes) → async where possible
- **CPU-heavy** (embedding, tokenization) → `asyncio.to_thread()` to avoid blocking event loop
- **In-memory** (dict ops, string ops) → sync is fine

---

## Deployment

### Render

1. Push code to GitHub
2. New Web Service → connect repo
3. **Build Command:** `pip install -r requirements.txt`
4. **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example` in the Render dashboard

### Railway

1. Push code to GitHub
2. New Project → Deploy from GitHub repo
3. Railway auto-detects the `Dockerfile`
4. Add environment variables in the Railway dashboard

### Environment Variables for Production

```bash
ENVIRONMENT=production
JWT_SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
GROQ_API_KEY=<your key>
DEMO_USERNAME=<real username>
DEMO_PASSWORD=<real password>
```

---

## Security Notes for Production

1. **Rotate the JWT secret** — generate with `secrets.token_hex(32)`
2. **Replace demo credentials** — wire up a real user database
3. **Hash passwords with bcrypt** — `passlib[bcrypt]` is already in requirements.txt
4. **Add CORS** — use `fastapi.middleware.cors.CORSMiddleware` if browser clients connect
5. **Use Redis for rate limiting** — swap `get_remote_address` for Redis storage at scale
6. **Move embeddings to a worker** — ChromaDB + embedding is CPU-heavy; use Celery at scale

---

*Built by Team Token Burners — Day 2 Production Upgrade*
