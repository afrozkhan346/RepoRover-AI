from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services.lessons import list_lessons

router = APIRouter()


@router.get("")
def get_lessons(
    id: int | None = Query(default=None),
    learningPathId: int | None = Query(default=None),
):
    try:
        lessons = list_lessons(lesson_id=id, learning_path_id=learningPathId)
        return lessons
    except LookupError as error:
        raise HTTPException(status_code=404, detail={"detail": str(error), "code": "NOT_FOUND"}) from error
