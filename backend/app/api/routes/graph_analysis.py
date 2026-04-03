from fastapi import APIRouter, HTTPException

from app.engine.graph_builder import GraphBuilderEngine
from app.schemas.graph_analysis import GraphAnalysisRequest, GraphAnalysisResponse

router = APIRouter()
graph_builder_engine = GraphBuilderEngine()


@router.post("/from-path", response_model=GraphAnalysisResponse)
def graph_analysis_from_path(payload: GraphAnalysisRequest) -> GraphAnalysisResponse:
    try:
        return graph_builder_engine.graph_analysis(
            local_path=payload.local_path,
            graph_type=payload.graph_type,
            max_files=payload.max_files,
            traversal_start=payload.traversal_start,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "GRAPH_ANALYSIS_ERROR"}) from error
