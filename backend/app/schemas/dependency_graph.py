from pydantic import BaseModel, Field


class DependencyGraphRequest(BaseModel):
    local_path: str = Field(..., min_length=1)
    max_files: int = Field(default=2000, ge=10, le=20000)


class DependencyNode(BaseModel):
    id: str
    node_type: str
    label: str


class DependencyEdge(BaseModel):
    source: str
    target: str
    edge_type: str


class DependencyGraphSummary(BaseModel):
    files_scanned: int
    import_edges: int
    package_nodes: int
    total_nodes: int
    total_edges: int


class DependencyGraphResponse(BaseModel):
    root: str
    nodes: list[DependencyNode]
    edges: list[DependencyEdge]
    summary: DependencyGraphSummary
