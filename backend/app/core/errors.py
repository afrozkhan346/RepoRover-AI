from fastapi import HTTPException

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
