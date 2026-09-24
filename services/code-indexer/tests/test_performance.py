"""Lightweight indexing performance benchmark."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from code_indexer.indexer import RepositoryIndexer


def _generate_repo(root: Path, count: int = 120) -> None:
    src = root / "src"
    src.mkdir(parents=True)
    for index in range(count):
        path = src / f"module_{index:03d}.py"
        path.write_text(
            f"def func_{index}():\n    return {index}\n\nclass Class{index}:\n    pass\n",
            encoding="utf-8",
        )


@pytest.mark.integration
def test_incremental_skips_unchanged_files(tmp_path: Path, offline_indexer_config):
    workspace = tmp_path / "perf_repo"
    _generate_repo(workspace, count=120)
    indexer = RepositoryIndexer(workspace, config=offline_indexer_config)

    start = time.perf_counter()
    _run, stats = indexer.index(incremental=False)
    full_duration = time.perf_counter() - start
    assert stats.indexed == 120

    start = time.perf_counter()
    _run2, stats2 = indexer.index(incremental=True)
    incremental_duration = time.perf_counter() - start
    assert stats2.skipped_unchanged == 120
    assert stats2.indexed == 0
    assert incremental_duration < full_duration

    target = workspace / "src" / "module_005.py"
    target.write_text("def func_5():\n    return 99\n", encoding="utf-8")
    _run3, stats3 = indexer.index(incremental=True)
    assert stats3.indexed == 1
    assert stats3.skipped_unchanged == 119
