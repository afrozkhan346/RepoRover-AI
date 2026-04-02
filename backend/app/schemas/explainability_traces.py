from pydantic import BaseModel, Field


class ExplainabilityTraceRequest(BaseModel):
    local_path: str = Field(..., min_length=1)
    max_files: int = Field(default=2000, ge=10, le=20000)
    focus_file: str | None = None
    graph_type: str = Field(default="call")


class FindingTrace(BaseModel):
    finding_id: str
    title: str
    severity: str
    evidence_type: str
    evidence: str


class TokenTrace(BaseModel):
    finding_id: str
    file_path: str
    token_type: str
    lexeme: str
    start_point: tuple[int, int]
    end_point: tuple[int, int]


class AstTrace(BaseModel):
    finding_id: str
    file_path: str
    unit_type: str
    name: str | None
    start_point: tuple[int, int]
    end_point: tuple[int, int]


class GraphTrace(BaseModel):
    finding_id: str
    graph_type: str
    start_node: str
    path: list[str]


class ExplainabilityTraceResponse(BaseModel):
    focus_file: str
    findings: list[FindingTrace]
    token_traces: list[TokenTrace]
    ast_traces: list[AstTrace]
    graph_traces: list[GraphTrace]
    summary: str
