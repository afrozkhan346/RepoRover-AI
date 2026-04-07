from pydantic import BaseModel, Field


class AIExplanationRequest(BaseModel):
    code: str = Field(..., min_length=1)
    language: str | None = None
    question: str | None = None


class ExplanationEvidence(BaseModel):
    kind: str
    label: str
    excerpt: str
    start_point: tuple[int, int] | None = None
    end_point: tuple[int, int] | None = None
    related_symbols: list[str] = Field(default_factory=list)
    note: str | None = None


class AIExplanationResponse(BaseModel):
    explanation: str
    language: str | None = None
    timestamp: str
    pipeline: str | None = None
    model: str | None = None
    complexity_score: float | None = None
    key_concepts: list[str] = Field(default_factory=list)
    named_entities: list[str] = Field(default_factory=list)
    evidence: list[ExplanationEvidence] = Field(default_factory=list)
