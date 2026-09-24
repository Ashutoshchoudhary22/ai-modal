import shutil
from pathlib import Path

from code_indexer.scanner import WorkspaceScanner


def test_scan_ignores_node_modules_and_env(fixture_repo: Path, tmp_path: Path):
    workspace = tmp_path / "scan"
    shutil.copytree(fixture_repo, workspace)
    scanner = WorkspaceScanner(workspace)
    files, stats = scanner.scan()
    paths = {f.relative_path for f in files}
    assert "node_modules/ignored.js" not in paths
    assert ".env" not in paths
    assert stats.ignored > 0
