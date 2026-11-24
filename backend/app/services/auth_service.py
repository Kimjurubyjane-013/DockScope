from typing import Optional
import uuid
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.logging import logger
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate
from app.security.jwt import decode_access_token, get_token_from_request
from app.security.password import hash_password, verify_password


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(self, user_in: UserCreate) -> User:
        clean_email = user_in.email.lower().strip()
        existing_user = await self.user_repo.get_by_email(clean_email)
        if existing_user:
            logger.warning(f"Registration failed: Email '{clean_email}' already registered.")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists.",
            )

        hashed_pw = hash_password(user_in.password)
        new_user = await self.user_repo.create_user(
            email=clean_email,
            hashed_password=hashed_pw,
        )
        logger.info(f"User successfully registered: {new_user.id} ({clean_email})")
        return new_user

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        clean_email = email.lower().strip()
        user = await self.user_repo.get_by_email(clean_email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user


async def get_current_user(
    token: Optional[str] = Depends(get_token_from_request),
    db: AsyncSession = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials or session expired.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not token:
        raise credentials_exception

    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise credentials_exception

    try:
        user_id = uuid.UUID(payload["sub"])
    except (ValueError, TypeError):
        raise credentials_exception

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise credentials_exception

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated.",
        )

    return user
