from pydantic import BaseModel


class APIError(BaseModel):
    detail: str
    code: str | None = None


class APIStatus(BaseModel):
    status: str


class APISuccessMessage(BaseModel):
    message: str
