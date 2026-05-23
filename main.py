"""
main.py — ARIRAS FastAPI Backend
=================================
Day 1: FastAPI wrapper around the existing RAG pipeline.

Endpoints:
  GET  /              → Welcome message
  GET  /health        → System health check (vectorstore status)
  POST /upload        → Upload & index a regulation PDF
  POST /query         → Ask a question against loaded regulation
  POST /gap-analysis  → Run gap detector against uploaded policy
  POST /policy-guidance → Generate policy guidance for a company

Run with:
    uvicorn main:app --reload

Swagger UI:
    http://127.0.0.1:8000/docs
"""

import os
import shutil
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import io

# ── Import your existing RAG pipeline (unchanged) ────────────────────────────
from core.vectorstore import build_vectorstore, load_vectorstore
from agents.rag_agent import ask_regulation
from agents.gap_detector import detect_gaps, build_gap_excel
from agents.policy_builder import generate_policy_guidance, build_excel
from core.edge_handler import detect_reg_conflicts

# ── Constants ─────────────────────────────────────────────────────────────────
UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

CHROMA_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma_db")

# ── FastAPI app setup ─────────────────────────────────────────────────────────
app = FastAPI(
    title="ARIRAS API",
    description=(
        "AI Regulatory Intelligence & Reporting Assurance System — "
        "FastAPI backend exposing your RAG pipeline as production REST endpoints.\n\n"
        "**Day 1 endpoints:** health check, regulation upload, Q&A query, "
        "gap analysis, and policy guidance generation."
    ),
    version="1.0.0",
    contact={
        "name": "Team Token Burners",
        "email": "team@ariras.ai",
    },
)


# ═════════════════════════════════════════════════════════════════════════════
# Pydantic request / response models
# These define the shape of JSON in and out — auto-documented in Swagger
# ═════════════════════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    """Request body for the /query endpoint."""
    question: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What are the breach notification obligations under this regulation?"
            }
        }
    }


class PolicyGuidanceRequest(BaseModel):
    """Request body for the /policy-guidance endpoint."""
    company_name: str
    company_description: str
    information_flows: str
    key_stakeholders: str
    compliance_concerns: str
    existing_policies: str = ""          # optional field

    model_config = {
        "json_schema_extra": {
            "example": {
                "company_name": "Finova Technologies Pvt Ltd",
                "company_description": "Fintech startup providing short-term loans via mobile app.",
                "information_flows": "We collect Aadhaar, PAN, salary slips, bank account details.",
                "key_stakeholders": "Customers, HDFC Bank, AWS, CIBIL, investors.",
                "compliance_concerns": "Not sure if consent process is valid or if we need to register.",
                "existing_policies": "Basic privacy policy on website, last updated 2 years ago.",
            }
        }
    }


class ConflictCheckRequest(BaseModel):
    """Request body for the /conflict-check endpoint."""
    regulation_names: list[str]

    model_config = {
        "json_schema_extra": {
            "example": {
                "regulation_names": ["GDPR", "DPDP Act 2023"]
            }
        }
    }


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINT 1 — Root
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/", tags=["General"])
def root():
    """
    Welcome endpoint. Confirms the API is running.
    """
    return {
        "message": "ARIRAS API is running.",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINT 2 — Health Check
# ═════════════════════════════════════════════════════════════════════════════

@app.get("/health", tags=["General"])
def health_check():
    """
    Returns system health status.

    - **vectorstore_ready**: True if a regulation has been indexed and ChromaDB has data.
    - **chroma_dir**: Path to the persisted vector store on disk.
    - **uploaded_files**: List of regulation PDFs found in the uploads folder.
    """
    # Check whether ChromaDB directory exists and has content
    chroma_exists = (
        os.path.exists(CHROMA_DIR)
        and any(Path(CHROMA_DIR).iterdir())  # not empty
    )

    uploaded_files = [f.name for f in UPLOAD_DIR.glob("*.pdf")]

    return {
        "status": "ok",
        "vectorstore_ready": chroma_exists,
        "chroma_dir": CHROMA_DIR,
        "uploaded_files": uploaded_files,
    }


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINT 3 — Upload & Index Regulation PDF
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/upload", tags=["Regulation Management"])
async def upload_regulation(file: UploadFile = File(...)):
    """
    Upload a regulation PDF and index it into ChromaDB.

    - Accepts a single PDF file.
    - Saves it to `data/uploads/`.
    - Calls your existing `build_vectorstore()` to chunk + embed it.
    - Returns the filename and chunk count metadata.

    **This must be called before /query or /gap-analysis.**
    """
    # Validate file type
    if not file.filename.endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF files are supported. Got: {file.filename}"
        )

    # Save uploaded file to disk (same pattern as your Streamlit app)
    save_path = UPLOAD_DIR / file.filename
    try:
        with open(save_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Call your existing build_vectorstore — completely unchanged
    try:
        vectorstore = build_vectorstore(str(save_path))
        # Get a rough chunk count from the collection
        collection  = vectorstore._collection
        chunk_count = collection.count()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index regulation: {str(e)}")

    return {
        "message":     "Regulation indexed successfully.",
        "filename":    file.filename,
        "saved_to":    str(save_path),
        "chunk_count": chunk_count,
        "next_step":   "Use POST /query to ask questions about this regulation.",
    }


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINT 4 — Query (RAG Q&A)
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/query", tags=["RAG Q&A"])
def query_rag(request: QueryRequest):
    """
    Ask a question against the indexed regulation using RAG.

    - Retrieves relevant regulation chunks from ChromaDB.
    - Generates an answer grounded in those chunks via Groq LLM.
    - Returns the answer, source clause references, and a **confidence score**.

    **Requires:** A regulation must be indexed first via POST /upload.

    **Response includes:**
    - `answer`: The LLM-generated answer with clause references.
    - `sources`: Excerpts from the regulation chunks used.
    - `confidence`: HIGH / MEDIUM / LOW / INSUFFICIENT.
    - `confidence_score`: 0–100 composite score (semantic + faithfulness).
    - `warnings`: Any grounding or hallucination warnings.
    """
    # Guard — check vectorstore exists before calling ask_regulation
    chroma_exists = (
        os.path.exists(CHROMA_DIR)
        and any(Path(CHROMA_DIR).iterdir())
    )
    if not chroma_exists:
        raise HTTPException(
            status_code=400,
            detail="No regulation indexed yet. Upload a PDF via POST /upload first."
        )

    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    # Call your existing ask_regulation — completely unchanged
    try:
        result = ask_regulation(request.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG pipeline error: {str(e)}")

    # Flatten the _edge dict to the top level for cleaner API response
    edge = result.get("_edge", {})

    return {
        "question":        request.question,
        "answer":          result.get("answer", ""),
        "sources":         result.get("sources", []),
        "confidence":      edge.get("confidence", "UNKNOWN"),
        "confidence_score": edge.get("confidence_score", 0),
        "warnings":        edge.get("warnings", []),
        "answer_safe":     edge.get("answer_safe", False),
        # Full edge metadata — useful for debugging / advanced clients
        "_edge":           edge,
    }


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINT 5 — Gap Analysis
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/gap-analysis", tags=["Compliance Analysis"])
async def gap_analysis(
    file: UploadFile = File(...),
    regulation_name: str = Form(default=""),
):
    """
    Upload your company policy and run gap analysis against the indexed regulation.

    - Accepts a PDF or TXT policy file.
    - Compares it against the indexed regulation in ChromaDB.
    - Returns a detailed gap report with compliance score.

    **Requires:** A regulation must be indexed first via POST /upload.

    **Form fields:**
    - `file`: Your company policy document (PDF or TXT).
    - `regulation_name`: Optional label for the regulation being checked against.

    **Response includes:**
    - `compliance_score`: 0–100 overall score.
    - `gaps`: List of obligations not met, with severity + recommended actions.
    - `met`: List of obligations your policy already satisfies.
    - `preflight`: Pre-analysis quality checks (document relevance warnings).
    """
    # Guard — check vectorstore exists
    chroma_exists = (
        os.path.exists(CHROMA_DIR)
        and any(Path(CHROMA_DIR).iterdir())
    )
    if not chroma_exists:
        raise HTTPException(
            status_code=400,
            detail="No regulation indexed yet. Upload a PDF via POST /upload first."
        )

    # Validate file type
    if not (file.filename.endswith(".pdf") or file.filename.endswith(".txt")):
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF or TXT files supported. Got: {file.filename}"
        )

    # Save policy file to disk — detect_gaps() internally uses PyPDFLoader
    # which requires a real file path, same as in your Streamlit app
    save_path = UPLOAD_DIR / f"policy_{file.filename}"
    try:
        content = await file.read()
        with open(save_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # Build a thin file-like adapter so detect_gaps() works without modification.
    # detect_gaps() calls: policy_file.name, policy_file.read()
    # We give it a real path adapter instead of re-uploading the stream.
    class _FileAdapter:
        """
        Minimal adapter that mimics the Streamlit UploadedFile interface
        that detect_gaps() expects (just .name and .read()).
        """
        def __init__(self, path: Path):
            self.name = path.name
            self._path = path

        def read(self) -> bytes:
            return self._path.read_bytes()

    adapter = _FileAdapter(save_path)

    # Call your existing detect_gaps — completely unchanged
    try:
        result = detect_gaps(policy_file=adapter, regulation_name=regulation_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gap analysis error: {str(e)}")

    # Surface the response cleanly — no internal keys leaked
    return {
        "policy_file":      file.filename,
        "regulation_name":  result.get("regulation_name", regulation_name),
        "compliance_score": result.get("compliance_score", 0),
        "gaps":             result.get("gaps", []),
        "met":              result.get("met", []),
        "preflight":        result.get("_preflight", {}),
        # Include edge_case block if analysis was blocked by preflight
        "blocked":          result.get("_edge_case", {}).get("blocked", False),
        "block_reason":     result.get("_edge_case", {}).get("reason", ""),
    }


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINT 6 — Gap Analysis Excel Export
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/gap-analysis/export", tags=["Compliance Analysis"])
async def gap_analysis_export(
    file: UploadFile = File(...),
    regulation_name: str = Form(default=""),
):
    """
    Run gap analysis and return the result as a downloadable Excel report.

    Same as POST /gap-analysis but returns a `.xlsx` file instead of JSON.
    Useful for direct download by frontend clients or automation pipelines.
    """
    chroma_exists = (
        os.path.exists(CHROMA_DIR)
        and any(Path(CHROMA_DIR).iterdir())
    )
    if not chroma_exists:
        raise HTTPException(
            status_code=400,
            detail="No regulation indexed yet. Upload a PDF via POST /upload first."
        )

    if not (file.filename.endswith(".pdf") or file.filename.endswith(".txt")):
        raise HTTPException(
            status_code=400,
            detail=f"Only PDF or TXT files supported. Got: {file.filename}"
        )

    save_path = UPLOAD_DIR / f"policy_{file.filename}"
    content   = await file.read()
    with open(save_path, "wb") as f:
        f.write(content)

    class _FileAdapter:
        def __init__(self, path: Path):
            self.name = path.name
            self._path = path
        def read(self) -> bytes:
            return self._path.read_bytes()

    adapter = _FileAdapter(save_path)

    try:
        result      = detect_gaps(policy_file=adapter, regulation_name=regulation_name)
        excel_bytes = build_gap_excel(
            result=result,
            regulation_name=regulation_name,
            policy_name=file.filename,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel export error: {str(e)}")

    filename = f"ARIRAS_Gap_Analysis_{file.filename.replace('.', '_')}.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINT 7 — Policy Guidance (JSON)
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/policy-guidance", tags=["Policy Builder"])
def policy_guidance(request: PolicyGuidanceRequest):
    """
    Generate company-specific compliance policy guidance.

    - Pulls regulation context from the indexed vectorstore (if available).
    - Calls Groq LLM to generate tailored guidance sections, sample clauses,
      priority actions, and risk areas.
    - Returns a readiness score and structured guidance.

    **Works without a regulation indexed** (falls back to general best practices).

    **Response includes:**
    - `readiness_score`: 0–100 compliance readiness score.
    - `regulation_used`: Which regulation was identified from the indexed content.
    - `summary`: Plain-English compliance situation summary.
    - `sections`: Guidance sections with sample clauses and regulation references.
    - `priority_actions`: Concrete immediate steps for the company.
    - `risk_areas`: Key compliance risk areas for this company.
    """
    # Pull regulation context from vectorstore if one is indexed
    # This mirrors exactly what your Streamlit app does in Tab 2
    regulation_context = ""
    chroma_exists = (
        os.path.exists(CHROMA_DIR)
        and any(Path(CHROMA_DIR).iterdir())
    )
    if chroma_exists:
        try:
            vs        = load_vectorstore()
            retriever = vs.as_retriever(search_kwargs={"k": 6})
            docs      = retriever.invoke(
                "obligations requirements compliance reporting disclosure penalties"
            )
            regulation_context = "\n\n".join([d.page_content for d in docs])[:3500]
        except Exception:
            # Vectorstore load failed — proceed without context
            regulation_context = ""

    # Call your existing generate_policy_guidance — completely unchanged
    try:
        guidance = generate_policy_guidance(
            company_name        = request.company_name,
            company_description = request.company_description,
            information_flows   = request.information_flows,
            key_stakeholders    = request.key_stakeholders,
            compliance_concerns = request.compliance_concerns,
            existing_policies   = request.existing_policies,
            regulation_context  = regulation_context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy guidance error: {str(e)}")

    return guidance


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINT 8 — Policy Guidance Excel Export
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/policy-guidance/export", tags=["Policy Builder"])
def policy_guidance_export(request: PolicyGuidanceRequest):
    """
    Generate policy guidance and return it as a downloadable Excel report.

    Same as POST /policy-guidance but returns a `.xlsx` file.
    The Excel has two sheets: Policy Guidance (with sample clauses) + Summary & Score.
    """
    regulation_context = ""
    chroma_exists = (
        os.path.exists(CHROMA_DIR)
        and any(Path(CHROMA_DIR).iterdir())
    )
    if chroma_exists:
        try:
            vs        = load_vectorstore()
            retriever = vs.as_retriever(search_kwargs={"k": 6})
            docs      = retriever.invoke(
                "obligations requirements compliance reporting disclosure penalties"
            )
            regulation_context = "\n\n".join([d.page_content for d in docs])[:3500]
        except Exception:
            regulation_context = ""

    try:
        guidance    = generate_policy_guidance(
            company_name        = request.company_name,
            company_description = request.company_description,
            information_flows   = request.information_flows,
            key_stakeholders    = request.key_stakeholders,
            compliance_concerns = request.compliance_concerns,
            existing_policies   = request.existing_policies,
            regulation_context  = regulation_context,
        )
        excel_bytes = build_excel(guidance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Excel export error: {str(e)}")

    filename = f"ARIRAS_Policy_{request.company_name.replace(' ', '_')}.xlsx"
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ═════════════════════════════════════════════════════════════════════════════
# ENDPOINT 9 — Conflict Check
# ═════════════════════════════════════════════════════════════════════════════

@app.post("/conflict-check", tags=["Compliance Analysis"])
def conflict_check(request: ConflictCheckRequest):
    """
    Detect conflicts between two or more loaded regulations.

    - Pass a list of regulation names (2 or more).
    - Returns detected cross-regulation conflicts with severity ratings.

    **Example:** GDPR + DPDP Act may conflict on data retention vs erasure rights.
    """
    if len(request.regulation_names) < 2:
        raise HTTPException(
            status_code=400,
            detail="Provide at least 2 regulation names to check for conflicts."
        )

    # Call your existing detect_reg_conflicts — completely unchanged
    try:
        result = detect_reg_conflicts(request.regulation_names)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conflict check error: {str(e)}")

    return result
