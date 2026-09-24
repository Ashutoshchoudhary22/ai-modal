"""Agent tools configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

from ai_platform_shared.config import Settings, get_settings


@dataclass
class ToolSettings:
    enabled: bool = True
    max_file_size: int = 1_048_576
    max_output_chars: int = 32_000
    max_search_results: int = 50
    max_context_chars: int = 16_000
    max_list_results: int = 500
    write_enabled: bool = True
    create_parent_dirs: bool = True
    terminal_enabled: bool = True
    terminal_timeout_sec: int = 120
    terminal_max_output_chars: int = 32_000
    terminal_allowed_commands: list[str] = field(default_factory=list)
    terminal_denied_commands: list[str] = field(default_factory=list)
    diagnostics_commands: list[str] = field(default_factory=list)
    max_diff_chars: int = 32_000
    default_permissions: list[str] = field(
        default_factory=lambda: ["read", "write", "execute", "git_read"]
    )


@dataclass
class AgentSettings:
    enabled: bool = True
    max_iterations: int = 25
    max_tool_calls: int = 50
    max_same_tool_calls: int = 10
    max_model_calls: int = 30
    max_runtime_sec: int = 600
    max_context_chars: int = 32_000
    max_tool_result_chars: int = 8_000
    max_history_messages: int = 50
    max_retries: int = 3
    max_retries_per_tool: int = 2
    default_policy: str = "coding"


def load_agent_settings(settings: Settings | None = None) -> AgentSettings:
    cfg = settings or get_settings()
    return AgentSettings(
        enabled=cfg.agent_enabled,
        max_iterations=cfg.agent_max_iterations,
        max_tool_calls=cfg.agent_max_tool_calls,
        max_same_tool_calls=cfg.agent_max_same_tool_calls,
        max_model_calls=cfg.agent_max_model_calls,
        max_runtime_sec=cfg.agent_max_runtime_sec,
        max_context_chars=cfg.agent_max_context_chars,
        max_tool_result_chars=cfg.agent_max_tool_result_chars,
        max_history_messages=cfg.agent_max_history_messages,
        max_retries=cfg.agent_max_retries,
        max_retries_per_tool=cfg.agent_max_retries_per_tool,
        default_policy=cfg.agent_default_policy,
    )


@dataclass
class UISettings:
    enabled: bool = True
    max_context_chars: int = 24_000
    max_files: int = 40
    max_components: int = 30
    default_validation: str = "build"
    max_generation_files: int = 20
    max_iterations: int = 25


def load_ui_settings(settings: Settings | None = None) -> UISettings:
    cfg = settings or get_settings()
    return UISettings(
        enabled=cfg.ui_generation_enabled,
        max_context_chars=cfg.ui_max_context_chars,
        max_files=cfg.ui_max_files,
        max_components=cfg.ui_max_components,
        default_validation=cfg.ui_default_validation,
        max_generation_files=cfg.ui_max_generation_files,
        max_iterations=cfg.agent_max_iterations,
    )


@dataclass
class ScreenshotSettings:
    enabled: bool = True
    max_image_bytes: int = 10_485_760
    max_width: int = 4096
    max_height: int = 4096
    max_pixels: int = 16_777_216
    vision_timeout_sec: int = 120
    visual_validation_enabled: bool = True
    visual_threshold: float = 0.85
    max_visual_iterations: int = 3
    render_timeout_sec: int = 120
    max_iterations: int = 25


def load_screenshot_settings(settings: Settings | None = None) -> ScreenshotSettings:
    cfg = settings or get_settings()
    return ScreenshotSettings(
        enabled=cfg.screenshot_to_code_enabled,
        max_image_bytes=cfg.vision_max_image_bytes,
        max_width=cfg.vision_max_width,
        max_height=cfg.vision_max_height,
        max_pixels=cfg.vision_max_pixels,
        vision_timeout_sec=cfg.vision_timeout_sec,
        visual_validation_enabled=cfg.visual_validation_enabled,
        visual_threshold=cfg.visual_validation_threshold,
        max_visual_iterations=cfg.visual_max_iterations,
        render_timeout_sec=cfg.ui_render_timeout_sec,
        max_iterations=cfg.agent_max_iterations,
    )


def load_tool_settings(settings: Settings | None = None) -> ToolSettings:
    cfg = settings or get_settings()
    return ToolSettings(
        enabled=cfg.tools_enabled,
        max_file_size=cfg.tool_max_file_size,
        max_output_chars=cfg.tool_max_output_chars,
        max_search_results=cfg.tool_max_search_results,
        max_context_chars=cfg.tool_max_context_chars,
        write_enabled=cfg.tool_write_enabled,
        terminal_enabled=cfg.terminal_enabled,
        terminal_timeout_sec=cfg.terminal_timeout_sec,
        terminal_max_output_chars=cfg.terminal_max_output_chars,
        terminal_allowed_commands=cfg.terminal_allowed_commands_list,
        terminal_denied_commands=cfg.terminal_denied_commands_list,
        diagnostics_commands=cfg.diagnostics_commands_list,
    )
