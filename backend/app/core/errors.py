from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.schemas.common import APIError


class NotFoundError(Exception):
    pass


class BadRequestError(Exception):
    pass


def bad_request(detail: str, code: str | None = None) -> HTTPException:
    return HTTPException(status_code=400, detail=APIError(detail=detail, code=code).model_dump())


def not_found(detail: str, code: str | None = None) -> HTTPException:
    return HTTPException(status_code=404, detail=APIError(detail=detail, code=code).model_dump())


def service_unavailable(detail: str, code: str | None = None) -> HTTPException:
    return HTTPException(status_code=503, detail=APIError(detail=detail, code=code).model_dump())


def normalize_error_detail(detail: Any, fallback_code: str | None = None) -> APIError:
    if isinstance(detail, APIError):
        return detail

    if isinstance(detail, Mapping):
        mapped_detail = detail.get("detail")
        mapped_code = detail.get("code")
        if isinstance(mapped_detail, str):
            return APIError(detail=mapped_detail, code=mapped_code if isinstance(mapped_code, str) else fallback_code)

    if isinstance(detail, str):
        return APIError(detail=detail, code=fallback_code)

    return APIError(detail="Unexpected error", code=fallback_code)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        payload = normalize_error_detail(exc.detail)
        return JSONResponse(status_code=exc.status_code, content=payload.model_dump())

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        payload = APIError(detail="Validation error", code="VALIDATION_ERROR").model_dump()
        payload["issues"] = exc.errors()
        return JSONResponse(status_code=422, content=payload)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, __: Exception) -> JSONResponse:
        payload = APIError(detail="Internal server error", code="INTERNAL_SERVER_ERROR")
        return JSONResponse(status_code=500, content=payload.model_dump())
