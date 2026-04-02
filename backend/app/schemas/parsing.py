from pydantic import BaseModel, Field


class ParseRequest(BaseModel):
    language: str | None = Field(default=None)
    file_extension: str | None = Field(default=None)
    source_code: str = Field(..., min_length=1)
    max_nodes: int = Field(default=200, ge=10, le=2000)


class NormalizedAstNode(BaseModel):
    node_type: str
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    end_point: tuple[int, int]
    child_count: int


class ParseResponse(BaseModel):
    language: str
    total_nodes: int
    truncated: bool
    nodes: list[NormalizedAstNode]


class AstStructureRequest(ParseRequest):
    max_tree_nodes: int = Field(default=300, ge=20, le=5000)
    max_depth: int = Field(default=6, ge=1, le=20)


class SyntaxUnit(BaseModel):
    unit_type: str
    name: str | None = None
    start_point: tuple[int, int]
    end_point: tuple[int, int]


class AstTreeNode(BaseModel):
    node_type: str
    start_point: tuple[int, int]
    end_point: tuple[int, int]
    children: list["AstTreeNode"]


class AstStructureResponse(BaseModel):
    language: str
    total_nodes: int
    tree_nodes_returned: int
    truncated: bool
    root: AstTreeNode
    imports: list[SyntaxUnit]
    classes: list[SyntaxUnit]
    functions: list[SyntaxUnit]


AstTreeNode.model_rebuild()
