"""Workspace file scanner."""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

from code_indexer.binary import is_binary_file
from code_indexer.config import IndexerConfig
from code_indexer.ignore import IgnoreMatcher
from code_indexer.languages import LanguageRegistry
from code_indexer.models import RepositoryFile
from code_indexer.security import resolve_workspace_path, safe_relative_path


@dataclass
class ScanStats:
    discovered: int = 0
    ignored: int = 0
    binary: int = 0
    supported: int = 0
    skipped_size: int = 0


class WorkspaceScanner:
    def __init__(
        self,
        workspace_root: str | Path,
        config: IndexerConfig | None = None,
    ) -> None:
        self.root = resolve_workspace_path(workspace_root)
        self.config = config or IndexerConfig()
        self.ignore = IgnoreMatcher(self.root, self.config)
        self.languages = LanguageRegistry()

    def scan(self) -> tuple[list[RepositoryFile], ScanStats]:
        files: list[RepositoryFile] = []
        stats = ScanStats()
        total_size = 0

        for dirpath, dirnames, filenames in os.walk(self.root, followlinks=False):
            dirnames[:] = sorted(
                name
                for name in dirnames
                if not self.ignore.is_ignored(safe_relative_path(self.root, Path(dirpath) / name))
            )
            for filename in sorted(filenames):
                full_path = Path(dirpath) / filename
                try:
                    rel = safe_relative_path(self.root, full_path)
                except ValueError:
                    stats.ignored += 1
                    continue
                stats.discovered += 1
                if self.ignore.is_ignored(rel):
                    stats.ignored += 1
                    continue
                try:
                    stat = full_path.stat()
                except OSError:
                    stats.ignored += 1
                    continue
                if stat.st_size > self.config.max_file_size:
                    stats.skipped_size += 1
                    continue
                total_size += stat.st_size
                if total_size > self.config.max_total_workspace_size:
                    break
                try:
                    data = full_path.read_bytes()
                except OSError:
                    stats.ignored += 1
                    continue
                binary = is_binary_file(full_path, data)
                if binary:
                    stats.binary += 1
                    files.append(
                        RepositoryFile(
                            relative_path=rel,
                            language=None,
                            size_bytes=stat.st_size,
                            sha256=hashlib.sha256(data).hexdigest(),
                            line_count=0,
                            is_binary=True,
                            mtime=stat.st_mtime,
                        )
                    )
                    continue
                text = data.decode("utf-8", errors="replace")
                line_count = text.count("\n") + (1 if text else 0)
                lang = self.languages.detect(full_path, text)
                if lang and lang.parser_available:
                    stats.supported += 1
                files.append(
                    RepositoryFile(
                        relative_path=rel,
                        language=lang.id if lang else None,
                        size_bytes=stat.st_size,
                        sha256=hashlib.sha256(data).hexdigest(),
                        line_count=line_count,
                        is_binary=False,
                        mtime=stat.st_mtime,
                    )
                )
        files.sort(key=lambda item: item.relative_path)
        return files, stats
