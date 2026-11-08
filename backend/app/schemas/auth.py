"""Authentication request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class RegisterInput(BaseModel):
    """New account credentials and display name."""

    name: str = Field(..., min_length=1, max_length=128)
    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=8, max_length=128)


class LoginInput(BaseModel):
    """Account credentials used to obtain a bearer token."""

    email: str = Field(..., min_length=3, max_length=320)
    password: str = Field(..., min_length=1, max_length=128)


class AuthUser(BaseModel):
    """Authenticated account summary returned to the mobile app."""

    id: str
    name: str
    email: str
    created_at: datetime


class AuthResponse(BaseModel):
    """Bearer token and authenticated account summary."""

    token: str
    user: AuthUser
