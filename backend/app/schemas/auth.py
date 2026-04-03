from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class AuthUser(BaseModel):
    id: str
    name: str
    email: EmailStr
    email_verified: bool
    image: str | None = None
    created_at: str
    updated_at: str


class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class AuthSessionResponse(BaseModel):
    token: str
    user: AuthUser


class SessionResponse(BaseModel):
    user: AuthUser | None = None
    token: str | None = None
