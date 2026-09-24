"""Filesystem storage abstraction for dataset artifacts."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path


class DatasetStorage(ABC):
    @abstractmethod
    def resolve(self, key: str) -> Path: ...

    @abstractmethod
    def write_bytes(self, key: str, data: bytes) -> Path: ...

    @abstractmethod
    def write_text(self, key: str, text: str) -> Path: ...

    @abstractmethod
    def exists(self, key: str) -> bool: ...


_UNSAFE = re.compile(r"(\.\.)|[\x00-\x1f]")


def _safe_key(key: str) -> str:
    normalized = key.replace("\\", "/").strip("/")
    if _UNSAFE.search(normalized):
        raise ValueError(f"Unsafe storage key: {key}")
    return normalized


class FilesystemDatasetStorage(DatasetStorage):
    def __init__(self, root: Path) -> None:
        self._root = root.resolve()
        self._root.mkdir(parents=True, exist_ok=True)

    def resolve(self, key: str) -> Path:
        safe = _safe_key(key)
        path = (self._root / safe).resolve()
        if self._root not in path.parents and path != self._root:
            raise ValueError(f"Path traversal blocked for key: {key}")
        return path

    def write_bytes(self, key: str, data: bytes) -> Path:
        path = self.resolve(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def write_text(self, key: str, text: str) -> Path:
        return self.write_bytes(key, text.encode("utf-8"))

    def exists(self, key: str) -> bool:
        return self.resolve(key).exists()
