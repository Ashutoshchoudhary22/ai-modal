"""API smoke tests for code indexer."""

from __future__ import annotations

import shutil
from pathlib import Path

from code_indexer.main import create_app
from fastapi.testclient import TestClient


def test_api_index_search_context(fixture_repo: Path, tmp_path: Path):
    workspace = tmp_path / "api_repo"
    shutil.copytree(fixture_repo, workspace)
    client = TestClient(create_app())
    root = str(workspace)
    workspace_id = "test-workspace"

    index_resp = client.post(
        f"/v1/workspaces/{workspace_id}/index",
        json={"root_path": root, "force": True},
    )
    assert index_resp.status_code == 200
    assert index_resp.json()["status"] == "completed"

    search_resp = client.post(
        f"/v1/workspaces/{workspace_id}/search?root_path={root}",
        json={"query": "AuthService", "limit": 5},
    )
    assert search_resp.status_code == 200
    results = search_resp.json()["results"]
    assert results
    assert results[0]["symbol_name"] == "AuthService"

    context_resp = client.post(
        f"/v1/workspaces/{workspace_id}/context?root_path={root}",
        json={"query": "auth"},
    )
    assert context_resp.status_code == 200
    assert context_resp.json()["snippets"]

    graph_resp = client.get(f"/v1/workspaces/{workspace_id}/graph?root_path={root}")
    assert graph_resp.status_code == 200
    assert graph_resp.json()["edges"]
