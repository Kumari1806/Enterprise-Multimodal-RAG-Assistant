# 🏢 Enterprise Multimodal RAG Assistant

A secure enterprise AI knowledge assistant that enables employees to query organizational documents using Retrieval-Augmented Generation (RAG), while enforcing **strict role-based access control**, **grounded answering**, **source citations**, **prompt-injection protection**, **sensitive-information controls**, and **multimodal document processing**.

---

## 🔐 Strict Role-Based Access Control (RBAC)

RBAC is enforced **server-side at three independent layers**, providing defense-in-depth security with no single point of failure.

### Layer 1 — Endpoint Authentication & Authorization

- Every endpoint except `/api/login` and `/health` requires a **signed bearer token**.
- Tokens are issued **only** to registered users with correct credentials.
- The user's **role is always derived from the token server-side**. The client cannot claim or modify a role in the request body.
- Tokens are **HMAC-signed**, and forged or tampered tokens are rejected.
- Tokens expire after **8 hours**.
- Privileged operations are **role-restricted**. For example, document upload is **Admin-only** and unauthorized users receive HTTP 403.

### Layer 2 — Security Pre-Checks

Security checks are performed **before document retrieval**.

- **Prompt-injection detection** blocks malicious instructions such as system-prompt extraction, role overrides, jailbreak attempts, and unauthorized data-dump requests.
- **Sensitive-information detection** applies role-aware restrictions to protected information. For example, Employees cannot request salary information, and Finance users cannot access HR policies.

### Layer 3 — Retrieval-Layer RBAC

- ChromaDB queries are **metadata-filtered** using the user's authorized document list before retrieved chunks reach the LLM.
- Unauthorized document chunks **never enter the LLM context**.
- Access control therefore does not depend on the LLM to decide whether information should be disclosed.

---

## 🎯 Key Features

| Feature | Description |
|---------|-------------|
| 🔐 **Strict RBAC** | Server-side role enforcement from signed tokens |
| 📚 **Multi-Format Ingestion** | PDF, PPTX, DOCX, XLSX, Scanned PDF |
| 🔎 **RAG Pipeline** | ChromaDB vector retrieval with semantic search |
| 📌 **Source Citations** | Every answer cites document name and page/slide |
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

### 1. Clone and Set Up

```bash
git clone https://github.com/Kumari1806/Enterprise-Multimodal-RAG-Assistant.git
cd Enterprise-Multimodal-RAG-Assistant

python -m venv .venv
```

Activate the virtual environment:

```bash
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 2. Configure Environment (Optional)

```bash
# Windows PowerShell
Copy-Item .env.example .env

# macOS / Linux
cp .env.example .env
```

Set `GOOGLE_API_KEY` for Gemini (optional) and configure a strong `TOKEN_SECRET` for production deployments.

> **Security:** Never commit your actual `.env` file, API keys, production credentials, or other real secrets to source control. The repository contains synthetic demo data and demo credentials only.

### 3. Generate Dummy Documents

```bash
python scripts/generate_dummy_documents.py
```

### 4. Start the Backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```

### 5. Start the Frontend

Open another terminal with the virtual environment activated:

```bash
streamlit run frontend/app.py --server.port 8501
```

Open the application at:

**http://localhost:8501**

---

## 👥 Demo Accounts

> These credentials are **synthetic demo credentials** intended only for local demonstration and testing.

| Role | Username | Password | Accessible Documents |
|------|----------|----------|----------------------|
| **Employee** | `emp001` | `Emp@123` | HR Policy, Leave Policy |
| **HR** | `hr001` | `HR@123` | HR Policy, Leave Policy, Termination Policy, Salary Records |
| **Finance** | `fin001` | `Fin@123` | Finance Policy |
| **Admin** | `admin001` | `Admin@123` | All 5 Documents |

---

## 📂 Enterprise Documents

The project includes synthetic enterprise-style documents covering multiple file formats and access scopes.

| Document | Format | Content |
|----------|--------|---------|
| `HR_Policy.pdf` | PDF | Working hours (9:30–6:30), probation (6 months), dress code, attendance, grievance |
| `Leave_Policy.pptx` | PowerPoint | Casual Leave (12), Sick Leave (10), Earned Leave (18), approval workflow |
| `Finance_Policy.docx` | Word | Travel reimbursement, meal allowance (₹800/day), hotel reimbursement |
| `Termination_Policy_Scanned.pdf` | Scanned PDF | Notice periods (60/15 days), resignation, exit clearance, F&F settlement |
| `Employee_Salary_Records.xlsx` | Excel | 5 employees with salary data (₹62K–₹98K/month) |

**All documents and data in this repository are synthetic demo data.**

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
| POST | `/api/query` | Token | RAG query with role derived from token |
| POST | `/api/documents/upload` | **Admin** | Ingest document (403 otherwise) |
| GET | `/api/documents` | Token | List role-authorized documents |
| GET | `/api/documents/stats` | Token | Vector DB statistics |
| POST | `/api/evaluate` | Token | Run AI evaluation |
| GET | `/health` | Public | Health check |

**Authentication header:**

```text
Authorization: Bearer <token>
```

---

## 📸 Application Screenshots

The following screenshots demonstrate the application's key workflows, security controls, and enterprise RAG capabilities.

### 🔐 Login Interface
Secure authentication interface for employees and administrators using role-based credentials.

![Login Interface](screenshots/login_screen.png)

### 💬 Employee Chat Experience
Employees can query authorized organizational documents and receive grounded answers with source citations.

![Employee Chat](screenshots/employee_chat.png)

### 📄 Document Access
Displays documents available to the authenticated user based on their assigned role and permissions.

![Document Access](screenshots/documents_page.png)

### 🛡️ Role-Based Access Control
Unauthorized document or information requests are blocked according to the user's role and access scope.

![RBAC Blocked](screenshots/rbac_blocked.png)

### 🚨 Prompt-Injection Protection
Malicious prompt-injection attempts are detected and blocked before reaching the retrieval pipeline.

![Prompt Injection Protection](screenshots/prompt_injection.png)

### 🎯 Insufficient-Information Handling
When the required information is not available in authorized documents, the system avoids hallucination and clearly indicates insufficient information.

![Insufficient Information](screenshots/insufficient_info.png)

### 📊 AI Evaluation Dashboard
Provides an evaluation view showing the system's performance across correctness, security, RBAC, and grounded-answering scenarios.

![Evaluation Dashboard](screenshots/evaluation_dashboard.png)

---

## 📁 Project Structure

```text
Enterprise-Multimodal-RAG-Assistant/
│
├── backend/
│   ├── main.py             # FastAPI server (token-based RBAC)
│   ├── auth.py             # Signed-token authentication
│   ├── rbac.py             # Role-document registry & checks
│   ├── security.py         # Prompt injection & sensitive-info detection
│   ├── ingestion.py        # Multi-format document ingestion
│   ├── retriever.py        # Role-filtered secure retrieval
│   ├── rag_pipeline.py     # RAG orchestration
│   ├── citation.py         # Citation extraction & validation
│   ├── models.py           # Pydantic models
│   └── config.py           # Configuration
│
├── frontend/
│   └── app.py              # Streamlit enterprise UI
│
├── data/
│   ├── documents/          # Synthetic enterprise documents
│   ├── evaluation/         # AI evaluation dataset
│   └── chroma/             # ChromaDB vector store
│
├── tests/
│   ├── test_token_rbac.py
│   ├── test_authentication.py
│   ├── test_rbac.py
│   ├── test_security.py
│   ├── test_retrieval.py
│   └── test_evaluation.py
│
├── scripts/
│   └── generate_dummy_documents.py
│
├── screenshots/             # Application screenshots
├── .env.example             # Environment variable template
├── requirements.txt
└── README.md
```

---

## 🛠️ Technology Stack

| Technology | Purpose |
|------------|---------|
| **FastAPI** | Async backend API |
| **Streamlit** | Enterprise user interface |
| **ChromaDB** | Vector database |
| **Google Gemini** | LLM & embeddings (optional) |
| **LangChain** | RAG orchestration |
| **PyMuPDF / PyPDF** | PDF processing |
| **python-pptx / python-docx** | Office document processing |
| **openpyxl / pandas** | Excel processing |
| **EasyOCR** | Scanned document OCR |
| **pytest** | Testing framework |
