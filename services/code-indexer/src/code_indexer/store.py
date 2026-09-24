"""Filesystem-backed index store."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from code_indexer.config import INDEX_VERSION
from code_indexer.models import ImportRecord, IndexRun, RepositoryFile, Symbol


class IndexStore:
    def __init__(self, workspace_root: Path, workspace_id: str) -> None:
        self.workspace_root = workspace_root
        self.workspace_id = workspace_id
        self.index_dir = workspace_root / ".code_index"
        self.index_dir.mkdir(parents=True, exist_ok=True)

    def load_file_hashes(self) -> dict[str, str]:
        path = self.index_dir / "file_hashes.json"
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    def save_file_hashes(self, hashes: dict[str, str]) -> None:
        path = self.index_dir / "file_hashes.json"
        path.write_text(json.dumps(dict(sorted(hashes.items())), indent=2), encoding="utf-8")

    def save_index(
        self,
        *,
        files: list[RepositoryFile],
        symbols: list[Symbol],
        imports: list[ImportRecord],
        run: IndexRun,
    ) -> None:
        payload = {
            "workspace_id": self.workspace_id,
            "index_version": INDEX_VERSION,
            "files": [asdict(f) for f in files],
            "symbols": [asdict(s) for s in symbols],
            "imports": [asdict(i) for i in imports],
            "run": asdict(run),
        }
        (self.index_dir / "index.json").write_text(
            json.dumps(payload, indent=2),
            encoding="utf-8",
        )

    def load_index(self) -> dict | None:
        path = self.index_dir / "index.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def remove_file(self, relative_path: str) -> None:
        data = self.load_index()
        if not data:
            return
        data["files"] = [f for f in data["files"] if f["relative_path"] != relative_path]
        data["symbols"] = [s for s in data["symbols"] if s["file_path"] != relative_path]
        data["imports"] = [i for i in data["imports"] if i["file_path"] != relative_path]
        (self.index_dir / "index.json").write_text(
            json.dumps(data, indent=2),
            encoding="utf-8",
        )
        hashes = self.load_file_hashes()
        hashes.pop(relative_path, None)
        self.save_file_hashes(hashes)
