from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.learning_path import LearningPath, LearningPathCreate, LearningPathUpdate


_SEEDED_LEARNING_PATHS: list[LearningPath] = [
    LearningPath(
        id=1,
        title="JavaScript Basics",
        description="Master the fundamentals of JavaScript programming including variables, functions, loops, and DOM manipulation",
        difficulty="beginner",
        estimated_hours=12,
        icon="🟨",
        order_index=1,
        created_at=datetime.now(timezone.utc).isoformat(),
    ),
    LearningPath(
        id=2,
        title="Python Fundamentals",
        description="Learn Python from scratch with hands-on exercises covering data types, control flow, functions, and object-oriented programming",
        difficulty="beginner",
        estimated_hours=15,
        icon="🐍",
        order_index=2,
        created_at=datetime.now(timezone.utc).isoformat(),
    ),
    LearningPath(
        id=3,
        title="React Mastery",
        description="Build modern web applications with React including hooks, state management, routing, and performance optimization",
        difficulty="intermediate",
        estimated_hours=20,
        icon="⚛️",
        order_index=3,
        created_at=datetime.now(timezone.utc).isoformat(),
    ),
]


def list_learning_paths(
    *,
    path_id: int | None = None,
    search: str | None = None,
    difficulty: str | None = None,
    limit: int = 10,
    offset: int = 0,
    sort: str = "orderIndex",
    order: str = "asc",
) -> list[LearningPath] | LearningPath:
    if path_id is not None:
        for item in _SEEDED_LEARNING_PATHS:
            if item.id == path_id:
                return item
        raise LookupError("Learning path not found")

    items = list(_SEEDED_LEARNING_PATHS)

    if search:
        search_lower = search.lower()
        items = [
            item for item in items
            if search_lower in item.title.lower() or (item.description and search_lower in item.description.lower())
        ]

    if difficulty:
        items = [item for item in items if item.difficulty == difficulty]

    sort_key_map = {
        "createdAt": lambda item: item.created_at,
        "title": lambda item: item.title,
        "difficulty": lambda item: item.difficulty,
        "estimatedHours": lambda item: item.estimated_hours,
        "orderIndex": lambda item: item.order_index,
    }
    sort_key = sort_key_map.get(sort, sort_key_map["orderIndex"])
    items.sort(key=sort_key, reverse=order == "desc")

    return items[offset : offset + limit]


def create_learning_path(payload: LearningPathCreate) -> LearningPath:
    next_id = max((item.id for item in _SEEDED_LEARNING_PATHS), default=0) + 1
    created = LearningPath(
        id=next_id,
        title=payload.title.strip(),
        description=payload.description.strip() if payload.description else None,
        difficulty=payload.difficulty.strip(),
        estimated_hours=payload.estimated_hours,
        icon=payload.icon.strip() if payload.icon else None,
        order_index=payload.order_index,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    _SEEDED_LEARNING_PATHS.append(created)
    return created


def update_learning_path(path_id: int, payload: LearningPathUpdate) -> LearningPath:
    for index, item in enumerate(_SEEDED_LEARNING_PATHS):
        if item.id != path_id:
            continue

        updated = item.model_copy(update={
            "title": payload.title.strip() if payload.title is not None else item.title,
            "description": payload.description.strip() if payload.description is not None else item.description,
            "difficulty": payload.difficulty.strip() if payload.difficulty is not None else item.difficulty,
            "estimated_hours": payload.estimated_hours if payload.estimated_hours is not None else item.estimated_hours,
            "icon": payload.icon.strip() if payload.icon is not None else item.icon,
            "order_index": payload.order_index if payload.order_index is not None else item.order_index,
        })
        _SEEDED_LEARNING_PATHS[index] = updated
        return updated

    raise LookupError("Learning path not found")


def delete_learning_path(path_id: int) -> None:
    for index, item in enumerate(_SEEDED_LEARNING_PATHS):
        if item.id == path_id:
            del _SEEDED_LEARNING_PATHS[index]
            return
    raise LookupError("Learning path not found")
