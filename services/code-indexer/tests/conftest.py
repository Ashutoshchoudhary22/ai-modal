from pathlib import Path

import pytest

FIXTURE_REPO = Path(__file__).parent / "fixtures" / "fixture_repo"


@pytest.fixture
def fixture_repo() -> Path:
    return FIXTURE_REPO
