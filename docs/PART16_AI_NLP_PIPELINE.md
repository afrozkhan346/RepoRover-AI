# Part 16 - AI/NLP Pipeline Using PyTorch + HuggingFace + spaCy

Date: 2026-04-06
Status: Completed

## Goal

Consolidate the code-explanation path into a reusable AI/NLP pipeline that uses PyTorch, HuggingFace, and spaCy-backed extraction while preserving the current explanation API.

## Implemented Changes

### 1) Structured NLP signals in code explanations

Updated `backend/app/services/ai_explanation.py` so the explanation pipeline now returns named entities alongside key concepts and complexity metadata.

The pipeline now extracts:

- key concepts
- named entities
- complexity score
- generated explanation text
- pipeline mode metadata

### 2) spaCy-backed extraction with safe fallback

The pipeline continues to prefer spaCy for concept and entity extraction.

When a full spaCy model is unavailable, it falls back to deterministic regex-based extraction so the response still contains useful structured NLP signals.

### 3) HuggingFace + PyTorch explanation path preserved

The existing HuggingFace text-generation path remains in place for richer explanations, with PyTorch used for the complexity estimator and model selection path.

### 4) Schema update

Extended `backend/app/schemas/ai_explanation.py` with a `named_entities` field so the NLP output is serialized cleanly without breaking the current response contract.

### 5) Validation

Smoke-tested the pipeline with the checked-in virtualenv.

Observed output confirmed:

- the pipeline runs end to end
- the fallback mode is stable when HF/spaCy models are unavailable
- key concepts are populated
- named entities are populated

## Outcome

Part 16 is complete:

- the AI/NLP pipeline is backed by PyTorch, HuggingFace, and spaCy
- the response now exposes structured NLP output
- existing explanation routes remain compatible
