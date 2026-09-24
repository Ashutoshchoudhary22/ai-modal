"""Vision and screenshot-to-code types — Phase 8."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from ai_platform_protocol.ui import (
    ImplementationPlan,
    UIFramework,
    UISpec,
    UIValidationMode,
    UIValidationResult,
)


class ConfidenceLevel(StrEnum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    UNCERTAIN = "uncertain"


class VisionErrorCode(StrEnum):
    INVALID_IMAGE = "invalid_image"
    UNSUPPORTED_IMAGE_FORMAT = "unsupported_image_format"
    IMAGE_TOO_LARGE = "image_too_large"
    IMAGE_DIMENSIONS_EXCEEDED = "image_dimensions_exceeded"
    VISION_PROVIDER_UNAVAILABLE = "vision_provider_unavailable"
    VISION_ANALYSIS_FAILED = "vision_analysis_failed"
    UI_SPEC_GENERATION_FAILED = "ui_spec_generation_failed"
    RENDER_FAILED = "render_failed"
    VISUAL_COMPARISON_FAILED = "visual_comparison_failed"
    VISUAL_VALIDATION_FAILED = "visual_validation_failed"
    DEPENDENCY_REQUIRED = "dependency_required"
    WORKSPACE_ACCESS_DENIED = "workspace_access_denied"


class ImageInput(BaseModel):
    data: bytes
    mime_type: str
    filename: str | None = None
    image_id: str | None = None
    viewport: str | None = None  # e.g. desktop, tablet, mobile


class ImageMetadata(BaseModel):
    image_id: str
    mime_type: str
    width: int
    height: int
    size_bytes: int
    filename: str | None = None
    viewport: str | None = None


class VisualRegion(BaseModel):
    x: float = Field(ge=0.0, le=1.0)
    y: float = Field(ge=0.0, le=1.0)
    width: float = Field(ge=0.0, le=1.0)
    height: float = Field(ge=0.0, le=1.0)
    label: str | None = None


class VisualStyle(BaseModel):
    background_color: str | None = None
    text_color: str | None = None
    border_color: str | None = None
    font_family: str | None = None
    font_size: str | None = None
    font_weight: str | None = None
    border_radius: str | None = None
    padding: str | None = None
    margin: str | None = None
    shadow: str | None = None
    confidence: ConfidenceLevel = ConfidenceLevel.INFERRED


class LayoutSpec(BaseModel):
    direction: str | None = None  # row, column
    alignment: str | None = None
    justification: str | None = None
    gap: str | None = None
    columns: int | None = None
    width_behavior: str | None = None
    height_behavior: str | None = None
    layout_type: str | None = None  # flex, grid, stack
    confidence: ConfidenceLevel = ConfidenceLevel.INFERRED


class VisualElement(BaseModel):
    element_type: str
    label: str | None = None
    text: str | None = None
    region: VisualRegion | None = None
    style: VisualStyle | None = None
    layout: LayoutSpec | None = None
    children: list[VisualElement] = Field(default_factory=list)
    properties: dict[str, Any] = Field(default_factory=dict)
    confidence: ConfidenceLevel = ConfidenceLevel.OBSERVED
    accessibility_hint: str | None = None


class DesignTokens(BaseModel):
    colors: dict[str, str] = Field(default_factory=dict)
    typography: dict[str, str] = Field(default_factory=dict)
    spacing: dict[str, str] = Field(default_factory=dict)
    radius: dict[str, str] = Field(default_factory=dict)
    shadows: dict[str, str] = Field(default_factory=dict)
    breakpoints: dict[str, str] = Field(default_factory=dict)


class VisualAnalysis(BaseModel):
    page_title: str | None = None
    page_type: str | None = None
    regions: list[VisualElement] = Field(default_factory=list)
    layout: LayoutSpec | None = None
    design_tokens: DesignTokens = Field(default_factory=DesignTokens)
    responsive_hints: list[str] = Field(default_factory=list)
    accessibility_notes: list[str] = Field(default_factory=list)
    overall_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    provider: str | None = None
    model: str | None = None
    source_image_id: str | None = None


class VisionRequest(BaseModel):
    images: list[ImageInput]
    prompt: str | None = None
    instructions: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class VisionResponse(BaseModel):
    analysis: VisualAnalysis
    provider: str
    model: str | None = None
    duration_ms: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class RenderRequest(BaseModel):
    workspace_id: str
    workspace_root: str
    route: str | None = None
    viewport_width: int = 1280
    viewport_height: int = 720
    timeout_sec: int = 60


class RenderResult(BaseModel):
    success: bool
    screenshot_path: str | None = None
    screenshot_bytes: bytes | None = None
    width: int | None = None
    height: int | None = None
    error: str | None = None
    duration_ms: int = 0


class RegionComparisonResult(BaseModel):
    region: str
    score: float
    passed: bool
    differences: list[str] = Field(default_factory=list)


class VisualValidationResult(BaseModel):
    passed: bool
    score: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(ge=0.0, le=1.0)
    pixel_difference_ratio: float | None = None
    structural_similarity: float | None = None
    region_results: list[RegionComparisonResult] = Field(default_factory=list)
    differences: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    duration_ms: int = 0


class ScreenshotToCodeRequest(BaseModel):
    workspace_id: str
    images: list[ImageInput] = Field(default_factory=list)
    prompt: str | None = None
    route: str | None = None
    framework: UIFramework | None = None
    responsive: bool = True
    accessibility: bool = True
    validation_mode: UIValidationMode = UIValidationMode.BUILD
    visual_validation_enabled: bool = True
    visual_validation_threshold: float | None = None
    max_visual_iterations: int | None = None
    request_id: str | None = None
    actor_id: str | None = None
    root_path: str | None = None


class ScreenshotToCodeResult(BaseModel):
    run_id: str
    request_id: str
    workspace_id: str
    status: str
    framework: UIFramework | None = None
    visual_analysis: VisualAnalysis | None = None
    specification: UISpec | None = None
    plan: ImplementationPlan | None = None
    files_created: list[str] = Field(default_factory=list)
    files_modified: list[str] = Field(default_factory=list)
    validation: UIValidationResult | None = None
    visual_validation: VisualValidationResult | None = None
    visual_iterations: int = 0
    warnings: list[str] = Field(default_factory=list)
    final_response: str | None = None
    stop_reason: str | None = None
    error: str | None = None
    error_code: VisionErrorCode | None = None
    duration_ms: int = 0
