"""Knowledge retrieval interfaces for RAG (no fake retrieval)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass
class KnowledgeSnippet:
    source: str
    content: str
    score: float | None = None


@dataclass
class KnowledgeRetrievalResult:
    query: str
    snippets: list[KnowledgeSnippet] = field(default_factory=list)

    @property
    def context_text(self) -> str:
        if not self.snippets:
            return ""
        parts: list[str] = []
        for snippet in self.snippets:
            parts.append(f"[{snippet.source}]\n{snippet.content}")
        return "\n\n".join(parts)


class KnowledgeRetriever(Protocol):
    async def retrieve(
        self,
        query: str,
        *,
        workspace_id: str | None = None,
        max_chars: int = 4000,
    ) -> KnowledgeRetrievalResult: ...
