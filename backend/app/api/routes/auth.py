from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.schemas.auth import AuthSessionResponse, LoginRequest, RegisterRequest, SessionResponse
from app.services.auth_service import authenticate_user, get_user_by_session_token, logout_session, register_user

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _build_auth_session_response(token: str, user) -> AuthSessionResponse:
    return AuthSessionResponse(
        token=token,
        user=AuthSessionResponse.model_validate({"token": token, "user": user}).user,
    )


@router.post("/register", response_model=AuthSessionResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        result = register_user(db, payload.name, payload.email, payload.password)
        return AuthSessionResponse.model_validate({
            "token": result.token,
            "user": {
                "id": result.user.id,
                "name": result.user.name,
                "email": result.user.email,
                "email_verified": result.user.email_verified,
                "image": result.user.image,
                "created_at": result.user.created_at.isoformat() if hasattr(result.user.created_at, "isoformat") else str(result.user.created_at),
                "updated_at": result.user.updated_at.isoformat() if hasattr(result.user.updated_at, "isoformat") else str(result.user.updated_at),
            },
        })
    except ValueError as error:
        code = str(error)
        status = 409 if code == "USER_ALREADY_EXISTS" else 400
        raise HTTPException(status_code=status, detail={"detail": "User already exists", "code": code}) from error


@router.post("/login", response_model=AuthSessionResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        result = authenticate_user(db, payload.email, payload.password)
        return AuthSessionResponse.model_validate({
            "token": result.token,
            "user": {
                "id": result.user.id,
                "name": result.user.name,
                "email": result.user.email,
                "email_verified": result.user.email_verified,
                "image": result.user.image,
                "created_at": result.user.created_at.isoformat() if hasattr(result.user.created_at, "isoformat") else str(result.user.created_at),
                "updated_at": result.user.updated_at.isoformat() if hasattr(result.user.updated_at, "isoformat") else str(result.user.updated_at),
            },
        })
    except ValueError as error:
        raise HTTPException(status_code=401, detail={"detail": "Invalid email or password", "code": str(error)}) from error


@router.get("/session", response_model=SessionResponse)
def session(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    token = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()

    if not token:
        return SessionResponse(user=None, token=None)

    result = get_user_by_session_token(db, token)
    if not result.user:
        return SessionResponse(user=None, token=None)

    return SessionResponse(
        user={
            "id": result.user.id,
            "name": result.user.name,
            "email": result.user.email,
            "email_verified": result.user.email_verified,
            "image": result.user.image,
            "created_at": result.user.created_at.isoformat() if hasattr(result.user.created_at, "isoformat") else str(result.user.created_at),
            "updated_at": result.user.updated_at.isoformat() if hasattr(result.user.updated_at, "isoformat") else str(result.user.updated_at),
        },
        token=result.token,
    )


@router.post("/logout")
def logout(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        logout_session(db, token)
    return {"message": "Signed out"}
