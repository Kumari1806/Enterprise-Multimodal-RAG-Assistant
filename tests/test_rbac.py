"""Tests for Role-Based Access Control module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.rbac import (
    get_authorized_documents,
    is_document_authorized,
    get_authorized_metadata,
    check_access,
)
from backend.config import ROLE_DOCUMENTS


class TestRBAC:
    """Test suite for Role-Based Access Control."""

    def test_employee_documents(self):
        """Test Employee has access to HR Policy and Leave Policy only."""
        docs = get_authorized_documents("Employee")
        assert "HR_Policy.pdf" in docs
        assert "Leave_Policy.pptx" in docs
        assert "Finance_Policy.docx" not in docs
        assert "Termination_Policy_Scanned.pdf" not in docs
        assert "Employee_Salary_Records.xlsx" not in docs

    def test_hr_documents(self):
        """Test HR has access to HR, Leave, Termination, and Salary documents."""
        docs = get_authorized_documents("HR")
        assert "HR_Policy.pdf" in docs
        assert "Leave_Policy.pptx" in docs
        assert "Termination_Policy_Scanned.pdf" in docs
        assert "Employee_Salary_Records.xlsx" in docs
        assert "Finance_Policy.docx" not in docs

    def test_finance_documents(self):
        """Test Finance has access to Finance Policy only."""
        docs = get_authorized_documents("Finance")
        assert "Finance_Policy.docx" in docs
        assert "HR_Policy.pdf" not in docs
        assert "Leave_Policy.pptx" not in docs
        assert "Termination_Policy_Scanned.pdf" not in docs
        assert "Employee_Salary_Records.xlsx" not in docs

    def test_admin_documents(self):
        """Test Admin has access to all documents."""
        docs = get_authorized_documents("Admin")
        assert len(docs) == 5
        all_docs = set()
        for role_docs in ROLE_DOCUMENTS.values():
            all_docs.update(role_docs)
        for doc in all_docs:
            assert doc in docs

    def test_is_document_authorized_true(self):
        """Test authorized check returns True for allowed documents."""
        assert is_document_authorized("Employee", "HR_Policy.pdf") is True
        assert is_document_authorized("HR", "Termination_Policy_Scanned.pdf") is True
        assert is_document_authorized("Finance", "Finance_Policy.docx") is True
        assert is_document_authorized("Admin", "Employee_Salary_Records.xlsx") is True

    def test_is_document_authorized_false(self):
        """Test authorized check returns False for disallowed documents."""
        assert is_document_authorized("Employee", "Finance_Policy.docx") is False
        assert is_document_authorized("Employee", "Employee_Salary_Records.xlsx") is False
        assert is_document_authorized("Finance", "HR_Policy.pdf") is False
        assert is_document_authorized("HR", "Finance_Policy.docx") is False

    def test_check_access_allowed(self):
        """Test check_access returns GRANTED for authorized access."""
        allowed, reason = check_access("Employee", "HR_Policy.pdf")
        assert allowed is True
        assert "GRANTED" in reason

    def test_check_access_denied(self):
        """Test check_access returns DENIED for unauthorized access."""
        allowed, reason = check_access("Employee", "Finance_Policy.docx")
        assert allowed is False
        assert "DENIED" in reason

    def test_get_authorized_metadata(self):
        """Test that metadata is returned for authorized documents."""
        meta_list = get_authorized_metadata("Employee")
        assert len(meta_list) == 2  # HR Policy + Leave Policy
        names = [m["name"] for m in meta_list]
        assert "HR Policy" in names
        assert "Leave Policy" in names

    def test_get_authorized_metadata_empty(self):
        """Test that unknown role gets empty metadata."""
        meta_list = get_authorized_metadata("UnknownRole")
        assert meta_list == []

    def test_all_roles_have_documents(self):
        """Test every role has at least one accessible document."""
        for role in ["Employee", "HR", "Finance", "Admin"]:
            docs = get_authorized_documents(role)
            assert len(docs) > 0, f"Role {role} has no documents!"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])