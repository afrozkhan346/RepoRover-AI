from pydantic import BaseModel, Field


class ProjectSummariesRequest(BaseModel):
    local_path: str = Field(..., min_length=1)
    max_files: int = Field(default=2000, ge=10, le=20000)


class SummaryMetrics(BaseModel):
    files_scanned: int
    total_lines: int
    language_breakdown: dict[str, int]
    dependency_edges: int
    call_edges: int


class ProjectSummariesResponse(BaseModel):
    project_summary: str
    architecture_summary: str
    execution_flow_summary: str
    key_modules: list[str]
    key_dependencies: list[str]
    flow_path: list[str]
    metrics: SummaryMetrics
