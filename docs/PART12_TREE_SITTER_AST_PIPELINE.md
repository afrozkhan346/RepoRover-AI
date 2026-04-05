# Part 12 - Tree-sitter Parser Pipeline + Normalized AST Outputs

Date: 2026-04-06
Status: Completed

## Goal

Replace the project-wide regex AST scan with a Tree-sitter-backed pipeline and emit normalized AST evidence alongside the legacy compatibility payload.

## Implemented Changes

### 1) Tree-sitter-backed project parsing

Updated `backend/app/services/ast_parser.py` so supported source files now use Tree-sitter parsing for project-wide AST extraction.

Supported files now flow through a normalized pipeline for:

- Python
- JavaScript / JSX
- TypeScript / TSX

Each parsed file now includes:

- preview AST nodes
- syntax-tree root snapshot
- imports
- classes
- functions
- call-site evidence

### 2) Normalized AST schema layer

Added `backend/app/schemas/project_ast.py` to make the project AST output explicit and serializable.

The normalized file payload includes:

- `preview_nodes`
- `root`
- `imports`
- `classes`
- `functions`
- `calls`

### 3) Legacy compatibility preserved

`parse_project_code(...)` still returns the legacy list-of-dicts shape consumed by existing services, but each file entry now carries a `normalized_ast` object for downstream use.

This keeps compatibility for:

- graph building
- risk analysis
- priority scoring
- understanding summaries

### 4) Validation

Smoke-tested the project parser against the backend workspace using the local virtualenv runtime.

Observed output shape includes:

- `file`
- `path`
- `language`
- `data`
  - `imports`
  - `classes`
  - `functions`
  - `normalized_ast`

## Outcome

Part 12 is complete:

- project AST extraction is Tree-sitter-backed
- normalized AST evidence is emitted per file
- downstream services continue to work against the preserved compatibility shape