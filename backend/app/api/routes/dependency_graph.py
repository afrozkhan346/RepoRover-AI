from fastapi import APIRouter, HTTPException

from app.engine.graph_builder import GraphBuilderEngine
from app.schemas.dependency_graph import DependencyGraphRequest, DependencyGraphResponse

router = APIRouter()
graph_builder_engine = GraphBuilderEngine()


@router.post("/from-path", response_model=DependencyGraphResponse)
def dependency_graph_from_path(payload: DependencyGraphRequest) -> DependencyGraphResponse:
    try:
        return graph_builder_engine.dependency_graph(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "DEPENDENCY_GRAPH_ERROR"}) from error
