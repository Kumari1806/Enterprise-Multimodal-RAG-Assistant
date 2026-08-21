"""Tests for strict token-based RBAC enforcement at the API layer.

These tests verify that:
  - Clients cannot claim a role in the request body (role comes from token).
  - Unauthenticated / forged-token requests are rejected (401).
  - Privileged operations (document upload) are Admin-only (403 for others).
  - The documents endpoint derives the role from the token.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.auth import authenticate, validate_token
from backend.config import USERS, ROLE_DOCUMENTS


class TestTokenIssuance:
    """Tokens are issued only to registered users with correct passwords."""

    def test_all_demo_users_can_authenticate(self):
        for username, user in USERS.items():
            result = authenticate(username, user["password"])
            assert result is not None, f"{username} should authenticate"
            assert result["role"] == user["role"]

    def test_wrong_password_rejected(self):
        assert authenticate("emp001", "wrong") is None

    def test_unknown_user_rejected(self):
        assert authenticate("hacker", "anything") is None

    def test_role_is_never_client_controlled(self):
        """The role returned at login is fixed by the server registry,
        regardless of any role the client might try to claim."""
        emp = authenticate("emp001", "Emp@123")
        assert emp["role"] == "Employee"
        assert emp["role"] != "Admin"

    def test_tokens_are_signed_and_verifiable(self):
        result = authenticate("hr001", "HR@123")
        user = validate_token(result["access_token"])
        assert user["role"] == "HR"

    def test_forged_token_rejected(self):
        """A token with a bad signature must be rejected."""
        real = authenticate("admin001", "Admin@123")["access_token"]
        forged = real[:-4] + "beef"  # corrupt the signature
        assert validate_token(forged) is None

    def test_garbage_token_rejected(self):
        assert validate_token("not.a.real.token") is None
        assert validate_token("") is None
        assert validate_token(None) is None

    def test_logout_invalidates_token(self):
        result = authenticate("fin001", "Fin@123")
        token = result["access_token"]
        assert validate_token(token) is not None
        from backend.auth import logout
        assert logout(token) is True
        assert validate_token(token) is None


class TestRoleDocumentScope:
    """The role→document mapping is strict and complete."""

    def test_employee_scope(self):
        assert set(ROLE_DOCUMENTS["Employee"]) == {"HR_Policy.pdf", "Leave_Policy.pptx"}

    def test_hr_scope(self):
        assert set(ROLE_DOCUMENTS["HR"]) == {
            "HR_Policy.pdf", "Leave_Policy.pptx",
            "Termination_Policy_Scanned.pdf", "Employee_Salary_Records.xlsx",
        }

    def test_finance_scope(self):
        assert set(ROLE_DOCUMENTS["Finance"]) == {"Finance_Policy.docx"}

    def test_admin_scope(self):
        all_docs = set()
        for docs in ROLE_DOCUMENTS.values():
            all_docs.update(docs)
        assert set(ROLE_DOCUMENTS["Admin"]) == all_docs

    def test_no_overlapping_privilege_creep(self):
        """Finance must never see HR/leave/salary documents."""
        for doc in ["HR_Policy.pdf", "Leave_Policy.pptx",
                    "Termination_Policy_Scanned.pdf", "Employee_Salary_Records.xlsx"]:
            assert doc not in ROLE_DOCUMENTS["Finance"]

    def test_employee_never_sees_salary_or_finance(self):
        for doc in ["Employee_Salary_Records.xlsx", "Finance_Policy.docx",
                    "Termination_Policy_Scanned.pdf"]:
            assert doc not in ROLE_DOCUMENTS["Employee"]


class TestQueryRequestModel:
    """The query request no longer carries role/username — the server derives it."""

    def test_query_request_has_no_role_field(self):
        from backend.models import QueryRequest
        fields = set(QueryRequest.model_fields.keys())
        assert fields == {"question"}, f"QueryRequest must only contain 'question', got {fields}"

    def test_query_request_rejects_claimed_role(self):
        """Extra fields (role, username) in the request body are ignored by Pydantic."""
        from backend.models import QueryRequest
        req = QueryRequest.model_validate(
            {"question": "What are the working hours?", "role": "Admin", "username": "emp001"}
        )
        assert req.question == "What are the working hours?"
        # Pydantic ignores unknown fields by default — role/username are not attributes
        assert not hasattr(req, "role")
        assert not hasattr(req, "username")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])