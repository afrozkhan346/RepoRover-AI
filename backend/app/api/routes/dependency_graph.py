from fastapi import APIRouter, HTTPException

from app.schemas.dependency_graph import DependencyGraphRequest, DependencyGraphResponse
from app.services.dependency_graph_service import build_dependency_graph

router = APIRouter()


@router.post("/from-path", response_model=DependencyGraphResponse)
def dependency_graph_from_path(payload: DependencyGraphRequest) -> DependencyGraphResponse:
    try:
        return build_dependency_graph(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "DEPENDENCY_GRAPH_ERROR"}) from error
