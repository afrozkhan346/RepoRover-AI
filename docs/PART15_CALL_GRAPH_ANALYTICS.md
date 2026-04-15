# Part 15 - Call Graph + Impact Analysis + Graph Analytics Endpoints

Date: 2026-04-06
Status: Completed

## Goal

Upgrade call graph generation to a NetworkX-backed internal graph and expose impact analytics through the backend graph surface.

## Implemented Changes

### 1) NetworkX-backed call graph construction

Updated `backend/app/services/call_graph_service.py` so the call graph is now built as a `networkx.DiGraph` internally.

The graph now tracks:

- file nodes
- function nodes
- external call targets
- import-context nodes
- labeled edges for defines, calls, and imports-context

### 2) Call graph analytics payload

Extended `backend/app/schemas/call_graph.py` with a reusable analytics payload.

Call graph responses can now carry:

- degree centrality rankings
- betweenness centrality rankings
- impact rankings
- strongly connected component counts
- cycle counts

### 3) Dedicated analytics endpoint

Added a dedicated `/call-graph/analytics` endpoint through the existing FastAPI router and graph builder engine.

This provides a direct impact-analysis surface without changing the existing `/call-graph/from-path` contract.

### 4) Validation

Smoke-tested the call graph service with the checked-in virtualenv.

Observed output confirmed:

- call graph generation succeeds
- analytics are populated
- the dedicated analytics helper returns rankings and graph-level counts

## Outcome

Part 15 is complete:

- call graph generation is NetworkX-backed
- impact analysis is exposed through analytics data
- graph analytics endpoints are available without breaking existing call graph consumers
