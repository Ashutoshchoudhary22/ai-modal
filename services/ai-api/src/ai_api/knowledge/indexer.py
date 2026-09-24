"""Indexer-backed knowledge retrieval using Phase 4 repository intelligence."""

from __future__ import annotations

import httpx
from ai_api.knowledge.base import KnowledgeRetrievalResult, KnowledgeSnippet


class IndexerKnowledgeRetriever:
    def __init__(self, indexer_url: str, *, timeout_sec: float = 10.0) -> None:
        self._indexer_url = indexer_url.rstrip("/")
        self._timeout = timeout_sec

    async def retrieve(
        self,
        query: str,
        *,
        workspace_id: str | None = None,
        max_chars: int = 4000,
    ) -> KnowledgeRetrievalResult:
        if not workspace_id or not query.strip():
            return KnowledgeRetrievalResult(query=query, snippets=[])

        snippets: list[KnowledgeSnippet] = []
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                symbol_res = await client.get(
                    f"{self._indexer_url}/v1/workspaces/{workspace_id}/symbols",
                    params={"query": query},
                )
                if symbol_res.is_success:
                    symbols = symbol_res.json().get("symbols", [])
                    for sym in symbols[:5]:
                        snippets.append(
                            KnowledgeSnippet(
                                source=f"symbol:{sym.get('path', 'unknown')}",
                                content=f"{sym.get('kind', 'symbol')} {sym.get('name', '')}",
                            )
                        )
            except httpx.HTTPError:
                pass

            try:
                search_res = await client.post(
                    f"{self._indexer_url}/v1/workspaces/{workspace_id}/search",
                    json={"query": query, "limit": 3},
                )
                if search_res.is_success:
                    results = search_res.json().get("results", [])
                    for hit in results[:3]:
                        snippets.append(
                            KnowledgeSnippet(
                                source=f"file:{hit.get('path', 'unknown')}",
                                content=hit.get("path", ""),
                                score=hit.get("score"),
                            )
                        )
            except httpx.HTTPError:
                pass

        trimmed: list[KnowledgeSnippet] = []
        used = 0
        for snippet in snippets:
            chunk = f"[{snippet.source}]\n{snippet.content}"
            if used + len(chunk) > max_chars:
                break
            trimmed.append(snippet)
            used += len(chunk)

        return KnowledgeRetrievalResult(query=query, snippets=trimmed)
