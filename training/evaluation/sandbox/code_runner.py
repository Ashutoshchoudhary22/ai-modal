"""Sandboxed code execution for coding benchmarks."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CodeExecutionResult:
    passed: bool
    tests_passed: int
    tests_failed: int
    tests_total: int
    pass_rate: float
    stdout: str
    stderr: str
    error: str | None = None
    timed_out: bool = False


def run_code_tests(
    solution_code: str,
    test_code: str,
    *,
    timeout_sec: float = 5.0,
) -> CodeExecutionResult:
    with tempfile.TemporaryDirectory(prefix="eval-code-") as tmp:
        workspace = Path(tmp)
        solution_path = workspace / "solution.py"
        test_path = workspace / "test_solution.py"
        solution_path.write_text(solution_code, encoding="utf-8")
        test_path.write_text(test_code, encoding="utf-8")

        env = {
            "PYTHONPATH": str(workspace),
            "PYTHONNOUSERSITE": "1",
            "PATH": os.environ.get("PATH", ""),
        }
        for secret in (
            "OPENAI_API_KEY",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "DATABASE_URL",
        ):
            env.pop(secret, None)

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "unittest", "test_solution"],
                cwd=workspace,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
            )
        except subprocess.TimeoutExpired as exc:
            return CodeExecutionResult(
                passed=False,
                tests_passed=0,
                tests_failed=1,
                tests_total=1,
                pass_rate=0.0,
                stdout=exc.stdout or "",
                stderr=exc.stderr or "",
                error="EXECUTION_TIMEOUT",
                timed_out=True,
            )

        output = (proc.stdout or "") + (proc.stderr or "")
        proc_returncode = 1 if "NO TESTS RAN" in output else proc.returncode
        if proc_returncode == 0:
            passed_count, failed_count, tests_total = 1, 0, 1
        else:
            passed_count, failed_count, tests_total = 0, 1, 1

        pass_rate = passed_count / tests_total if tests_total else 0.0
        return CodeExecutionResult(
            passed=proc_returncode == 0,
            tests_passed=passed_count,
            tests_failed=failed_count,
            tests_total=tests_total,
            pass_rate=pass_rate,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            error=None if proc_returncode == 0 else "EXECUTION_ERROR",
        )
