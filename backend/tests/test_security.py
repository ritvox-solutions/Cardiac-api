"""Tests for authentication primitives."""

from app.core import security


def test_password_hashing_and_token_round_trip(monkeypatch) -> None:
    """Passwords verify without storing plaintext and tokens identify users."""
    monkeypatch.setattr(security.settings, "AUTH_SECRET", "t" * 32)
    encoded = security.hash_password("correct horse battery staple")

    assert encoded != "correct horse battery staple"
    assert security.verify_password("correct horse battery staple", encoded)
    assert not security.verify_password("wrong password", encoded)
    assert security.decode_access_token(security.create_access_token("USER_1")) == "USER_1"
