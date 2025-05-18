from pydantic import BaseModel
from typing import Optional

class TokenRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SignUpRequest(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None  # refresh token for session renewal
    token_type: str = "bearer"


class UserInfo(BaseModel):
    preferred_username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
