"""Renderer factory."""

from __future__ import annotations

from agent.render.base import UIRenderer
from agent.render.development_mock import DevelopmentMockRenderer
from agent.render.local_browser import LocalBrowserRenderer
from ai_platform_shared.config import Settings, get_settings


def create_renderer(settings: Settings | None = None) -> UIRenderer:
    cfg = settings or get_settings()
    renderer = cfg.ui_renderer
    if renderer == "development_mock":
        return DevelopmentMockRenderer()
    if renderer == "local_browser":
        return LocalBrowserRenderer()
    raise ValueError(f"Unknown UI renderer: {renderer}")
