from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.ast_parser import parse_project_code
from app.services.graph_builder import analyze_graph, build_graph
from app.services.parser import parse_project
from app.services.repository_loader import clone_repository

router = APIRouter()


def _projects_root() -> Path:
    root = Path(__file__).resolve().parents[3] / "projects"
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_relative_path(raw_path: str) -> Path:
    normalized = raw_path.replace("\\", "/").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail={"detail": "Invalid file path", "code": "INVALID_PATH"})

    candidate = Path(normalized)
    if candidate.is_absolute() or any(part in {"", ".", ".."} for part in candidate.parts):
        raise HTTPException(status_code=400, detail={"detail": "Unsafe file path", "code": "UNSAFE_PATH"})

    if os.path.splitdrive(normalized)[0]:
        raise HTTPException(status_code=400, detail={"detail": "Drive paths are not allowed", "code": "UNSAFE_PATH"})

    return candidate


@router.post("/upload")
async def upload_project(files: list[UploadFile] = File(...), relative_paths: list[str] = Form(default=[])) -> dict:
    if not files:
        raise HTTPException(status_code=400, detail={"detail": "At least one file is required", "code": "MISSING_FILE"})

    if relative_paths and len(relative_paths) != len(files):
        raise HTTPException(status_code=400, detail={"detail": "Path/file count mismatch", "code": "PATH_MISMATCH"})

    projects_root = _projects_root()
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    project_dir = projects_root / f"upload-project-{timestamp}-{uuid4().hex[:8]}"
    project_dir.mkdir(parents=True, exist_ok=True)

    saved_count = 0
    total_bytes = 0

    for index, file in enumerate(files):
        if not file.filename:
            continue

        incoming_path = relative_paths[index] if relative_paths else file.filename
        safe_relative = _safe_relative_path(incoming_path)
        target_path = project_dir / safe_relative
        target_path.parent.mkdir(parents=True, exist_ok=True)

        contents = await file.read()
        if not contents:
            continue

        target_path.write_bytes(contents)
        saved_count += 1
        total_bytes += len(contents)

    if saved_count == 0:
        raise HTTPException(status_code=400, detail={"detail": "No valid file content found", "code": "EMPTY_UPLOAD"})

    return {
        "message": "Project uploaded",
        "project_path": str(project_dir),
        "files_saved": saved_count,
        "total_size": total_bytes,
    }


@router.post("/clone")
def clone_project(repo_url: str = Form(...)) -> dict:
    if not repo_url.strip():
        raise HTTPException(status_code=400, detail={"detail": "repo_url is required", "code": "MISSING_REPO_URL"})

    try:
        _, local_path = clone_repository(repo_url.strip())
    except Exception as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "CLONE_FAILED"}) from error

    return {
        "message": "Repo cloned",
        "repo_url": repo_url,
        "project_path": str(local_path),
    }


@router.get("/analyze/{project_name}")
def analyze_project(project_name: str) -> dict:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        return parse_project(str(path))
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "PARSE_FAILED"}) from error


@router.get("/code-analysis/{project_name}")
def analyze_code(project_name: str) -> list[dict]:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        return parse_project_code(str(path))
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "CODE_ANALYSIS_FAILED"}) from error


@router.get("/graph/{project_name}")
def get_graph(project_name: str) -> dict[str, int]:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        ast_data = parse_project_code(str(path))
        graph, call_edge_info = build_graph(ast_data)
        return analyze_graph(graph, call_edge_info)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "GRAPH_BUILD_FAILED"}) from error
