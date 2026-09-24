"""End-to-end repository intelligence tests."""

from __future__ import annotations

from pathlib import Path

from code_indexer.context import build_context
from code_indexer.indexer import RepositoryIndexer
from code_indexer.models import ImportRecord, Symbol
from code_indexer.search import lexical_search


def test_full_index_search_context(fixture_repo: Path, tmp_path: Path, offline_indexer_config):
    import shutil

    workspace = tmp_path / "repo"
    shutil.copytree(fixture_repo, workspace)
    indexer = RepositoryIndexer(workspace, config=offline_indexer_config)
    run, stats = indexer.index(incremental=False)
    assert run.status == "completed"
    assert stats.indexed > 0
    assert stats.symbols > 0

    data = indexer.store.load_index()
    assert data is not None
    symbols = [Symbol(**s) for s in data["symbols"]]
    assert any(s.name == "AuthService" for s in symbols)

    contents = {s.file_path: (workspace / s.file_path).read_text(encoding="utf-8") for s in symbols}
    results = lexical_search("AuthService", symbols=symbols, file_contents=contents)
    assert results
    assert results[0].symbol_name == "AuthService"

    ctx = build_context(
        "auth",
        symbols=symbols,
        imports=[ImportRecord(**i) for i in data["imports"]],
        file_contents=contents,
    )
    assert ctx.snippets


def test_incremental_and_deletion(fixture_repo: Path, tmp_path: Path, offline_indexer_config):
    import shutil

    workspace = tmp_path / "repo2"
    shutil.copytree(fixture_repo, workspace)
    indexer = RepositoryIndexer(workspace, config=offline_indexer_config)
    indexer.index(incremental=False)
    target = workspace / "src/auth/controller.ts"
    target.unlink()
    run, stats = indexer.index(incremental=True)
    data = indexer.store.load_index()
    symbols = [Symbol(**s) for s in data["symbols"]]
    assert not any(s.file_path == "src/auth/controller.ts" for s in symbols)
    assert stats.indexed >= 0
