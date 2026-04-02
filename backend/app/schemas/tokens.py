from pydantic import BaseModel, Field


class TokenizeRequest(BaseModel):
    language: str | None = Field(default=None)
    file_extension: str | None = Field(default=None)
    source_code: str = Field(..., min_length=1)
    max_tokens: int = Field(default=500, ge=20, le=5000)


class NormalizedToken(BaseModel):
    token_type: str
    lexeme: str
    start_byte: int
    end_byte: int
    start_point: tuple[int, int]
    end_point: tuple[int, int]


class TokenizeResponse(BaseModel):
    language: str
    total_tokens: int
    truncated: bool
    tokens: list[NormalizedToken]
