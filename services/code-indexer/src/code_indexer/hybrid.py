"""Hybrid lexical + semantic search fusion."""

from __future__ import annotations

from code_indexer.config import IndexerConfig
from code_indexer.embeddings import EmbeddingProvider
from code_indexer.models import SearchResult
from code_indexer.search import lexical_search
from code_indexer.vector_store import VectorStore


def hybrid_search(
    query: str,
    *,
    symbols: list,
    file_contents: dict[str, str],
    vector_store: VectorStore | None = None,
    embedding_provider: EmbeddingProvider | None = None,
    config: IndexerConfig | None = None,
    limit: int = 20,
) -> list[SearchResult]:
    cfg = config or IndexerConfig()
    lexical = lexical_search(query, symbols=symbols, file_contents=file_contents, limit=limit)

    if vector_store is None or embedding_provider is None:
        return lexical

    query_vector = embedding_provider.embed([query])[0]
    semantic_hits = vector_store.search(query_vector, limit=limit)
    semantic_map: dict[str, float] = {}
    for chunk_id, score, meta in semantic_hits:
        key = meta.get("relative_path", chunk_id)
        semantic_map[key] = max(semantic_map.get(key, 0.0), score * 100.0)

    merged: dict[str, SearchResult] = {}
    for result in lexical:
        sem = semantic_map.get(result.relative_path, 0.0)
        result.semantic_score = sem
        result.final_score = cfg.lexical_weight * result.lexical_score + cfg.semantic_weight * sem
        merged[result.relative_path + str(result.line_start)] = result

    for path, sem_score in semantic_map.items():
        key = path + "0"
        if key not in merged:
            merged[key] = SearchResult(
                file_id=path,
                relative_path=path,
                symbol_id=None,
                symbol_name=None,
                line_start=1,
                line_end=1,
                snippet="",
                match_type="text",
                lexical_score=0.0,
                semantic_score=sem_score,
                final_score=cfg.semantic_weight * sem_score,
            )

    results = sorted(merged.values(), key=lambda r: (-r.final_score, r.relative_path))
    return results[:limit]
