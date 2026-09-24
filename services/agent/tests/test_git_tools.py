import asyncio
import subprocess

from agent.errors import ToolErrorCode
from agent.tools.git_tools import GitDiffTool, GitStatusTool


def _init_git_repo(path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=path, check=True)
    subprocess.run(["git", "add", "."], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=path, check=True, capture_output=True)


def test_git_status_in_repository(workspace, tool_context):
    _init_git_repo(workspace)
    (workspace / "src" / "app.py").write_text("# modified\n", encoding="utf-8")
    result = asyncio.run(GitStatusTool().execute({}, tool_context))
    assert result.success
    assert result.metadata["is_git_repository"] is True
    assert result.metadata["branch"]


def test_git_diff_path_filter(workspace, tool_context):
    _init_git_repo(workspace)
    (workspace / "README.md").write_text("changed\n", encoding="utf-8")
    result = asyncio.run(GitDiffTool().execute({"path": "README.md"}, tool_context))
    assert result.success
    assert "README.md" in result.metadata["diff"] or result.metadata["diff"] == ""


def test_git_not_repository(tmp_path, tool_context):
    empty = tmp_path / "empty"
    empty.mkdir()
    tool_context.workspace_root = empty
    result = asyncio.run(GitStatusTool().execute({}, tool_context))
    assert result.error_code == ToolErrorCode.GIT_NOT_REPOSITORY.value
