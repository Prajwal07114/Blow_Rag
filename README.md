ARIRAS
AI Regulatory Intelligence & Reporting Assurance System
Hosted on Streamlit
Overview

ARIRAS is a multi-agent AI-powered compliance intelligence platform designed to help enterprises understand, interpret, and comply with complex regulations — without requiring large legal teams or expensive consulting engagements.

It enables organizations to upload regulatory documents such as the DPDP Act, SEBI circulars, RBI guidelines, GDPR policies, and more, then instantly interact with them using AI-driven analysis, policy gap detection, and compliance guidance generation.

Built with a regulation-agnostic architecture, ARIRAS transforms static legal documents into actionable compliance intelligence.

Why ARIRAS Exists
The Compliance Problem
Indian Context

Regulatory compliance in India is becoming increasingly difficult for enterprises, especially MSMEs and mid-sized organizations.

Recent industry findings show:

81% of Indian enterprises have not updated their DPDP-aligned privacy policies
83% have not started end-to-end implementation
71% struggle to interpret regulatory requirements
Maximum fine under the DPDP Act can reach ₹250 crore per violation
Global Context

Compliance complexity scales exponentially across jurisdictions.

Modern enterprises must simultaneously manage overlapping regulations such as:

GDPR
SOX
HIPAA
Basel III
AML/BSA
RBI Guidelines
SEBI Circulars

Each framework introduces:

Different terminology
Different interpretations
Different reporting obligations
Different operational requirements

Despite massive spending on compliance:

Organizations still rely heavily on manual interpretation
Policies remain static and reactive
Compliance processes are fragmented and expensive

The result is not just regulatory penalties — but:

Delayed business decisions
Operational inefficiencies
Hidden enterprise risk exposure

Even leading technology companies face these challenges.

For example, in 2019, Google was fined €50 million under GDPR by the French regulator due to lack of transparency and invalid consent mechanisms.

What ARIRAS Does

Upload any regulation PDF and ARIRAS will:

Read it
Understand it
Index it
Enable intelligent compliance workflows

Supported examples include:

DPDP Act
SEBI Circulars
RBI Guidelines
Companies Act
GDPR
SOX
AML/BSA frameworks
Core Features
1. Regulation Q&A with Clause Citations

Ask compliance-related questions in plain English and receive:

AI-generated answers
Exact clause references
Source-backed explanations
Example Questions
“What are the breach reporting obligations?”
“What penalties apply for non-compliance?”
“What consent requirements exist for data collection?”
2. Policy Gap Analysis

Upload your organization’s existing policy document and ARIRAS will:

Compare it against the regulation
Detect missing obligations
Assign severity levels
Generate a compliance score
Output Includes
Compliance score (0–100%)
Missing compliance obligations
Severity classification
HIGH
MEDIUM
LOW
Obligations already satisfied
3. AI Policy Guidance Builder

ARIRAS asks plain-English questions about:

Your business
Your data flows
Existing compliance posture

It then generates:

Tailored compliance guidance
Sample clauses
Recommended policy structures
Priority action items
Exportable Deliverables
Excel compliance guidance report
Readiness score
Regulation references
4. Compliance Dashboard

Real-time compliance intelligence dashboard with:

Compliance score tracking
Severity breakdowns
Gap trend analysis
Regulation coverage metrics
Exportable reports
5. Full Audit Trail

Every AI action is logged for regulatory traceability.

Includes:

Document indexing logs
Query history
Agent activity
Generated outputs
Timestamped audit records

Exportable as JSON.

Demo Flow
Feature 1
→ Upload DPDP Act / SEBI Circular PDF
→ Process & Index (~30 seconds)
→ Ask:
   "What are our reporting obligations?"
→ Receive AI answer with clause citations

Feature 2
→ Upload company policy
→ Run gap analysis
→ Get compliance score + identified gaps

Feature 3
→ Answer business-related questions
→ Generate downloadable policy guidance report

Feature 4
→ Open dashboard
→ Export compliance reports and audit logs
Technology Stack
Component	Technology
Frontend	Streamlit
LLM	Groq — Llama 3.3 70B Versatile
Orchestration	LangChain
Vector Database	ChromaDB
Embeddings	HuggingFace all-MiniLM-L6-v2
PDF Parsing	PyPDF
Excel Export	openpyxl
Environment	Python 3.10+
Cost Model

ARIRAS is designed for extremely low operational cost.

Runs locally
No paid vector database
No cloud GPU dependency
Only external dependency is Groq API (free tier available)
System Architecture
┌─────────────────────────────────────────────────────────┐
│                     STREAMLIT UI                       │
│  Tab 1: Q&A   │  Tab 2: Gap Detector │ Tab 3: Builder │
└───────────────────────┬─────────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────────┐
│              LANGCHAIN ORCHESTRATION                   │
│     Agent Routing · Error Handling · Logging           │
└──────┬─────────────────┬──────────────────┬─────────────┘
       │                 │                  │

┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────────┐
│  RAG Agent  │   │ Gap Detector│   │ Policy Builder  │
│ rag_agent   │   │gap_detector │   │policy_builder   │
└──────┬──────┘   └──────┬──────┘   └──────┬──────────┘
       │                 │                  │

┌──────▼─────────────────▼──────────────────▼──────────┐
│               RAG INTELLIGENCE LAYER                │
│ ChromaDB ↔ HuggingFace Embeddings ↔ PyPDF           │
│ Regulation PDFs vectorized and indexed here         │
└──────────────────────────┬───────────────────────────┘
                           │

┌──────────────────────────▼───────────────────────────┐
│               Groq — Llama 3.3 70B                  │
│                 LLM Inference Layer                 │
└──────────────────────────┬───────────────────────────┘
                           │

┌──────────────────────────▼───────────────────────────┐
│                    AUDIT TRAIL                      │
│ Every action logged and exportable as JSON          │
└──────────────────────────────────────────────────────┘
Project Structure
ariras/
│
├── app.py                       # Main Streamlit application
│
├── agents/
│   ├── __init__.py
│   ├── rag_agent.py             # RAG Q&A with clause citations
│   ├── gap_detector.py          # Policy vs regulation analysis
│   ├── policy_builder.py        # Guidance generation + Excel export
│   └── breach_agent.py          # Breach simulation workflows
│
├── core/
│   ├── __init__.py
│   └── vectorstore.py           # ChromaDB + embedding pipeline
│
├── data/
│   └── uploads/                 # Uploaded regulation PDFs
│
├── requirements.txt
├── .env
└── README.md
Setup & Installation
Prerequisites
Python 3.10+
Groq API Key
Available from: Groq
1. Clone Repository
git clone https://github.com/YOUR_USERNAME/ariras.git

cd ariras
2. Install Dependencies
pip install -r requirements.txt

Note: The first installation downloads the HuggingFace embedding model (~80MB).

3. Configure Environment Variables
Windows
copy .env.example .env
macOS / Linux
cp .env.example .env

Add the following:

GROQ_API_KEY=gsk_your_groq_key_here
CHROMA_PERSIST_DIR=./data/chroma_db
4. Create Required Folders
Windows
mkdir data\uploads

type nul > agents\__init__.py
type nul > core\__init__.py
macOS / Linux
mkdir -p data/uploads

touch agents/__init__.py
touch core/__init__.py
5. Run the Application
streamlit run app.py

Open in browser:

http://localhost:8501
How to Use
Tab 1 — Regulation Q&A
Upload a regulation PDF
Click Process & Index
Ask compliance questions in plain English
Receive answers with clause citations
Tab 2 — Policy Gap Detector
Upload and index a regulation
Upload your company policy
Run gap analysis
Review compliance score and missing obligations
Tab 3 — Policy Builder

Answer business-context questions regarding:

Business operations
Information flows
Compliance concerns

ARIRAS generates:

Tailored compliance guidance
Sample clauses
Actionable recommendations
Downloadable Excel report
Dashboard & Reporting

The dashboard includes:

Compliance score gauge
Severity distribution charts
Top violated obligations
Trend analysis
Regulation coverage tracking

Reports exportable as JSON.

Audit Trail

Every system interaction is logged:

Uploaded documents
Agent executions
Compliance queries
Generated outputs

Exportable for regulatory traceability.

Supported Regulations

ARIRAS is fully regulation-agnostic.

Tested with:

Regulation	Region	Domain
DPDP Act 2023	India	Data Protection
SEBI Circulars	India	Capital Markets
RBI Guidelines	India	Banking / Fintech
Companies Act 2013	India	Corporate Governance
GDPR	European Union	Data Protection
SOX	United States	Financial Reporting
AML / BSA	United States	Anti-Money Laundering
Key Capabilities
Feature	Description
Regulation-Agnostic RAG	Works with any uploaded regulation PDF
Clause-Level Citations	Every answer references exact regulation clauses
Policy Gap Analysis	Detects missing obligations automatically
AI Compliance Guidance	Generates practical compliance recommendations
Excel Report Export	Downloadable policy guidance and action plans
Full Audit Trail	Every AI decision logged
Zero Hardcoded Rules	Intelligence derived directly from uploaded regulations
India-First Design	Optimized for Indian regulatory ecosystems
Environment Variables
Variable	Description	Required
GROQ_API_KEY	Groq API key	Yes
CHROMA_PERSIST_DIR	Local ChromaDB storage path	Optional
Requirements
streamlit>=1.32.0
langchain>=0.1.16
langchain-community>=0.0.36
langchain-chroma>=0.1.0
langchain-groq>=0.1.6
langchain-huggingface>=0.0.3
groq>=0.9.0
chromadb>=0.4.24
pypdf>=4.2.0
pdfplumber>=0.11.0
python-dotenv>=1.0.1
sentence-transformers>=3.0.0
plotly>=5.20.0
openpyxl>=3.1.2
tiktoken>=0.7.0
Impact Model
Metric	Estimate
Target Market	6.3 crore MSMEs + 1,400+ listed Indian companies
SME Compliance Consulting Cost	₹2–80 lakh per engagement
Enterprise Compliance Consulting Cost	₹80 lakh+ per engagement
ARIRAS Build Cost	~₹5,000/hour development cost
Typical Build Time	~50 hours
Time to First Compliance Insight	Under 60 seconds
Built With
Streamlit — Frontend framework
LangChain — Agent orchestration
Groq — LLM inference
Chroma — Vector database
Hugging Face — Embeddings
Plotly — Analytics dashboard
openpyxl — Excel generation
