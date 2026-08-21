"""Authentication module for the Enterprise RAG Assistant.

Security model:
  - Users authenticate with credentials → receive a signed bearer token.
  - The role is ALWAYS derived server-side from the token. The client never
    tells the server what role it has — this prevents privilege escalation
    (e.g., an Employee claiming to be Admin by editing the request body).
"""

import hashlib
import hmac
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

from backend.config import USERS, TOKEN_SECRET, TOKEN_TTL_HOURS

# Store active tokens: token -> {username, role, name, expires_at}
_tokens: dict[str, dict] = {}


def _sign(payload: str) -> str:
    """HMAC signature so tokens cannot be forged without the secret."""
    return hmac.new(TOKEN_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _generate_token(username: str) -> str:
    """Generate a signed token for the user."""
    random_part = secrets.token_hex(16)
    payload = f"{username}:{random_part}"
    sig = _sign(payload)
    return f"{payload}.{sig}"


def _verify_token_signature(token: str) -> bool:
    """Verify the token's HMAC signature to prevent forgery."""
    try:
        payload, sig = token.rsplit(".", 1)
        expected = _sign(payload)
        return hmac.compare_digest(sig, expected)
    except (ValueError, TypeError):
        return False


def authenticate(username: str, password: str) -> Optional[dict]:
    """Authenticate a user with username + password.

    Returns a dict with access_token, role, name on success, else None.
    Only users defined in the server-side USERS registry can authenticate.
    """
    if not username or not password:
        return None

    user = USERS.get(username)
    if not user:
        return None

    # Constant-time comparison to avoid timing attacks
    if not hmac.compare_digest(user["password"], password):
        return None

    token = _generate_token(username)
    _tokens[token] = {
        "username": username,
        "role": user["role"],
        "name": user["name"],
        "expires_at": time.time() + TOKEN_TTL_HOURS * 3600,
    }
    return {
        "access_token": token,
        "role": user["role"],
        "name": user["name"],
    }


def validate_token(token: str) -> Optional[dict]:
    """Validate a token and return the user info (role derived server-side).

    Returns None if the token is invalid, expired, or forged.
    """
    if not token or not isinstance(token, str):
        return None

    # Reject forged tokens (bad HMAC signature)
    if not _verify_token_signature(token):
        return None

    token_data = _tokens.get(token)
    if not token_data:
        return None

    if time.time() > token_data["expires_at"]:
        del _tokens[token]
        return None

    return {
        "username": token_data["username"],
        "role": token_data["role"],
        "name": token_data["name"],
    }


def logout(token: str) -> bool:
    """Invalidate a token (server-side session removal)."""
    if token in _tokens:
        del _tokens[token]
        return True
    return False