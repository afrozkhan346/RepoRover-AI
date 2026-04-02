from pydantic import BaseModel, Field


class QualityAnalysisRequest(BaseModel):
    local_path: str = Field(..., min_length=1)
    max_files: int = Field(default=2000, ge=10, le=20000)


class QualityIssue(BaseModel):
    severity: str
    category: str
    file_path: str | None = None
    detail: str
    recommendation: str


class QualityAnalysisResponse(BaseModel):
    overall_score: float
    issues: list[QualityIssue]
    design_gaps: list[str]
    summary: str
