from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models import Account, Session as AuthSession, User

PASSWORD_ALGORITHM = "pbkdf2_sha256"
PASSWORD_ITERATIONS = 200_000
SESSION_DAYS = 30


@dataclass(frozen=True)
class AuthResult:
    token: str
    user: User


@dataclass(frozen=True)
class AuthSessionResult:
    token: str | None
    user: User | None


def _now() -> datetime:
    return datetime.now(UTC)


def _coerce_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def hash_password(password: str) -> str:
    salt = base64.urlsafe_b64encode(uuid4().bytes).decode("utf-8").rstrip("=")
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PASSWORD_ITERATIONS,
    )
    digest = base64.urlsafe_b64encode(derived).decode("utf-8").rstrip("=")
    return f"{PASSWORD_ALGORITHM}${PASSWORD_ITERATIONS}${salt}${digest}"


def verify_password(password: str, encoded_password: str | None) -> bool:
    if not encoded_password:
        return False

    try:
        algorithm, iterations_text, salt, stored_digest = encoded_password.split("$", 3)
    except ValueError:
        return False

    if algorithm != PASSWORD_ALGORITHM:
        return False

    try:
        iterations = int(iterations_text)
    except ValueError:
        return False

    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        iterations,
    )
    computed_digest = base64.urlsafe_b64encode(derived).decode("utf-8").rstrip("=")
    return hmac.compare_digest(computed_digest, stored_digest)


def _build_user_payload(user: User) -> User:
    return user


def _create_session(db: Session, user: User) -> str:
    token = uuid4().hex
    now = _now()
    expires_at = now + timedelta(days=SESSION_DAYS)

    session = AuthSession(
        id=uuid4().hex,
        expires_at=expires_at,
        token=token,
        created_at=now,
        updated_at=now,
        ip_address=None,
        user_agent=None,
        user_id=user.id,
    )
    db.add(session)
    db.commit()
    return token


def _account_password_exists(db: Session, email: str) -> bool:
    normalized = _normalize_email(email)
    return db.query(Account).filter(Account.provider_id == "credentials", Account.account_id == normalized).first() is not None


def register_user(db: Session, name: str, email: str, password: str) -> AuthResult:
    normalized_email = _normalize_email(email)
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise ValueError("USER_ALREADY_EXISTS")

    now = _now()
    user = User(
        id=uuid4().hex,
        name=name.strip(),
        email=normalized_email,
        email_verified=False,
        image=None,
        created_at=now,
        updated_at=now,
    )
    account = Account(
        id=uuid4().hex,
        account_id=normalized_email,
        provider_id="credentials",
        user_id=user.id,
        access_token=None,
        refresh_token=None,
        id_token=None,
        access_token_expires_at=None,
        refresh_token_expires_at=None,
        scope=None,
        password=hash_password(password),
        created_at=now,
        updated_at=now,
    )

    db.add(user)
    db.add(account)
    db.commit()
    db.refresh(user)

    token = _create_session(db, user)
    return AuthResult(token=token, user=_build_user_payload(user))


def authenticate_user(db: Session, email: str, password: str) -> AuthResult:
    normalized_email = _normalize_email(email)
    user = db.query(User).filter(User.email == normalized_email).first()
    if not user:
        raise ValueError("INVALID_CREDENTIALS")

    account = (
        db.query(Account)
        .filter(Account.user_id == user.id, Account.provider_id == "credentials")
        .first()
    )
    if not account or not verify_password(password, account.password):
        raise ValueError("INVALID_CREDENTIALS")

    token = _create_session(db, user)
    return AuthResult(token=token, user=_build_user_payload(user))


def get_user_by_session_token(db: Session, token: str) -> AuthSessionResult:
    session = (
        db.query(AuthSession)
        .filter(AuthSession.token == token)
        .order_by(AuthSession.created_at.desc())
        .first()
    )
    if not session:
        return AuthSessionResult(token=None, user=None)

    if _coerce_utc(session.expires_at) <= _now():
        db.delete(session)
        db.commit()
        return AuthSessionResult(token=None, user=None)

    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        return AuthSessionResult(token=None, user=None)

    return AuthSessionResult(token=session.token, user=_build_user_payload(user))


def logout_session(db: Session, token: str) -> None:
    session = db.query(AuthSession).filter(AuthSession.token == token).first()
    if session:
        db.delete(session)
        db.commit()
