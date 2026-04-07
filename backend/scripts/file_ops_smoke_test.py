from __future__ import annotations

import io
import json
import tempfile
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient
from fastapi import HTTPException

from app.core.config import settings
from app.main import app
from app.api.routes.project import _safe_relative_path
from app.services.ast_parser import parse_project_code
from app.services.repository_loader import RepositoryLoadError, load_repository_from_zip


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_upload_handler(client: TestClient) -> dict:
    ext = settings.projects_allowed_extensions[0] if settings.projects_allowed_extensions else ".txt"
    filename = f"sample{ext}"

    response = client.post(
        "/project/upload",
        files=[("files", (filename, b"print('hello')\n", "text/plain"))],
    )

    _assert(response.status_code == 200, f"upload failed: {response.status_code} {response.text}")
    payload = response.json()
    _assert("project_path" in payload, "upload response missing project_path")
    _assert(payload.get("files_saved") == 1, "upload response files_saved should be 1")
    return {"status": "PASS", "http_status": response.status_code, "project_path": payload.get("project_path")}


def test_file_type_validation(client: TestClient) -> dict:
    if not settings.projects_allowed_extensions:
        return {
            "status": "SKIP",
            "reason": "projects_allowed_extensions is empty; extension validation is disabled by config",
        }

    forbidden_name = "forbidden.invalidext"
    response = client.post(
        "/project/upload",
        files=[("files", (forbidden_name, b"x", "application/octet-stream"))],
    )

    _assert(response.status_code == 400, f"expected 400 for forbidden extension, got {response.status_code}")
    detail = response.json().get("detail", {})
    _assert(detail.get("code") == "UNSUPPORTED_FILE_EXTENSION", f"unexpected error code: {detail}")
    return {"status": "PASS", "http_status": response.status_code, "error_code": detail.get("code")}


def test_path_normalization(client: TestClient) -> dict:
    _ = client  # keep consistent signature with other test helpers

    try:
        _safe_relative_path("../escape.py")
        raise AssertionError("unsafe path should fail but succeeded")
    except HTTPException as exc:
        _assert(exc.status_code == 400, f"expected 400, got {exc.status_code}")
        detail = exc.detail if isinstance(exc.detail, dict) else {}
        _assert(detail.get("code") == "UNSAFE_PATH", f"unexpected error detail: {exc.detail}")

    safe = _safe_relative_path("src/main.py")
    _assert(str(safe).replace("\\", "/") == "src/main.py", "safe normalized path mismatch")
    return {"status": "PASS", "unsafe": "blocked:UNSAFE_PATH", "safe": "src/main.py"}


def test_zip_extraction() -> dict:
    safe_buf = io.BytesIO()
    with zipfile.ZipFile(safe_buf, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("project/main.py", "print('ok')\n")

    safe_result = load_repository_from_zip(safe_buf.getvalue(), "safe.zip")
    _assert(Path(safe_result.local_path).exists(), "safe zip result path does not exist")

    unsafe_buf = io.BytesIO()
    with zipfile.ZipFile(unsafe_buf, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("../evil.py", "print('no')\n")

    try:
        load_repository_from_zip(unsafe_buf.getvalue(), "unsafe.zip")
        raise AssertionError("unsafe zip should fail but succeeded")
    except RepositoryLoadError as exc:
        _assert(exc.code == "UNSAFE_PATH", f"unexpected zip error code: {exc.code}")

    return {"status": "PASS", "safe_zip": "accepted", "unsafe_zip": "blocked:UNSAFE_PATH"}


def test_directory_traversal_os_walk() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        nested = root / "pkg" / "sub"
        nested.mkdir(parents=True, exist_ok=True)
        (root / "a.py").write_text("import os\n", encoding="utf-8")
        (nested / "b.py").write_text("def x():\n    return 1\n", encoding="utf-8")

        parsed = parse_project_code(str(root))
        files = {item.get("file") for item in parsed}
        _assert("a.py" in files, f"root file missing from parse results: {files}")
        _assert("pkg/sub/b.py" in files, f"nested file missing from parse results: {files}")

    return {"status": "PASS", "parsed_files": sorted(files)}


def main() -> None:
    results: dict[str, dict] = {}
    failures: list[str] = []

    client = TestClient(app)

    checks = [
        ("file_upload_handler", lambda: test_upload_handler(client)),
        ("zip_extraction_zipfile", test_zip_extraction),
        ("file_type_validation", lambda: test_file_type_validation(client)),
        ("path_normalization", lambda: test_path_normalization(client)),
        ("directory_traversal_os_walk", test_directory_traversal_os_walk),
    ]

    for name, fn in checks:
        try:
            results[name] = fn()
        except Exception as exc:  # pragma: no cover
            results[name] = {"status": "FAIL", "error": str(exc)}
            failures.append(name)

    summary = {
        "passed": sum(1 for item in results.values() if item.get("status") == "PASS"),
        "failed": len(failures),
        "skipped": sum(1 for item in results.values() if item.get("status") == "SKIP"),
        "failures": failures,
    }

    print(json.dumps({"summary": summary, "results": results}, indent=2))

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
