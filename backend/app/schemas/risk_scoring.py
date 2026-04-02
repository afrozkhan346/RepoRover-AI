from pydantic import BaseModel, Field


class RiskScoringRequest(BaseModel):
    local_path: str = Field(..., min_length=1)
    max_files: int = Field(default=2000, ge=10, le=20000)


class SeverityDistribution(BaseModel):
    high: int
    medium: int
    low: int


class RiskSignal(BaseModel):
    title: str
    weight: float
    detail: str


class RiskScoringResponse(BaseModel):
    reliability_score: float
    risk_score: float
    severity_distribution: SeverityDistribution
    top_signals: list[RiskSignal]
    summary: str
