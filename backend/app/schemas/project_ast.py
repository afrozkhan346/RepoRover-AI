from __future__ import annotations

from pydantic import BaseModel

from app.schemas.parsing import AstTreeNode, NormalizedAstNode, SyntaxUnit


class AstCallSite(BaseModel):
    called_name: str
    call_line: int
    call_type: str


class ProjectAstSnapshot(BaseModel):
    language: str
    total_nodes: int
    truncated: bool
    preview_nodes: list[NormalizedAstNode]
    tree_nodes_returned: int
    root: AstTreeNode
    imports: list[SyntaxUnit]
    classes: list[SyntaxUnit]
    functions: list[SyntaxUnit]
    calls: list[AstCallSite]


class ProjectAstFile(BaseModel):
    file: str
    path: str
    language: str
    data: dict
    normalized_ast: ProjectAstSnapshot


class ProjectAstResponse(BaseModel):
    language: str
    total_files: int
    total_nodes: int
    truncated: bool
    files: list[ProjectAstFile]
