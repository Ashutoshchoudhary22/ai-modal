"""Windows and Unicode path tests."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from code_indexer.indexer import RepositoryIndexer
from code_indexer.security import (
    PathSecurityError,
    normalize_path_for_storage,
    resolve_relative_path,
    resolve_workspace_path,
    safe_relative_path,
)


def test_windows_style_relative_path(tmp_path: Path):
    root = resolve_workspace_path(tmp_path)
    nested = root / "src" / "main.py"
    nested.parent.mkdir(parents=True)
    nested.write_text("print('ok')\n", encoding="utf-8")
    rel = safe_relative_path(root, Path(str(root / "src\\main.py")))
    assert rel == "src/main.py"


@pytest.mark.skipif(sys.platform != "win32", reason="Drive-letter handling is Windows-specific")
def test_windows_drive_path_normalization():
    normalized = normalize_path_for_storage("C:/workspace/project")
    assert normalized.lower().startswith("c:")


def test_unicode_paths_index_and_search(tmp_path: Path, offline_indexer_config):
    workspace = tmp_path / "unicode_repo"
    cafe_dir = workspace / "src" / "café"
    cafe_dir.mkdir(parents=True)
    (cafe_dir / "résumé.py").write_text("def greet():\n    return 'hi'\n", encoding="utf-8")
    indexer = RepositoryIndexer(workspace, config=offline_indexer_config)
    run, stats = indexer.index(incremental=False)
    assert run.status == "completed"
    assert stats.indexed >= 1
    data = indexer.store.load_index()
    paths = [s["file_path"] for s in data["symbols"]]
    assert any("résumé.py" in p for p in paths)


def test_traversal_rejected(tmp_path: Path):
    root = resolve_workspace_path(tmp_path)
    with pytest.raises(PathSecurityError):
        resolve_relative_path(root, "../outside")


def test_symlink_inside_workspace(tmp_path: Path, offline_indexer_config):
    workspace = tmp_path / "symlink_repo"
    src = workspace / "src"
    src.mkdir(parents=True)
    real = src / "real.py"
    real.write_text("def real_fn(): pass\n", encoding="utf-8")
    link = src / "linked.py"
    try:
        if os.name == "nt":
            os.symlink(real, link)
        else:
            link.symlink_to(real)
    except OSError as exc:
        pytest.skip(f"Symlink creation not permitted: {exc}")
    indexer = RepositoryIndexer(workspace, config=offline_indexer_config)
    run, _stats = indexer.index(incremental=False)
    assert run.status == "completed"


def test_symlink_escape_not_followed(tmp_path: Path):
    workspace = tmp_path / "ws"
    workspace.mkdir()
    outside = tmp_path / "outside_secret.txt"
    outside.write_text("secret", encoding="utf-8")
    link = workspace / "escape"
    try:
        if os.name == "nt":
            os.symlink(outside, link)
        else:
            link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"Symlink creation not permitted: {exc}")
    with pytest.raises(PathSecurityError):
        safe_relative_path(workspace.resolve(), link)
