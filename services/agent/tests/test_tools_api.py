from agent.main import create_app
from fastapi.testclient import TestClient


def test_list_tools():
    client = TestClient(create_app())
    resp = client.get("/v1/tools")
    assert resp.status_code == 200
    names = {t["name"] for t in resp.json()["tools"]}
    assert "file.read" in names
    assert "terminal.exec" in names


def test_execute_file_read(workspace):
    client = TestClient(create_app())
    resp = client.post(
        "/v1/tools/execute",
        json={
            "workspace_id": "local-ws",
            "tool_name": "file.read",
            "arguments": {"path": "README.md"},
            "root_path": str(workspace),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_execute_denied_command(workspace):
    client = TestClient(create_app())
    resp = client.post(
        "/v1/tools/execute",
        json={
            "workspace_id": "local-ws",
            "tool_name": "terminal.exec",
            "arguments": {"command": "rm -rf ."},
            "root_path": str(workspace),
        },
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is False
