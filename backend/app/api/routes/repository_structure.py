from fastapi import APIRouter, HTTPException

from app.schemas.repository_structure import RepositoryStructureRequest, RepositoryStructureResponse
from app.services.repository_tree import build_repository_tree

router = APIRouter()


@router.post("/analyze-repo", response_model=RepositoryStructureResponse)
def analyze_repo(payload: RepositoryStructureRequest) -> RepositoryStructureResponse:
    try:
        ignored = set(payload.ignored_dirs) if payload.ignored_dirs else None
        tree = build_repository_tree(
            payload.local_path,
            ignored_dirs=ignored,
            max_nodes=payload.max_nodes,
            max_depth=payload.max_depth,
            include_errors=payload.include_errors,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "REPO_ANALYZE_ERROR"}) from error

    errors = tree.get("errors", []) if isinstance(tree.get("errors"), list) else []
    truncated = bool(tree.get("truncated", False))

    hierarchy = dict(tree)
    hierarchy.pop("errors", None)
    hierarchy.pop("truncated", None)

    return RepositoryStructureResponse(
        hierarchy=hierarchy,
        truncated=truncated,
        errors=errors,
    )
