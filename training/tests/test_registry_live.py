"""Live MySQL model registry integration tests."""

from __future__ import annotations

import os
import uuid

import pytest

from training.core.config import load_training_config
from training.core.errors import TrainingRegistryError
from training.core.experiment import ExperimentMetadata
from training.core.registry import register_trained_model


def _mysql_available() -> bool:
    try:
        import pymysql

        url = os.environ.get(
            "AI_PLATFORM_DATABASE_URL",
            "mysql+pymysql://root:@localhost:3306/aiplatform",
        )
        import re

        match = re.match(
            r"mysql\+pymysql://([^:]+):([^@]*)@([^:]+):(\d+)/(.+)",
            url,
        )
        if not match:
            return False
        conn = pymysql.connect(
            host=match.group(3),
            port=int(match.group(4)),
            user=match.group(1),
            password=match.group(2),
            database=match.group(5),
            connect_timeout=2,
        )
        cur = conn.cursor()
        cur.execute("SHOW TABLES LIKE 'provider_model_registry'")
        ok = cur.fetchone() is not None
        conn.close()
        return ok
    except Exception:
        return False


@pytest.mark.integration
@pytest.mark.skipif(not _mysql_available(), reason="MySQL provider_model_registry not available")
def test_live_registry_upsert_and_lookup():
    os.environ.setdefault(
        "AI_PLATFORM_DATABASE_URL",
        "mysql+pymysql://root:@localhost:3306/aiplatform",
    )
    from ai_platform_shared.db import session_scope
    from ai_platform_shared.db.repository import ModelRegistryRepository

    model_id = f"phase2-test-{uuid.uuid4().hex[:8]}"
    config = load_training_config("models/configs/smoke_test.yaml")
    config.registry.enabled = True
    config.registry.model_id = model_id
    config.registry.model_name = "Phase 2 Live Test"
    config.registry.version = "0.0.1-test"

    experiment = ExperimentMetadata(
        experiment_id=str(uuid.uuid4()),
        name="live-registry-test",
        description="",
        started_at="2026-01-01T00:00:00Z",
        base_model="tiny",
        dataset_name="smoke",
        dataset_version="1",
        dataset_hash="abc",
        training_config_path="cfg",
        seed=1,
        smoke_test=True,
    )

    record = register_trained_model(
        config,
        experiment,
        checkpoint_path="/tmp/phase2-test-checkpoint",
        context_length=128,
    )
    assert record.model_id == model_id

    with session_scope() as session:
        repo = ModelRegistryRepository(session)
        fetched = repo.get_by_model_id(model_id)
        assert fetched is not None
        assert fetched.version == "0.0.1-test"

        record.version = "0.0.2-test"
        updated = repo.upsert(record)
        assert updated.version == "0.0.2-test"
        rows = repo.list_models(provider="local")
        assert any(row.model_id == model_id for row in rows)

        # cleanup test record
        from ai_platform_shared.db.models import ProviderModelRegistryORM
        from sqlalchemy import delete

        session.execute(
            delete(ProviderModelRegistryORM).where(
                ProviderModelRegistryORM.model_id == model_id
            )
        )


def test_registry_still_fails_when_disabled():
    config = load_training_config("models/configs/smoke_test.yaml")
    experiment = ExperimentMetadata(
        experiment_id="exp-1",
        name="test",
        description="",
        started_at="now",
        base_model="tiny",
        dataset_name="ds",
        dataset_version="1",
        dataset_hash="abc",
        training_config_path="cfg",
        seed=1,
    )
    with pytest.raises(TrainingRegistryError):
        register_trained_model(
            config,
            experiment,
            checkpoint_path="/tmp/model",
            context_length=128,
        )
