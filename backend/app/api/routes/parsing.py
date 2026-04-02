from fastapi import APIRouter, HTTPException

from app.schemas.parsing import AstStructureRequest, AstStructureResponse, ParseRequest, ParseResponse
from app.services.parser_service import parse_source, parse_structure

router = APIRouter()


@router.post("/ast-preview", response_model=ParseResponse)
def parse_ast_preview(payload: ParseRequest) -> ParseResponse:
    try:
        result = parse_source(
            payload.source_code,
            language=payload.language,
            file_extension=payload.file_extension,
            max_nodes=payload.max_nodes,
        )
        return ParseResponse(
            language=result.language,
            total_nodes=result.total_nodes,
            truncated=result.truncated,
            nodes=result.nodes,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "PARSER_ERROR"}) from error


@router.post("/ast-structure", response_model=AstStructureResponse)
def parse_ast_structure(payload: AstStructureRequest) -> AstStructureResponse:
    try:
        result = parse_structure(
            payload.source_code,
            language=payload.language,
            file_extension=payload.file_extension,
            max_tree_nodes=payload.max_tree_nodes,
            max_depth=payload.max_depth,
        )
        return AstStructureResponse(
            language=result.language,
            total_nodes=result.total_nodes,
            tree_nodes_returned=result.tree_nodes_returned,
            truncated=result.truncated,
            root=result.root,
            imports=result.imports,
            classes=result.classes,
            functions=result.functions,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail={"detail": str(error), "code": "PARSER_ERROR"}) from error
