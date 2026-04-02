from __future__ import annotations

import os
import re
from datetime import datetime, timezone
from typing import Any

import torch

try:
    import spacy
except Exception:  # pragma: no cover - optional runtime dependency handling
    spacy = None

try:
    from transformers import pipeline as hf_pipeline
except Exception:  # pragma: no cover - optional runtime dependency handling
    hf_pipeline = None


DEFAULT_MODEL = "google/flan-t5-small"


class AICodeTutorPipeline:
    def __init__(self) -> None:
        self.model_name = os.getenv("HF_CODE_TUTOR_MODEL", DEFAULT_MODEL)
        self._spacy_nlp: Any = None
        self._hf_generator: Any = None

    def _load_spacy(self) -> Any:
        if self._spacy_nlp is not None:
            return self._spacy_nlp
        if spacy is None:
            return None
        try:
            self._spacy_nlp = spacy.load("en_core_web_sm")
        except Exception:
            self._spacy_nlp = spacy.blank("en")
            if "sentencizer" not in self._spacy_nlp.pipe_names:
                self._spacy_nlp.add_pipe("sentencizer")
        return self._spacy_nlp

    def _load_hf_generator(self) -> Any:
        if self._hf_generator is not None:
            return self._hf_generator
        if hf_pipeline is None:
            return None
        try:
            device = 0 if torch.cuda.is_available() else -1
            self._hf_generator = hf_pipeline(
                "text2text-generation",
                model=self.model_name,
                device=device,
            )
        except Exception:
            self._hf_generator = None
        return self._hf_generator

    def _extract_key_concepts(self, code: str, question: str | None, language: str | None) -> list[str]:
        concept_source = "\n".join(part for part in [language or "", question or "", code] if part)
        nlp = self._load_spacy()
        if nlp is None:
            identifiers = re.findall(r"[A-Za-z_][A-Za-z0-9_]{3,}", concept_source)
            return list(dict.fromkeys(identifiers))[:8]

        doc = nlp(concept_source)
        candidates: list[str] = []
        for token in doc:
            if token.is_stop or token.is_punct or token.like_num:
                continue
            if len(token.text) < 4:
                continue
            candidates.append(token.lemma_.lower())
        return list(dict.fromkeys(candidates))[:8]

    def _estimate_complexity(self, code: str) -> float:
        lines = [ln for ln in code.splitlines() if ln.strip()]
        branch_count = len(re.findall(r"\b(if|for|while|match|case|try|except|elif)\b", code))
        function_count = len(re.findall(r"\b(def|function|class)\b", code))
        import_count = len(re.findall(r"\b(import|from)\b", code))
        avg_line_len = (sum(len(ln) for ln in lines) / len(lines)) if lines else 0.0

        features = torch.tensor(
            [
                float(len(lines)),
                float(branch_count),
                float(function_count),
                float(import_count),
                float(avg_line_len),
            ],
            dtype=torch.float32,
        )
        weights = torch.tensor([0.04, 0.25, 0.2, 0.1, 0.03], dtype=torch.float32)
        raw_score = torch.dot(features, weights).item()
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

    def _hf_explanation(self, code: str, language: str | None, question: str | None, complexity_score: float) -> str | None:
        generator = self._load_hf_generator()
        if generator is None:
            return None

        prompt = build_explanation_prompt(code=code, language=language, question=question)
        augmented_prompt = (
            prompt
            + "\n\n"
            + f"Estimated complexity score: {complexity_score}/10. "
            + "Respond as concise markdown with sections: Overview, Flow, Key Concepts, Improvements."
        )
        try:
            output = generator(augmented_prompt, max_new_tokens=220, do_sample=False)
            if output and isinstance(output, list):
                generated = output[0].get("generated_text", "").strip()
                if generated:
                    return generated
        except Exception:
            return None
        return None


def build_explanation_prompt(code: str, language: str | None, question: str | None) -> str:
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


def explain_code(code: str, language: str | None, question: str | None) -> dict[str, str | float | list[str] | None]:
    key_concepts = PIPELINE._extract_key_concepts(code=code, question=question, language=language)
    complexity_score = PIPELINE._estimate_complexity(code)

    hf_output = PIPELINE._hf_explanation(
        code=code,
        language=language,
        question=question,
        complexity_score=complexity_score,
    )

    explanation = hf_output or PIPELINE._fallback_explanation(
        code=code,
        language=language,
        question=question,
        key_concepts=key_concepts,
        complexity_score=complexity_score,
    )

    pipeline_mode = "huggingface+spacy+pytorch" if hf_output else "spacy+pytorch+fallback"

    return {
        "explanation": explanation,
        "language": language,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pipeline": pipeline_mode,
        "model": PIPELINE.model_name if hf_output else None,
        "complexity_score": complexity_score,
        "key_concepts": key_concepts,
    }
