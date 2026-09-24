"""No-op knowledge retriever."""

from __future__ import annotations

from ai_api.knowledge.base import KnowledgeRetrievalResult


class NullKnowledgeRetriever:
    async def retrieve(
        self,
        query: str,
        *,
        workspace_id: str | None = None,
        max_chars: int = 4000,
    ) -> KnowledgeRetrievalResult:
        return KnowledgeRetrievalResult(query=query, snippets=[])
