from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db.models import Achievement, UserAchievement
from app.db.session import SessionLocal
from app.schemas.common import APIError
from app.services.auth_service import get_user_by_session_token

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_token(authorization: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization.split(" ", 1)[1].strip()
    return None


def _require_user(authorization: str | None, db: Session):
    token = _get_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail={"detail": "Authentication required", "code": "UNAUTHORIZED"})

    result = get_user_by_session_token(db, token)
    if not result.user:
        raise HTTPException(status_code=401, detail={"detail": "Invalid session", "code": "UNAUTHORIZED"})

    return result.user


@router.get("")
def list_achievements():
    db = SessionLocal()
    try:
        achievements = db.query(Achievement).order_by(Achievement.id.asc()).all()
        return {
            "achievements": [
                {
                    "id": achievement.id,
                    "title": achievement.title,
                    "description": achievement.description,
                    "icon": achievement.icon,
                    "xp_reward": achievement.xp_reward,
                    "requirement": f"{achievement.requirement_type}: {achievement.requirement_value}",
                }
                for achievement in achievements
            ]
        }
    finally:
        db.close()


@router.get("/user")
def list_user_achievements(authorization: str | None = Header(default=None), db: Session = Depends(get_db)):
    user = _require_user(authorization, db)

    user_achievements = (
        db.query(UserAchievement)
        .filter(UserAchievement.user_id == user.id)
        .order_by(UserAchievement.earned_at.desc())
        .all()
    )

    return {
        "achievements": [
            {
                "id": entry.id,
                "user_id": entry.user_id,
                "achievement_id": entry.achievement_id,
                "earned_at": entry.earned_at,
                "created_at": entry.created_at,
            }
            for entry in user_achievements
        ]
    }
