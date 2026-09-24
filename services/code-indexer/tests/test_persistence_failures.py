"""Persistence failure behavior tests."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from code_indexer.config import IndexerConfig
from code_indexer.indexer import RepositoryIndexer
from code_indexer.persistence import IndexPersistenceError


def test_mysql_failure_does_not_claim_success(fixture_repo: Path, tmp_path: Path, monkeypatch):
    workspace = tmp_path / "fail_repo"
    shutil.copytree(fixture_repo, workspace)

    def _boom(*_args, **_kwargs):
        raise IndexPersistenceError("simulated mysql failure")

    monkeypatch.setattr(
        "code_indexer.indexer.MySQLIndexStore.is_available",
        lambda: True,
    )
    monkeypatch.setattr(
        "code_indexer.persistence.mysql_store.MySQLIndexStore.persist_index",
        _boom,
    )
    indexer = RepositoryIndexer(
        workspace,
        config=IndexerConfig(mysql_persistence=True, require_mysql=True),
    )
    with pytest.raises(IndexPersistenceError):
        indexer.index(incremental=False)


def test_filesystem_cache_failure_reported(
    fixture_repo: Path, tmp_path: Path, offline_indexer_config, monkeypatch
):
    workspace = tmp_path / "cache_fail"
    shutil.copytree(fixture_repo, workspace)
    indexer = RepositoryIndexer(workspace, config=offline_indexer_config)

    def _fail_save(*_args, **_kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(indexer.store, "save_index", _fail_save)
    with pytest.raises(IndexPersistenceError):
        indexer.index(incremental=False)
