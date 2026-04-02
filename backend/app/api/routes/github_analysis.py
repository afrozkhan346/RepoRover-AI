from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.github_analysis import (
    GitHubAnalysisRequest,
    GitHubAnalysisResponse,
    LocalRepositoryAnalysisRequest,
)
from app.services.github_analysis import analyze_local_repository, analyze_repository, analyze_zip_repository

router = APIRouter()


@router.post("/analyze", response_model=GitHubAnalysisResponse)
def analyze_github_repository(payload: GitHubAnalysisRequest) -> dict:
    try:
        return analyze_repository(payload.github_url)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "INVALID_INPUT"}) from error
    except RuntimeError as error:
        raise HTTPException(status_code=502, detail={"detail": str(error), "code": "GITHUB_API_ERROR"}) from error


@router.post("/analyze-local", response_model=GitHubAnalysisResponse)
def analyze_local_folder(payload: LocalRepositoryAnalysisRequest) -> dict:
    try:
        return analyze_local_repository(payload.local_path)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "INVALID_LOCAL_PATH"}) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail={"detail": str(error), "code": "LOCAL_ANALYSIS_ERROR"}) from error


@router.post("/analyze-archive", response_model=GitHubAnalysisResponse)
async def analyze_zip_archive(file: UploadFile = File(...)) -> dict:
    try:
        if not file.filename or not file.filename.lower().endswith(".zip"):
            raise ValueError("Only ZIP archives are supported")
        archive_bytes = await file.read()
        return analyze_zip_repository(archive_bytes, file.filename)
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "INVALID_ARCHIVE"}) from error
    except RuntimeError as error:
        raise HTTPException(status_code=500, detail={"detail": str(error), "code": "ARCHIVE_ANALYSIS_ERROR"}) from error
