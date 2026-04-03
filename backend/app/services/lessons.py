from __future__ import annotations

from datetime import datetime, timezone

from app.schemas.learning_path import LearningPath

_SEEDED_LESSONS: list[dict[str, object]] = [
    {
        "id": 1,
        "learning_path_id": 1,
        "title": "Variables and Data Types",
        "description": "Learn how to store and work with values in JavaScript.",
        "content": "Introduction to variables, strings, numbers, and booleans.",
        "difficulty": "beginner",
        "xp_reward": 50,
        "estimated_minutes": 18,
        "order_index": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": 2,
        "learning_path_id": 1,
        "title": "Functions and Scope",
        "description": "Understand reusable functions and variable scope.",
        "content": "Function declarations, parameters, returns, and block scope.",
        "difficulty": "beginner",
        "xp_reward": 65,
        "estimated_minutes": 22,
        "order_index": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": 3,
        "learning_path_id": 2,
        "title": "Python Syntax Basics",
        "description": "Get comfortable with Python syntax and indentation.",
        "content": "Python variables, control flow, and function definitions.",
        "difficulty": "beginner",
        "xp_reward": 55,
        "estimated_minutes": 20,
        "order_index": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": 4,
        "learning_path_id": 2,
        "title": "Objects and Modules",
        "description": "Work with Python modules and object-oriented design.",
        "content": "Importing modules, building classes, and organizing code.",
        "difficulty": "intermediate",
        "xp_reward": 70,
        "estimated_minutes": 26,
        "order_index": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": 5,
        "learning_path_id": 3,
        "title": "React Components",
        "description": "Build reusable user interfaces with React components.",
        "content": "JSX, props, state, and component composition.",
        "difficulty": "intermediate",
        "xp_reward": 80,
        "estimated_minutes": 30,
        "order_index": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
    {
        "id": 6,
        "learning_path_id": 3,
        "title": "Hooks and Data Flow",
        "description": "Use hooks to manage state and side effects.",
        "content": "useState, useEffect, and structured data flow in React.",
        "difficulty": "intermediate",
        "xp_reward": 90,
        "estimated_minutes": 34,
        "order_index": 2,
        "created_at": datetime.now(timezone.utc).isoformat(),
    },
]


def list_lessons(*, lesson_id: int | None = None, learning_path_id: int | None = None) -> list[dict[str, object]] | dict[str, object]:
    items = list(_SEEDED_LESSONS)

    if learning_path_id is not None:
        items = [item for item in items if item["learning_path_id"] == learning_path_id]

    if lesson_id is not None:
        for item in items:
            if item["id"] == lesson_id:
                return item
        raise LookupError("Lesson not found")

    items.sort(key=lambda item: (item["learning_path_id"], item["order_index"]))
    return items
