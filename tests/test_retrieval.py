"""Tests for retrieval module — secure retrieval with RBAC filtering."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.retriever import SecureRetriever
from backend.config import ROLE_DOCUMENTS


class TestRetriever:
    """Test suite for secure retrieval."""

    def test_retriever_initialization(self):
        """Test that the retriever initializes."""
        retriever = SecureRetriever()
        assert retriever is not None

    def test_retriever_no_collection_fallback(self):
        """Test retrieval when no collection exists yet."""
        retriever = SecureRetriever()
        results = retriever.retrieve("test query", "Employee")
        assert isinstance(results, list)


class TestRoleDocumentMapping:
    """Test role-document mapping integrity."""

    def test_employee_no_salary(self):
        """Employee should not have access to salary records."""
        assert "Employee_Salary_Records.xlsx" not in ROLE_DOCUMENTS.get("Employee", [])

    def test_employee_no_termination(self):
        """Employee should not have access to termination policy."""
        assert "Termination_Policy_Scanned.pdf" not in ROLE_DOCUMENTS.get("Employee", [])

    def test_employee_no_finance(self):
        """Employee should not have access to finance policy."""
        assert "Finance_Policy.docx" not in ROLE_DOCUMENTS.get("Employee", [])

    def test_finance_only_finance(self):
        """Finance should only have access to Finance Policy."""
        finance_docs = ROLE_DOCUMENTS.get("Finance", [])
        assert len(finance_docs) == 1
        assert finance_docs[0] == "Finance_Policy.docx"

    def test_hr_no_finance(self):
        """HR should not have access to Finance Policy."""
        assert "Finance_Policy.docx" not in ROLE_DOCUMENTS.get("HR", [])

    def test_admin_has_all(self):
        """Admin should have access to all documents."""
        admin_docs = ROLE_DOCUMENTS.get("Admin", [])
        all_docs = []
        for role_docs in ROLE_DOCUMENTS.values():
            all_docs.extend(role_docs)
        unique_docs = set(all_docs)
        for doc in unique_docs:
            assert doc in admin_docs


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])