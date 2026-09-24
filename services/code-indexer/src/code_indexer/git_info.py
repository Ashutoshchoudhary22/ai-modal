"""Read-only Git metadata for workspaces."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from code_indexer.models import GitMetadata


def get_git_metadata(workspace_root: Path) -> GitMetadata:
    if shutil.which("git") is None:
        return GitMetadata()
    try:
        if not _git_ok(workspace_root, "rev-parse", "--is-inside-work-tree"):
            return GitMetadata()
        root = _git_output(workspace_root, "rev-parse", "--show-toplevel")
        branch = _git_output(workspace_root, "branch", "--show-current") or None
        commit = _git_output(workspace_root, "rev-parse", "HEAD") or None
        status_lines = _git_output_lines(workspace_root, "status", "--porcelain")
        modified = sum(1 for line in status_lines if line.startswith((" M", "M ", "MM", "AM")))
        untracked = sum(1 for line in status_lines if line.startswith("??"))
        tracked = len(_git_output_lines(workspace_root, "ls-files"))
        return GitMetadata(
            is_git_repository=True,
            repository_root=root,
            branch=branch,
            commit=commit,
            tracked_files=tracked,
            modified_files=modified,
            untracked_files=untracked,
        )
    except (OSError, subprocess.SubprocessError):
        return GitMetadata()


def _git_ok(cwd: Path, *args: str) -> bool:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip().lower() == "true"


def _git_output(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=5,
        check=False,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _git_output_lines(cwd: Path, *args: str) -> list[str]:
    output = _git_output(cwd, *args)
    if not output:
        return []
    return [line for line in output.splitlines() if line.strip()]
