"""Repository indexing orchestration."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from code_indexer.config import INDEX_VERSION, IndexerConfig
from code_indexer.graph import RepositoryGraph
from code_indexer.imports.resolve import resolve_imports
from code_indexer.models import ImportRecord, IndexRun, RepositoryFile, Symbol
from code_indexer.parsing import build_default_registry
from code_indexer.persistence import IndexPersistenceError, MySQLIndexStore
from code_indexer.scanner import WorkspaceScanner
from code_indexer.security import resolve_workspace_path
from code_indexer.store import IndexStore


@dataclass
class IndexStats:
    files_discovered: int = 0
    ignored: int = 0
    binary: int = 0
    supported: int = 0
    indexed: int = 0
    skipped_unchanged: int = 0
    failed: int = 0
    symbols: int = 0
    imports: int = 0
    resolved_imports: int = 0
    unresolved_imports: int = 0


class RepositoryIndexer:
    def __init__(
        self,
        workspace_root: str | Path,
        workspace_id: str | None = None,
        config: IndexerConfig | None = None,
    ) -> None:
        self.root = resolve_workspace_path(workspace_root)
        self.workspace_id = workspace_id or str(uuid.uuid5(uuid.NAMESPACE_URL, str(self.root)))
        self.config = config or IndexerConfig()
        self.store = IndexStore(self.root, self.workspace_id)
        self.parsers = build_default_registry()
        self.mysql_store: MySQLIndexStore | None = None
        if self.config.mysql_persistence:
            if not MySQLIndexStore.is_available():
                if self.config.require_mysql:
                    raise IndexPersistenceError("MySQL persistence required but unavailable")
            else:
                self.mysql_store = MySQLIndexStore(self.workspace_id)
                self.mysql_store.ensure_workspace(self.root)

    def index(self, *, incremental: bool = True) -> tuple[IndexRun, IndexStats]:
        started = time.perf_counter()
        run = IndexRun(run_id=str(uuid.uuid4()), workspace_id=self.workspace_id)
        stats = IndexStats()

        scanner = WorkspaceScanner(self.root, self.config)
        discovered, scan_stats = scanner.scan()
        stats.files_discovered = scan_stats.discovered
        stats.ignored = scan_stats.ignored
        stats.binary = scan_stats.binary
        stats.supported = scan_stats.supported

        previous_hashes = self._load_previous_hashes()
        existing_data = self.store.load_index() if incremental else None
        existing_symbols = (
            [Symbol(**s) for s in existing_data.get("symbols", [])] if existing_data else []
        )
        existing_imports = (
            [ImportRecord(**i) for i in existing_data.get("imports", [])] if existing_data else []
        )
        current_paths = {f.relative_path for f in discovered if not f.is_binary}
        deleted_paths = sorted(set(previous_hashes) - current_paths)

        all_symbols: list[Symbol] = []
        all_imports: list[ImportRecord] = []
        indexed_files: list[RepositoryFile] = []
        graph = RepositoryGraph()
        known_paths = {f.relative_path for f in discovered}
        changed_paths: set[str] = set()

        unchanged_paths: set[str] = set()
        if incremental:
            unchanged_paths = {
                p
                for p in current_paths
                if previous_hashes.get(p)
                == next((f.sha256 for f in discovered if f.relative_path == p), None)
            }
        if unchanged_paths:
            all_symbols.extend(s for s in existing_symbols if s.file_path in unchanged_paths)
            all_imports.extend(i for i in existing_imports if i.file_path in unchanged_paths)

        for repo_file in discovered:
            repo_file.workspace_id = self.workspace_id
            if repo_file.is_binary or not repo_file.language:
                continue
            if repo_file.relative_path in unchanged_paths:
                stats.skipped_unchanged += 1
                indexed_files.append(repo_file)
                continue
            changed_paths.add(repo_file.relative_path)
            full_path = self.root / repo_file.relative_path
            try:
                source = full_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                repo_file.parser_status = "error"
                stats.failed += 1
                indexed_files.append(repo_file)
                continue
            result = self.parsers.parse_file(
                language_id=repo_file.language,
                workspace_id=self.workspace_id,
                file_path=repo_file.relative_path,
                source=source,
            )
            if result.errors and not result.symbols:
                repo_file.parser_status = "error"
                stats.failed += 1
            elif result.errors:
                repo_file.parser_status = "partial"
            else:
                repo_file.parser_status = "ok"
            file_imports = resolve_imports(
                result.imports,
                file_path=repo_file.relative_path,
                known_paths=known_paths,
            )
            for imp in file_imports:
                if imp.resolution_status == "resolved_local":
                    stats.resolved_imports += 1
                elif imp.resolution_status in {"unresolved_local", "unknown"}:
                    stats.unresolved_imports += 1
            repo_file.indexed_at = datetime.now(UTC).isoformat()
            repo_file.index_version = INDEX_VERSION
            indexed_files.append(repo_file)
            all_symbols.extend(result.symbols)
            all_imports.extend(file_imports)
            graph.add_file(repo_file.file_id, repo_file.relative_path)
            for sym in result.symbols:
                graph.add_symbol(sym)
            for imp in file_imports:
                graph.add_import(repo_file.file_id, imp)
            stats.indexed += 1

        stats.symbols = len(all_symbols)
        stats.imports = len(all_imports)
        run.files_seen = stats.files_discovered
        run.files_indexed = stats.indexed
        run.files_skipped = stats.skipped_unchanged + stats.ignored + stats.binary
        run.files_failed = stats.failed
        run.symbols_extracted = stats.symbols
        run.imports_extracted = stats.imports
        run.duration_ms = int((time.perf_counter() - started) * 1000)
        run.completed_at = datetime.now(UTC).isoformat()

        if self.mysql_store and self.config.mysql_persistence:
            try:
                self.mysql_store.persist_index(
                    run=run,
                    files=indexed_files,
                    symbols=all_symbols,
                    imports=all_imports,
                    deleted_paths=deleted_paths,
                    changed_paths=changed_paths,
                )
                run.status = "completed"
            except IndexPersistenceError as exc:
                run.status = "failed"
                run.error_summary = str(exc)
                raise
        else:
            for path in deleted_paths:
                self.store.remove_file(path)
            run.status = "completed"

        hashes = {f.relative_path: f.sha256 for f in discovered if not f.is_binary}
        try:
            self.store.save_file_hashes(hashes)
            self.store.save_index(
                files=indexed_files,
                symbols=all_symbols,
                imports=all_imports,
                run=run,
            )
        except OSError as exc:
            run.status = "failed"
            run.error_summary = f"Filesystem cache write failed: {exc}"
            raise IndexPersistenceError(run.error_summary) from exc

        return run, stats

    def _load_previous_hashes(self) -> dict[str, str]:
        if self.mysql_store and self.config.mysql_persistence:
            try:
                return self.mysql_store.load_file_hashes()
            except IndexPersistenceError:
                if self.config.require_mysql:
                    raise
        return self.store.load_file_hashes()
