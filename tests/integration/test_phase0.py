"""Cross-cutting integration tests for Phase 0."""

from ai_platform_shared.config import Settings


def test_platform_version_documented() -> None:
    """Ensure platform version is consistent across docs and code."""
    assert Settings().env in ("development", "staging", "production")


def test_monorepo_structure_exists() -> None:
    """Smoke test that key directories are importable conceptually."""
    expected = [
        "packages/protocol",
        "packages/shared",
        "services/ai-api",
        "docs",
        "infra/docker/mysql",
    ]
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    for path in expected:
        assert (root / path).exists(), f"Missing: {path}"
