"""AI API test fixtures."""

import pytest
from ai_api.dependencies import reset_dependencies


@pytest.fixture(autouse=True)
def _reset_cached_dependencies() -> None:
    reset_dependencies()
    yield
    reset_dependencies()
