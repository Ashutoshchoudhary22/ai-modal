"""Future repository indexer interfaces — Phase 4."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class IndexedFile(BaseModel):
    path: str
    language: str | None = None
    symbols: list[str] = Field(default_factory=list)


class SearchHit(BaseModel):
    path: str
    score: float
    snippet: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class IndexRequest(BaseModel):
    workspace_root: str
    include_globs: list[str] = Field(default_factory=lambda: ["**/*"])


@runtime_checkable
class RepositoryIndexer(Protocol):
    async def index(self, request: IndexRequest) -> None: ...
    async def search(self, query: str, limit: int = 20) -> list[SearchHit]: ...
