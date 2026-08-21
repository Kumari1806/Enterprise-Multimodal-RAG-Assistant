"""Citation generation and validation module."""

import re
from typing import Optional


def extract_citations_from_chunks(chunks: list[dict]) -> list[dict]:
    """Extract citation metadata from retrieved chunks."""
    citations = []
    seen = set()

    for chunk in chunks:
        metadata = chunk.get("metadata", {})
        doc_name = metadata.get("document", metadata.get("document_name", "Unknown"))
        page = metadata.get("page")
        slide = metadata.get("slide")
        sheet = metadata.get("sheet")
        content = chunk.get("content", "")[:200]  # First 200 chars

        citation_key = f"{doc_name}_{page}_{slide}_{sheet}"
        if citation_key not in seen:
            seen.add(citation_key)
            citation = {
                "document": doc_name,
                "content": content,
            }
            if page:
                citation["page"] = str(page)
            if slide:
                citation["slide"] = str(slide)
            if sheet:
                citation["sheet"] = sheet
            citations.append(citation)

    return citations


def validate_citations(answer: str, citations: list[dict]) -> tuple[bool, list[str]]:
    """Validate that citations in the answer correspond to actual retrieved sources.

    Returns:
        (is_valid: bool, issues: list[str])
    """
    issues = []

    # Check that citations are referenced in the answer
    for citation in citations:
        doc_name = citation.get("document", "")
        if doc_name and doc_name not in answer:
            # Some citations may be implicit — not necessarily an issue
            pass

    # Check that the answer doesn't cite documents not in the citations list
    doc_ref_pattern = r'[`"\'*]*([A-Za-z_\-]+\.(pdf|pptx|docx|xlsx))[`"\'*]*'
    answer_doc_refs = set(re.findall(doc_ref_pattern, answer))
    cited_docs = set()
    for citation in citations:
        doc = citation.get("document", "")
        if doc:
            cited_docs.add(doc)

    for ref_tuple in answer_doc_refs:
        ref = ref_tuple[0]
        if ref not in cited_docs:
            issues.append(f"Answer references '{ref}' but it is not in the retrieved citations.")

    return len(issues) == 0, issues


def format_citations_text(citations: list[dict]) -> str:
    """Format citations as readable text."""
    if not citations:
        return ""

    lines = ["\n\n**📚 Sources:**\n"]
    for i, citation in enumerate(citations, 1):
        doc = citation.get("document", "Unknown")
        parts = [f"{i}. **{doc}**"]
        if citation.get("page"):
            parts.append(f"Page {citation['page']}")
        if citation.get("slide"):
            parts.append(f"Slide {citation['slide']}")
        if citation.get("sheet"):
            parts.append(f"Sheet: {citation['sheet']}")
        lines.append(" — ".join(parts))

    return "\n".join(lines)