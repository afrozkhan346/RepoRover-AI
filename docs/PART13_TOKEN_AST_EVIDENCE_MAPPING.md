# Part 13 - Token-Level Lexical Extraction + AST Evidence Mapping

Date: 2026-04-06
Status: Completed

## Goal

Attach explicit source-backed evidence to token and AST traces so explainability output can cite the exact lexical spans and AST containers involved in a finding.

## Implemented Changes

### 1) Evidence-rich trace schema

Updated `backend/app/schemas/explainability_traces.py` to add a reusable `SourceEvidence` model.

Token and AST traces now carry optional nested evidence with:

- `kind`
- `excerpt`
- `start_point`
- `end_point`
- `unit_type`
- `unit_name`

### 2) Token trace evidence mapping

Updated `backend/app/services/explainability_trace_service.py` so lexical tokens are matched against the surrounding AST unit when possible.

Token traces now include:

- the token span
- a source excerpt around the token
- the containing AST unit type/name when available

### 3) AST trace source evidence

AST traces now include a source excerpt for each traced unit span.

This keeps the trace output aligned with the normalized Tree-sitter parsing work completed in Part 12.

### 4) Validation

Smoke-tested the explainability trace service with the checked-in virtualenv.

Observed output confirmed:

- token traces are emitted
- AST traces are emitted
- token evidence kind is `lexical-token`
- AST evidence kind is `ast-span`
- token evidence includes AST unit context

## Outcome

Part 13 is complete:

- explainability traces now carry explicit source evidence
- token traces are linked to AST context when possible
- AST traces now include source-backed span excerpts