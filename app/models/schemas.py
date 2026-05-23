"""
models/schemas.py — Pydantic request & response schemas
=======================================================
Centralises all data shapes used across routes and services.
Keeping them here (instead of inside route files) makes it easy to:
  • reuse a schema in multiple routes
  • version schemas independently
  • write unit tests against schemas alone
"""

from typing import Any
from pydantic import BaseModel, Field


# ═══════════════════════════════════════════════════════════════════════════
# AUTH
# ═══════════════════════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    username: str = Field(..., example="ariras_user")
    password: str = Field(..., example="ariras_pass")


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


# ═══════════════════════════════════════════════════════════════════════════
# RAG Q&A
# ═══════════════════════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    """Request body for POST /query."""
    question: str = Field(..., min_length=3, max_length=2000)

    model_config = {
        "json_schema_extra": {
            "example": {
                "question": "What are the breach notification obligations under this regulation?"
            }
        }
    }


class QueryResponse(BaseModel):
    question: str
    answer: str
    sources: list[Any]
    confidence: str
    confidence_score: int
    warnings: list[str]
    answer_safe: bool
    _edge: dict[str, Any] = {}


# ═══════════════════════════════════════════════════════════════════════════
# POLICY GUIDANCE
# ═══════════════════════════════════════════════════════════════════════════

class PolicyGuidanceRequest(BaseModel):
    """Request body for POST /policy-guidance."""
    company_name: str = Field(..., min_length=2, max_length=200)
    company_description: str = Field(..., min_length=10, max_length=2000)
    information_flows: str = Field(..., min_length=5, max_length=2000)
    key_stakeholders: str = Field(..., min_length=3, max_length=1000)
    compliance_concerns: str = Field(..., min_length=5, max_length=2000)
    existing_policies: str = Field(default="", max_length=2000)

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


# ═══════════════════════════════════════════════════════════════════════════
# CONFLICT CHECK
# ═══════════════════════════════════════════════════════════════════════════

class ConflictCheckRequest(BaseModel):
    """Request body for POST /conflict-check."""
    regulation_names: list[str] = Field(..., min_length=2)

    model_config = {
        "json_schema_extra": {
            "example": {
                "regulation_names": ["GDPR", "DPDP Act 2023"]
            }
        }
    }


# ═══════════════════════════════════════════════════════════════════════════
# GENERIC
# ═══════════════════════════════════════════════════════════════════════════

class HealthResponse(BaseModel):
    status: str
    vectorstore_ready: bool
    chroma_dir: str
    uploaded_files: list[str]
    environment: str


class ErrorResponse(BaseModel):
    detail: str
