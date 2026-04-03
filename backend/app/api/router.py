from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.ai_explanation import router as ai_explanation_router
from app.api.routes.achievements import router as achievements_router
from app.api.routes.health import router as health_router
from app.api.routes.github_analysis import router as github_analysis_router
from app.api.routes.lessons import router as lessons_router
from app.api.routes.learning_paths import router as learning_paths_router
from app.api.routes.parsing import router as parsing_router
from app.api.routes.tokens import router as tokens_router
from app.api.routes.dependency_graph import router as dependency_graph_router
from app.api.routes.call_graph import router as call_graph_router
from app.api.routes.graph_analysis import router as graph_analysis_router

api_router = APIRouter()
api_router.include_router(achievements_router, prefix="/achievements", tags=["achievements"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(health_router, prefix="/health", tags=["health"])
api_router.include_router(github_analysis_router, prefix="/github", tags=["github"])
api_router.include_router(lessons_router, prefix="/lessons", tags=["lessons"])
api_router.include_router(ai_explanation_router, prefix="/ai", tags=["ai"])
api_router.include_router(learning_paths_router, prefix="/learning-paths", tags=["learning-paths"])
api_router.include_router(parsing_router, prefix="/parsing", tags=["parsing"])
api_router.include_router(tokens_router, prefix="/tokens", tags=["tokens"])
api_router.include_router(dependency_graph_router, prefix="/dependency-graph", tags=["dependency-graph"])
api_router.include_router(call_graph_router, prefix="/call-graph", tags=["call-graph"])
api_router.include_router(graph_analysis_router, prefix="/graph-analysis", tags=["graph-analysis"])
