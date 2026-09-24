"""Browser agent types — Phase 9."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class BrowserErrorCode(StrEnum):
    BROWSER_PROVIDER_UNAVAILABLE = "browser_provider_unavailable"
    BROWSER_SESSION_NOT_FOUND = "browser_session_not_found"
    BROWSER_TIMEOUT = "browser_timeout"
    NAVIGATION_BLOCKED = "navigation_blocked"
    DOMAIN_NOT_ALLOWED = "domain_not_allowed"
    UNSAFE_URL = "unsafe_url"
    SSRF_BLOCKED = "ssrf_blocked"
    ELEMENT_NOT_FOUND = "element_not_found"
    STALE_ELEMENT_REFERENCE = "stale_element_reference"
    ELEMENT_NOT_VISIBLE = "element_not_visible"
    ELEMENT_NOT_ENABLED = "element_not_enabled"
    ACTION_NOT_ALLOWED = "action_not_allowed"
    PAGE_LIMIT_REACHED = "page_limit_reached"
    ACTION_LIMIT_REACHED = "action_limit_reached"
    NAVIGATION_LIMIT_REACHED = "navigation_limit_reached"
    SCREENSHOT_LIMIT_REACHED = "screenshot_limit_reached"
    BROWSER_CRASHED = "browser_crashed"
    BROWSER_CANCELLED = "browser_cancelled"
    INVALID_ACTION = "invalid_action"


class BrowserElement(BaseModel):
    element_id: str
    tag: str | None = None
    role: str | None = None
    name: str | None = None
    text: str | None = None
    placeholder: str | None = None
    value: str | None = None
    href: str | None = None
    visible: bool = True
    enabled: bool = True
    sensitive: bool = False


class BrowserObservation(BaseModel):
    observation_id: str
    url: str
    title: str | None = None
    viewport: dict[str, int] = Field(default_factory=dict)
    elements: list[BrowserElement] = Field(default_factory=list)
    visible_text: str | None = None
    accessibility_summary: str | None = None
    screenshot_reference: str | None = None
    truncated: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class BrowserSession(BaseModel):
    session_id: str
    run_id: str | None = None
    current_url: str | None = None
    title: str | None = None
    status: str = "active"
    page_count: int = 1
    action_count: int = 0
    navigation_count: int = 0
    screenshot_count: int = 0
    current_observation_id: str | None = None


class BrowserActionRecord(BaseModel):
    action_type: str
    success: bool
    element_id: str | None = None
    url: str | None = None
    error_code: str | None = None
    timestamp: str | None = None


class BrowserRunRequest(BaseModel):
    workspace_id: str
    task: str
    start_url: str | None = None
    policy: str = "browser_agent"
    max_iterations: int | None = None
    request_id: str | None = None
    actor_id: str | None = None
    allowed_domains: list[str] | None = None


class BrowserRunResult(BaseModel):
    run_id: str
    request_id: str
    workspace_id: str
    status: str
    session: BrowserSession | None = None
    current_url: str | None = None
    page_title: str | None = None
    action_count: int = 0
    navigation_count: int = 0
    iteration_count: int = 0
    action_history: list[BrowserActionRecord] = Field(default_factory=list)
    final_response: str | None = None
    stop_reason: str | None = None
    error: str | None = None
    error_code: BrowserErrorCode | None = None
    duration_ms: int = 0
