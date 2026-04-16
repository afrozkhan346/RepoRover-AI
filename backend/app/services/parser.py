from __future__ import annotations

import os
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

IGNORED_DIRS = {
    ".git",
    "node_modules",
    ".next",
    "dist",
    "build",
    "venv",
    ".venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".java": "Java",
    ".go": "Go",
    ".rs": "Rust",
    ".rb": "Ruby",
    ".php": "PHP",
    ".cs": "C#",
    ".cpp": "C++",
    ".cc": "C++",
    ".c": "C",
    ".h": "C/C++ Header",
    ".hpp": "C/C++ Header",
    ".kt": "Kotlin",
    ".swift": "Swift",
    ".scala": "Scala",
    ".sql": "SQL",
    ".sh": "Shell",
    ".ps1": "PowerShell",
    ".html": "HTML",
    ".css": "CSS",
    ".scss": "SCSS",
    ".md": "Markdown",
    ".json": "JSON",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".toml": "TOML",
    ".xml": "XML",
}

AST_SUPPORTED_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".cs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
    ".kt",
    ".swift",
    ".scala",
    ".sql",
    ".sh",
}

TEST_DIR_MARKERS = {"test", "tests", "__tests__", "spec", "specs"}
TEST_FILE_PREFIXES = ("test_",)
TEST_FILE_SUFFIXES = ("_test", ".test", ".spec")
SOURCE_DIR_MARKERS = {"src", "source", "app", "lib", "packages"}
CONFIG_DIR_MARKERS = {"config", "configs", ".github", ".vscode", ".idea"}
CONFIG_FILE_NAMES = {
    "dockerfile",
    "makefile",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "webpack.config.js",
    "rollup.config.js",
    "jest.config.js",
    "jest.config.ts",
    ".env",
}
CONFIG_EXTENSIONS = {
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    ".xml",
}
CONFIG_BASENAME_SUFFIXES = (
    ".config",
    ".config.js",
    ".config.ts",
    ".config.cjs",
    ".config.mjs",
)


@dataclass(frozen=True)
class FileMetadata:
    path: str
    name: str
    extension: str
    size: int
    category: str
    language: str
    ast_supported: bool


@dataclass(frozen=True)
class DirectoryMetadata:
    path: str
    name: str
    depth: int


@dataclass(frozen=True)
class ProjectMetadata:
    root_path: str
    project_name: str
    total_files: int
    total_directories: int
    total_size_bytes: int
    primary_language: str
    language_breakdown: dict[str, int]


@dataclass(frozen=True)
class ProjectScanResult:
    project: ProjectMetadata
    files: list[FileMetadata]
    directories: list[DirectoryMetadata]
    structure: dict[str, Any]
    ast_ready_files: list[str]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["files"] = sorted(payload["files"], key=lambda item: item["path"])
        payload["directories"] = sorted(payload["directories"], key=lambda item: item["path"])
        payload["ast_ready_files"] = sorted(payload["ast_ready_files"])
        return payload


class ProjectParsingEngine:
    """Scans a project and returns structure + language metadata for later AST parsing."""

    def scan_project(self, project_path: str, max_files: int = 20_000) -> ProjectScanResult:
        root = Path(project_path).expanduser().resolve()
        if not root.exists():
            raise ValueError("project_path does not exist")
        if not root.is_dir():
            raise ValueError("project_path must be a directory")

        files: list[FileMetadata] = []
        directories: list[DirectoryMetadata] = []
        language_counter: Counter[str] = Counter()
        total_size_bytes = 0

        for current_dir, dir_names, file_names in root.walk(top_down=True):
            dir_names[:] = [name for name in dir_names if name not in IGNORED_DIRS]

            relative_dir = current_dir.relative_to(root)
            if relative_dir.parts:
                directories.append(
                    DirectoryMetadata(
                        path=relative_dir.as_posix(),
                        name=current_dir.name,
                        depth=len(relative_dir.parts),
                    )
                )

            for file_name in file_names:
                file_path = current_dir / file_name
                relative_path = file_path.relative_to(root).as_posix()

                try:
                    size = file_path.stat().st_size
                except OSError:
                    continue

                extension = file_path.suffix.lower()
                category = _categorize_file(relative_path=relative_path, file_name=file_name, extension=extension)
                language = LANGUAGE_BY_EXTENSION.get(extension, "Unknown")
                ast_supported = extension in AST_SUPPORTED_EXTENSIONS

                if language != "Unknown":
                    language_counter[language] += 1

                files.append(
                    FileMetadata(
                        path=relative_path,
                        name=file_name,
                        extension=extension,
                        size=size,
                        category=category,
                        language=language,
                        ast_supported=ast_supported,
                    )
                )
                total_size_bytes += size

                if len(files) >= max_files:
                    break

            if len(files) >= max_files:
                break

        files_sorted = sorted(files, key=lambda item: item.path)
        directories_sorted = sorted(directories, key=lambda item: item.path)
        ast_ready_files = [entry.path for entry in files_sorted if entry.ast_supported]

        primary_language = language_counter.most_common(1)[0][0] if language_counter else "Unknown"

        project = ProjectMetadata(
            root_path=str(root),
            project_name=root.name,
            total_files=len(files_sorted),
            total_directories=len(directories_sorted),
            total_size_bytes=total_size_bytes,
            primary_language=primary_language,
            language_breakdown=dict(language_counter),
        )

        structure = _build_structure_tree(root_name=root.name, directories=directories_sorted, files=files_sorted)

        return ProjectScanResult(
            project=project,
            files=files_sorted,
            directories=directories_sorted,
            structure=structure,
            ast_ready_files=ast_ready_files,
        )


def scan_project_metadata(project_path: str, max_files: int = 20_000) -> dict[str, Any]:
    """Advanced scanner returning structure, language breakdown, and AST-ready files."""

    engine = ProjectParsingEngine()
    return engine.scan_project(project_path=project_path, max_files=max_files).to_dict()


def scan_project(project_path: str) -> list[dict[str, str]]:
    """Simple file scanner that returns flat file structure rows."""

    root = Path(project_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("project_path must be an existing directory")

    structure: list[dict[str, str]] = []

    for current_root, dir_names, files in os.walk(root):
        dir_names[:] = [name for name in dir_names if name not in IGNORED_DIRS]

        for file_name in files:
            file_path = Path(current_root) / file_name
            relative_path = file_path.relative_to(root).as_posix()
            extension = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""
            category = _categorize_file(relative_path=relative_path, file_name=file_name, extension=f".{extension}" if extension else "")

            structure.append(
                {
                    "name": file_name,
                    "path": relative_path,
                    "extension": extension,
                    "category": category,
                }
            )

    return structure


def detect_language(structure: list[dict[str, str]]) -> str:
    """Infer primary language from discovered file extensions."""

    counts: Counter[str] = Counter()
    for file in structure:
        extension = file.get("extension", "").lower()
        if not extension:
            continue
        language = LANGUAGE_BY_EXTENSION.get(f".{extension}")
        if language:
            counts[language] += 1

    return counts.most_common(1)[0][0] if counts else "Unknown"


def parse_project(project_path: str) -> dict[str, Any]:
    """Combine file scanning and language detection for parser entrypoint."""

    structure = scan_project(project_path)
    analyzable_extensions = {ext.lstrip(".") for ext in AST_SUPPORTED_EXTENSIONS}
    analyzable_files = [entry for entry in structure if entry.get("extension", "") in analyzable_extensions]

    # Prefer code-oriented files for primary language inference and UI output.
    language_source = analyzable_files if analyzable_files else structure
    language = detect_language(language_source)

    return {
        "language": language,
        "total_files": len(structure),
        "total_files_scanned": len(structure),
        "files": structure,
    }


def _build_structure_tree(
    *,
    root_name: str,
    directories: list[DirectoryMetadata],
    files: list[FileMetadata],
) -> dict[str, Any]:
    tree: dict[str, Any] = {
        "name": root_name,
        "type": "folder",
        "path": ".",
        "children": {},
    }

    for directory in directories:
        _ensure_folder_node(tree, directory.path)

    for file_entry in files:
        parent_path = str(Path(file_entry.path).parent).replace("\\", "/")
        if parent_path == ".":
            parent_node = tree
        else:
            parent_node = _ensure_folder_node(tree, parent_path)

        children = parent_node.setdefault("children", {})
        children[file_entry.name] = {
            "name": file_entry.name,
            "type": "file",
            "path": file_entry.path,
            "extension": file_entry.extension,
            "category": file_entry.category,
            "language": file_entry.language,
            "size": file_entry.size,
            "ast_supported": file_entry.ast_supported,
        }

    return _sort_tree(tree)


def _ensure_folder_node(tree: dict[str, Any], relative_dir: str) -> dict[str, Any]:
    node = tree
    for part in Path(relative_dir).parts:
        children = node.setdefault("children", {})
        if part not in children:
            children[part] = {
                "name": part,
                "type": "folder",
                "path": _join_paths(node.get("path", "."), part),
                "children": {},
            }
        node = children[part]
    return node


def _join_paths(base: str, part: str) -> str:
    if base in {"", "."}:
        return part
    return f"{base}/{part}"


def _sort_tree(node: dict[str, Any]) -> dict[str, Any]:
    children = node.get("children")
    if not isinstance(children, dict):
        return node

    sorted_items = sorted(
        children.items(),
        key=lambda item: (0 if item[1].get("type") == "folder" else 1, item[0].lower()),
    )

    normalized_children = []
    for _, child in sorted_items:
        normalized_children.append(_sort_tree(child))

    next_node = dict(node)
    next_node["children"] = normalized_children
    return next_node


def _categorize_file(*, relative_path: str, file_name: str, extension: str) -> str:
    normalized_parts = [part.lower() for part in Path(relative_path).parts]
    lower_name = file_name.lower()
    stem = Path(lower_name).stem

    if any(part in TEST_DIR_MARKERS for part in normalized_parts):
        return "test"
    if lower_name.startswith(TEST_FILE_PREFIXES):
        return "test"
    if any(stem.endswith(suffix) for suffix in TEST_FILE_SUFFIXES):
        return "test"

    if lower_name in CONFIG_FILE_NAMES:
        return "config"
    if any(lower_name.endswith(suffix) for suffix in CONFIG_BASENAME_SUFFIXES):
        return "config"
    if any(part in CONFIG_DIR_MARKERS for part in normalized_parts):
        return "config"
    if extension in CONFIG_EXTENSIONS:
        # Do not force config classification for data/fixtures under source trees.
        if any(part in SOURCE_DIR_MARKERS for part in normalized_parts):
            return "source"
        return "config"

    return "source"
