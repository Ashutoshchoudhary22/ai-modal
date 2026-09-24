"""Ignore rule handling (.gitignore + defaults)."""

from __future__ import annotations

import fnmatch
from pathlib import Path

from code_indexer.config import DEFAULT_IGNORES, SENSITIVE_PATTERNS, IndexerConfig


class IgnoreMatcher:
    def __init__(self, workspace_root: Path, config: IndexerConfig | None = None) -> None:
        self._config = config or IndexerConfig()
        self._patterns: list[str] = list(DEFAULT_IGNORES)
        self._patterns.extend(self._config.extra_ignores)
        self._load_gitignore(workspace_root)

    def _load_gitignore(self, workspace_root: Path) -> None:
        gitignore = workspace_root / ".gitignore"
        if not gitignore.is_file():
            return
        for line in gitignore.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            self._patterns.append(stripped)

    def is_ignored(self, relative_path: str) -> bool:
        normalized = relative_path.replace("\\", "/")
        if self._config.allow_env_example and normalized.endswith(".env.example"):
            return False
        basename = Path(normalized).name
        for pattern in SENSITIVE_PATTERNS:
            if pattern.endswith("."):
                if basename.startswith(pattern):
                    return True
            elif fnmatch.fnmatch(basename, pattern) or fnmatch.fnmatch(normalized, pattern):
                return True
        return any(self._match_pattern(normalized, pattern) for pattern in self._patterns)

    @staticmethod
    def _match_pattern(path: str, pattern: str) -> bool:
        if pattern.endswith("/"):
            return path.startswith(pattern) or f"/{pattern}" in f"/{path}/"
        if "/" in pattern:
            return fnmatch.fnmatch(path, pattern)
        return fnmatch.fnmatch(path, pattern) or fnmatch.fnmatch(Path(path).name, pattern)
