"""UI generation types — Phase 7."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class UIFramework(StrEnum):
    NEXTJS_APP = "nextjs_app"
    NEXTJS_PAGES = "nextjs_pages"
    VITE_REACT = "vite_react"
    REACT = "react"
    UNKNOWN = "unknown"


class StylingSystem(StrEnum):
    TAILWIND = "tailwind"
    CSS_MODULES = "css_modules"
    PLAIN_CSS = "plain_css"
    SCSS = "scss"
    STYLED_COMPONENTS = "styled_components"
    UNKNOWN = "unknown"


class UIGenerationTarget(StrEnum):
    PAGE = "page"
    COMPONENT = "component"
    LAYOUT = "layout"
    ANALYSIS = "analysis"


class UIValidationMode(StrEnum):
    NONE = "none"
    DIAGNOSTICS = "diagnostics"
    BUILD = "build"
    TEST = "test"
    FULL = "full"


class ComponentSpec(BaseModel):
    name: str
    purpose: str
    props: list[str] = Field(default_factory=list)
    states: list[str] = Field(default_factory=list)
    variants: list[str] = Field(default_factory=list)
    responsive: bool = True
    accessibility: list[str] = Field(default_factory=list)
    reuse_existing: str | None = None


class PageSpec(BaseModel):
    name: str
    route: str | None = None
    layout: str | None = None
    sections: list[str] = Field(default_factory=list)
    components: list[str] = Field(default_factory=list)
    responsive: bool = True
    accessibility: list[str] = Field(default_factory=list)


class UISpec(BaseModel):
    name: str
    description: str
    framework: UIFramework = UIFramework.UNKNOWN
    styling_system: StylingSystem = StylingSystem.UNKNOWN
    pages: list[PageSpec] = Field(default_factory=list)
    components: list[ComponentSpec] = Field(default_factory=list)
    theme: dict[str, Any] = Field(default_factory=dict)
    responsive: bool = True
    accessibility: bool = True
    constraints: list[str] = Field(default_factory=list)
    screenshot_metadata: dict[str, Any] = Field(default_factory=dict)


class UIFrameworkProfile(BaseModel):
    framework: UIFramework
    language: str = "typescript"
    routing: str = "unknown"
    styling_system: StylingSystem = StylingSystem.UNKNOWN
    component_directory: str | None = None
    page_directory: str | None = None
    entry_points: list[str] = Field(default_factory=list)
    build_command: str | None = None
    test_command: str | None = None
    dev_command: str | None = None
    ui_libraries: list[str] = Field(default_factory=list)
    design_token_files: list[str] = Field(default_factory=list)


class ImplementationPlanItem(BaseModel):
    step: int
    action: str
    target: str | None = None
    reuse: str | None = None


class ImplementationPlan(BaseModel):
    items: list[ImplementationPlanItem] = Field(default_factory=list)
    files_to_create: list[str] = Field(default_factory=list)
    files_to_modify: list[str] = Field(default_factory=list)
    validation_commands: list[str] = Field(default_factory=list)


class UIRepositoryContext(BaseModel):
    framework: UIFrameworkProfile
    components: list[str] = Field(default_factory=list)
    pages: list[str] = Field(default_factory=list)
    layouts: list[str] = Field(default_factory=list)
    design_tokens: dict[str, Any] = Field(default_factory=dict)
    relevant_files: list[str] = Field(default_factory=list)


class UIGenerationRequest(BaseModel):
    workspace_id: str
    prompt: str
    target: UIGenerationTarget = UIGenerationTarget.PAGE
    framework: UIFramework | None = None
    styling_system: StylingSystem | None = None
    route: str | None = None
    responsive: bool = True
    accessibility: bool = True
    validation_mode: UIValidationMode = UIValidationMode.BUILD
    request_id: str | None = None
    actor_id: str | None = None
    root_path: str | None = None


class UIValidationResult(BaseModel):
    success: bool
    diagnostics: dict[str, Any] | None = None
    build: dict[str, Any] | None = None
    tests: dict[str, Any] | None = None
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    duration_ms: int = 0


class UIGenerationResult(BaseModel):
    run_id: str
    request_id: str
    workspace_id: str
    status: str
    framework: UIFramework
    specification: UISpec | None = None
    plan: ImplementationPlan | None = None
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    components_created: list[str] = Field(default_factory=list)
    validation: UIValidationResult | None = None
    warnings: list[str] = Field(default_factory=list)
    final_response: str | None = None
    stop_reason: str | None = None
    error: str | None = None
    duration_ms: int = 0
