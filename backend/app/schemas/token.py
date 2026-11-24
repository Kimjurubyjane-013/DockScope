from typing import Optional
from pydantic import BaseModel, Field


class Token(BaseModel):
    access_token: str = Field(..., description="JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")


class TokenPayload(BaseModel):
    sub: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
