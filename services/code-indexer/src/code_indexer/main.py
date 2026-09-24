"""FastAPI application for code indexer."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai_platform_shared.config import get_settings
from ai_platform_shared.logging import setup_logging
from fastapi import FastAPI

from code_indexer.routes import health, workspaces


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Platform — Code Indexer",
        version="0.1.0",
        description="Repository scanning, indexing, and search",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(workspaces.router, prefix="/v1")
    return app


app = create_app()
