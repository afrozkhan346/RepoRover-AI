from pydantic import BaseModel, Field


class GraphAnalysisRequest(BaseModel):
    local_path: str = Field(..., min_length=1)
    graph_type: str = Field(default="dependency")
    max_files: int = Field(default=2000, ge=10, le=20000)
    traversal_start: str | None = None


class RankedNode(BaseModel):
    node_id: str
    label: str
    score: float


class GraphMetrics(BaseModel):
    node_count: int
    edge_count: int
    connected_components: int


class TraversalResult(BaseModel):
    start_node: str | None
    bfs_order: list[str]


class GraphAnalysisResponse(BaseModel):
    graph_type: str
    metrics: GraphMetrics
    top_degree_centrality: list[RankedNode]
    top_betweenness_centrality: list[RankedNode]
    top_impact_rank: list[RankedNode]
    traversal: TraversalResult
