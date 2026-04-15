# Feature Recall Baseline

Date: 2026-04-02
Branch: updateNew

This document captures the user-provided full feature recall and a quick implementation alignment snapshot.

Official finalized stack reference: see docs/FINAL_TECH_STACK.md.

## Full Feature Recall (User Source)

1. Input and project acquisition

- Analyze GitHub repositories via URL
- Analyze local projects from file manager
- Supports zipped projects and folders
- Language-aware project detection

1. Project structure understanding

- Folder hierarchy analysis
- File categorization
- Entry-point detection
- Dependency file detection
- AST generation
- Function/class/module extraction
- Import/include analysis

1. Project graph construction

- Nodes: files, classes, functions, configs
- Edges: imports, function calls, inheritance, dependency usage
- Cross-file tracing and interaction mapping

1. Semantic project understanding

- Purpose inference
- Module responsibility identification
- Core vs utility separation
- Data flow understanding
- Execution flow explanation

1. Learning-oriented explanations

- Beginner/intermediate/advanced explanation levels
- Concept breakdown
- Learning roadmap and reading order

1. Code and design quality analysis

- Error handling gaps
- Complex functions and duplicate logic
- Hardcoded values
- Modularity/coupling/abstraction gaps

1. Risk and reliability analysis

- High-risk modules
- Single points of failure
- Untested critical code
- Dependency risk
- Severity and mitigation suggestions

1. Explainable AI features

- Why a file/function is important
- Why a risk/gap is detected
- Signals used for decisions
- Rule/graph/metric/LLM-backed explanation

1. NLP and LLM features

- Natural language project explanation and summaries
- LLM as interpreter, not decision-maker

1. Output and UX features

- Project summary
- Architecture and execution explanation
- Risk and gap report
- Learning roadmap
- Structured outputs and optional visuals

1. Research and academic features

- Repository-level understanding
- Learning-oriented explainable analysis
- Hybrid AI architecture (Graph + ML + LLM)
- Evaluation support

1. Future-ready extensions

- Multi-language support
- CI/CD integration
- Project evolution analysis
- Personalized learning paths
- IDE plugin support
- Continuous monitoring

1. Unique tech

- Multi-view code representation
  - Token-level (lexical understanding)
  - AST-level (syntax and structure)
  - Inter-file graph-level (system behavior)
- Core technology choices
  - Tree-sitter for AST extraction
  - Call graph and dependency graph construction
  - Lightweight graph algorithms for ranking and traversal

## Quick Implementation Snapshot (Current Repo)

Implemented now (evidence in code):

- GitHub URL analysis endpoint and dashboard flow
- AI code explanation API and AI Tutor UI
- Learning paths API and seeded path content
- Analysis result display UX

Partially implemented:

- Learning roadmap data model and presentation pieces
- Explainable outputs at UI level, but limited signal provenance

Not yet implemented as core engine:

- Local folder/zip ingestion pipeline
- AST parser pipeline and graph engine
- Execution flow inference engine
- Risk/reliability scoring engine
- Full XAI signal tracing (rules/paths/metrics)
- Research evaluation instrumentation
- Multi-view representation pipeline (token, AST, graph)
- Tree-sitter based parser integration and language adapters
- Graph algorithms layer (centrality, shortest path, impact ranking)

## Notes for Next Iteration

1. Build ingestion layer for local folders and zip uploads.
2. Add parser adapters and graph schema.
3. Add dependency and call graph generation service.
4. Add risk heuristics and severity scoring.
5. Add explanation trace output per finding.
6. Add multi-level teaching mode selector in AI Tutor.
7. Add token extraction pipeline for lexical-level representation.
8. Integrate Tree-sitter and normalize AST output schema.
9. Build inter-file dependency and call graph constructors.
10. Add lightweight graph algorithms for key-node ranking and path tracing.
