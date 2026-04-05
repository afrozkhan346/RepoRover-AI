from __future__ import annotations

from dataclasses import asdict, dataclass
from textwrap import dedent
from typing import Any

from app.services.llm_service import generate_learning_explanations


@dataclass(frozen=True)
class LearningExplanations:
    beginner: str
    intermediate: str
    advanced: str


@dataclass(frozen=True)
class LearningExplanationResult:
    entry_point: str | None
    core_functions: list[str]
    project_type: str
    summary: str
    explanations: LearningExplanations

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _clean_symbol(symbol: str) -> str:
    if symbol.startswith("func:"):
        return symbol.split("func:", 1)[1]
    if symbol.startswith("function:"):
        return symbol.split(":", 1)[1]
    return symbol


def beginner_explanation(summary: str, entry: str | None) -> str:
    entry_text = entry or "an inferred entry module"
    return dedent(
        f"""
    This project is a software system that runs from {entry_text}.

    It performs specific tasks by organizing code into functions and modules.

    The system processes data step by step and produces output based on given inputs.

    Overall, it is designed to help users perform a defined task in a structured way.
    """
    ).strip()


def intermediate_explanation(summary: str, core_funcs: list[str]) -> str:
    cleaned = [_clean_symbol(item) for item in core_funcs]
    core_text = ", ".join(cleaned) if cleaned else "no dominant functions detected"
    return dedent(
        f"""
    The project follows a modular structure where core logic is implemented using functions such as {core_text}.

    These functions interact with each other to process data and control the execution flow.

    The system uses imports and dependencies to organize functionality across multiple files.

    Execution begins from the main entry point and flows through different modules.
    """
    ).strip()


def advanced_explanation(project_type: str, core_funcs: list[str]) -> str:
    core_text = ", ".join(core_funcs) if core_funcs else "no dominant functions detected"
    return dedent(
        f"""
    This {project_type} follows a structured architectural approach with clear separation of concerns.

    Core functionalities are encapsulated within key functions such as {core_text}, which form the backbone of the system.

    The design reflects modular programming principles, enabling scalability and maintainability.

    Inter-module communication and function-level dependencies indicate a layered execution model.
    """
    ).strip()


def generate_explanations(summary: str, entry: str | None, core_funcs: list[str], project_type: str) -> dict[str, str]:
    llm_explanations = generate_learning_explanations(
        summary=summary,
        entry=entry,
        core_funcs=core_funcs,
        project_type=project_type,
    )
    if llm_explanations:
        return llm_explanations

    return {
        "beginner": beginner_explanation(summary, entry),
        "intermediate": intermediate_explanation(summary, core_funcs),
        "advanced": advanced_explanation(project_type, core_funcs),
    }


def explain_project_learning(local_path: str, max_files: int = 2000) -> dict[str, Any]:
    """
    Generate project explanations at three learning levels:
    - beginner
    - intermediate
    - advanced
    """

    from app.services.understanding import understand_project

    understanding = understand_project(local_path, max_files=max_files)

    entry_point = understanding.get("entry_point")
    core_functions = understanding.get("core_functions") or []
    project_type = understanding.get("project_type") or "General Software Project"
    summary = understanding.get("summary") or "Project purpose inferred from repository structure and call graph."

    explanation_payload = generate_explanations(summary, entry_point, core_functions, project_type)
    explanations = LearningExplanations(
        beginner=explanation_payload["beginner"],
        intermediate=explanation_payload["intermediate"],
        advanced=explanation_payload["advanced"],
    )

    result = LearningExplanationResult(
        entry_point=entry_point,
        core_functions=core_functions,
        project_type=project_type,
        summary=summary,
        explanations=explanations,
    )
    return result.to_dict()
