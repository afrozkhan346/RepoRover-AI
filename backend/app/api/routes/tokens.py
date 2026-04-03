from fastapi import APIRouter, HTTPException

from app.engine.parser import ParserEngine
from app.schemas.tokens import TokenizeRequest, TokenizeResponse

router = APIRouter()
parser_engine = ParserEngine()


@router.post("/preview", response_model=TokenizeResponse)
def tokenize_preview(payload: TokenizeRequest) -> TokenizeResponse:
    try:
        result = parser_engine.extract_tokens(
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
