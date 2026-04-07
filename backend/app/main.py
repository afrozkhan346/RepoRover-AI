from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

from app.api.routes.project import router as project_router
from app.api.router import api_router
from app.core.config import settings
from app.core.errors import register_exception_handlers
from app.db.connection import create_tables, get_database_info

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    openapi_version="3.0.3",
    docs_url="/docs",
    redoc_url="/redoc",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(project_router, prefix="/project", tags=["project"])


def custom_openapi() -> dict:
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
        description=app.description,
    )

    schema_name = "Body_upload_project_project_upload_post"
    component = (openapi_schema.get("components") or {}).get("schemas", {}).get(schema_name)
    if isinstance(component, dict):
        properties = component.get("properties")
        if isinstance(properties, dict):
            files = properties.get("files")
            if isinstance(files, dict):
                items = files.get("items")
                if isinstance(items, dict):
                    items.pop("contentMediaType", None)
                    items["format"] = "binary"

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.on_event("startup")
def on_startup() -> None:
    database_info = get_database_info()
    if database_info.backend == "sqlite":
        create_tables()


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "ok",
        "environment": settings.environment,
        "api_prefix": settings.api_prefix,
    }
