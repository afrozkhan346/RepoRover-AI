from fastapi import APIRouter, HTTPException

from app.schemas.call_graph import CallGraphRequest, CallGraphResponse
from app.services.call_graph_service import build_call_graph

router = APIRouter()


@router.post("/from-path", response_model=CallGraphResponse)
def call_graph_from_path(payload: CallGraphRequest) -> CallGraphResponse:
    try:
        return build_call_graph(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "CALL_GRAPH_ERROR"}) from error
