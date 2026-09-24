from unittest.mock import MagicMock, patch

import pytest

from training.core.config import load_training_config
from training.core.errors import TrainingRegistryError
from training.core.experiment import ExperimentMetadata
from training.core.registry import register_trained_model


def test_registry_fails_when_disabled():
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


@patch("ai_platform_shared.db.session_scope")
@patch("ai_platform_shared.db.repository.ModelRegistryRepository")
def test_registry_upsert(mock_repo_cls, mock_session_scope):
    from ai_platform_protocol.models.registry import ModelRegistryRecord

    config = load_training_config("models/configs/smoke_test.yaml")
    config.registry.enabled = True
    config.registry.model_id = "smoke-model-v1"
    config.registry.model_name = "Smoke Model"
    config.registry.version = "1.0.0"

    session = MagicMock()
    mock_session_scope.return_value.__enter__.return_value = session
    mock_repo_cls.return_value.upsert.return_value = ModelRegistryRecord(
        model_id="smoke-model-v1",
        model_name="Smoke Model",
        version="1.0.0",
        provider="local",
    )

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

    record = register_trained_model(
        config,
        experiment,
        checkpoint_path="/tmp/model",
        context_length=128,
    )
    assert record.model_id == "smoke-model-v1"
