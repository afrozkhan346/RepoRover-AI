from fastapi import APIRouter, HTTPException

from app.engine.graph_builder import GraphBuilderEngine
from app.schemas.call_graph import CallGraphAnalytics, CallGraphRequest, CallGraphResponse

router = APIRouter()
graph_builder_engine = GraphBuilderEngine()


@router.post("/from-path", response_model=CallGraphResponse)
def call_graph_from_path(payload: CallGraphRequest) -> CallGraphResponse:
    try:
        return graph_builder_engine.call_graph(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "CALL_GRAPH_ERROR"}) from error


@router.post("/analytics", response_model=CallGraphAnalytics)
def call_graph_analytics_from_path(payload: CallGraphRequest) -> CallGraphAnalytics:
    try:
        return graph_builder_engine.call_graph_analytics(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "CALL_GRAPH_ANALYTICS_ERROR"}) from error
