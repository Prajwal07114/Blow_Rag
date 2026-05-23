
# ARIRAS
### AI Regulatory Intelligence & Reporting Assurance System

[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=flat&logo=chainlink&logoColor=white)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6B35?style=flat)](https://trychroma.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Render](https://img.shields.io/badge/Live_on-Render-46E3B7?style=flat&logo=render&logoColor=white)](https://ariras-api.onrender.com)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)](LICENSE)

**Production-grade GenAI backend for automated regulatory compliance analysis.**

🚀 **Live API:** [https://ariras-api.onrender.com](https://ariras-api.onrender.com)
📖 **Swagger UI:** [https://ariras-api.onrender.com/docs](https://ariras-api.onrender.com/docs)


</div>

---

## What is ARIRAS?

ARIRAS is a **production-deployed AI backend** that transforms how companies interact with regulatory documents. Instead of lawyers spending hours reading PDFs, ARIRAS lets you:

- **Ask questions** about any regulation in plain English and get clause-referenced answers
- **Score your compliance** — upload your company policy and get a 0–100 gap analysis
- **Generate policy guidance** — AI-tailored recommendations with sample clauses for your specific company
- **Detect regulation conflicts** — find legal contradictions between frameworks like GDPR vs DPDP Act

Built to demonstrate **GenAI engineering**, **MLOps**, and **production FastAPI** skills for internship applications.

---

## Live Demo

> ⚠️ Free tier on Render — first request may take 30–60 seconds to cold start.

```bash
# 1. Health check (no auth needed)
curl https://ariras-api.onrender.com/health

# 2. Get auth token
curl -X POST https://ariras-api.onrender.com/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "ariras_user", "password": "ariras_pass_2024"}'

# 3. Ask a question (use token from step 2)
curl -X POST https://ariras-api.onrender.com/query \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the penalties for a data breach?"}'
```

Or open **[/docs](https://ariras-api.onrender.com/docs)** and try everything interactively in Swagger UI.

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| **API Framework** | FastAPI 0.115 + Uvicorn | Async-native, auto Swagger docs, production-grade |
| **LLM** | Groq (Llama 3.3 70B) via LangChain | Fast inference, free tier, structured output |
| **Vector Store** | ChromaDB | Local-first, no cloud dependency, persistent on disk |
| **Embeddings** | `all-MiniLM-L6-v2` (HuggingFace) | Lightweight, fast, good semantic similarity |
| **Agent Framework** | LangChain | Prompt chaining, retrieval, output parsing |
| **Authentication** | PyJWT (HS256 Bearer tokens) | Stateless, no session storage, horizontally scalable |
| **Rate Limiting** | SlowAPI | Per-IP limits, protects LLM cost |
| **Config** | Pydantic Settings | Type-validated env vars, single source of truth |
| **Containerisation** | Docker | Reproducible builds, Render/Railway compatible |
| **Language** | Python 3.11 | `asyncio.to_thread()` available, modern type hints |

---

## Project Structure

```
ARIRAS/
│
├── app/                          ← FastAPI application
│   ├── main.py                   ← App factory, middleware, router registration
│   ├── config.py                 ← Centralised settings (pydantic-settings)
│   │
│   ├── routes/                   ← One file per endpoint group
│   │   ├── auth.py               ← POST /auth/token, GET /auth/me
│   │   ├── general.py            ← GET /, GET /health
│   │   ├── regulation.py         ← POST /upload, POST /query
│   │   ├── compliance.py         ← POST /gap-analysis, POST /conflict-check
│   │   └── policy.py             ← POST /policy-guidance
│   │
│   ├── middleware/
│   │   ├── auth.py               ← JWT create / verify / FastAPI dependency
│   │   ├── logging.py            ← Request/response timing + structured logging
│   │   └── rate_limit.py         ← SlowAPI limiter + custom 429 handler
│   │
│   ├── models/
│   │   └── schemas.py            ← All Pydantic request/response models
│   │
│   └── services/
│       └── rag_service.py        ← Async service layer wrapping RAG pipeline
│
├── agents/                       ← RAG pipeline (core business logic)
│   ├── rag_agent.py              ← ask_regulation() — retrieval + LLM Q&A
│   ├── gap_detector.py           ← detect_gaps() — compliance gap analysis
│   └── policy_builder.py         ← generate_policy_guidance() — policy AI
│
├── core/                         ← Infrastructure
│   ├── vectorstore.py            ← ChromaDB build + load + embedding
│   └── edge_handler.py           ← Confidence scoring + preflight checks
│
├── data/
│   ├── uploads/                  ← Uploaded PDFs (regulation + policy)
│   └── chroma_db/                ← Persisted ChromaDB vector embeddings
│
├── Dockerfile                    ← Production Docker build
├── .dockerignore
├── requirements.txt
├── .env.example                  ← Environment variable template
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Auth | Rate Limit | Description |
|---|---|---|---|---|
| `GET` | `/` | ❌ | 30/min | Welcome + API info |
| `GET` | `/health` | ❌ | 30/min | System health check |
| `POST` | `/auth/token` | ❌ | 30/min | Login → get JWT token |
| `GET` | `/auth/me` | ✅ | 30/min | Verify token + current user |
| `POST` | `/upload` | ✅ | 10/min | Upload & index regulation PDF |
| `POST` | `/query` | ✅ | 5/min | RAG Q&A against regulation |
| `POST` | `/gap-analysis` | ✅ | 5/min | Gap analysis → JSON report |
| `POST` | `/gap-analysis/export` | ✅ | 5/min | Gap analysis → Excel download |
| `POST` | `/policy-guidance` | ✅ | 5/min | AI policy guidance → JSON |
| `POST` | `/policy-guidance/export` | ✅ | 5/min | AI policy guidance → Excel |
| `POST` | `/conflict-check` | ✅ | 5/min | Detect conflicts between regulations |

---

## Quick Start

### Prerequisites
- Python 3.11+
- A free [Groq API key](https://console.groq.com)

### 1. Clone the repo
```bash
git clone https://github.com/Prajwal07114/Blow_Rag.git
cd Blow_Rag
```

### 2. Create virtual environment
```bash
# Windows
py -3.11 -m venv venv
venv\Scripts\activate

# Mac / Linux
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment
```bash
# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
```

Edit `.env`:
```env
GROQ_API_KEY=your_groq_key_here
JWT_SECRET_KEY=your_secret        # generate: python -c "import secrets; print(secrets.token_hex(32))"
DEMO_USERNAME=ariras_user
DEMO_PASSWORD=ariras_pass_2024
APP_ENV=development
```

### 5. Run the server
```bash
uvicorn app.main:app --reload --port 10000
```

### 6. Open Swagger UI
```
http://localhost:10000/docs
```

---

## Authentication Flow

All sensitive endpoints require a Bearer JWT token.

### Step 1 — Get a token
```bash
curl -X POST http://localhost:10000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "ariras_user", "password": "ariras_pass_2024"}'
```

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Step 2 — Use the token
```bash
curl -X POST http://localhost:10000/query \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the breach notification obligations?"}'
```

### In Swagger UI
1. Call `POST /auth/token`
2. Copy the `access_token`
3. Click **Authorize 🔒** at the top of `/docs`
4. Enter: `Bearer YOUR_TOKEN`
5. All protected endpoints are now unlocked

---

## Example Requests & Responses

### Query a regulation
```json
POST /query
{
  "question": "What are the penalties for data breach under DPDP Act?"
}
```
```json
{
  "question": "What are the penalties for data breach under DPDP Act?",
  "answer": "Under Section 33(1) of the DPDP Act 2023, penalties for data breaches can reach ₹250 crore...",
  "sources": ["[Page 18] Section 33 — Penalties and adjudication..."],
  "confidence": "HIGH",
  "confidence_score": 87,
  "warnings": [],
  "answer_safe": true
}
```

### Gap Analysis
```bash
POST /gap-analysis
Content-Type: multipart/form-data

file: company_policy.pdf
regulation_name: DPDP Act 2023
```
```json
{
  "compliance_score": 42,
  "gaps": [
    {
      "obligation": "Breach Notification",
      "severity": "high",
      "regulation_source": "Section 8(6) requires notification to the Board...",
      "what_is_missing": "Policy has no breach notification procedure.",
      "rationale": "Failure to notify exposes company to ₹200 crore penalty.",
      "recommended_action": "Add breach response SOP with 72-hour notification window."
    }
  ],
  "met": [
    { "obligation": "Privacy Policy Existence", "note": "Policy published on website." }
  ]
}
```

### Policy Guidance
```json
POST /policy-guidance
{
  "company_name": "Finova Technologies Pvt Ltd",
  "company_description": "Fintech startup providing short-term loans via mobile app.",
  "information_flows": "We collect Aadhaar, PAN, salary slips, bank account details.",
  "key_stakeholders": "Customers, HDFC Bank, AWS, CIBIL, investors.",
  "compliance_concerns": "Not sure if our consent process is legally valid.",
  "existing_policies": "Basic privacy policy, last updated 2 years ago."
}
```

### Conflict Check
```json
POST /conflict-check
{
  "regulation_names": ["GDPR", "DPDP Act 2023"]
}
```

---

## Engineering Decisions

*The non-obvious choices — and exactly what interviewers ask about.*

### 1. `asyncio.to_thread()` over `async def` in RAG functions
LangChain, ChromaDB, and the Groq SDK are all **synchronous** libraries. Simply marking an endpoint `async def` does not make blocking I/O non-blocking — it still freezes the event loop during the LLM call (~1–3 seconds).

The correct pattern is `asyncio.to_thread()`, which runs the synchronous code in a **thread pool executor** and yields control back to FastAPI's event loop so other requests can be served concurrently.

```python
# ❌ Wrong — still blocks the event loop
async def query_rag():
    result = ask_regulation(question)   # blocks for 2s, server frozen

# ✅ Correct — event loop stays free
async def query_rag():
    result = await asyncio.to_thread(ask_regulation, question)
```

### 2. FastAPI `Depends()` for auth instead of middleware
JWT validation is a **FastAPI dependency**, not an ASGI middleware. The difference:

- **Middleware** runs on *every* request including `/health`, `/docs`, and `/openapi.json`
- **Depends()** runs only on endpoints that explicitly declare it

Public endpoints stay public with zero special-casing, and the auth logic is independently unit-testable by overriding the dependency in tests.

### 3. `_FileAdapter` pattern — zero changes to RAG logic
`detect_gaps()` was written for Streamlit's `UploadedFile` interface (`.name` + `.read()`). Rather than rewriting the agent, a 6-line adapter class gives FastAPI's `UploadFile` the exact same interface — the RAG pipeline never knew anything changed.

```python
class _FileAdapter:
    def __init__(self, path: Path):
        self.name  = path.name
        self._path = path
    def read(self) -> bytes:
        return self._path.read_bytes()
```

### 4. Two-layer confidence scoring
Every RAG answer passes two validation layers before reaching the client:
- **Layer 1 — Semantic grounding:** Cosine similarity between the answer embedding and retrieved chunk embeddings
- **Layer 2 — LLM-as-judge:** A second zero-temperature Groq call verifies every factual claim is explicitly supported by the source chunks

This catches hallucinations that pass semantic similarity (the answer *sounds* related but makes unsupported claims).

---

## Request Lifecycle

```
Client Request
      │
      ▼
SlowAPIMiddleware          ← Check rate limit by IP → HTTP 429 if exceeded
      │
      ▼
LoggingMiddleware           ← Log "→ POST /query" + start timer
      │
      ▼
CORSMiddleware              ← Add CORS headers
      │
      ▼
FastAPI Router              ← Match route to handler
      │
      ▼
require_auth (Depends)      ← Decode + validate JWT → HTTP 401 if invalid
      │
      ▼
Route Handler (async)       ← Parse + validate request body (Pydantic)
      │
      ▼
Service Layer
      ├── asyncio.to_thread() → ChromaDB retrieval   (~50ms, blocking)
      ├── asyncio.to_thread() → Groq LLM call        (~1–3s, blocking)
      └── asyncio.to_thread() → Faithfulness judge   (~1s,   blocking)
      │
      ▼
LoggingMiddleware           ← Log "← POST /query | 200 | 1.42s"
      │
      ▼
Client Response
```

---

## Production Features

### Structured Request Logging
```
2024-01-15 14:32:01 | INFO  | → POST   /query           | from 127.0.0.1
2024-01-15 14:32:03 | INFO  | ← POST   /query           | 200 | 1.423s | 127.0.0.1
2024-01-15 14:32:05 | WARN  | ← POST   /query           | 429 | 0.001s | 127.0.0.1
2024-01-15 14:32:07 | ERROR | ← POST   /gap-analysis    | 500 | 0.112s | 127.0.0.1
```
- Handles `X-Forwarded-For` for correct IP behind Render/Railway reverse proxies
- Adds `X-Process-Time` header to every response

### Rate Limiting
| Endpoint Type | Limit | Reason |
|---|---|---|
| LLM endpoints (`/query`, `/gap-analysis`, `/policy-guidance`) | 5 req/min | Groq API cost protection |
| Upload endpoints | 10 req/min | File I/O + embedding compute |
| Read endpoints | 30 req/min | Cheap config/health reads |

### Async Architecture
| Operation | Pattern | Reason |
|---|---|---|
| File upload | `await file.read()` | Native async I/O |
| LLM calls (Groq) | `asyncio.to_thread()` | Sync library — thread pool |
| ChromaDB queries | `asyncio.to_thread()` | Disk + CPU I/O |
| Embedding generation | `asyncio.to_thread()` | CPU-bound |
| Excel generation | Sync | Pure in-memory, <10ms |

---

## Docker

```bash
# Build
docker build -t ariras-api .

# Run
docker run -p 10000:10000 --env-file .env ariras-api

# With persistent data volumes (recommended)
docker run -p 10000:10000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  ariras-api
```

---

## Deployment

### Render (Free Tier)
1. Push to GitHub
2. New Web Service → connect repo
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`

> **Note:** Free tier has ephemeral disk — ChromaDB resets on restart. Re-upload your regulation PDF after each cold start. Use Render's persistent disk (paid) or swap to Pinecone for production persistence.

### Railway
1. Push to GitHub → New Project → Deploy from GitHub
2. Railway auto-detects the Dockerfile
3. Add environment variables in dashboard

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `GROQ_API_KEY` | ✅ | Groq API key from [console.groq.com](https://console.groq.com) |
| `JWT_SECRET_KEY` | ✅ | Secret for signing JWTs — `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DEMO_USERNAME` | ✅ | Login username |
| `DEMO_PASSWORD` | ✅ | Login password |
| `APP_ENV` | ❌ | `development` or `production` (default: `development`) |
| `GROQ_MODEL` | ❌ | Groq model name (default: `llama-3.3-70b-versatile`) |
| `CHROMA_PERSIST_DIR` | ❌ | ChromaDB path (default: `./data/chroma_db`) |
| `UPLOAD_DIR` | ❌ | PDF storage path (default: `./data/uploads`) |
| `JWT_EXPIRE_MINUTES` | ❌ | Token expiry in minutes (default: `60`) |
| `RATE_LIMIT_QUERY` | ❌ | LLM endpoint rate limit (default: `5/minute`) |

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

<div align="center">


[Live API](https://ariras-api.onrender.com) · [Swagger Docs](https://ariras-api.onrender.com/docs) · [GitHub](https://github.com/Prajwal07114/Blow_Rag)

</div>
