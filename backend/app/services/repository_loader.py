from __future__ import annotations

import re
import shutil
import stat
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from uuid import uuid4

from git import InvalidGitRepositoryError, Repo

from app.core.config import settings


class RepositoryLoadError(ValueError):
    def __init__(self, detail: str, code: str = "REPOSITORY_LOAD_ERROR"):
        super().__init__(detail)
        self.code = code


@dataclass(frozen=True)
class IngestionMetadata:
    operation: str
    workspace_path: str
    workspace_policy: str
    cleaned_entries: int
    fetched_updates: bool


@dataclass(frozen=True)
class CloneResult:
    repo: Repo
    local_path: Path
    metadata: IngestionMetadata


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
    ingestion: IngestionMetadata


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


def _allowed_extensions() -> set[str]:
    return {extension.lower() for extension in settings.projects_allowed_extensions if extension}


def _is_symlink(path: Path) -> bool:
    try:
        return path.is_symlink()
    except OSError:
        return False


def _validate_repository_tree(root: Path, *, source_label: str) -> tuple[int, int]:
    allowed_extensions = _allowed_extensions()
    max_file_count = max(settings.projects_max_file_count, 1)
    max_total_size = max(settings.projects_max_total_size_bytes, 1)

    file_count = 0
    total_size = 0

    for file_path in root.rglob("*"):
        if ".git" in file_path.parts:
            continue

        if _is_symlink(file_path):
            if settings.projects_disallow_symlinks:
                raise RepositoryLoadError(
                    f"Symlinks are not allowed in {source_label}",
                    code="UNSAFE_SYMLINK",
                )
            continue

        if not file_path.is_file():
            continue

        if allowed_extensions and file_path.suffix.lower() not in allowed_extensions:
            raise RepositoryLoadError(
                f"File type not allowed in {source_label}: {file_path.name}",
                code="UNSUPPORTED_FILE_EXTENSION",
            )

        try:
            file_size = file_path.stat().st_size
        except OSError as error:
            raise RepositoryLoadError(
                f"Unable to inspect file in {source_label}: {file_path.name}",
                code="INVALID_LOCAL_PATH",
            ) from error

        file_count += 1
        total_size += file_size

        if file_count > max_file_count:
            raise RepositoryLoadError(
                f"File count exceeds limit for {source_label}",
                code="TOO_MANY_FILES",
            )

        if total_size > max_total_size:
            raise RepositoryLoadError(
                f"Project size exceeds limit for {source_label}",
                code="PROJECT_TOO_LARGE",
            )

    return file_count, total_size


def _zip_member_is_symlink(member: zipfile.ZipInfo) -> bool:
    mode = member.external_attr >> 16
    return stat.S_ISLNK(mode)


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
    configured = Path(settings.projects_workspace_path)
    projects_dir = configured if configured.is_absolute() else (Path(__file__).resolve().parents[2] / configured)
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir


def _create_project_directory(prefix: str, parent: Path | None = None) -> Path:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    unique = uuid4().hex[:8]
    root = parent if parent is not None else _projects_root()
    target = root / f"{prefix}-{timestamp}-{unique}"
    target.mkdir(parents=True, exist_ok=False)
    return target


def _sanitize_name(raw: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9._-]+", "-", raw).strip("-")
    return cleaned or "repository"


def _workspace_policy_label() -> str:
    return (
        f"retention_days={settings.projects_retention_days};"
        f"max_entries={settings.projects_max_entries};"
        f"cleanup_enabled={str(settings.projects_cleanup_enabled).lower()}"
    )


def _cleanup_workspace_entries(root: Path) -> int:
    if not settings.projects_cleanup_enabled:
        return 0

    cleaned = 0
    now = datetime.now(timezone.utc)
    max_age = timedelta(days=max(settings.projects_retention_days, 1))

    entries = [entry for entry in root.iterdir() if entry.is_dir()]
    for entry in entries:
        try:
            modified = datetime.fromtimestamp(entry.stat().st_mtime, tz=timezone.utc)
        except OSError:
            continue

        if now - modified > max_age:
            shutil.rmtree(entry, ignore_errors=True)
            cleaned += 1

    remaining = [entry for entry in root.iterdir() if entry.is_dir()]
    overflow = max(0, len(remaining) - max(settings.projects_max_entries, 1))
    if overflow > 0:
        remaining.sort(key=lambda p: p.stat().st_mtime)
        for entry in remaining[:overflow]:
            shutil.rmtree(entry, ignore_errors=True)
            cleaned += 1

    return cleaned


def _default_branch(repo: Repo) -> str:
    try:
        return repo.remotes.origin.refs["HEAD"].reference.remote_head
    except Exception:
        pass

    try:
        return repo.active_branch.name
    except Exception:
        return "main"


def _clone_or_update_remote(source_url: str) -> CloneResult:
    repo_name, full_name = _repo_identity_from_source_url(source_url)
    owner = full_name.split("/")[0] if "/" in full_name else "unknown"
    shared_root = _projects_root() / "github" / _sanitize_name(owner)
    shared_root.mkdir(parents=True, exist_ok=True)
    cleaned_entries = _cleanup_workspace_entries(shared_root)

    target = shared_root / _sanitize_name(repo_name)
    fetched_updates = False

    if target.exists():
        try:
            repo = Repo(target)
            if "origin" in [remote.name for remote in repo.remotes]:
                repo.remotes.origin.fetch(prune=True)
                branch = _default_branch(repo)
                try:
                    repo.git.checkout(branch)
                except Exception:
                    pass
                try:
                    repo.remotes.origin.pull("--ff-only", branch)
                except Exception:
                    # Non-fast-forward or detached HEAD should not hard-fail ingestion.
                    pass
                fetched_updates = True
            return CloneResult(
                repo=repo,
                local_path=target,
                metadata=IngestionMetadata(
                    operation="updated",
                    workspace_path=str(target),
                    workspace_policy=_workspace_policy_label(),
                    cleaned_entries=cleaned_entries,
                    fetched_updates=fetched_updates,
                ),
            )
        except InvalidGitRepositoryError:
            shutil.rmtree(target, ignore_errors=True)

    try:
        repo = Repo.clone_from(source_url, target, depth=1)
    except Exception as error:
        raise RepositoryLoadError(f"Failed to clone repository: {error}", code="CLONE_FAILED") from error

    return CloneResult(
        repo=repo,
        local_path=target,
        metadata=IngestionMetadata(
            operation="cloned",
            workspace_path=str(target),
            workspace_policy=_workspace_policy_label(),
            cleaned_entries=cleaned_entries,
            fetched_updates=False,
        ),
    )


def _copy_local_into_workspace(local_candidate: Path) -> CloneResult:
    _validate_repository_tree(local_candidate, source_label="local project")

    workspace = _projects_root() / "local"
    workspace.mkdir(parents=True, exist_ok=True)
    cleaned_entries = _cleanup_workspace_entries(workspace)
    target = _create_project_directory(f"local-{_sanitize_name(local_candidate.name)}", parent=workspace)
    shutil.copytree(local_candidate, target, dirs_exist_ok=True)
    _validate_repository_tree(target, source_label="workspace copy")

    try:
        repo = Repo(target)
    except InvalidGitRepositoryError:
        repo = Repo.init(target)

    return CloneResult(
        repo=repo,
        local_path=target,
        metadata=IngestionMetadata(
            operation="copied",
            workspace_path=str(target),
            workspace_policy=_workspace_policy_label(),
            cleaned_entries=cleaned_entries,
            fetched_updates=False,
        ),
    )


def clone_repository_with_metadata(source_url: str) -> CloneResult:
    source = source_url.strip()
    if not source:
        raise RepositoryLoadError("Repository source URL is required", code="MISSING_SOURCE_URL")

    local_candidate = Path(source).expanduser()
    if local_candidate.exists() and local_candidate.is_dir():
        return _copy_local_into_workspace(local_candidate)

    parsed = urlparse(source)
    if parsed.scheme == "file":
        # Preserve absolute POSIX paths (e.g. file:///tmp/repo) and support
        # Windows file URLs (e.g. file:///C:/repo).
        raw_path = unquote(parsed.path or "")
        if parsed.netloc:
            raw_path = f"//{parsed.netloc}{raw_path}"
        if len(raw_path) >= 3 and raw_path.startswith("/") and raw_path[2] == ":":
            raw_path = raw_path.lstrip("/")
        local_path = Path(raw_path).expanduser()
        if not local_path.exists() or not local_path.is_dir():
            raise RepositoryLoadError("Local file:// repository path does not exist", code="INVALID_LOCAL_PATH")
        return _copy_local_into_workspace(local_path)

    return _clone_or_update_remote(source)


def clone_repository(source_url: str) -> tuple[Repo, Path]:
    result = clone_repository_with_metadata(source_url)
    return result.repo, result.local_path


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
    ingestion: IngestionMetadata,
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
        ingestion=ingestion,
    )


def _safe_extract_zip(zip_bytes: bytes, target_dir: Path) -> None:
    with zipfile.ZipFile(BytesIO(zip_bytes)) as archive:
        if len(archive.infolist()) > max(settings.projects_max_zip_entry_count, 1):
            raise RepositoryLoadError("ZIP archive contains too many entries", code="ZIP_TOO_LARGE")

        total_uncompressed_size = 0
        for member in archive.infolist():
            member_path = Path(member.filename.replace("\\", "/"))
            if member_path.is_absolute() or ".." in member_path.parts:
                raise RepositoryLoadError("ZIP archive contains unsafe paths", code="UNSAFE_PATH")

            if _zip_member_is_symlink(member) and settings.projects_disallow_symlinks:
                raise RepositoryLoadError("ZIP archive contains symlinks", code="UNSAFE_SYMLINK")

            total_uncompressed_size += member.file_size
            if total_uncompressed_size > max(settings.projects_max_zip_uncompressed_bytes, 1):
                raise RepositoryLoadError("ZIP archive is too large when extracted", code="ZIP_TOO_LARGE")

            destination = target_dir / member_path
            if member.is_dir():
                destination.mkdir(parents=True, exist_ok=True)
                continue

            destination.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(member, "r") as source, destination.open("wb") as target_file:
                shutil.copyfileobj(source, target_file)


def _find_project_root(extract_root: Path) -> Path:
    entries = [entry for entry in extract_root.iterdir()]
    if len(entries) == 1 and entries[0].is_dir():
        return entries[0]
    return extract_root


def load_repository_from_url(source_url: str) -> RepositoryLoadResult:
    clone_result = clone_repository_with_metadata(source_url)
    repo_name, full_name = _repo_identity_from_source_url(source_url)
    root = Path(clone_result.local_path)
    return _build_load_result(
        source_url=source_url,
        root=root,
        repo_name=repo_name,
        full_name=full_name,
        ingestion=clone_result.metadata,
    )


def load_repository_from_path(local_path: str) -> RepositoryLoadResult:
    root = Path(local_path).expanduser().resolve()
    if not root.exists():
        raise RepositoryLoadError("Local path does not exist", code="INVALID_LOCAL_PATH")
    if not root.is_dir():
        raise RepositoryLoadError("Local path must be a directory", code="INVALID_LOCAL_PATH")

    copied = _copy_local_into_workspace(root)
    workspace_root = Path(copied.local_path)

    repo_name, full_name = _repo_identity_from_path(workspace_root)
    return _build_load_result(
        source_url=str(root),
        root=workspace_root,
        repo_name=repo_name,
        full_name=full_name,
        ingestion=copied.metadata,
    )


def load_repository_from_zip(zip_bytes: bytes, archive_name: str = "uploaded.zip") -> RepositoryLoadResult:
    if not zip_bytes:
        raise RepositoryLoadError("ZIP archive is empty", code="INVALID_ARCHIVE")

    upload_root = _projects_root() / "upload"
    upload_root.mkdir(parents=True, exist_ok=True)
    cleaned_entries = _cleanup_workspace_entries(upload_root)
    temp_dir = _create_project_directory("upload", parent=upload_root)
    try:
        _safe_extract_zip(zip_bytes, temp_dir)
        root = _find_project_root(temp_dir)
        _validate_repository_tree(root, source_label="ZIP archive")
        repo_name = Path(archive_name).stem or root.name or "uploaded-project"
        full_name = repo_name
        return _build_load_result(
            source_url=f"zip:{archive_name}",
            root=root,
            repo_name=repo_name,
            full_name=full_name,
            ingestion=IngestionMetadata(
                operation="uploaded",
                workspace_path=str(temp_dir),
                workspace_policy=_workspace_policy_label(),
                cleaned_entries=cleaned_entries,
                fetched_updates=False,
            ),
        )
    except zipfile.BadZipFile as error:
        raise RepositoryLoadError("Invalid ZIP archive", code="INVALID_ARCHIVE") from error
