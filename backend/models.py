"""Pydantic models for the Enterprise RAG Assistant."""

from pydantic import BaseModel, Field
from typing import Optional


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    name: str


class QueryRequest(BaseModel):
    """Query request — the role and username are derived from the
    bearer token server-side, never from the request body."""
    question: str = Field(..., min_length=1, max_length=2000)


class Citation(BaseModel):
    document: str = ""
    page: Optional[str] = None
    slide: Optional[str] = None
    sheet: Optional[str] = None
    content: str = ""


class QueryResponse(BaseModel):
    answer: str
    citations: list[Citation] = []
    access_decision: str = "ALLOWED"
    insufficient_information: bool = False
    blocked: bool = False
    block_reason: Optional[str] = None


class DocumentUploadResponse(BaseModel):
    filename: str
    status: str
    message: str
    chunks_indexed: int = 0


class EvaluationResult(BaseModel):
    test_id: str
    question: str
    expected_answer: str
    expected_source: str
    user_role: str
    expected_result: str
    actual_result: str
    passed: bool
    details: str = ""


class EvaluationReport(BaseModel):
    total: int
    passed: int
    failed: int
    pass_rate: float
    results: list[EvaluationResult]


class ErrorResponse(BaseModel):
    detail: str
    error_code: str = "UNKNOWN_ERROR"