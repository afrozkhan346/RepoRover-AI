from __future__ import annotations

from collections import deque

import networkx as nx

from app.schemas.call_graph import CallGraphResponse
from app.schemas.dependency_graph import DependencyGraphResponse
from app.schemas.graph_analysis import (
    GraphAnalysisResponse,
    GraphMetrics,
    RankedNode,
    TraversalResult,
)
from app.services.call_graph_service import build_call_graph
from app.services.dependency_graph_service import build_dependency_graph


def _to_networkx_from_dependency(graph: DependencyGraphResponse) -> nx.DiGraph:
    g = nx.DiGraph()
    for node in graph.nodes:
        g.add_node(node.id, label=node.label, node_type=node.node_type)
    for edge in graph.edges:
        g.add_edge(edge.source, edge.target, edge_type=edge.edge_type)
    return g


def _to_networkx_from_call(graph: CallGraphResponse) -> nx.DiGraph:
    g = nx.DiGraph()
    for node in graph.nodes:
        g.add_node(node.id, label=node.label, node_type=node.node_type)
    for edge in graph.edges:
        g.add_edge(edge.source, edge.target, edge_type=edge.edge_type)
    return g


def _ranked(metric: dict[str, float], labels: dict[str, str], top_n: int = 10) -> list[RankedNode]:
    ordered = sorted(metric.items(), key=lambda item: item[1], reverse=True)[:top_n]
    return [
        RankedNode(node_id=node_id, label=labels.get(node_id, node_id), score=float(score))
        for node_id, score in ordered
    ]


def _dfs(g: nx.DiGraph, start: str | None, top_limit: int = 100) -> TraversalResult:
    if g.number_of_nodes() == 0:
        return TraversalResult(start_node=None, dfs_order=[], bfs_order=[])

    chosen = start if start and start in g.nodes else next(iter(g.nodes))
    visited: set[str] = set()
    stack: list[str] = [chosen]
    order: list[str] = []

    while stack and len(order) < top_limit:
        node = stack.pop()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)

        neighbors = list(g.neighbors(node))
        for neighbor in reversed(neighbors):
            if neighbor not in visited:
                stack.append(neighbor)

    return TraversalResult(start_node=chosen, dfs_order=order, bfs_order=[])


def _impact_rank(g: nx.DiGraph, labels: dict[str, str], top_n: int = 10) -> list[RankedNode]:
    degree = nx.degree_centrality(g) if g.number_of_nodes() else {}
    betweenness = nx.betweenness_centrality(g) if g.number_of_nodes() else {}
    impact: dict[str, float] = {}
    for node in g.nodes:
        out_degree = g.out_degree(node)
        impact[node] = float(degree.get(node, 0.0) * 0.4 + betweenness.get(node, 0.0) * 0.4 + out_degree * 0.2)
    return _ranked(impact, labels, top_n=top_n)


def _bfs(g: nx.DiGraph, start: str | None, top_limit: int = 100) -> TraversalResult:
    if g.number_of_nodes() == 0:
        return TraversalResult(start_node=None, dfs_order=[], bfs_order=[])

    chosen = start if start and start in g.nodes else next(iter(g.nodes))
    visited: set[str] = set()
    queue: deque[str] = deque([chosen])
    order: list[str] = []

    while queue and len(order) < top_limit:
        node = queue.popleft()
        if node in visited:
            continue
        visited.add(node)
        order.append(node)
        for neighbor in g.successors(node):
            if neighbor not in visited:
                queue.append(neighbor)

    return TraversalResult(start_node=chosen, dfs_order=[], bfs_order=order)


def analyze_graph(
    *,
    local_path: str,
    graph_type: str = "dependency",
    max_files: int = 2000,
    traversal_start: str | None = None,
) -> GraphAnalysisResponse:
    normalized = graph_type.strip().lower()

    if normalized == "dependency":
        dependency_graph = build_dependency_graph(local_path, max_files=max_files)
        g = _to_networkx_from_dependency(dependency_graph)
    elif normalized == "call":
        call_graph = build_call_graph(local_path, max_files=max_files)
        g = _to_networkx_from_call(call_graph)
    else:
        raise ValueError("graph_type must be either 'dependency' or 'call'")

    labels = {node_id: data.get("label", node_id) for node_id, data in g.nodes(data=True)}

    degree = nx.degree_centrality(g) if g.number_of_nodes() else {}
    betweenness = nx.betweenness_centrality(g) if g.number_of_nodes() else {}

    undirected = g.to_undirected()
    components = nx.number_connected_components(undirected) if undirected.number_of_nodes() else 0

    metrics = GraphMetrics(
        node_count=g.number_of_nodes(),
        edge_count=g.number_of_edges(),
        connected_components=components,
    )

    dfs_result = _dfs(g, traversal_start)
    bfs_result = _bfs(g, traversal_start)

    return GraphAnalysisResponse(
        graph_type=normalized,
        metrics=metrics,
        top_degree_centrality=_ranked(degree, labels),
        top_betweenness_centrality=_ranked(betweenness, labels),
        top_impact_rank=_impact_rank(g, labels),
        traversal=TraversalResult(
            start_node=dfs_result.start_node or bfs_result.start_node,
            dfs_order=dfs_result.dfs_order,
            bfs_order=bfs_result.bfs_order,
        ),
    )
