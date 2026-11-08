"""Account registration and login endpoints."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db_session
from app.core.security import create_access_token, hash_password, verify_password
from app.models.postgres_models import AccountORM
from app.schemas.auth import AuthResponse, AuthUser, LoginInput, RegisterInput

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _response(account: AccountORM) -> AuthResponse:
    """Build the public authentication response for an account."""
    return AuthResponse(
        token=create_access_token(account.user_id),
        user=AuthUser(
            id=account.user_id,
            name=account.name,
            email=account.email,
            created_at=account.created_at,
        ),
    )


@router.post("/register", response_model=AuthResponse, status_code=201)
async def register(payload: RegisterInput, session: AsyncSession = Depends(get_db_session)) -> AuthResponse:
    """Create an account and return its first access token."""
    email = payload.email.strip().lower()
    result = await session.execute(select(AccountORM).where(AccountORM.email == email))
    if result.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    account = AccountORM(
        user_id=f"USER_{uuid4().hex[:12].upper()}",
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
    )
    session.add(account)
    await session.commit()
    await session.refresh(account)
    return _response(account)


@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginInput, session: AsyncSession = Depends(get_db_session)) -> AuthResponse:
    """Validate credentials and return an access token."""
    result = await session.execute(select(AccountORM).where(AccountORM.email == payload.email.strip().lower()))
    account = result.scalar_one_or_none()
    if account is None or not verify_password(payload.password, account.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return _response(account)
