"""Replaceable vector store abstraction."""

from __future__ import annotations

import json
import math
from abc import ABC, abstractmethod
from pathlib import Path


class VectorStore(ABC):
    @abstractmethod
    def upsert(self, chunk_id: str, vector: list[float], metadata: dict) -> None: ...

    @abstractmethod
    def delete(self, chunk_id: str) -> None: ...

    @abstractmethod
    def search(self, vector: list[float], limit: int = 10) -> list[tuple[str, float, dict]]: ...

    @abstractmethod
    def count(self) -> int: ...


class InMemoryVectorStore(VectorStore):
    def __init__(self) -> None:
        self._entries: dict[str, tuple[list[float], dict]] = {}

    def upsert(self, chunk_id: str, vector: list[float], metadata: dict) -> None:
        self._entries[chunk_id] = (vector, metadata)

    def delete(self, chunk_id: str) -> None:
        self._entries.pop(chunk_id, None)

    def search(self, vector: list[float], limit: int = 10) -> list[tuple[str, float, dict]]:
        scored = [
            (cid, _cosine_similarity(vector, vec), meta)
            for cid, (vec, meta) in self._entries.items()
        ]
        scored.sort(key=lambda item: -item[1])
        return scored[:limit]

    def count(self) -> int:
        return len(self._entries)


class FilesystemVectorStore(VectorStore):
    def __init__(self, path: Path) -> None:
        self._path = path
        self._path.mkdir(parents=True, exist_ok=True)
        self._entries: dict[str, tuple[list[float], dict]] = {}
        index_file = self._path / "vectors.json"
        if index_file.exists():
            raw = json.loads(index_file.read_text(encoding="utf-8"))
            self._entries = {k: (v["vector"], v["metadata"]) for k, v in raw.items()}

    def _persist(self) -> None:
        payload = {k: {"vector": v, "metadata": m} for k, (v, m) in self._entries.items()}
        (self._path / "vectors.json").write_text(json.dumps(payload), encoding="utf-8")

    def upsert(self, chunk_id: str, vector: list[float], metadata: dict) -> None:
        self._entries[chunk_id] = (vector, metadata)
        self._persist()

    def delete(self, chunk_id: str) -> None:
        self._entries.pop(chunk_id, None)
        self._persist()

    def search(self, vector: list[float], limit: int = 10) -> list[tuple[str, float, dict]]:
        store = InMemoryVectorStore()
        store._entries = dict(self._entries)
        return store.search(vector, limit)

    def count(self) -> int:
        return len(self._entries)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
