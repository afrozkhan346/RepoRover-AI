from fastapi import APIRouter, HTTPException

from app.schemas.graph_analysis import GraphAnalysisRequest, GraphAnalysisResponse
from app.services.graph_analysis_service import analyze_graph

router = APIRouter()


@router.post("/from-path", response_model=GraphAnalysisResponse)
def graph_analysis_from_path(payload: GraphAnalysisRequest) -> GraphAnalysisResponse:
    try:
        return analyze_graph(
            local_path=payload.local_path,
            graph_type=payload.graph_type,
            max_files=payload.max_files,
            traversal_start=payload.traversal_start,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "GRAPH_ANALYSIS_ERROR"}) from error
