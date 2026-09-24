"""Internal repository intelligence models."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

SymbolKind = Literal[
    "module", "class", "function", "method", "variable", "constant", "interface", "type"
]
ImportResolution = Literal["resolved_local", "unresolved_local", "external", "unknown"]
MatchType = Literal["exact_symbol", "path", "symbol_name", "text"]


ParserStatus = Literal["pending", "ok", "partial", "error", "skipped"]


@dataclass
class RepositoryFile:
    relative_path: str
    size_bytes: int
    sha256: str
    line_count: int
    is_binary: bool
    language: str | None = None
    workspace_id: str | None = None
    is_ignored: bool = False
    is_generated: bool = False
    parser_status: ParserStatus = "pending"
    mtime: float = 0.0
    indexed_at: str | None = None
    index_version: int = 1

    @property
    def file_id(self) -> str:
        scope = self.workspace_id or ""
        normalized = self.relative_path.replace("\\", "/")
        return hashlib.sha256(f"{scope}:{normalized}".encode()).hexdigest()


@dataclass
class Symbol:
    workspace_id: str
    file_path: str
    kind: SymbolKind
    name: str
    qualified_name: str
    start_line: int
    end_line: int
    start_byte: int = 0
    end_byte: int = 0
    signature: str | None = None
    parent_symbol_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def id(self) -> str:
        payload = (
            f"{self.workspace_id}:{self.file_path}:{self.kind}:"
            f"{self.qualified_name}:{self.start_line}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class ImportRecord:
    workspace_id: str
    file_path: str
    module_path: str
    imported_name: str | None
    alias: str | None
    start_line: int
    resolution_status: ImportResolution = "unknown"
    resolved_path: str | None = None

    @property
    def id(self) -> str:
        payload = f"{self.workspace_id}:{self.file_path}:{self.module_path}:{self.start_line}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class GraphEdge:
    source_id: str
    target_id: str
    edge_type: Literal["defines", "imports", "exports", "contains", "child_of"]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IndexRun:
    run_id: str
    workspace_id: str
    status: Literal["running", "completed", "failed"] = "running"
    files_seen: int = 0
    files_indexed: int = 0
    files_skipped: int = 0
    files_failed: int = 0
    symbols_extracted: int = 0
    imports_extracted: int = 0
    duration_ms: int | None = None
    error_summary: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    completed_at: str | None = None


@dataclass
class SearchResult:
    file_id: str
    relative_path: str
    symbol_id: str | None
    symbol_name: str | None
    line_start: int
    line_end: int
    snippet: str
    match_type: MatchType
    lexical_score: float
    semantic_score: float | None = None
    final_score: float = 0.0


@dataclass
class CodeChunk:
    chunk_id: str
    file_id: str
    symbol_id: str | None
    relative_path: str
    language: str | None
    start_line: int
    end_line: int
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ContextResult:
    query: str
    files: list[RepositoryFile] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    snippets: list[SearchResult] = field(default_factory=list)
    imports: list[ImportRecord] = field(default_factory=list)


@dataclass
class GitMetadata:
    is_git_repository: bool = False
    repository_root: str | None = None
    branch: str | None = None
    commit: str | None = None
    tracked_files: int = 0
    modified_files: int = 0
    untracked_files: int = 0


@dataclass
class WorkspaceRecord:
    id: str
    name: str
    root_path: str
    team_id: str
