"""Tests for authentication module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.auth import authenticate, validate_token, logout


class TestAuthentication:
    """Test suite for authentication functionality."""

    def test_valid_login_employee(self):
        """Test that valid Employee credentials are accepted."""
        result = authenticate("emp001", "Emp@123")
        assert result is not None
        assert result["role"] == "Employee"
        assert result["name"] == "Employee User"
        assert "access_token" in result

    def test_valid_login_hr(self):
        """Test that valid HR credentials are accepted."""
        result = authenticate("hr001", "HR@123")
        assert result is not None
        assert result["role"] == "HR"

    def test_valid_login_finance(self):
        """Test that valid Finance credentials are accepted."""
        result = authenticate("fin001", "Fin@123")
        assert result is not None
        assert result["role"] == "Finance"

    def test_valid_login_admin(self):
        """Test that valid Admin credentials are accepted."""
        result = authenticate("admin001", "Admin@123")
        assert result is not None
        assert result["role"] == "Admin"

    def test_invalid_password(self):
        """Test that wrong password is rejected."""
        result = authenticate("emp001", "wrong_password")
        assert result is None

    def test_invalid_username(self):
        """Test that unknown username is rejected."""
        result = authenticate("unknown", "Pass@123")
        assert result is None

    def test_empty_credentials(self):
        """Test that empty credentials are rejected."""
        result = authenticate("", "")
        assert result is None

    def test_token_validation(self):
        """Test that a valid token is accepted."""
        auth_result = authenticate("emp001", "Emp@123")
        token = auth_result["access_token"]
        user_info = validate_token(token)
        assert user_info is not None
        assert user_info["username"] == "emp001"
        assert user_info["role"] == "Employee"

    def test_invalid_token(self):
        """Test that an invalid token is rejected."""
        user_info = validate_token("invalid_token_12345")
        assert user_info is None

    def test_logout(self):
        """Test that logout invalidates the token."""
        auth_result = authenticate("emp001", "Emp@123")
        token = auth_result["access_token"]

        # Token should be valid before logout
        assert validate_token(token) is not None

        # Logout
        assert logout(token) is True

        # Token should be invalid after logout
        assert validate_token(token) is None

    def test_logout_invalid_token(self):
        """Test logout with invalid token."""
        assert logout("nonexistent_token") is False


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])