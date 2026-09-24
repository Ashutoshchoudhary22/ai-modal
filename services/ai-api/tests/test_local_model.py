"""LocalModelProvider tests with mocked Transformers."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from ai_api.providers.errors import ProviderError
from ai_api.providers.local_model import LocalModelProvider
from ai_platform_protocol.models.errors import ProviderErrorCode
from ai_platform_protocol.models.inference import ChatMessage, GenerateRequest


@pytest.fixture
def provider() -> LocalModelProvider:
    return LocalModelProvider(
        model_id="sshleifer/tiny-gpt2",
        device_setting="cpu",
        dtype_setting="float32",
        max_context=512,
    )


@pytest.mark.asyncio
async def test_status_configured_before_load(provider: LocalModelProvider) -> None:
    status = await provider.get_status()
    assert status.state.value in {"configured", "ready", "unavailable"}
    assert status.provider_id == "local_hf"


@pytest.mark.asyncio
async def test_unconfigured_provider_status() -> None:
    provider = LocalModelProvider()
    status = await provider.get_status()
    assert status.state.value == "unavailable"


def test_count_tokens_with_loaded_tokenizer(provider: LocalModelProvider) -> None:
    tokenizer = MagicMock()
    tokenizer.encode.return_value = [1, 2, 3]
    provider._tokenizer = tokenizer
    assert provider.count_tokens("hello") == 3


@pytest.mark.asyncio
async def test_context_length_validation(provider: LocalModelProvider) -> None:
    provider._tokenizer = MagicMock()
    provider._tokenizer.encode.return_value = list(range(600))
    provider._model = MagicMock()
    with pytest.raises(ProviderError) as exc:
        await provider.generate(
            GenerateRequest(
                messages=[ChatMessage(role="user", content="x")],
                max_tokens=100,
            )
        )
    assert exc.value.code.value == "CONTEXT_LENGTH_EXCEEDED"


@pytest.mark.asyncio
async def test_generate_with_mocked_model(provider: LocalModelProvider) -> None:
    tokenizer = MagicMock()
    tokenizer.encode.return_value = [1, 2]
    tokenizer.eos_token_id = 0
    input_ids = MagicMock()
    input_ids.shape = (1, 2)
    input_ids.to.return_value = input_ids
    tokenizer.return_value = {"input_ids": input_ids}
    tokenizer.decode.return_value = "generated text"
    tokenizer.apply_chat_template.side_effect = Exception("skip")

    model = MagicMock()
    model.device = "cpu"
    model.generate.return_value = [[1, 2, 3, 4, 5]]

    provider._tokenizer = tokenizer
    provider._model = model

    response = await provider.generate(
        GenerateRequest(messages=[ChatMessage(role="user", content="hello")], max_tokens=5)
    )
    assert response.content == "generated text"
    assert response.provider == "local_hf"


@pytest.mark.asyncio
async def test_model_not_found_maps_to_provider_error(provider: LocalModelProvider) -> None:
    provider._load_error = ProviderError(
        ProviderErrorCode.REAL_MODEL_UNAVAILABLE,
        "REAL_MODEL_UNAVAILABLE: configured local model could not be loaded",
        status_code=503,
    )
    with pytest.raises(ProviderError) as exc:
        await provider.generate(
            GenerateRequest(messages=[ChatMessage(role="user", content="hello")])
        )
    assert exc.value.code.value == "REAL_MODEL_UNAVAILABLE"
