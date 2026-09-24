from pathlib import Path

import pytest


@pytest.mark.integration
def test_local_model_provider_loads_smoke_checkpoint(tmp_path: Path):
    pytest.importorskip("torch")
    pytest.importorskip("transformers")

    import yaml
    from ai_api.providers.local_model import LocalModelProvider
    from ai_platform_protocol.models.inference import GenerateRequest

    from training.core.config import load_training_config
    from training.core.trainer import run_training

    source_config = load_training_config("models/configs/smoke_test.yaml")
    config_dict = source_config.model_dump(mode="json")
    config_dict["output"]["dir"] = str(tmp_path / "provider-output")
    config_path = tmp_path / "provider_config.yaml"
    config_path.write_text(yaml.safe_dump(config_dict), encoding="utf-8")

    final_dir = run_training(config_path)

    provider = LocalModelProvider(
        model_path=str(final_dir),
        device_setting="cpu",
        dtype_setting="fp32",
        max_context=128,
    )

    async def _run():
        status = await provider.get_status()
        assert status.state.value in {"ready", "loading", "configured"}
        response = await provider.generate(
            GenerateRequest(prompt="### Instruction:\nWrite add\n\n### Response:\n", max_tokens=16)
        )
        assert response.content
        assert provider.count_tokens("hello") > 0

    import asyncio

    asyncio.run(_run())
