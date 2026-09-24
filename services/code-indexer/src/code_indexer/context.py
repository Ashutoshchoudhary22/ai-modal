"""Repository context builder."""

from __future__ import annotations

from code_indexer.config import IndexerConfig
from code_indexer.hybrid import hybrid_search
from code_indexer.models import ContextResult, ImportRecord, RepositoryFile, Symbol


def build_context(
    query: str,
    *,
    symbols: list[Symbol],
    imports: list[ImportRecord],
    file_contents: dict[str, str],
    config: IndexerConfig | None = None,
    **search_kwargs,
) -> ContextResult:
    cfg = config or IndexerConfig()
    hits = hybrid_search(
        query,
        symbols=symbols,
        file_contents=file_contents,
        config=cfg,
        limit=cfg.max_context_files,
        **search_kwargs,
    )

    selected_symbols: list[Symbol] = []
    selected_files: list[RepositoryFile] = []
    selected_imports: list[ImportRecord] = []
    seen_files: set[str] = set()
    char_budget = cfg.max_context_chars

    for hit in hits:
        if hit.relative_path in seen_files:
            continue
        if len(selected_files) >= cfg.max_context_files:
            break
        seen_files.add(hit.relative_path)
        content = file_contents.get(hit.relative_path, "")
        if char_budget <= 0:
            break
        char_budget -= len(hit.snippet)
        selected_files.append(
            RepositoryFile(
                relative_path=hit.relative_path,
                language=None,
                size_bytes=len(content.encode("utf-8")),
                sha256="",
                line_count=content.count("\n") + 1,
                is_binary=False,
            )
        )
        if hit.symbol_id:
            sym = next((s for s in symbols if s.id == hit.symbol_id), None)
            if sym and len(selected_symbols) < cfg.max_context_symbols:
                selected_symbols.append(sym)
        for imp in imports:
            if imp.file_path == hit.relative_path:
                selected_imports.append(imp)

    return ContextResult(
        query=query,
        files=selected_files,
        symbols=selected_symbols,
        snippets=hits[: cfg.max_context_files],
        imports=selected_imports,
    )
