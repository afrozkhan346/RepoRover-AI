from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import os

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.services.ast_parser import parse_project_code
from app.services.gap_detector import analyze_gaps
from app.services.graph_analysis_service import dfs_traversal
from app.services.graph_builder import analyze_graph, build_graph, build_system_graph
from app.services.parser import parse_project
from app.services.priority_engine import generate_priority
from app.services.repository_loader import RepositoryLoadError, clone_repository_with_metadata
from app.services.understanding import understand_project
from app.services.risk_analyzer import analyze_risks

router = APIRouter()


def graph_to_json(graph) -> dict[str, list[dict[str, object]]]:
    nodes: list[dict[str, object]] = []
    edges: list[dict[str, object]] = []

    for node in graph.nodes:
        nodes.append(
            {
                "id": str(node),
                "data": {"label": str(node)},
            }
        )

    for source, target, data in graph.edges(data=True):
        edges.append(
            {
                "id": f"{source}-{target}",
                "source": str(source),
                "target": str(target),
                "label": str(data.get("relation", "")),
            }
        )

    return {"nodes": nodes, "edges": edges}


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
        clone_result = clone_repository_with_metadata(repo_url.strip())
        local_path = clone_result.local_path
    except RepositoryLoadError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": error.code}) from error
    except Exception as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "CLONE_FAILED"}) from error

    return {
        "message": "Repo cloned",
        "repo_url": repo_url,
        "project_path": str(local_path),
        "ingestion": {
            "operation": clone_result.metadata.operation,
            "workspace_path": clone_result.metadata.workspace_path,
            "workspace_policy": clone_result.metadata.workspace_policy,
            "cleaned_entries": clone_result.metadata.cleaned_entries,
            "fetched_updates": clone_result.metadata.fetched_updates,
        },
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
def get_graph(project_name: str) -> dict[str, object]:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        ast_data = parse_project_code(str(path))
        graph, call_edge_info = build_graph(ast_data)
        summary = analyze_graph(graph, call_edge_info)
        full_graph = build_system_graph(str(path))
        return {
            **summary,
            "graph": full_graph,
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "GRAPH_BUILD_FAILED"}) from error


@router.get("/graph-full/{project_name}")
def full_graph(project_name: str) -> dict[str, list[dict[str, object]]]:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        ast_data = parse_project_code(str(path))
        graph, _ = build_graph(ast_data)
        return graph_to_json(graph)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "GRAPH_BUILD_FAILED"}) from error


@router.get("/flow/{project_name}")
def get_flow(project_name: str) -> dict[str, list[str]]:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        ast_data = parse_project_code(str(path))
        graph, _ = build_graph(ast_data)
        start_node = next(iter(graph.nodes), None)
        flow = dfs_traversal(graph, start_node)
        return {"execution_flow": flow}
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "FLOW_BUILD_FAILED"}) from error


@router.get("/understand/{project_name}")
def understand(project_name: str) -> dict:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        return understand_project(str(path))
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "UNDERSTAND_FAILED"}) from error


@router.get("/gaps/{project_name}")
def get_gaps(project_name: str) -> dict[str, list[dict[str, str]]]:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        ast_data = parse_project_code(str(path))
        gaps = analyze_gaps(str(path), ast_data)
        return {"gaps": gaps}
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "GAP_ANALYSIS_FAILED"}) from error


@router.get("/risk/{project_name}")
def get_risk(project_name: str) -> dict[str, list[dict[str, object]]]:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        ast_data = parse_project_code(str(path))
        graph, _ = build_graph(ast_data)
        risks = analyze_risks(ast_data, graph)
        return {"risks": risks}
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "RISK_ANALYSIS_FAILED"}) from error


@router.get("/priority/{project_name}")
def get_priority(project_name: str) -> dict[str, object]:
    safe_name = Path(project_name).name
    if safe_name != project_name or safe_name in {"", ".", ".."}:
        raise HTTPException(status_code=400, detail={"detail": "Invalid project name", "code": "INVALID_PROJECT"})

    path = _projects_root() / safe_name
    if not path.exists() or not path.is_dir():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "PROJECT_NOT_FOUND"})

    try:
        ast_data = parse_project_code(str(path))
        graph, _ = build_graph(ast_data)
        risks = analyze_risks(ast_data, graph)
        return generate_priority(ast_data, graph, risks)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "PRIORITY_ANALYSIS_FAILED"}) from error
