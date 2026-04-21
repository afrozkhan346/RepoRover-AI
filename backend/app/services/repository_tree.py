from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

# Directories that are almost always noise for repository visualization.
DEFAULT_IGNORED_DIRS = {
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

ICON_BY_EXTENSION = {
    ".py": "file-code",
    ".ts": "file-code",
    ".tsx": "file-code",
    ".js": "file-code",
    ".jsx": "file-code",
    ".java": "file-code",
    ".go": "file-code",
    ".rs": "file-code",
    ".rb": "file-code",
    ".php": "file-code",
    ".cs": "file-code",
    ".cpp": "file-code",
    ".cc": "file-code",
    ".c": "file-code",
    ".h": "file-code",
    ".hpp": "file-code",
    ".kt": "file-code",
    ".swift": "file-code",
    ".scala": "file-code",
    ".sql": "database",
    ".sh": "terminal",
    ".ps1": "terminal",
    ".html": "file-code",
    ".css": "palette",
    ".scss": "palette",
    ".md": "file-text",
    ".txt": "file-text",
    ".json": "file-json",
    ".yml": "file-json",
    ".yaml": "file-json",
    ".toml": "file-json",
    ".xml": "file-json",
    ".png": "image",
    ".jpg": "image",
    ".jpeg": "image",
    ".gif": "image",
    ".svg": "image",
}

COLOR_BY_EXTENSION = {
    ".py": "#3572A5",
    ".ts": "#3178C6",
    ".tsx": "#3178C6",
    ".js": "#F7DF1E",
    ".jsx": "#F7DF1E",
    ".java": "#B07219",
    ".go": "#00ADD8",
    ".rs": "#DEA584",
    ".rb": "#CC342D",
    ".php": "#777BB4",
    ".cs": "#178600",
    ".cpp": "#F34B7D",
    ".cc": "#F34B7D",
    ".c": "#555555",
    ".h": "#555555",
    ".hpp": "#555555",
    ".kt": "#A97BFF",
    ".swift": "#F05138",
    ".scala": "#C22D40",
    ".sql": "#E38C00",
    ".sh": "#89E051",
    ".ps1": "#012456",
    ".html": "#E34F26",
    ".css": "#1572B6",
    ".scss": "#CF649A",
    ".md": "#083FA1",
    ".json": "#F5A623",
    ".yml": "#CB171E",
    ".yaml": "#CB171E",
    ".toml": "#9C4221",
    ".xml": "#0060AC",
    ".png": "#8AA1B1",
    ".jpg": "#8AA1B1",
    ".jpeg": "#8AA1B1",
    ".gif": "#8AA1B1",
    ".svg": "#FFB13B",
}


# Folder-level defaults used by frontend viewers.
FOLDER_ICON = "folder"
FOLDER_COLOR = "#F59E0B"


def _normalize_ignored_dirs(ignored_dirs: set[str] | None) -> set[str]:
    """Normalize ignore rules once so checks are fast during deep traversal."""

    source = DEFAULT_IGNORED_DIRS if ignored_dirs is None else ignored_dirs
    return {name.strip().lower() for name in source if name and name.strip()}


def _should_ignore_dir(name: str, blocked_dirs: set[str]) -> bool:
    """Return True when a folder name should be skipped entirely."""

    return name.lower() in blocked_dirs


def build_repository_tree(
    repository_path: str | Path,
    *,
    ignored_dirs: set[str] | None = None,
    max_nodes: int = 200_000,
    max_depth: int | None = None,
    include_errors: bool = False,
) -> dict[str, Any]:
    """Build a recursive repository tree with metadata for files and folders.

    Output schema per node:
    - name: str
    - type: "folder" | "file"
    - path: repository-relative POSIX path ("." for root)
    - size: int (files only)
    - extension: str (files only)
    - icon: str (frontend icon key)
    - color: str (hex color for rendering)
    - language: str | null
    - children: list[dict] (folders only)

    Performance/safety options:
    - max_nodes: hard cap to avoid runaway memory/time on very large repositories
    - max_depth: optional recursion depth cap (None = unlimited)
    - include_errors: include non-fatal traversal errors under "errors" on root node
    """

    root = Path(repository_path).expanduser().resolve()
    if not root.exists():
        raise ValueError("repository_path does not exist")
    if not root.is_dir():
        raise ValueError("repository_path must be a directory")

    if max_nodes < 1:
        raise ValueError("max_nodes must be >= 1")

    blocked_dirs = _normalize_ignored_dirs(ignored_dirs)
    state = {"nodes": 0, "truncated": False, "errors": []}
    tree = _build_folder_node(
        root=root,
        current=root,
        blocked_dirs=blocked_dirs,
        state=state,
        depth=0,
        max_nodes=max_nodes,
        max_depth=max_depth,
    )

    # Optional diagnostics for UI/debug surfaces.
    if include_errors:
        tree["errors"] = state["errors"]
    if state["truncated"]:
        tree["truncated"] = True

    return tree


def to_json(tree: dict[str, Any], *, indent: int = 2) -> str:
    """Serialize a tree produced by build_repository_tree to JSON."""

    return json.dumps(tree, indent=indent, ensure_ascii=False)


def save_repository_tree(
    repository_path: str | Path,
    *,
    output_path: str | Path | None = None,
    indent: int = 2,
    ignored_dirs: set[str] | None = None,
    max_nodes: int = 200_000,
    max_depth: int | None = None,
    include_errors: bool = False,
) -> Path:
    """Build and save the repository tree into repo_structure.json.

    If output_path is omitted, the JSON file is written to:
    <repository_path>/repo_structure.json
    """

    root = Path(repository_path).expanduser().resolve()
    tree = build_repository_tree(
        root,
        ignored_dirs=ignored_dirs,
        max_nodes=max_nodes,
        max_depth=max_depth,
        include_errors=include_errors,
    )

    target = Path(output_path).expanduser().resolve() if output_path else (root / "repo_structure.json")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(to_json(tree, indent=indent) + "\n", encoding="utf-8")
    return target


def _build_folder_node(
    *,
    root: Path,
    current: Path,
    blocked_dirs: set[str],
    state: dict[str, Any],
    depth: int,
    max_nodes: int,
    max_depth: int | None,
) -> dict[str, Any]:
    # Folder nodes are always emitted, then filled with child nodes.
    state["nodes"] += 1
    children: list[dict[str, Any]] = []

    # If we reached a depth limit, do not recurse further.
    if max_depth is not None and depth >= max_depth:
        return {
            "name": current.name if current != root else root.name,
            "type": "folder",
            "path": _relative_posix(root=root, current=current),
            "icon": FOLDER_ICON,
            "color": FOLDER_COLOR,
            "language": None,
            "children": children,
        }

    # os.scandir is faster and lower-overhead than repeatedly calling Path.iterdir/stat.
    try:
        with os.scandir(current) as iterator:
            entries = list(iterator)
    except OSError as error:
        state["errors"].append({"path": str(current), "error": str(error)})
        entries = []

    # Keep folders first, then files, so the UI tree is predictable.
    def _safe_sort_key(entry: os.DirEntry[str]) -> tuple[int, str]:
        try:
            return (0 if entry.is_dir(follow_symlinks=False) else 1, entry.name.lower())
        except OSError as error:
            state["errors"].append({"path": entry.path, "error": str(error)})
            return (1, entry.name.lower())

    entries.sort(key=_safe_sort_key)

    for entry in entries:
        # Hard stop for extremely large trees.
        if state["nodes"] >= max_nodes:
            state["truncated"] = True
            break

        try:
            if entry.is_symlink():
                continue
        except OSError as error:
            state["errors"].append({"path": entry.path, "error": str(error)})
            continue

        entry_path = Path(entry.path)

        try:
            is_dir = entry.is_dir(follow_symlinks=False)
            is_file = entry.is_file(follow_symlinks=False)
        except OSError as error:
            state["errors"].append({"path": entry.path, "error": str(error)})
            continue

        if is_dir:
            if _should_ignore_dir(entry.name, blocked_dirs):
                continue
            children.append(
                _build_folder_node(
                    root=root,
                    current=entry_path,
                    blocked_dirs=blocked_dirs,
                    state=state,
                    depth=depth + 1,
                    max_nodes=max_nodes,
                    max_depth=max_depth,
                )
            )
            continue

        if is_file:
            try:
                file_size = entry.stat(follow_symlinks=False).st_size
            except OSError:
                state["errors"].append({"path": entry.path, "error": "Unable to read file metadata"})
                continue

            extension = Path(entry.name).suffix.lower()
            state["nodes"] += 1

            children.append(
                {
                    "name": entry.name,
                    "type": "file",
                    "path": _relative_posix(root=root, current=entry_path),
                    "size": file_size,
                    "extension": extension,
                    "icon": _icon_for_file(extension),
                    "color": _color_for_file(extension),
                    "language": _language_for_file(extension),
                }
            )

    return {
        "name": current.name if current != root else root.name,
        "type": "folder",
        "path": _relative_posix(root=root, current=current),
        "icon": FOLDER_ICON,
        "color": FOLDER_COLOR,
        "language": None,
        "children": children,
    }


def _relative_posix(*, root: Path, current: Path) -> str:
    relative = current.relative_to(root)
    return "." if str(relative) == "." else relative.as_posix()


def _icon_for_file(extension: str) -> str:
    return ICON_BY_EXTENSION.get(extension, "file")


def _color_for_file(extension: str) -> str:
    return COLOR_BY_EXTENSION.get(extension, "#94A3B8")


def _language_for_file(extension: str) -> str | None:
    return LANGUAGE_BY_EXTENSION.get(extension)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build and save a nested repository file tree as JSON")
    parser.add_argument("repository_path", help="Local repository path")
    parser.add_argument(
        "--output",
        dest="output_path",
        default=None,
        help="Optional output JSON path (default: <repository_path>/repo_structure.json)",
    )
    parser.add_argument("--indent", type=int, default=2, help="JSON indentation level")
    parser.add_argument("--max-nodes", type=int, default=200_000, help="Max nodes to include in output")
    parser.add_argument("--max-depth", type=int, default=None, help="Optional max folder depth")
    parser.add_argument(
        "--include-errors",
        action="store_true",
        help="Attach non-fatal traversal errors to the root node",
    )
    args = parser.parse_args()

    output_file = save_repository_tree(
        args.repository_path,
        output_path=args.output_path,
        indent=args.indent,
        max_nodes=args.max_nodes,
        max_depth=args.max_depth,
        include_errors=args.include_errors,
    )
    print(f"Saved repository structure to: {output_file}")
