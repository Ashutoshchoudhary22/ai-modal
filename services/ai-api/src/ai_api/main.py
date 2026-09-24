"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai_platform_shared.config import get_settings
from ai_platform_shared.logging import setup_logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ai_api.exceptions import register_exception_handlers
from ai_api.middleware.request_id import RequestIdMiddleware
from ai_api.routes import health, inference, meta


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    settings.validate_production_provider()
    yield


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="AI Platform — Inference API",
        version="0.1.0",
        description="Model inference, embeddings, and streaming generation",
        lifespan=lifespan,
    )

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(health.router)
    app.include_router(meta.router, prefix="/v1")
    app.include_router(inference.router, prefix="/v1")

    return app


app = create_app()
