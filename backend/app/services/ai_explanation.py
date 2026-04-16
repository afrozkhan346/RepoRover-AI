from __future__ import annotations

import os
import re
from datetime import datetime, timezone

from app.schemas.ai_explanation import ExplanationEvidence
from app.services.llm_service import generate_text
from app.services.parser_service import parse_structure
from app.services.token_service import tokenize_source


DEFAULT_MODEL = "google/flan-t5-small"


class AICodeTutorPipeline:
    def __init__(self) -> None:
        self.model_name = os.getenv("HF_CODE_TUTOR_MODEL", DEFAULT_MODEL)

    def _extract_key_concepts(
        self, code: str, question: str | None, language: str | None
    ) -> list[str]:
        concept_source = "\n".join(
            part for part in [language or "", question or "", code] if part
        )
        identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", concept_source)
        return list(dict.fromkeys(identifiers))[:8]

    def _extract_named_entities(
        self, code: str, question: str | None, language: str | None
    ) -> list[str]:
        entity_source = "\n".join(
            part for part in [language or "", question or "", code] if part
        )
        matches = re.findall(r"\b[A-Z][A-Za-z0-9_]{2,}\b", entity_source)
        return list(dict.fromkeys(matches))[:8]

    def _line_excerpt(
        self,
        code: str,
        start_point: tuple[int, int] | None,
        end_point: tuple[int, int] | None,
    ) -> str:
        if start_point is None or end_point is None:
            return code[:240].strip()

        lines = code.splitlines()
        if not lines:
            return code[:240].strip()

        start_line = max(start_point[0] - 1, 0)
        end_line = min(end_point[0] + 1, len(lines) - 1)
        excerpt = "\n".join(lines[start_line : end_line + 1]).strip()
        return excerpt[:240]

    def _extract_evidence(
        self, code: str, language: str | None, question: str | None
    ) -> list[ExplanationEvidence]:
        token_result = tokenize_source(
            code, language=language, file_extension=None, max_tokens=400
        )
        structure = parse_structure(
            code,
            language=language,
            file_extension=None,
            max_tree_nodes=200,
            max_depth=8,
        )

        interesting_tokens = [
            token
            for token in token_result.tokens
            if token.token_type.lower()
            in {"identifier", "name", "keyword", "call_expression", "comment"}
            or token.lexeme.strip()
            in {"def", "class", "import", "from", "return", "async"}
        ]

        evidence: list[ExplanationEvidence] = []

        for token in interesting_tokens[:6]:
            label = token.lexeme.strip() or token.token_type
            evidence.append(
                ExplanationEvidence(
                    kind="token",
                    label=label,
                    excerpt=self._line_excerpt(
                        code, token.start_point, token.end_point
                    ),
                    start_point=token.start_point,
                    end_point=token.end_point,
                    related_symbols=[label] if label else [],
                    note=f"lexical token from {token.token_type}",
                )
            )

        ast_units = (
            structure.imports[:4] + structure.classes[:4] + structure.functions[:8]
        )
        for unit in ast_units[:8]:
            label = unit.name or unit.unit_type
            evidence.append(
                ExplanationEvidence(
                    kind="ast",
                    label=label,
                    excerpt=self._line_excerpt(code, unit.start_point, unit.end_point),
                    start_point=unit.start_point,
                    end_point=unit.end_point,
                    related_symbols=[symbol for symbol in [unit.name] if symbol],
                    note=f"AST {unit.unit_type}",
                )
            )

        call_matches = list(
            dict.fromkeys(re.findall(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(", code))
        )
        graph_nodes = [unit.name for unit in ast_units if unit.name]
        graph_labels = [name for name in graph_nodes[:4] if name]
        if call_matches:
            graph_labels.extend(call_matches[:4])

        graph_excerpt = (
            "Nodes: " + ", ".join(graph_labels[:6])
            if graph_labels
            else "No graph nodes inferred"
        )
        if question:
            graph_excerpt = f"Question focus: {question.strip()} | " + graph_excerpt

        evidence.append(
            ExplanationEvidence(
                kind="graph",
                label="micro-call-graph",
                excerpt=graph_excerpt[:240],
                related_symbols=graph_labels[:6],
                note="inferred local graph from imports, declarations, and call candidates",
            )
        )

        return evidence

    def _estimate_complexity(self, code: str) -> float:
        lines = [ln for ln in code.splitlines() if ln.strip()]
        branch_count = len(
            re.findall(r"\b(if|for|while|match|case|try|except|elif)\b", code)
        )
        function_count = len(re.findall(r"\b(def|function|class)\b", code))
        import_count = len(re.findall(r"\b(import|from)\b", code))
        avg_line_len = (sum(len(ln) for ln in lines) / len(lines)) if lines else 0.0

        feature_values = [
            float(len(lines)),
            float(branch_count),
            float(function_count),
            float(import_count),
            float(avg_line_len),
        ]
        weight_values = [0.04, 0.25, 0.2, 0.1, 0.03]
        raw_score = sum(f * w for f, w in zip(feature_values, weight_values))
        return round(min(10.0, max(0.0, raw_score)), 2)

    def _fallback_explanation(
        self,
        code: str,
        language: str | None,
        question: str | None,
        key_concepts: list[str],
        complexity_score: float,
    ) -> str:
        line_count = len([ln for ln in code.splitlines() if ln.strip()])
        summary = [
            f"Language focus: {language or 'unknown'}.",
            f"Approximate complexity score: {complexity_score}/10.",
            f"Non-empty lines: {line_count}.",
        ]
        if question:
            summary.append(f"Question intent: {question.strip()}")

        concept_line = ", ".join(key_concepts[:6]) if key_concepts else "none detected"
        return (
            "Overview:\n"
            + "\n".join(f"- {item}" for item in summary)
            + "\n\n"
            + "Likely key concepts:\n"
            + f"- {concept_line}\n\n"
            + "How to read this code:\n"
            + "- Start from top-level imports and declarations.\n"
            + "- Trace control flow branches and function boundaries.\n"
            + "- Validate side effects, data transformations, and return paths.\n"
            + "- If behavior is unclear, add targeted unit tests around branch-heavy sections."
        )

    def _api_explanation(
        self,
        code: str,
        language: str | None,
        question: str | None,
        complexity_score: float,
    ) -> str | None:
        system_prompt = "You are an expert code tutor. Explain code clearly with sections: Overview, Flow, Key Concepts, Improvements."
        prompt = build_explanation_prompt(
            code=code, language=language, question=question
        )
        user_prompt = prompt + f"\n\nEstimated complexity score: {complexity_score}/10."
        return generate_text(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.3,
            max_tokens=350,
        )


def build_explanation_prompt(
    code: str, language: str | None, question: str | None
) -> str:
    if question:
        return (
            f"You are an expert code tutor. A student is learning {language or 'programming'} and has the following question about this code:\n\n"
            f"Code:\n```{language or ''}\n{code}\n```\n\n"
            f"Question: {question}\n\n"
            "Provide a clear, educational explanation that helps them understand the code and answers their question. "
            "Break down complex concepts into simple terms."
        )

    return (
        f"You are an expert code tutor. Explain the following {language or ''} code in a clear, educational way. "
        "Break down what each part does, explain key concepts, and highlight any best practices or potential improvements:\n\n"
        f"```{language or ''}\n{code}\n```"
    )


PIPELINE = AICodeTutorPipeline()


def explain_code(
    code: str, language: str | None, question: str | None
) -> dict[str, str | float | list[str] | None]:
    key_concepts = PIPELINE._extract_key_concepts(
        code=code, question=question, language=language
    )
    named_entities = PIPELINE._extract_named_entities(
        code=code, question=question, language=language
    )
    evidence = PIPELINE._extract_evidence(
        code=code, language=language, question=question
    )
    complexity_score = PIPELINE._estimate_complexity(code)

    api_output = PIPELINE._api_explanation(
        code=code,
        language=language,
        question=question,
        complexity_score=complexity_score,
    )

    explanation = api_output or PIPELINE._fallback_explanation(
        code=code,
        language=language,
        question=question,
        key_concepts=key_concepts,
        complexity_score=complexity_score,
    )

    pipeline_mode = "api-llm" if api_output else "regex-fallback"

    return {
        "explanation": explanation,
        "language": language,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline": pipeline_mode,
        "model": PIPELINE.model_name if api_output else None,
        "complexity_score": complexity_score,
        "key_concepts": key_concepts,
        "named_entities": named_entities,
        "evidence": evidence,
    }
