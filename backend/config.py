"""Configuration module for the Enterprise RAG Assistant."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DOCUMENTS_DIR = DATA_DIR / "documents"
CHROMA_DIR = DATA_DIR / "chroma"
EVALUATION_DIR = DATA_DIR / "evaluation"

# Ensure directories exist
for d in [DATA_DIR, DOCUMENTS_DIR, CHROMA_DIR, EVALUATION_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Google AI / Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

# Backend
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Auth security
# IMPORTANT: In production, set a strong random value via environment variable.
TOKEN_SECRET = os.getenv("TOKEN_SECRET", "enterprise-rag-demo-secret-change-me")
TOKEN_TTL_HOURS = int(os.getenv("TOKEN_TTL_HOURS", "8"))

# ChromaDB
CHROMA_COLLECTION_NAME = "enterprise_documents"
CHUNK_SIZE = 1000           # Larger chunks so questions match more of the document
CHUNK_OVERLAP = 100
TOP_K_RETRIEVAL = 5

# Auth
# Dummy users for demo purposes
USERS = {
    "emp001": {"password": "Emp@123", "role": "Employee", "name": "Employee User"},
    "hr001": {"password": "HR@123", "role": "HR", "name": "HR User"},
    "fin001": {"password": "Fin@123", "role": "Finance", "name": "Finance User"},
    "admin001": {"password": "Admin@123", "role": "Admin", "name": "Admin User"},
}

# RBAC - map roles to accessible documents
ROLE_DOCUMENTS = {
    "Employee": ["HR_Policy.pdf", "Leave_Policy.pptx"],
    "HR": ["HR_Policy.pdf", "Leave_Policy.pptx", "Termination_Policy_Scanned.pdf", "Employee_Salary_Records.xlsx"],
    "Finance": ["Finance_Policy.docx"],
    "Admin": ["HR_Policy.pdf", "Leave_Policy.pptx", "Finance_Policy.docx",
              "Termination_Policy_Scanned.pdf", "Employee_Salary_Records.xlsx"],
}

# Document metadata
DOCUMENT_METADATA = {
    "HR_Policy.pdf": {
        "name": "HR Policy",
        "format": "PDF",
        "description": "HR policies and workplace rules",
    },
    "Leave_Policy.pptx": {
        "name": "Leave Policy",
        "format": "PowerPoint",
        "description": "Leave policies and approval workflow",
    },
    "Finance_Policy.docx": {
        "name": "Finance Policy",
        "format": "Word",
        "description": "Finance and reimbursement policies",
    },
    "Termination_Policy_Scanned.pdf": {
        "name": "Termination Policy",
        "format": "Scanned PDF",
        "description": "Resignation and termination policies",
    },
    "Employee_Salary_Records.xlsx": {
        "name": "Employee Salary Records",
        "format": "Excel",
        "description": "Employee salary information",
    },
}