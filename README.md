# 🏢 Enterprise Multimodal RAG Assistant

A secure enterprise AI knowledge assistant that enables employees to query organizational documents using Retrieval-Augmented Generation (RAG), while enforcing **strict role-based access control**, **grounded answering**, **source citations**, **prompt-injection protection**, **sensitive-information controls**, and **multimodal document processing**.

---

## 🔐 Strict Role-Based Access Control (RBAC)

RBAC is enforced **server-side at three independent layers** — no single point of failure:

### Layer 1 — Endpoint Authentication & Authorization
- Every endpoint (except `/api/login` and `/health`) requires a **signed bearer token**.
- Tokens are issued **only** to registered users with correct credentials.
- The user's **role is always derived from the token server-side** — the client can never claim a role in the request body. Privilege escalation is impossible.
- Tokens are **HMAC-signed** (forged tokens are rejected) and expire after 8 hours.
- Privileged operations are **role-restricted**: e.g., document upload is **Admin-only** (others get HTTP 403).

### Layer 2 — Security Pre-checks (before retrieval)
- **Prompt-injection detection**: malicious instructions (system-prompt reveals, role overrides, jailbreaks, data dumps) are blocked before any retrieval happens.
- **Sensitive-information detection**: role-aware rules deny restricted-data requests (e.g., Employees may not ask about salaries; Finance may not ask about HR policies).

### Layer 3 — Retrieval-Layer RBAC
- ChromaDB queries are **metadata-filtered** to the role's authorized document list **before** the chunks reach the LLM context.
- Unauthorized chunks never enter the LLM context — security is not left to the LLM's discretion.

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| 🔐 **Strict RBAC** | Server-side role enforcement from signed tokens |
| 📚 **Multi-Format Ingestion** | PDF, PPTX, DOCX, XLSX, Scanned PDF |
| 🔎 **RAG Pipeline** | ChromaDB vector retrieval with semantic search |
| 📌 **Source Citations** | Every answer cites document name, page/slide |
| 🛡️ **Prompt Injection Protection** | Malicious instructions blocked pre-retrieval |
| 🎯 **Grounded Answering** | Returns "insufficient information" instead of hallucinating |
| 👁️ **OCR** | Scanned document processing |
| ⚡ **Async Backend** | FastAPI async endpoints for concurrent users |
| 📊 **AI Evaluation** | 21 test cases across 6 categories |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Gemini API key (optional — fallback mode works without it)

### 1. Setup
```bash
git clone <repository-url>
cd enterprise-multimodal-rag-assistant
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)
```bash
cp .env.example .env
# Set GOOGLE_API_KEY for Gemini (optional) and a strong TOKEN_SECRET (required in prod)
```

### 3. Generate Dummy Documents
```bash
python scripts/generate_dummy_documents.py
```

### 4. Start Backend
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 5. Start Frontend
```bash
streamlit run frontend/app.py --server.port 8501
```

Visit **http://localhost:8501**.

---

## 👥 Demo Accounts

| Role | Username | Password | Accessible Documents |
|------|----------|----------|---------------------|
| **Employee** | `emp001` | `Emp@123` | HR Policy, Leave Policy |
| **HR** | `hr001` | `HR@123` | HR Policy, Leave Policy, Termination Policy, Salary Records |
| **Finance** | `fin001` | `Fin@123` | Finance Policy |
| **Admin** | `admin001` | `Admin@123` | All 5 Documents |

---

## 📂 Enterprise Documents

| Document | Format | Content |
|----------|--------|---------|
| HR_Policy.pdf | PDF | Working hours (9:30–6:30), probation (6 months), dress code, attendance, grievance |
| Leave_Policy.pptx | PowerPoint | Casual Leave (12), Sick Leave (10), Earned Leave (18), approval workflow |
| Finance_Policy.docx | Word | Travel reimbursement, meal allowance (₹800/day), hotel reimbursement |
| Termination_Policy_Scanned.pdf | Scanned PDF | Notice periods (60/15 days), resignation, exit clearance, F&F settlement |
| Employee_Salary_Records.xlsx | Excel | 5 employees with salary data (₹62K–₹98K/month) |

---

## 🧪 Test Results

### Unit Tests: 68/68 ✅
| Suite | Tests | Focus |
|-------|-------|-------|
| `test_token_rbac.py` | 15 | Token signing, forged-token rejection, strict role scopes, request model |
| `test_authentication.py` | 11 | Login validation, token lifecycle |
| `test_rbac.py` | 11 | Role-document mapping & access checks |
| `test_security.py` | 16 | Injection detection, sensitive-info rules, sanitization |
| `test_retrieval.py` | 8 | RBAC-filtered retrieval & mapping integrity |
| `test_evaluation.py` | 11 | Evaluation dataset & citation validation |

### AI Evaluation: 21/21 ✅ (100% Pass Rate)

| Category | Tests | Passed |
|----------|-------|--------|
| Answer Correctness | 7 | 7 |
| RBAC Enforcement | 4 | 4 |
| Prompt Injection | 4 | 4 |
| Insufficient Information | 4 | 4 |
| End-to-End | 2 | 2 |

---

## 🔄 API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/login` | Public | Authenticate → signed token |
| GET | `/api/verify` | Token | Verify token & identity |
| POST | `/api/query` | Token | RAG query (role from token) |
| POST | `/api/documents/upload` | **Admin** | Ingest document (403 otherwise) |
| GET | `/api/documents` | Token | List role-authorized documents |
| GET | `/api/documents/stats` | Token | Vector DB statistics |
| POST | `/api/evaluate` | Token | Run AI evaluation |
| GET | `/health` | Public | Health check |

**Auth header:** `Authorization: Bearer <token>`

---

## 📁 Project Structure

```
enterprise-multimodal-rag-assistant/
├── backend/
│   ├── main.py            # FastAPI server (token-based RBAC)
│   ├── auth.py            # Signed-token authentication
│   ├── rbac.py            # Role-document registry & checks
│   ├── security.py        # Prompt injection & sensitive-info detection
│   ├── ingestion.py       # Multi-format document ingestion
│   ├── retriever.py       # Role-filtered secure retrieval
│   ├── rag_pipeline.py    # RAG orchestration
│   ├── citation.py        # Citation extraction & validation
│   ├── models.py          # Pydantic models
│   └── config.py          # Configuration
├── frontend/
│   └── app.py             # Streamlit enterprise UI
├── data/
│   ├── documents/         # Enterprise documents
│   ├── evaluation/        # AI evaluation dataset
│   └── chroma/            # ChromaDB vector store
├── tests/
│   ├── test_token_rbac.py
│   ├── test_authentication.py
│   ├── test_rbac.py
│   ├── test_security.py
│   ├── test_retrieval.py
│   └── test_evaluation.py
├── scripts/
│   └── generate_dummy_documents.py
├── screenshots/
├── .env.example
├── requirements.txt
└── README.md
```

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| FastAPI | Async backend API |
| Streamlit | Enterprise user interface |
| ChromaDB | Vector database |
| Google Gemini | LLM & embeddings (optional) |
| LangChain | RAG orchestration |
| PyMuPDF / PyPDF | PDF processing |
| python-pptx / python-docx | Office documents |
| openpyxl / pandas | Excel processing |
| EasyOCR | Scanned document OCR |
| pytest | Testing framework |

---

## 📝 License

Created for demonstration & educational purposes. All data is synthetic demo data.