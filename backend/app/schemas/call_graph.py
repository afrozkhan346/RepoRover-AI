from pydantic import BaseModel, Field


class CallGraphRequest(BaseModel):
    local_path: str = Field(..., min_length=1)
    max_files: int = Field(default=2000, ge=10, le=20000)


class CallGraphNode(BaseModel):
    id: str
    node_type: str
    label: str
    file_path: str | None = None


class CallGraphEdge(BaseModel):
    source: str
    target: str
    edge_type: str


class CallGraphSummary(BaseModel):
    files_scanned: int
    functions_found: int
    call_edges: int
    import_context_edges: int
    total_nodes: int
    total_edges: int


class CallGraphResponse(BaseModel):
    root: str
    nodes: list[CallGraphNode]
    edges: list[CallGraphEdge]
    summary: CallGraphSummary
