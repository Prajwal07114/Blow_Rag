
ARIRAS — AI Regulatory Intelligence & Reporting Assurance System

Production-grade RAG backend for automated compliance analysis, gap detection, and policy guidance generation.
Built with FastAPI · LangChain · ChromaDB · Groq LLM · Docker


What is ARIRAS?
ARIRAS is an AI-powered regulatory compliance backend that helps companies:

Understand regulations — Ask plain-English questions against any regulation PDF
Detect compliance gaps — Upload your company policy and get a scored gap report
Generate policy guidance — Get tailored compliance recommendations for your company
Detect regulation conflicts — Find contradictions between multiple regulations (e.g. GDPR vs DPDP)

Built as a portfolio project demonstrating GenAI engineering, MLOps, and production FastAPI skills.

Tech Stack
LayerTechnologyAPI FrameworkFastAPI 0.115 + UvicornLLMGroq (Llama 3) via LangChainVector StoreChromaDBEmbeddingsSentence Transformers (HuggingFace)Agent FrameworkLangGraphAuthenticationJWT (python-jose)Rate LimitingSlowAPIConfig ManagementPydantic Settings + .envContainerisationDocker (multi-stage build)LanguagePython 3.11

Project Structure
ARIRAS/
│
├── app/                        ← FastAPI application (Day 2)
│   ├── main.py                 ← App factory, middleware, router registration
│   ├── config.py               ← Centralised settings via pydantic-settings
│   │
│   ├── routes/                 ← One file per endpoint group
│   │   ├── auth.py             ← POST /auth/token
│   │   ├── general.py          ← GET /, GET /health
│   │   ├── regulation.py       ← POST /regulation/upload
│   │   ├── query.py            ← POST /query
│   │   ├── gap_analysis.py     ← POST /gap-analysis + export
│   │   ├── policy_guidance.py  ← POST /policy-guidance + export
│   │   └── conflict_check.py   ← POST /conflict-check
│   │
│   ├── middleware/
│   │   ├── logging_middleware.py  ← Request/response timing + logging
│   │   └── rate_limiter.py        ← SlowAPI rate limiter
│   │
│   ├── models/
│   │   └── schemas.py          ← All Pydantic request/response models
│   │
│   └── utils/
│       ├── auth.py             ← JWT create / verify / FastAPI dependency
│       └── helpers.py          ← Shared helpers (vectorstore guard, FileAdapter)
│
├── agents/                     ← RAG pipeline agents
│   ├── rag_agent.py            ← ask_regulation() — RAG Q&A
│   ├── gap_detector.py         ← detect_gaps() — compliance gap analysis
│   └── policy_builder.py       ← generate_policy_guidance() — policy AI
│
├── core/                       ← Core infrastructure
│   ├── vectorstore.py          ← ChromaDB build + load
│   └── edge_handler.py         ← Conflict detection + edge cases
│
├── data/
│   ├── uploads/                ← Uploaded regulation + policy PDFs
│   └── chroma_db/              ← Persisted ChromaDB vector store
│
├── Dockerfile                  ← Multi-stage production Docker build
├── .dockerignore
├── requirements.txt
├── .env.example                ← Environment variable template
└── README.md

API Endpoints
MethodEndpointAuthRate LimitDescriptionGET/❌30/minWelcome + API infoGET/health❌30/minSystem health checkPOST/auth/token❌30/minLogin → get JWT tokenPOST/regulation/upload✅10/minUpload & index regulation PDFPOST/query✅5/minRAG Q&A against regulationPOST/gap-analysis✅5/minGap analysis → JSON reportPOST/gap-analysis/export✅5/minGap analysis → Excel downloadPOST/policy-guidance✅5/minAI policy guidance → JSONPOST/policy-guidance/export✅5/minAI policy guidance → ExcelPOST/conflict-check✅5/minDetect conflicts between regulations

Quick Start
1. Clone the repo
bashgit clone https://github.com/Prajwal07114/Blow_Rag.git
cd Blow_Rag
2. Create virtual environment
bash# Windows
py -3.11 -m venv venv
venv\Scripts\activate

# Mac / Linux
python3.11 -m venv venv
source venv/bin/activate
3. Install dependencies
bashpip install -r requirements.txt
4. Set up environment variables
bash# Windows
copy .env.example .env

# Mac / Linux
cp .env.example .env
Edit .env and fill in:
JWT_SECRET_KEY=your_generated_secret   # python -c "import secrets; print(secrets.token_hex(32))"
GROQ_API_KEY=your_groq_api_key
5. Run the server
bashuvicorn app.main:app --reload --port 10000
6. Open Swagger UI
http://localhost:10000/docs

Authentication Flow
All sensitive endpoints require a Bearer JWT token.
Step 1 — Get a token
bashcurl -X POST http://localhost:10000/auth/token \
  -H "Content-Type: application/json" \
  -d '{"username": "ariras_user", "password": "ariras_pass"}'
Response:
json{
  "access_token": "eyJhbGciOiJIUzI1NiJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
Step 2 — Use the token
bashcurl -X POST http://localhost:10000/query \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the breach notification obligations?"}'
In Swagger UI

Call POST /auth/token
Copy the access_token
Click Authorize 🔒 at the top
Paste the token → Authorize
All protected endpoints now work


Usage Flow
1. POST /auth/token          → get JWT
2. POST /regulation/upload   → upload DPDP Act.pdf or GDPR.pdf
3. POST /query               → ask "What is the penalty for data breach?"
4. POST /gap-analysis        → upload your company policy → get compliance score
5. POST /conflict-check      → check ["GDPR", "DPDP Act"] for conflicts
6. POST /policy-guidance     → get tailored compliance recommendations

Example Requests
Query a regulation
jsonPOST /query
{
  "question": "What are the penalties for data breach under DPDP Act?"
}
Gap Analysis
POST /gap-analysis
Form: file = company_policy.pdf
Form: regulation_name = DPDP Act 2023
Policy Guidance
jsonPOST /policy-guidance
{
  "company_name": "Finova Technologies Pvt Ltd",
  "company_description": "Fintech startup providing short-term loans via mobile app.",
  "information_flows": "We collect Aadhaar, PAN, salary slips, bank account details.",
  "key_stakeholders": "Customers, HDFC Bank, AWS, CIBIL, investors.",
  "compliance_concerns": "Not sure if consent process is valid.",
  "existing_policies": "Basic privacy policy, last updated 2 years ago."
}
Conflict Check
jsonPOST /conflict-check
{
  "regulation_names": ["GDPR", "DPDP Act 2023"]
}

Production Features (Day 2)
JWT Authentication

Bearer token auth on all sensitive endpoints
Configurable expiry via environment variables
Clean FastAPI Depends() injection pattern
Swagger UI Authorize button built-in

Request Logging
Every request logs in a structured format:
INFO  - 2024-01-15 14:32:01 - → POST /query  [client=127.0.0.1]
INFO  - 2024-01-15 14:32:03 - ✓ POST /query  - 200 - 1.42s
WARN  - 2024-01-15 14:32:05 - ⚠ POST /query  - 429 - 0.01s
ERROR - 2024-01-15 14:32:07 - ✗ POST /gap-analysis - 500 - 0.12s
Rate Limiting
Endpoint TypeLimitLLM endpoints (/query, /gap-analysis, etc.)5 req / minUpload endpoints10 req / minRead endpoints30 req / min
Returns HTTP 429 with standard X-RateLimit-* headers when exceeded.
Async Architecture
OperationPatternReasonFile uploadawait file.read()Native async I/OLLM calls (Groq)asyncio.to_thread()Network I/O — sync libraryChromaDB queriesasyncio.to_thread()Disk + CPU I/OExcel generationSyncPure in-memory, <10ms

Docker
Build and run
bash# Build
docker build -t ariras-api .

# Run
docker run -p 10000:10000 --env-file .env ariras-api

# With persistent data volumes
docker run -p 10000:10000 \
  --env-file .env \
  -v $(pwd)/data:/app/data \
  ariras-api
Docker features

Multi-stage build (lean final image)
Non-root user for security
Health check endpoint configured
Render / Railway compatible via $PORT env var


Deployment
Render (Free tier)

Push to GitHub
New Web Service → connect repo
Build command: pip install -r requirements.txt
Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Add environment variables from .env.example

Railway

Push to GitHub
New Project → Deploy from GitHub
Railway auto-detects the Dockerfile
Add environment variables in dashboard


Environment Variables
VariableRequiredDescriptionJWT_SECRET_KEY✅Secret for signing JWTs — generate with secrets.token_hex(32)GROQ_API_KEY✅Your Groq API key from console.groq.comDEMO_USERNAME✅Login usernameDEMO_PASSWORD✅Login passwordENVIRONMENT❌development or productionCHROMA_PERSIST_DIR❌Path to ChromaDB (default: ./data/chroma_db)UPLOAD_DIR❌Path for uploaded PDFs (default: ./data/uploads)JWT_ACCESS_TOKEN_EXPIRE_MINUTES❌Token expiry in minutes (default: 60)PORT❌Server port (default: 10000)

Request Lifecycle
Client Request
      │
      ▼
SlowAPIMiddleware        ← Check rate limit → 429 if exceeded
      │
      ▼
LoggingMiddleware        ← Log request + start timer
      │
      ▼
FastAPI Router           ← Match route
      │
      ▼
get_current_user()       ← Decode JWT → 401 if invalid
      │
      ▼
Route Handler (async)    ← Business logic
      │
      ├── asyncio.to_thread() → LLM call (Groq)
      ├── asyncio.to_thread() → ChromaDB query
      │
      ▼
LoggingMiddleware        ← Log status + elapsed time
      │
      ▼
Client Response
