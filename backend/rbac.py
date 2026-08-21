"""Role-Based Access Control module."""

from typing import Optional
from backend.config import ROLE_DOCUMENTS, DOCUMENT_METADATA


def get_authorized_documents(role: str) -> list[str]:
    """Return list of document filenames accessible by the given role."""
    return ROLE_DOCUMENTS.get(role, [])


def is_document_authorized(role: str, document_filename: str) -> bool:
    """Check if a role can access a specific document."""
    authorized = get_authorized_documents(role)
    return document_filename in authorized


def get_authorized_metadata(role: str) -> list[dict]:
    """Return metadata for documents accessible by the given role."""
    authorized_filenames = get_authorized_documents(role)
    result = []
    for filename in authorized_filenames:
        if filename in DOCUMENT_METADATA:
            meta = DOCUMENT_METADATA[filename].copy()
            meta["filename"] = filename
            result.append(meta)
    return result


def check_access(role: str, document_filename: str) -> tuple[bool, str]:
    """Check access and return (allowed, reason)."""
    if is_document_authorized(role, document_filename):
        return True, "ACCESS GRANTED"
    doc_name = DOCUMENT_METADATA.get(document_filename, {}).get("name", document_filename)
    return False, f"ACCESS DENIED: You do not have permission to access '{doc_name}'"