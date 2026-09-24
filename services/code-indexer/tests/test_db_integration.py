"""MySQL repository index integration tests."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest
from ai_platform_shared.db import session_scope
from ai_platform_shared.db.repository_index_repository import RepositoryIndexRepository
from code_indexer.config import IndexerConfig
from code_indexer.indexer import RepositoryIndexer
from code_indexer.persistence.mysql_store import MySQLIndexStore
from sqlalchemy import delete


def _mysql_available() -> bool:
    return MySQLIndexStore.is_available()


@pytest.mark.integration
@pytest.mark.skipif(not _mysql_available(), reason="MySQL not available")
def test_mysql_persistence_and_consistency(fixture_repo: Path, tmp_path: Path):
    workspace = tmp_path / "mysql_repo"
    shutil.copytree(fixture_repo, workspace)
    workspace_id = str(uuid.uuid4())
    config = IndexerConfig(mysql_persistence=True, require_mysql=True)
    indexer = RepositoryIndexer(workspace, workspace_id=workspace_id, config=config)
    run, stats = indexer.index(incremental=False)
    assert run.status == "completed"
    assert stats.symbols > 0

    store = MySQLIndexStore(workspace_id)
    assert store.count_files() > 0
    assert store.count_symbols() > 0
    assert store.count_imports() > 0

    fs_data = indexer.store.load_index()
    assert fs_data is not None
    fs_symbols = {s["qualified_name"] for s in fs_data["symbols"]}
    with session_scope() as session:
        db_symbols = {
            row.qualified_name
            for row in RepositoryIndexRepository(session).list_symbols(workspace_id)
        }
    assert fs_symbols == db_symbols

    target = workspace / "src/auth/service.ts"
    original = target.read_text(encoding="utf-8")
    target.write_text(original + "\n// changed\n", encoding="utf-8")
    indexer.index(incremental=True)
    with session_scope() as session:
        db_symbols = RepositoryIndexRepository(session).list_symbols(workspace_id)
        names = [row.qualified_name for row in db_symbols]
    assert any("AuthService" in name for name in names)

    target.unlink()
    indexer.index(incremental=True)
    with session_scope() as session:
        repo = RepositoryIndexRepository(session)
        symbol_paths = [row.file_path for row in repo.list_symbols(workspace_id)]
        file_paths = [row.relative_path for row in repo.list_files(workspace_id)]
    assert "src/auth/service.ts" not in symbol_paths
    assert "src/auth/service.ts" not in file_paths

    _cleanup_workspace(workspace_id)


def _cleanup_workspace(workspace_id: str) -> None:
    with session_scope() as session:
        from ai_platform_shared.db.models import (
            RepositoryFileORM,
            RepositoryImportORM,
            RepositoryIndexRunORM,
            RepositorySymbolORM,
            WorkspaceORM,
        )

        session.execute(
            delete(RepositorySymbolORM).where(RepositorySymbolORM.workspace_id == workspace_id)
        )
        session.execute(
            delete(RepositoryImportORM).where(RepositoryImportORM.workspace_id == workspace_id)
        )
        session.execute(
            delete(RepositoryFileORM).where(RepositoryFileORM.workspace_id == workspace_id)
        )
        session.execute(
            delete(RepositoryIndexRunORM).where(RepositoryIndexRunORM.workspace_id == workspace_id)
        )
        session.execute(delete(WorkspaceORM).where(WorkspaceORM.id == workspace_id))


@pytest.mark.integration
@pytest.mark.skipif(not _mysql_available(), reason="MySQL not available")
def test_create_workspace_api(fixture_repo: Path, tmp_path: Path):
    from code_indexer.main import create_app
    from fastapi.testclient import TestClient

    workspace = tmp_path / "api_ws"
    shutil.copytree(fixture_repo, workspace)
    client = TestClient(create_app())
    create_resp = client.post(
        "/v1/workspaces",
        json={"name": "test-ws", "root_path": str(workspace)},
    )
    assert create_resp.status_code == 200
    workspace_id = create_resp.json()["id"]
    index_resp = client.post(
        f"/v1/workspaces/{workspace_id}/index",
        json={"force": True},
    )
    assert index_resp.status_code == 200
    assert index_resp.json()["status"] == "completed"
    _cleanup_workspace(workspace_id)
