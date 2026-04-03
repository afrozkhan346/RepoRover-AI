from fastapi import APIRouter, HTTPException

from app.engine.ai_nlp import AINLPEngine
from app.engine.explanation_engine import ExplanationEngine
from app.schemas.ai_explanation import AIExplanationRequest, AIExplanationResponse
from app.schemas.explainability_traces import ExplainabilityTraceRequest, ExplainabilityTraceResponse
from app.schemas.project_summaries import ProjectSummariesRequest, ProjectSummariesResponse
from app.schemas.quality_analysis import QualityAnalysisRequest, QualityAnalysisResponse
from app.schemas.risk_scoring import RiskScoringRequest, RiskScoringResponse

router = APIRouter()
ai_nlp_engine = AINLPEngine()
explanation_engine = ExplanationEngine()


@router.post("/explain-code", response_model=AIExplanationResponse)
def explain_code_route(payload: AIExplanationRequest) -> dict:
    if not payload.code.strip():
        raise HTTPException(status_code=400, detail={"detail": "Code is required", "code": "MISSING_CODE"})
    return ai_nlp_engine.explain_code(payload.code, payload.language, payload.question)


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
        return ai_nlp_engine.project_summaries(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "PROJECT_SUMMARY_ERROR"}) from error


@router.post("/quality-analysis", response_model=QualityAnalysisResponse)
def quality_analysis_route(payload: QualityAnalysisRequest) -> QualityAnalysisResponse:
    try:
        return ai_nlp_engine.quality_analysis(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "QUALITY_ANALYSIS_ERROR"}) from error


@router.post("/risk-scoring", response_model=RiskScoringResponse)
def risk_scoring_route(payload: RiskScoringRequest) -> RiskScoringResponse:
    try:
        return ai_nlp_engine.risk_scoring(payload.local_path, payload.max_files)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "RISK_SCORING_ERROR"}) from error


@router.post("/explainability-traces", response_model=ExplainabilityTraceResponse)
def explainability_traces_route(payload: ExplainabilityTraceRequest) -> ExplainabilityTraceResponse:
    try:
        return explanation_engine.explainability_traces(
            local_path=payload.local_path,
            max_files=payload.max_files,
            focus_file=payload.focus_file,
            graph_type=payload.graph_type,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "EXPLAINABILITY_TRACE_ERROR"}) from error
