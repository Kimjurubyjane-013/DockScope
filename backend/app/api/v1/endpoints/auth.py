from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.security.jwt import create_access_token
from app.services.auth_service import AuthService, get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Register a new user account with a unique email and secure Argon2 password hashing.
    """
    auth_service = AuthService(db)
    user = await auth_service.register(user_in)
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Authenticate user and issue JWT / HttpOnly cookie",
)
async def login(
    credentials: UserLogin,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate user credentials, return a JWT access token, and set an HttpOnly
    authentication cookie for secure browser sessions.
    """
    auth_service = AuthService(db)
    user = await auth_service.authenticate(
        email=credentials.email,
        password=credentials.password,
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive.",
        )

    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(subject=str(user.id), expires_delta=expires_delta)
    max_age_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60

    # Set secure HttpOnly cookie for browser flow
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        max_age=max_age_seconds,
        httponly=True,
        samesite=settings.COOKIE_SAMESITE,
        secure=settings.COOKIE_SECURE,
        domain=settings.COOKIE_DOMAIN,
        path="/",
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        expires_in=max_age_seconds,
    )


@router.post("/logout", summary="Log out current session")
async def logout(response: Response) -> dict:
    """
    Clear the HttpOnly authentication cookie.
    """
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        path="/",
        domain=settings.COOKIE_DOMAIN,
    )
    return {"message": "Successfully logged out."}


@router.get(
    "/me",
    response_model=UserRead,
    summary="Retrieve current user profile",
)
async def get_me(current_user: User = Depends(get_current_user)) -> User:
    """
    Return the profile of the currently authenticated user.
    """
    return current_user
