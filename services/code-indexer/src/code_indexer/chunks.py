"""Structural code chunking."""

from __future__ import annotations

import hashlib

from code_indexer.config import IndexerConfig
from code_indexer.models import CodeChunk, Symbol


def build_chunks(
    symbols: list[Symbol],
    file_contents: dict[str, str],
    config: IndexerConfig | None = None,
) -> list[CodeChunk]:
    cfg = config or IndexerConfig()
    chunks: list[CodeChunk] = []
    for symbol in sorted(symbols, key=lambda s: (s.file_path, s.start_line)):
        content = file_contents.get(symbol.file_path, "")
        lines = content.splitlines()
        start = max(0, symbol.start_line - 1)
        end = min(len(lines), symbol.end_line)
        chunk_text = "\n".join(lines[start:end])
        if len(chunk_text) > cfg.max_chunk_chars:
            chunk_text = chunk_text[: cfg.max_chunk_chars]
        chunk_id = hashlib.sha256(
            f"{symbol.file_path}:{symbol.start_line}:{symbol.end_line}".encode()
        ).hexdigest()
        chunks.append(
            CodeChunk(
                chunk_id=chunk_id,
                file_id=symbol.file_path,
                symbol_id=symbol.id,
                relative_path=symbol.file_path,
                language=None,
                start_line=symbol.start_line,
                end_line=symbol.end_line,
                content=chunk_text,
            )
        )
    return chunks
