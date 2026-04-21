from __future__ import annotations

from pydantic import BaseModel, Field


class RepositoryStructureRequest(BaseModel):
    local_path: str = Field(..., min_length=1)
    ignored_dirs: list[str] = Field(default_factory=list)
    max_nodes: int = Field(default=200_000, ge=1_000, le=2_000_000)
    max_depth: int | None = Field(default=None, ge=1, le=128)
    include_errors: bool = False


class RepositoryTreeError(BaseModel):
    path: str
    error: str


class RepositoryTreeNode(BaseModel):
    name: str
    type: str
    path: str
    icon: str
    color: str
    language: str | None = None
    size: int | None = None
    extension: str | None = None
    children: list["RepositoryTreeNode"] = Field(default_factory=list)


class RepositoryStructureResponse(BaseModel):
    hierarchy: RepositoryTreeNode
    truncated: bool = False
    errors: list[RepositoryTreeError] = Field(default_factory=list)


RepositoryTreeNode.model_rebuild()
