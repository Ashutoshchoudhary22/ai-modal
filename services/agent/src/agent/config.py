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
