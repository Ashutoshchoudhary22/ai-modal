"""Agent tools FastAPI application."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from ai_platform_shared.config import get_settings
from ai_platform_shared.logging import setup_logging
from fastapi import FastAPI

from agent.routes import agent, health, tools


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    setup_logging(settings.log_level)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Platform — Coding Agent",
        version="0.2.0",
        description="Coding agent tools and bounded agent loop",
        lifespan=lifespan,
    )
    app.include_router(health.router)
    app.include_router(tools.router, prefix="/v1")
    app.include_router(agent.router, prefix="/v1")
    return app


app = create_app()
