from fastapi import APIRouter, HTTPException

from app.schemas.ai_explanation import AIExplanationRequest, AIExplanationResponse
from app.schemas.explainability_traces import ExplainabilityTraceRequest, ExplainabilityTraceResponse
from app.schemas.project_summaries import ProjectSummariesRequest, ProjectSummariesResponse
from app.schemas.quality_analysis import QualityAnalysisRequest, QualityAnalysisResponse
from app.schemas.risk_scoring import RiskScoringRequest, RiskScoringResponse
from app.services.explainability_trace_service import build_explainability_traces
from app.services.project_summary_service import summarize_project
from app.services.quality_analysis_service import analyze_quality
from app.services.risk_scoring_service import score_risk
from app.services.ai_explanation import explain_code

router = APIRouter()


@router.post("/explain-code", response_model=AIExplanationResponse)
def explain_code_route(payload: AIExplanationRequest) -> dict:
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail={"detail": "Code is required", "code": "MISSING_CODE"})
    return explain_code(payload.code, payload.language, payload.question)


@router.get("/explain-code", response_model=AIExplanationResponse)
def ai_service_health() -> dict:
    return {
        "explanation": "AI explanation service is active with PyTorch/HuggingFace/spaCy pipeline and deterministic fallback.",
        "language": None,
        "timestamp": __import__("datetime").datetime.utcnow().isoformat(),
        "pipeline": "health-check",
        "model": None,
        "complexity_score": None,
        "key_concepts": [],
    }


@router.post("/project-summaries", response_model=ProjectSummariesResponse)
def project_summaries_route(payload: ProjectSummariesRequest) -> ProjectSummariesResponse:
    try:
        return summarize_project(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "PROJECT_SUMMARY_ERROR"}) from error


@router.post("/quality-analysis", response_model=QualityAnalysisResponse)
def quality_analysis_route(payload: QualityAnalysisRequest) -> QualityAnalysisResponse:
    try:
        return analyze_quality(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "QUALITY_ANALYSIS_ERROR"}) from error


@router.post("/risk-scoring", response_model=RiskScoringResponse)
def risk_scoring_route(payload: RiskScoringRequest) -> RiskScoringResponse:
    try:
        return score_risk(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "RISK_SCORING_ERROR"}) from error


@router.post("/explainability-traces", response_model=ExplainabilityTraceResponse)
def explainability_traces_route(payload: ExplainabilityTraceRequest) -> ExplainabilityTraceResponse:
    try:
        return build_explainability_traces(
            local_path=payload.local_path,
            max_files=payload.max_files,
            focus_file=payload.focus_file,
            graph_type=payload.graph_type,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "EXPLAINABILITY_TRACE_ERROR"}) from error
