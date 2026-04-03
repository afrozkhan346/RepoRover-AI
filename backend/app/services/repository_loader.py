from __future__ import annotations

import shutil
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from git import InvalidGitRepositoryError, Repo


@dataclass(frozen=True)
class RepositoryLoadResult:
    source_url: str
    local_path: str
    repo_name: str
    full_name: str
    default_branch: str
    readme: str
    file_structure: list[dict[str, Any]]
    recent_commits: list[dict[str, str]]
    language: str
    languages: dict[str, int]
    file_count: int
    size: int


_README_NAMES = (
    "README.md",
    "README.rst",
    "README.txt",
    "readme.md",
    "readme.rst",
    "readme.txt",
)

_LANGUAGE_MAP = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".html": "HTML",
    ".css": "CSS",
    ".md": "Markdown",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".sql": "SQL",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
}


def _repo_identity_from_source_url(source_url: str) -> tuple[str, str]:
    parsed = urlparse(source_url)
    path = parsed.path.strip("/")
    if not path:
        return ("repository", "repository")
    parts = path.split("/")
    if len(parts) >= 2:
        owner = parts[-2]
        repo = parts[-1].removesuffix(".git")
        return repo or "repository", f"{owner}/{repo or 'repository'}"
    repo = parts[-1].removesuffix(".git")
    return repo or "repository", repo or "repository"


def _repo_identity_from_path(path: Path) -> tuple[str, str]:
    repo_name = path.name or "repository"
    return repo_name, repo_name


def _projects_root() -> Path:
    projects_dir = Path(__file__).resolve().parents[2] / "projects"
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir


def _create_project_directory(prefix: str) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique = uuid4().hex[:8]
    target = _projects_root() / f"{prefix}-{timestamp}-{unique}"
    target.mkdir(parents=True, exist_ok=False)
    return target


def clone_repository(source_url: str) -> tuple[Repo, Path]:
    temp_dir = _create_project_directory("clone")
    try:
        repo = Repo.clone_from(source_url, temp_dir, depth=1)
        return repo, temp_dir
    except Exception:
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise


def _read_text_file(path: Path, limit: int = 5000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:limit]
    except OSError:
        return ""


def _collect_file_structure(root: Path) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for file_path in root.rglob("*"):
        if not file_path.is_file():
            continue
        if ".git" in file_path.parts:
            continue
        try:
            relative_path = file_path.relative_to(root)
            items.append(
                {
                    "path": relative_path.as_posix(),
                    "type": "blob",
                    "size": file_path.stat().st_size,
                }
            )
        except OSError:
            continue
    return items


def _detect_languages(root: Path) -> tuple[str, dict[str, int]]:
    counts: Counter[str] = Counter()
    for file_path in root.rglob("*"):
        if not file_path.is_file() or ".git" in file_path.parts:
            continue
        language = _LANGUAGE_MAP.get(file_path.suffix.lower())
        if language:
            counts[language] += 1
    primary_language = counts.most_common(1)[0][0] if counts else "Unknown"
    return primary_language, dict(counts)


def _read_readme(root: Path) -> str:
    for readme_name in _README_NAMES:
        candidate = root / readme_name
        if candidate.exists():
            return _read_text_file(candidate)
        nested_candidates = list(root.rglob(readme_name))
        if nested_candidates:
            return _read_text_file(nested_candidates[0])
    return ""


def _git_metadata_for_path(root: Path) -> tuple[str, list[dict[str, str]]]:
    try:
        repo = Repo(root)
    except (InvalidGitRepositoryError, OSError):
        return "main", []

    default_branch = repo.active_branch.name if not repo.head.is_detached else "main"
    recent_commits = [
        {
            "sha": commit.hexsha,
            "message": commit.message.strip(),
            "author": commit.author.name,
            "date": commit.committed_datetime.isoformat(),
        }
        for commit in list(repo.iter_commits(max_count=5))
    ]
    return default_branch, recent_commits


def _build_load_result(
    *,
    source_url: str,
    root: Path,
    repo_name: str,
    full_name: str,
) -> RepositoryLoadResult:
    readme = _read_readme(root)
    file_structure = _collect_file_structure(root)
    language, languages = _detect_languages(root)
    default_branch, recent_commits = _git_metadata_for_path(root)
    size = sum(item["size"] for item in file_structure if isinstance(item.get("size"), int))

    return RepositoryLoadResult(
        source_url=source_url,
        local_path=str(root),
        repo_name=repo_name,
        full_name=full_name,
        default_branch=default_branch,
        readme=readme,
        file_structure=file_structure[:100],
        recent_commits=recent_commits,
        language=language,
        languages=languages,
        file_count=len(file_structure),
        size=size,
    )


def _safe_extract_zip(zip_bytes: bytes, target_dir: Path) -> None:
    with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
        for member in archive.infolist():
            member_path = Path(member.filename)
            if member_path.is_absolute() or ".." in member_path.parts:
                raise ValueError("ZIP archive contains unsafe paths")
        archive.extractall(target_dir)


def _find_project_root(extract_root: Path) -> Path:
    entries = [entry for entry in extract_root.iterdir()]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extract_root


def load_repository_from_url(source_url: str) -> RepositoryLoadResult:
    _, local_path = clone_repository(source_url)
    repo_name, full_name = _repo_identity_from_source_url(source_url)
    root = Path(local_path)
    return _build_load_result(
        source_url=source_url,
        root=root,
        repo_name=repo_name,
        full_name=full_name,
    )


def load_repository_from_path(local_path: str) -> RepositoryLoadResult:
    root = Path(local_path).expanduser().resolve()
    if not root.exists():
        raise ValueError("Local path does not exist")
    if not root.is_dir():
        raise ValueError("Local path must be a directory")

    repo_name, full_name = _repo_identity_from_path(root)
    return _build_load_result(
        source_url=str(root),
        root=root,
        repo_name=repo_name,
        full_name=full_name,
    )


def load_repository_from_zip(zip_bytes: bytes, archive_name: str = "uploaded.zip") -> RepositoryLoadResult:
    if not zip_bytes:
        raise ValueError("ZIP archive is empty")

    temp_dir = _create_project_directory("upload")
    try:
        _safe_extract_zip(zip_bytes, temp_dir)
        root = _find_project_root(temp_dir)
        repo_name = Path(archive_name).stem or root.name or "uploaded-project"
        full_name = repo_name
        return _build_load_result(
            source_url=f"zip:{archive_name}",
            root=root,
            repo_name=repo_name,
            full_name=full_name,
        )
    except zipfile.BadZipFile as error:
        raise ValueError("Invalid ZIP archive") from error
