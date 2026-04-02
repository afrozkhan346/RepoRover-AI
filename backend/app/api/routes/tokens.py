from fastapi import APIRouter, HTTPException

from app.schemas.tokens import TokenizeRequest, TokenizeResponse
from app.services.token_service import tokenize_source

router = APIRouter()


@router.post("/preview", response_model=TokenizeResponse)
def tokenize_preview(payload: TokenizeRequest) -> TokenizeResponse:
    try:
        result = tokenize_source(
            payload.source_code,
            language=payload.language,
            file_extension=payload.file_extension,
            max_tokens=payload.max_tokens,
        )
        return TokenizeResponse(
            language=result.language,
            total_tokens=result.total_tokens,
            truncated=result.truncated,
            tokens=result.tokens,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "TOKENIZER_ERROR"}) from error
