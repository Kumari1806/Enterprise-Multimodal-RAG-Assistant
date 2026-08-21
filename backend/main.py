"""FastAPI Backend for the Enterprise Multimodal Role-Based RAG Assistant.

Security architecture:
  - Every protected endpoint requires a valid bearer token (issued at login).
  - The user's ROLE is always derived SERVER-SIDE from the token. The client
    cannot claim a role — privilege escalation is impossible.
  - RBAC is enforced at three layers:
      1. Endpoint-level: some operations are restricted by role (e.g., upload = Admin only).
      2. Security layer: prompt-injection & sensitive-request detection before retrieval.
      3. Retrieval layer: document chunks are metadata-filtered by the role's
         authorized document list BEFORE they ever reach the LLM context.
"""

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Header
from fastapi.middleware.cors import CORSMiddleware

from backend.models import (
    LoginRequest, LoginResponse, QueryRequest, QueryResponse,
    DocumentUploadResponse, EvaluationReport, EvaluationResult, Citation,
)
from backend.auth import authenticate, validate_token
from backend.rbac import get_authorized_metadata, check_access
from backend.security import detect_prompt_injection, detect_sensitive_request
from backend.rag_pipeline import RAGPipeline
from backend.ingestion import DocumentIngestor
from backend.config import DOCUMENTS_DIR, EVALUATION_DIR, ROLE_DOCUMENTS
from backend.retriever import SecureRetriever
from backend.citation import extract_citations_from_chunks

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Global state
rag_pipeline: Optional[RAGPipeline] = None
ingestor: Optional[DocumentIngestor] = None


# ─── Auth dependency (FastAPI) ───────────────────────────────────────────────

def require_user(authorization: Optional[str] = Header(default=None)) -> dict:
    """FastAPI dependency: requires a valid Bearer token.

    Returns the authenticated user dict {username, role, name}.
    Raises 401 if the token is missing, invalid, expired, or forged.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or malformed Authorization header. Use: 'Authorization: Bearer <token>'",
        )
    token = authorization.split(" ", 1)[1].strip()
    user = validate_token(token)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid, expired, or forged token. Please log in again.",
        )
    return user


def require_admin(user: dict = Depends(require_user)) -> dict:
    """FastAPI dependency: requires the Admin role."""
    if user["role"] != "Admin":
        raise HTTPException(
            status_code=403,
            detail=f"FORBIDDEN: Only the Admin role can perform this operation (your role: {user['role']}).",
        )
    return user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — initialize components on startup."""
    global rag_pipeline, ingestor
    logger.info("Initializing Enterprise RAG Assistant...")

    # Initialize components
    rag_pipeline = RAGPipeline()
    ingestor = DocumentIngestor()

    # Auto-ingest documents if they exist
    docs_dir = Path(DOCUMENTS_DIR)
    if docs_dir.exists() and any(docs_dir.iterdir()):
        logger.info("Found existing documents, running ingestion...")
        try:
            results = ingestor.ingest_all_documents()
            total = sum(results.values())
            logger.info(f"Ingestion complete: {total} total chunks indexed across {len(results)} documents")
        except Exception as e:
            logger.warning(f"Auto-ingestion failed: {e}")

    # Print stats
    stats = ingestor.get_collection_stats() if ingestor else {"total_chunks": 0}
    logger.info(f"ChromaDB stats: {stats}")

    yield

    logger.info("Shutting down Enterprise RAG Assistant...")


app = FastAPI(
    title="Enterprise Multimodal Role-Based RAG Assistant API",
    version="2.0.0",
    description=(
        "Secure enterprise RAG API. All endpoints (except /api/login and /health) "
        "require a Bearer token. The user's role is always derived server-side from "
        "the token — clients cannot claim a role."
    ),
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Authentication Endpoints ───────────────────────────────────────────────

@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Authenticate a user and return a signed token.

    This is the ONLY way to obtain a token. The role is assigned
    server-side based on the username in the credentials registry.
    """
    user = authenticate(request.username, request.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )
    logger.info(f"User '{request.username}' logged in as {user['role']}")
    return LoginResponse(**user)


@app.get("/api/verify", dependencies=[Depends(require_user)])
async def verify_token(user: dict = Depends(require_user)):
    """Verify a token is valid and return the caller's identity."""
    return {"valid": True, **user}


# ─── Query Endpoint (role derived from token — NOT from request body) ───────

@app.post("/api/query", response_model=QueryResponse)
async def query(request: QueryRequest, user: dict = Depends(require_user)):
    """Process a user query through the RAG pipeline with full security checks.

    RBAC enforcement:
      - The role comes from the validated token (user['role']).
      - Prompt injection & sensitive-request checks run before retrieval.
      - Retrieval filters chunks to role-authorized documents only.
    """
    role = user["role"]
    username = user["username"]

    # Step 1: Security — Prompt injection detection
    is_injection, inj_reason = detect_prompt_injection(request.question)
    if is_injection:
        logger.warning(f"Prompt injection blocked for user {username}: {inj_reason}")
        return QueryResponse(
            answer="🛡️ **Blocked:** Your query was detected as a potential prompt injection attempt. "
                   "Please ask a legitimate enterprise knowledge question.",
            citations=[],
            blocked=True,
            block_reason=inj_reason,
        )

    # Step 2: Security — Sensitive information detection
    is_sensitive, sens_reason = detect_sensitive_request(request.question, role)
    if is_sensitive:
        logger.warning(f"Sensitive info request blocked for {username} (role={role}): {sens_reason}")
        return QueryResponse(
            answer=f"🔒 **{sens_reason}**",
            citations=[],
            access_decision="DENIED",
            blocked=True,
            block_reason=sens_reason,
        )

    # Step 3: Generate answer through RAG pipeline (role-aware retrieval)
    try:
        result = await rag_pipeline.generate_answer(
            question=request.question,
            role=role,
        )

        citations = [Citation(**c) for c in result.get("citations", [])]

        return QueryResponse(
            answer=result.get("answer", "No answer generated."),
            citations=citations,
            insufficient_information=result.get("insufficient_information", False),
            blocked=result.get("blocked", False),
        )

    except Exception as e:
        logger.error(f"Error processing query: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}",
        )


# ─── Document Management Endpoints (role-restricted) ────────────────────────

@app.post("/api/documents/upload", response_model=DocumentUploadResponse,
          dependencies=[Depends(require_admin)])
async def upload_document(file: UploadFile = File(...), user: dict = Depends(require_admin)):
    """Upload a document for ingestion — ADMIN ONLY."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    allowed_extensions = {".pdf", ".pptx", ".docx", ".xlsx"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format: {ext}. Allowed: {', '.join(allowed_extensions)}",
        )

    filepath = DOCUMENTS_DIR / file.filename
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    if ingestor:
        extracted = ingestor.extract_text(filepath)
        if extracted:
            chunks = ingestor.chunk_and_embed(extracted, file.filename)
            logger.info(f"Admin uploaded {file.filename}: {chunks} chunks indexed")
            return DocumentUploadResponse(
                filename=file.filename,
                status="success",
                message=f"Document ingested successfully. {chunks} chunks indexed.",
                chunks_indexed=chunks,
            )
        return DocumentUploadResponse(
            filename=file.filename,
            status="warning",
            message="Document saved but no text could be extracted.",
            chunks_indexed=0,
        )
    return DocumentUploadResponse(
        filename=file.filename,
        status="error",
        message="Ingestion service not available.",
        chunks_indexed=0,
    )


@app.get("/api/documents")
async def list_documents(user: dict = Depends(require_user)):
    """List documents accessible by the CALLER's role (from token)."""
    role = user["role"]
    docs_metadata = get_authorized_metadata(role)
    return {"documents": docs_metadata, "role": role, "count": len(docs_metadata)}


@app.get("/api/documents/stats", dependencies=[Depends(require_user)])
async def get_document_stats():
    """Get vector database statistics."""
    if ingestor:
        return ingestor.get_collection_stats()
    return {"total_chunks": 0, "collection": "not_initialized"}


# ─── Evaluation Endpoint ────────────────────────────────────────────────────

@app.post("/api/evaluate", response_model=EvaluationReport)
async def run_evaluation(user: dict = Depends(require_user)):
    """Run the evaluation dataset against the RAG system.

    Measures answer correctness, citation correctness, RBAC enforcement,
    prompt injection resistance, and insufficient-information handling.
    """
    eval_file = EVALUATION_DIR / "evaluation_dataset.json"
    if not eval_file.exists():
        raise HTTPException(
            status_code=404,
            detail="Evaluation dataset not found.",
        )

    import json
    with open(eval_file) as f:
        test_cases = json.load(f)

    results = []
    passed = 0
    failed = 0

    for case in test_cases:
        question = case.get("question", "")
        expected_answer = case.get("expected_answer", "").lower()
        expected_source = case.get("expected_source", "").lower()
        role = case.get("user_role", "Employee")
        expected_result = case.get("expected_result", "PASS")

        is_injection, _ = detect_prompt_injection(question)
        is_sensitive, _ = detect_sensitive_request(question, role)

        if is_injection or is_sensitive:
            actual_result = "BLOCKED"
        else:
            try:
                result = await rag_pipeline.generate_answer(question, role)
                answer = result.get("answer", "").lower()
                insufficient = result.get("insufficient_information", False)

                if insufficient or "insufficient information" in answer:
                    actual_result = "INSUFFICIENT INFORMATION"
                else:
                    actual_result = "ALLOWED"
            except Exception as e:
                actual_result = f"ERROR: {str(e)}"

        if actual_result == "ALLOWED" and expected_result == "PASS":
            expected_keywords = expected_answer.split()
            answer_lower = answer.lower() if actual_result == "ALLOWED" else ""
            keyword_match = sum(1 for kw in expected_keywords if kw in answer_lower)
            answer_correct = keyword_match >= max(1, len(expected_keywords) // 2)
            source_correct = expected_source in answer_lower if expected_source else True
            is_pass = answer_correct and source_correct
        elif "BLOCK" in actual_result and "BLOCK" in expected_result:
            is_pass = True
        elif actual_result == "INSUFFICIENT INFORMATION" and "INSUFFICIENT" in expected_result:
            is_pass = True
        elif expected_result == "PASS" and "ERROR" in actual_result:
            is_pass = False
        else:
            is_pass = len(question.strip()) == 0

        if is_pass:
            passed += 1
        else:
            failed += 1

        results.append(EvaluationResult(
            test_id=case.get("id", str(len(results) + 1)),
            question=question,
            expected_answer=expected_answer,
            expected_source=expected_source,
            user_role=role,
            expected_result=expected_result,
            actual_result=actual_result,
            passed=is_pass,
            details=f"Expected: {expected_result}, Actual: {actual_result}",
        ))

    total = len(results)
    pass_rate = (passed / total * 100) if total > 0 else 0.0

    return EvaluationReport(
        total=total,
        passed=passed,
        failed=failed,
        pass_rate=round(pass_rate, 2),
        results=results,
    )


# ─── Health Endpoint (public) ───────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint (public)."""
    return {
        "status": "healthy",
        "service": "Enterprise RAG Assistant",
        "version": "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)