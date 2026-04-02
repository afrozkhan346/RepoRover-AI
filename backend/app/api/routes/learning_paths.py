from fastapi import APIRouter, HTTPException, Query

from app.schemas.learning_path import LearningPath, LearningPathCreate, LearningPathUpdate
from app.services.learning_paths import (
    create_learning_path,
    delete_learning_path,
    list_learning_paths,
    update_learning_path,
)

router = APIRouter()


@router.get("", response_model=list[LearningPath] | LearningPath)
def get_learning_paths(
    id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="orderIndex"),
    order: str = Query(default="asc", pattern="^(asc|desc)$"),
):
    try:
        return list_learning_paths(
            path_id=id,
            search=search,
            difficulty=difficulty,
            limit=limit,
            offset=offset,
            sort=sort,
            order=order,
        )
    except LookupError as error:
        raise HTTPException(status_code=404, detail={"detail": str(error), "code": "NOT_FOUND"}) from error


@router.post("", response_model=LearningPath, status_code=201)
def post_learning_path(payload: LearningPathCreate):
    return create_learning_path(payload)


@router.put("", response_model=LearningPath)
def put_learning_path(id: int = Query(..., ge=1), payload: LearningPathUpdate = ...):
    try:
        return update_learning_path(id, payload)
    except LookupError as error:
        raise HTTPException(status_code=404, detail={"detail": str(error), "code": "NOT_FOUND"}) from error


@router.delete("", status_code=204)
def delete_learning_path_route(id: int = Query(..., ge=1)):
    try:
        delete_learning_path(id)
    except LookupError as error:
        raise HTTPException(status_code=404, detail={"detail": str(error), "code": "NOT_FOUND"}) from error
