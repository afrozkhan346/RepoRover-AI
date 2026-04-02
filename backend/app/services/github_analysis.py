from __future__ import annotations

from typing import Any

from app.services.repository_loader import (
    load_repository_from_path,
    load_repository_from_url,
    load_repository_from_zip,
)


def analyze_repository(github_url: str) -> dict[str, Any]:
    loaded = load_repository_from_url(github_url)
    owner = loaded.full_name.split("/")[0] if "/" in loaded.full_name else loaded.full_name
    return {
        "name": loaded.repo_name,
        "full_name": loaded.full_name,
        "description": None,
        "owner": owner,
        "stars": 0,
        "forks": 0,
        "watchers": 0,
        "open_issues": 0,
        "language": loaded.language,
        "languages": loaded.languages,
        "topics": [],
        "license": "No license",
        "created_at": "",
        "updated_at": "",
        "size": loaded.size,
        "default_branch": loaded.default_branch,
        "readme": loaded.readme,
        "recent_commits": loaded.recent_commits,
        "file_count": loaded.file_count,
        "file_structure": loaded.file_structure,
    }


def analyze_local_repository(local_path: str) -> dict[str, Any]:
    loaded = load_repository_from_path(local_path)
    owner = loaded.full_name.split("/")[0] if "/" in loaded.full_name else loaded.full_name
    return {
        "name": loaded.repo_name,
        "full_name": loaded.full_name,
        "description": None,
        "owner": owner,
        "stars": 0,
        "forks": 0,
        "watchers": 0,
        "open_issues": 0,
        "language": loaded.language,
        "languages": loaded.languages,
        "topics": [],
        "license": "No license",
        "created_at": "",
        "updated_at": "",
        "size": loaded.size,
        "default_branch": loaded.default_branch,
        "readme": loaded.readme,
        "recent_commits": loaded.recent_commits,
        "file_count": loaded.file_count,
        "file_structure": loaded.file_structure,
    }


def analyze_zip_repository(zip_bytes: bytes, archive_name: str) -> dict[str, Any]:
    loaded = load_repository_from_zip(zip_bytes, archive_name)
    owner = loaded.full_name.split("/")[0] if "/" in loaded.full_name else loaded.full_name
    return {
        "name": loaded.repo_name,
        "full_name": loaded.full_name,
        "description": None,
        "owner": owner,
        "stars": 0,
        "forks": 0,
        "watchers": 0,
        "open_issues": 0,
        "language": loaded.language,
        "languages": loaded.languages,
        "topics": [],
        "license": "No license",
        "created_at": "",
        "updated_at": "",
        "size": loaded.size,
        "default_branch": loaded.default_branch,
        "readme": loaded.readme,
        "recent_commits": loaded.recent_commits,
        "file_count": loaded.file_count,
        "file_structure": loaded.file_structure,
    }
