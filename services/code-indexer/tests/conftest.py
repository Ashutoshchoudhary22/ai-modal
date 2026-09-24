from pathlib import Path

import pytest
from code_indexer.config import IndexerConfig

FIXTURE_REPO = Path(__file__).parent / "fixtures" / "fixture_repo"


@pytest.fixture
def fixture_repo() -> Path:
    return FIXTURE_REPO


@pytest.fixture
def offline_indexer_config() -> IndexerConfig:
    return IndexerConfig(mysql_persistence=False)
