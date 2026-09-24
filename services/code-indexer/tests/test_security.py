from pathlib import Path

import pytest
from code_indexer.security import PathSecurityError, resolve_relative_path, resolve_workspace_path


def test_reject_parent_traversal(tmp_path: Path):
    root = resolve_workspace_path(tmp_path)
    with pytest.raises(PathSecurityError):
        resolve_relative_path(root, "../outside")


def test_workspace_must_exist():
    with pytest.raises(PathSecurityError):
        resolve_workspace_path("/nonexistent/path/xyz")
