from __future__ import annotations

from pathlib import Path

import pytest
from agent.config import ToolSettings
from agent.context import ToolExecutionContext
from agent.registry import ToolRegistry, default_permissions
from code_indexer.config import IndexerConfig
from code_indexer.indexer import RepositoryIndexer

FIXTURE_WS = Path(__file__).parent / "fixtures" / "workspace"


@pytest.fixture
def tool_settings() -> ToolSettings:
    return ToolSettings(
        enabled=True,
        max_file_size=100_000,
        max_output_chars=10_000,
        write_enabled=True,
        terminal_enabled=True,
        terminal_allowed_commands=["python", "pytest", "echo", "git"],
        terminal_denied_commands=["rm", "del", "format"],
        diagnostics_commands=["python --version"],
        create_parent_dirs=True,
    )


@pytest.fixture
def workspace(tmp_path: Path) -> Path:
    import shutil

    target = tmp_path / "ws"
    shutil.copytree(FIXTURE_WS, target)
    return target


@pytest.fixture
def tool_context(workspace: Path) -> ToolExecutionContext:
    return ToolExecutionContext(
        workspace_id="test-ws",
        workspace_root=workspace,
        request_id="req-1",
        permissions=default_permissions(
            ToolSettings(default_permissions=["read", "write", "execute", "git_read"])
        ),
    )


@pytest.fixture
def registry(tool_settings: ToolSettings) -> ToolRegistry:
    return ToolRegistry(tool_settings)


@pytest.fixture
def indexed_workspace(workspace: Path) -> Path:
    indexer = RepositoryIndexer(
        workspace,
        workspace_id="test-ws",
        config=IndexerConfig(mysql_persistence=False),
    )
    indexer.index(incremental=False)
    return workspace
