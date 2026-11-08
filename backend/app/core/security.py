"""Password hashing and signed bearer-token helpers."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets

import jwt
from fastapi import HTTPException, status

from app.core.config import settings


def _secret() -> str:
    """Return the configured signing secret or fail closed."""
    if len(settings.AUTH_SECRET) < 32:
        raise HTTPException(
            status_code=500,
            detail="AUTH_SECRET must contain at least 32 characters",
        )
    return settings.AUTH_SECRET


def hash_password(password: str) -> str:
    """Hash a password with a per-password salt using PBKDF2-HMAC-SHA256."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded: str) -> bool:
    """Verify a plaintext password against a stored PBKDF2 hash."""
    try:
        salt_hex, digest_hex = encoded.split("$", 1)
        expected = bytes.fromhex(digest_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 310_000)
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(actual, expected)


def create_access_token(user_id: str) -> str:
    """Create an expiring JWT containing the authenticated user id."""
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.AUTH_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({"sub": user_id, "exp": expires}, _secret(), algorithm="HS256")


def decode_access_token(token: str) -> str:
    """Validate a bearer JWT and return its user id."""
    try:
        payload = jwt.decode(token, _secret(), algorithms=["HS256"])
        user_id = payload.get("sub")
        if not isinstance(user_id, str) or not user_id:
            raise ValueError
        return user_id
    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
