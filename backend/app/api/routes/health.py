from fastapi import APIRouter

from app.core.config import settings
from app.services.llm_service import get_llm_runtime_status

router = APIRouter()


@router.get("")
def health_check() -> dict[str, str]:
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


@router.get("/version")
def version_info() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "api_prefix": settings.api_prefix,
    }


@router.get("/llm")
def llm_health() -> dict:
    return get_llm_runtime_status()
