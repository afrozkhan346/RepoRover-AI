from pydantic import BaseModel, Field


class GitHubAnalysisRequest(BaseModel):
    github_url: str = Field(..., min_length=1)


class LocalRepositoryAnalysisRequest(BaseModel):
    local_path: str = Field(..., min_length=1)


class FileStructureItem(BaseModel):
    path: str
    type: str | None = None
    size: int | None = None


class RecentCommitItem(BaseModel):
    sha: str
    message: str
    author: str
    date: str


class GitHubAnalysisResponse(BaseModel):
    name: str
    full_name: str
    description: str | None = None
    owner: str
    stars: int
    forks: int
    watchers: int
    open_issues: int
    language: str
    languages: dict[str, int]
    topics: list[str]
    license: str
    created_at: str
    updated_at: str
    size: int
    default_branch: str
    readme: str
    recent_commits: list[RecentCommitItem]
    file_count: int
    file_structure: list[FileStructureItem]
