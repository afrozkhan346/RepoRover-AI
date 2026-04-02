from __future__ import annotations

from pathlib import Path

from app.schemas.risk_scoring import RiskScoringResponse, RiskSignal, SeverityDistribution
from app.services.call_graph_service import build_call_graph
from app.services.graph_analysis_service import analyze_graph
from app.services.quality_analysis_service import analyze_quality


def score_risk(local_path: str, max_files: int = 2000) -> RiskScoringResponse:
    root = Path(local_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError("local_path must be an existing directory")

    quality = analyze_quality(str(root), max_files=max_files)
    call_graph = build_call_graph(str(root), max_files=max_files)
    graph_analysis = analyze_graph(
        local_path=str(root),
        graph_type="dependency",
        max_files=max_files,
        traversal_start=None,
    )

    high = sum(1 for issue in quality.issues if issue.severity == "high")
    medium = sum(1 for issue in quality.issues if issue.severity == "medium")
    low = sum(1 for issue in quality.issues if issue.severity == "low")

    issue_penalty = high * 8 + medium * 4 + low * 1.5
    gap_penalty = len(quality.design_gaps) * 3.5
    graph_penalty = min(15.0, graph_analysis.metrics.connected_components * 0.8)
    flow_penalty = 0.0
    if call_graph.summary.functions_found > 0:
        external_ratio = call_graph.summary.call_edges / max(1, call_graph.summary.functions_found)
        flow_penalty = min(10.0, external_ratio * 1.2)

    total_penalty = issue_penalty + gap_penalty + graph_penalty + flow_penalty
    reliability_score = round(max(0.0, 100.0 - total_penalty), 2)
    risk_score = round(min(100.0, total_penalty), 2)

    top_signals = [
        RiskSignal(
            title="Issue severity burden",
            weight=round(issue_penalty, 2),
            detail=f"Computed from high/medium/low issue counts ({high}/{medium}/{low}).",
        ),
        RiskSignal(
            title="Design gap pressure",
            weight=round(gap_penalty, 2),
            detail=f"Detected {len(quality.design_gaps)} design gaps impacting delivery confidence.",
        ),
        RiskSignal(
            title="Graph fragmentation",
            weight=round(graph_penalty, 2),
            detail=f"Dependency graph has {graph_analysis.metrics.connected_components} connected components.",
        ),
        RiskSignal(
            title="Call-flow spread",
            weight=round(flow_penalty, 2),
            detail=(
                "Penalty derived from call-edge density relative to discovered functions "
                f"({call_graph.summary.call_edges}/{call_graph.summary.functions_found})."
            ),
        ),
    ]

    summary = (
        "Risk scoring combines static quality issues, design gaps, dependency fragmentation, and call-flow spread "
        f"into reliability={reliability_score} and risk={risk_score}."
    )

    return RiskScoringResponse(
        reliability_score=reliability_score,
        risk_score=risk_score,
        severity_distribution=SeverityDistribution(high=high, medium=medium, low=low),
        top_signals=top_signals,
        summary=summary,
    )
