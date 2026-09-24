"""Code indexer configuration."""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_IGNORES = [
    ".git/",
    "node_modules/",
    ".venv/",
    "venv/",
    "__pycache__/",
    ".pytest_cache/",
    ".ruff_cache/",
    "dist/",
    "build/",
    ".next/",
    "coverage/",
    ".cache/",
    "target/",
    ".code_index/",
]

SENSITIVE_PATTERNS = [
    ".env",
    ".pem",
    ".key",
    "credentials.",
    "secrets.",
]

INDEX_VERSION = 1
PARSER_VERSION = "1.0"
SCHEMA_VERSION = "1.0"


@dataclass
class IndexerConfig:
    mysql_persistence: bool = True
    require_mysql: bool = False
    allowed_workspace_roots: list[str] = field(default_factory=list)
    max_file_size: int = 1_048_576  # 1 MiB
    max_line_length: int = 10_000
    max_files_per_workspace: int = 50_000
    max_total_workspace_size: int = 500_000_000
    lexical_weight: float = 0.6
    semantic_weight: float = 0.4
    max_chunk_chars: int = 4000
    max_context_files: int = 10
    max_context_symbols: int = 20
    max_context_lines: int = 200
    max_context_chars: int = 16_000
    extra_ignores: list[str] = field(default_factory=list)
    allow_env_example: bool = True
