"""
Enterprise Multimodal RAG Assistant — Streamlit Frontend

A professional enterprise UI for querying organizational documents with
strict role-based access control and source citations.

Security model:
  - User logs in with credentials → receives a bearer token.
  - ALL API calls send the token in the Authorization header.
  - The backend derives the user's ROLE from the token (server-side),
    so a client can never escalate its own privileges.
"""

import os
import sys
from pathlib import Path

import streamlit as st
import httpx
import pandas as pd

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import BACKEND_URL, DOCUMENT_METADATA, ROLE_DOCUMENTS

# ─── Page Configuration ──────────────────────────────────────────────────────

APP_NAME = "Enterprise Multimodal RAG Assistant"

st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE = os.getenv("BACKEND_URL", "http://localhost:8000")

# ─── Custom CSS (professional enterprise theme) ──────────────────────────────

st.markdown("""
<style>
    :root {
        --primary: #1e3a5f;
        --accent: #2563eb;
        --accent-2: #7c3aed;
        --bg: #1f2937;            /* dark background */
        --bg-alt: #f4f6fa;
        --card: #ffffff;
        --border: #e2e8f0;
        --text: #0f172a;
        --muted: #475569;
        --success: #059669;
        --danger: #dc2626;
        --warning: #d97706;
    }
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        color: var(--text);
    }
    .stApp { background: var(--bg); }
    section.main > div { background: var(--bg); }

    /* Streamlit buttons — darker, clearly visible hover */
    .stButton > button {
        background: #ffffff !important;
        color: #1e293b !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: all 0.15s ease !important;
    }
    .stButton > button:hover {
        background: #1e3a5f !important;
        color: #ffffff !important;
        border-color: #1e3a5f !important;
        box-shadow: 0 2px 8px rgba(30, 58, 95, 0.25) !important;
    }
    .stButton > button:active {
        background: #0f172a !important;
        color: #ffffff !important;
    }
    /* Primary buttons keep the dark blue background */
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: none !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0f172a 0%, #1d4ed8 100%) !important;
        color: #ffffff !important;
    }

    /* Sidebar — slightly darker for separation */
    [data-testid="stSidebar"] { background: var(--bg-alt); }

    /* Top brand bar */
    .brand-bar {
        background: linear-gradient(135deg, #0f2b46 0%, #1e3a5f 45%, #7c3aed 100%);
        padding: 1.2rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 16px rgba(15, 43, 70, 0.18);
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    .brand-bar .logo { font-size: 2rem; }
    .brand-bar .title { color: #fff; font-size: 1.45rem; font-weight: 700; letter-spacing: 0.2px; }
    .brand-bar .subtitle { color: #cbd5e1; font-size: 0.85rem; margin-top: 2px; }

    .section-title { font-size: 1.25rem; font-weight: 700; color: var(--primary); margin: 1rem 0 0.5rem 0; }
    .section-subtitle { color: var(--muted); font-size: 0.9rem; margin-bottom: 1rem; }

    /* Cards */
    .doc-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.6rem;
        transition: all 0.15s ease;
    }
    .doc-card:hover { box-shadow: 0 2px 12px rgba(0,0,0,0.10); border-color: #cbd5e1; transform: translateY(-1px); }
    .doc-card .name { font-weight: 600; font-size: 1.02rem; }
    .doc-card .meta { color: var(--muted); font-size: 0.82rem; margin-top: 3px; }

    .stat-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 0.9rem;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .stat-card .num { font-size: 1.6rem; font-weight: 800; color: var(--primary); }
    .stat-card .label { font-size: 0.78rem; color: var(--muted); margin-top: 2px; }

    /* Chat bubbles — darker, more visible on hover */
    .chat-user {
        background: #c7d2fe; border-radius: 12px 12px 12px 2px;
        padding: 0.85rem 1.1rem; margin: 0.5rem 0 0.5rem 2rem;
        border: 1px solid #818cf8;
        transition: background 0.15s ease, transform 0.15s ease;
    }
    .chat-user:hover { background: #a5b4fc; transform: translateX(-2px); }
    .chat-user .who { color: #312e81; font-weight: 700; font-size: 0.82rem; margin-bottom: 4px; }
    .chat-assistant {
        background: #f1f5f9; border-radius: 12px 12px 2px 12px;
        padding: 0.85rem 1.1rem; margin: 0.5rem 2rem 0.5rem 0;
        border: 1px solid #cbd5e1;
        transition: background 0.15s ease, transform 0.15s ease;
    }
    .chat-assistant:hover { background: #e2e8f0; transform: translateX(2px); }
    .chat-assistant .who { color: #6b21a8; font-weight: 700; font-size: 0.82rem; margin-bottom: 4px; }

    .answer-box {
        background: #eff6ff; border-left: 4px solid var(--accent);
        border-radius: 6px; padding: 0.9rem 1.1rem; margin: 0.5rem 0;
        font-size: 0.95rem; color: #1e3a8a;
    }
    .citation-box {
        background: #fffbeb; border-left: 3px solid var(--warning);
        border-radius: 6px; padding: 0.6rem 0.9rem; margin: 0.3rem 0;
        font-size: 0.85rem; color: #92400e;
    }
    .blocked-box {
        background: #fee2e2; border-left: 4px solid var(--danger);
        border-radius: 6px; padding: 0.9rem 1.1rem; margin: 0.5rem 0;
        color: #991b1b; font-size: 0.95rem;
    }
    .insufficient-box {
        background: #fef3c7; border-left: 4px solid var(--warning);
        border-radius: 6px; padding: 0.9rem 1.1rem; margin: 0.5rem 0;
        color: #92400e; font-size: 0.95rem;
    }

    .role-badge { display: inline-block; padding: 0.18rem 0.75rem; border-radius: 20px;
                  font-size: 0.78rem; font-weight: 600; }
    .rb-Employee { background: #e0f2fe; color: #0369a1; }
    .rb-HR { background: #fee2e2; color: #b91c1c; }
    .rb-Finance { background: #dcfce7; color: #15803d; }
    .rb-Admin { background: #f3e8ff; color: #7e22ce; }

    .cred-table { font-size: 0.9rem; }
    footer { text-align: center; color: var(--muted); font-size: 0.78rem;
             padding: 1.5rem 0 0.5rem 0; margin-top: 2rem;
             border-top: 1px solid var(--border); }
</style>
""", unsafe_allow_html=True)


# ─── Session State ──────────────────────────────────────────────────────────

def init_session():
    defaults = {
        "authenticated": False, "token": None, "role": None,
        "username": None, "name": None, "chat_history": [],
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)


init_session()


# ─── API Client with token auth ─────────────────────────────────────────────

def _headers(token=None):
    token = token or st.session_state.get("token")
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def api_post(path: str, payload: dict, auth: bool = True):
    """POST to the backend. Returns (ok, data_or_error)."""
    try:
        with httpx.Client(base_url=API_BASE, timeout=30.0) as client:
            resp = client.post(path, json=payload, headers=_headers() if auth else {})
            if resp.status_code == 401:
                return False, {"auth_error": True, "detail": resp.json().get("detail", "Session expired")}
            if resp.status_code >= 400:
                try:
                    return False, resp.json()
                except Exception:
                    return False, {"detail": f"Server error ({resp.status_code})"}
            return True, resp.json()
    except Exception as e:
        return False, {"detail": f"Connection error: cannot reach backend at {API_BASE}"}


def api_get(path: str, params: dict = None):
    """GET to the backend with token auth."""
    try:
        with httpx.Client(base_url=API_BASE, timeout=30.0) as client:
            resp = client.get(path, params=params, headers=_headers())
            if resp.status_code == 401:
                return False, {"auth_error": True}
            if resp.status_code >= 400:
                return False, resp.json()
            return True, resp.json()
    except Exception as e:
        return False, {"detail": f"Connection error: cannot reach backend at {API_BASE}"}


def handle_auth_error(result):
    """If the backend rejected the token, force re-login."""
    if isinstance(result, dict) and result.get("auth_error"):
        st.session_state.authenticated = False
        st.session_state.token = None
        st.error("🔒 Session expired. Please log in again.")
        st.rerun()
        return True
    return False


# ─── Brand Bar ──────────────────────────────────────────────────────────────

def brand_bar():
    st.markdown(f"""
    <div class="brand-bar">
        <div class="logo">🏢</div>
        <div>
            <div class="title">{APP_NAME}</div>
            <div class="subtitle">Secure enterprise knowledge retrieval · Role-Based Access Control · Grounded RAG</div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ─── Login ──────────────────────────────────────────────────────────────────

def render_login():
    brand_bar()

    col1, col2, col3 = st.columns([1, 1.6, 1])
    with col2:
        st.markdown('<div class="section-title">🔐 Secure Sign In</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Authenticate to access your authorized enterprise documents.</div>',
                    unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("Username", placeholder="e.g., emp001")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("Sign In", use_container_width=True, type="primary")

        if submitted:
            if not username or not password:
                st.warning("Please enter both username and password.")
            else:
                ok, data = api_post("/api/login", {"username": username, "password": password}, auth=False)
                if ok:
                    st.session_state.authenticated = True
                    st.session_state.token = data["access_token"]
                    st.session_state.role = data["role"]
                    st.session_state.name = data["name"]
                    st.session_state.username = username
                    st.session_state.chat_history = []
                    st.rerun()
                else:
                    st.error(f"❌ Login failed: {data.get('detail', 'Invalid credentials')}")

        st.markdown("---")
        st.markdown('<div class="section-title">👥 Demo Accounts</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-subtitle">Each role can only access its authorized documents.</div>',
                    unsafe_allow_html=True)

        creds = pd.DataFrame([
            {"Role": "Employee", "Username": "emp001", "Password": "Emp@123",
             "Access": "HR Policy · Leave Policy"},
            {"Role": "HR", "Username": "hr001", "Password": "HR@123",
             "Access": "HR · Leave · Termination · Salary"},
            {"Role": "Finance", "Username": "fin001", "Password": "Fin@123",
             "Access": "Finance Policy"},
            {"Role": "Admin", "Username": "admin001", "Password": "Admin@123",
             "Access": "All Documents"},
        ])
        st.dataframe(creds, use_container_width=True, hide_index=True)

        st.markdown("""
        <div class="insufficient-box">
        🔐 <b>RBAC enforcement:</b> the server derives your role from your login token.
        A request can never claim a role — only your authenticated role's documents
        are retrieved, and only the <b>Admin</b> can upload documents.
        </div>
        """, unsafe_allow_html=True)


# ─── Sidebar ────────────────────────────────────────────────────────────────

def sidebar():
    role = st.session_state.role
    badge = {"Employee": "rb-Employee", "HR": "rb-HR", "Finance": "rb-Finance", "Admin": "rb-Admin"}.get(role, "rb-Employee")

    with st.sidebar:
        st.markdown(f"""
        <div style="padding:0.5rem 0 0.8rem 0;">
            <div style="font-size:2.1rem;">👤</div>
            <div style="font-weight:700; font-size:1.1rem;">{st.session_state.name}</div>
            <div style="margin-top:4px;"><span class="role-badge {badge}">{role}</span></div>
            <div style="font-size:0.78rem; color:var(--muted); margin-top:4px;">@{st.session_state.username}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("**Navigation**")
        nav = {
            "💬 Chat": "chat",
            "📚 Documents": "docs",
            "📊 Evaluation": "eval",
            "ℹ️ About": "about",
        }
        for label, key in nav.items():
            style = "primary" if st.session_state.get("page") == key else "secondary"
            if st.button(label, use_container_width=True, type=style):
                st.session_state.page = key
                st.rerun()

        st.markdown("---")
        ok, stats = api_get("/api/documents/stats")
        if ok and not handle_auth_error(stats):
            chunks = stats.get("total_chunks", 0)
        else:
            chunks = "—"
        st.markdown(f"""
        <div class="stat-card">
            <div class="num">{chunks}</div>
            <div class="label">Document Chunks Indexed</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.token = None
            st.session_state.role = None
            st.session_state.username = None
            st.session_state.name = None
            st.session_state.chat_history = []
            st.session_state.page = None
            st.rerun()


# ─── Chat ───────────────────────────────────────────────────────────────────

def send_query(question: str) -> dict:
    ok, data = api_post("/api/query", {"question": question})
    if handle_auth_error(data):
        return {"answer": "Session expired. Please log in again.", "citations": [], "blocked": False}
    if not ok:
        return {"answer": f"⚠️ {data.get('detail', 'Request failed')}", "citations": [], "blocked": False}
    return data


def process_and_display_query(question: str):
    st.session_state.chat_history.append({"role": "user", "content": question})
    with st.spinner("🔍 Retrieving authorized context & generating grounded answer..."):
        result = send_query(question)

    answer = result.get("answer", "No answer generated.")
    citations = result.get("citations", [])
    blocked = result.get("blocked", False)
    insufficient = result.get("insufficient_information", False)

    parts = []
    if blocked:
        parts.append(f'<div class="blocked-box">🛡️ {answer}</div>')
    elif insufficient:
        parts.append(f'<div class="insufficient-box">ℹ️ {answer}</div>')
    else:
        parts.append(f'<div class="answer-box">{answer}</div>')

    if citations and not blocked and not insufficient:
        for c in citations:
            doc = c.get("document", "Unknown")
            loc = []
            if c.get("page"):
                loc.append(f"Page {c['page']}")
            if c.get("slide"):
                loc.append(f"Slide {c['slide']}")
            if c.get("sheet"):
                loc.append(f"Sheet {c['sheet']}")
            suffix = " — " + " · ".join(loc) if loc else ""
            parts.append(f'<div class="citation-box">📄 <b>{doc}</b>{suffix}</div>')

    st.session_state.chat_history.append({"role": "assistant", "content": "\n".join(parts)})


def render_chat():
    st.markdown('<div class="section-title">💬 Enterprise Knowledge Chat</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-subtitle">Ask questions about your <b>authorized</b> documents as '
        f'<span class="role-badge {"rb-" + st.session_state.role}">{st.session_state.role}</span>.</div>',
        unsafe_allow_html=True,
    )

    quick = {
        "Employee": ["What are the working hours?",
                     "How many earned leaves are available?",
                     "What is the dress code?",
                     "What is the probation period?"],
        "HR": ["What is the notice period for permanent employees?",
               "How many sick leaves are provided?",
               "What is the resignation procedure?"],
        "Finance": ["What is the daily meal allowance?",
                    "What are the travel reimbursement rules?",
                    "What is the internet reimbursement policy?"],
        "Admin": ["What are the working hours?",
                  "What is the notice period?",
                  "What is the meal allowance?",
                  "How many earned leaves are available?"],
    }.get(st.session_state.role, [])

    if quick:
        st.markdown("**⚡ Quick questions**")
        cols = st.columns(len(quick))
        for i, q in enumerate(quick):
            with cols[i]:
                if st.button(q, use_container_width=True, key=f"q{i}"):
                    process_and_display_query(q)

    st.markdown("---")
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f'<div class="chat-user"><div class="who">👤 You</div><div>{msg["content"]}</div></div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-assistant"><div class="who">🤖 Assistant</div><div>{msg["content"]}</div></div>',
                        unsafe_allow_html=True)

    with st.form("query_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            question = st.text_input("Ask a question", placeholder="e.g., What are the working hours?",
                                     label_visibility="collapsed")
        with c2:
            submitted = st.form_submit_button("Ask", use_container_width=True, type="primary")

    if submitted and question.strip():
        process_and_display_query(question.strip())
        st.rerun()


# ─── Documents ──────────────────────────────────────────────────────────────

def render_docs():
    st.markdown('<div class="section-title">📚 Authorized Documents</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-subtitle">Only documents accessible to your role '
        f'<span class="role-badge rb-{st.session_state.role}">{st.session_state.role}</span> are shown.</div>',
        unsafe_allow_html=True,
    )

    ok, data = api_get("/api/documents")
    if handle_auth_error(data):
        return
    if not ok:
        st.error(data.get("detail", "Failed to load documents"))
        return

    docs = data.get("documents", [])
    if not docs:
        st.info("No documents available for your role.")
        return

    icons = {"PDF": "📕", "PowerPoint": "📊", "Word": "📝", "Scanned PDF": "📄", "Excel": "📗"}
    cols = st.columns(2)
    for i, doc in enumerate(docs):
        with cols[i % 2]:
            st.markdown(f"""
            <div class="doc-card">
                <div style="display:flex; align-items:center; gap:0.7rem;">
                    <div style="font-size:1.6rem;">{icons.get(doc.get('format',''), '📄')}</div>
                    <div>
                        <div class="name">{doc.get('name', doc.get('filename', ''))}</div>
                        <div class="meta">{doc.get('format','')} · {doc.get('description','')}</div>
                        <div class="meta">📁 {doc.get('filename','')}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('<div class="section-title" style="margin-top:1.2rem;">🔐 Role-Based Access Matrix</div>',
                unsafe_allow_html=True)
    rows = []
    for fname, meta in DOCUMENT_METADATA.items():
        rows.append({
            "Document": meta["name"],
            "Format": meta["format"],
            **{r: ("✅" if fname in ROLE_DOCUMENTS.get(r, []) else "🚫") for r in ["Employee", "HR", "Finance", "Admin"]},
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ─── Evaluation ─────────────────────────────────────────────────────────────

def render_eval():
    st.markdown('<div class="section-title">📊 AI Evaluation Suite</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Systematic measurement of correctness, RBAC, security & groundedness.</div>',
                unsafe_allow_html=True)

    cats = [
        ("✅", "Answer Correctness", "Answers match expected values from the knowledge base."),
        ("📚", "Citation Correctness", "Answers cite the correct documents, pages and slides."),
        ("🔐", "RBAC Enforcement", "Users can only access documents authorized for their role."),
        ("🛡️", "Prompt Injection", "Malicious override / reveal attempts are blocked."),
        ("ℹ️", "Insufficient Info", "System returns 'insufficient information' instead of hallucinating."),
        ("🔄", "Regression", "Evaluation re-runs after code changes to preserve behavior."),
    ]
    cols = st.columns(3)
    for i, (icon, name, desc) in enumerate(cats):
        with cols[i % 3]:
            st.markdown(f"""
            <div class="doc-card" style="min-height:108px;">
                <div style="font-size:1.5rem;">{icon}</div>
                <div style="font-weight:600; margin-top:2px;">{name}</div>
                <div class="meta" style="font-size:0.82rem; color:var(--muted); margin-top:3px;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    if st.button("🚀 Run Full Evaluation (21 tests)", use_container_width=True, type="primary"):
        with st.spinner("Running evaluation... this may take a moment."):
            ok, report = api_post("/api/evaluate", {})
            if handle_auth_error(report):
                return
            if not ok:
                st.error(report.get("detail", "Evaluation failed"))
                return

        total, passed, failed, rate = report["total"], report["passed"], report["failed"], report["pass_rate"]
        m1, m2, m3, m4 = st.columns(4)
        m1.markdown(f'<div class="stat-card"><div class="num">{total}</div><div class="label">Total Tests</div></div>', unsafe_allow_html=True)
        m2.markdown(f'<div class="stat-card"><div class="num" style="color:var(--success);">{passed}</div><div class="label">Passed</div></div>', unsafe_allow_html=True)
        m3.markdown(f'<div class="stat-card"><div class="num" style="color:var(--danger);">{failed}</div><div class="label">Failed</div></div>', unsafe_allow_html=True)
        m4.markdown(f'<div class="stat-card"><div class="num" style="color:{"var(--success)" if rate>=80 else "var(--warning)"};">{rate}%</div><div class="label">Pass Rate</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title" style="margin-top:1rem;">📋 Detailed Results</div>', unsafe_allow_html=True)
        rows = [{
            "Status": "✅" if r["passed"] else "❌",
            "Test ID": r["test_id"],
            "Question": (r["question"][:55] + "…") if len(r["question"]) > 56 else r["question"],
            "Role": r["user_role"],
            "Expected": r["expected_result"],
            "Actual": r["actual_result"],
        } for r in report["results"]]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        if failed == 0:
            st.success(f"🏆 All {total} evaluation tests passed ({rate}%)!")


# ─── About ──────────────────────────────────────────────────────────────────

def render_about():
    st.markdown('<div class="section-title">ℹ️ About This System</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="answer-box">
    <h3 style="margin:0 0 0.5rem 0;">🏢 {APP_NAME}</h3>
    <p style="margin:0;">A secure enterprise AI knowledge assistant that enables employees to query
    organizational documents using Retrieval-Augmented Generation (RAG), while enforcing
    <b>role-based access control</b>, <b>grounded answering</b>, <b>source citations</b>,
    <b>prompt-injection protection</b>, and <b>multimodal document processing</b>.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-title">🛡️ Security Architecture</div>', unsafe_allow_html=True)
    st.markdown("""
    1. **Authentication** — Login issues a signed bearer token.
    2. **Server-side RBAC** — Role is derived from the token; clients cannot claim a role.
    3. **Retrieval-layer filtering** — Unauthorized chunks never reach the LLM context.
    4. **Prompt-injection detection** — Malicious instructions blocked pre-retrieval.
    5. **Sensitive-info protection** — Restricted data requests are denied.
    6. **Citation validation** — Answers must trace back to retrieved sources.
    """)

    st.markdown('<div class="section-title">🛠️ Technology Stack</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Layer": ["Backend API", "User Interface", "Vector Database", "LLM", "Embeddings", "OCR", "Testing"],
        "Technology": ["FastAPI (Python)", "Streamlit", "ChromaDB", "Gemini (optional)", "Gemini / Chroma built-in", "EasyOCR", "pytest"],
        "Purpose": ["Async REST API", "Enterprise UI", "Semantic retrieval", "Answer generation", "Document vectors", "Scanned docs", "Automated tests"],
    }), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">📁 Enterprise Documents</div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame({
        "Document": ["HR Policy", "Leave Policy", "Finance Policy", "Termination Policy", "Employee Salary Records"],
        "Format": ["PDF", "PowerPoint", "Word", "Scanned PDF", "Excel"],
        "Content": ["Working hours, probation, dress code", "Leave types & workflow", "Reimbursements & allowances", "Notice periods & exit", "Employee salaries"],
    }), use_container_width=True, hide_index=True)


# ─── Main ───────────────────────────────────────────────────────────────────

def main():
    if not st.session_state.authenticated or not st.session_state.token:
        render_login()
    else:
        sidebar()
        brand_bar()
        page = st.session_state.get("page", "chat")
        if page == "chat":
            render_chat()
        elif page == "docs":
            render_docs()
        elif page == "eval":
            render_eval()
        else:
            render_about()

    st.markdown(f"""
    <footer>
        {APP_NAME} v2.0.0 · Built with FastAPI, Streamlit, ChromaDB & Google Gemini<br>
        © 2026 Enterprise AI — All data is synthetic demo data
    </footer>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()