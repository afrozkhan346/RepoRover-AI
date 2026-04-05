# Part 17 - Explanation Pipeline Tying AI Findings to Token/AST/Graph Evidence

Date: 2026-04-06
Status: Completed

## Goal

Tie the AI code-explanation output back to concrete token, AST, and graph evidence so the explanation layer is grounded in source-backed signals.

## Implemented Changes

### 1) Structured evidence model

Updated `backend/app/schemas/ai_explanation.py` with an `ExplanationEvidence` model and an `evidence` list on the explanation response.

Each evidence item includes:

- `kind`
- `label`
- `excerpt`
- optional span points
- related symbols
- a short note

### 2) Token evidence mapping

Updated `backend/app/services/ai_explanation.py` so code explanations now extract token evidence from the same lexical pipeline used elsewhere in the backend.

### 3) AST evidence mapping

The explanation pipeline now also extracts AST evidence from parsed imports, classes, and functions so the explanation is anchored to structural source units.

### 4) Graph evidence mapping

The explanation pipeline now emits a lightweight inferred graph evidence item based on imports, declarations, and call candidates found in the snippet.

This keeps the explanation output tied to graph-style reasoning even when the input is just a code snippet.

### 5) Validation

Smoke-tested the explanation pipeline with the checked-in virtualenv.

Observed output confirmed:

- the explanation pipeline still returns a normal explanation payload
- key concepts are populated
- named entities are populated
- token evidence is emitted
- AST evidence is emitted
- graph evidence is emitted

## Outcome

Part 17 is complete:

- AI findings are now grounded in token, AST, and graph evidence
- the explanation API remains backward compatible
- downstream consumers can surface richer evidence without changing the request shape