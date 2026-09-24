"""Optional local model integration tests.

Run manually with:
  pip install -e "services/ai-api[local]"
  AI_PLATFORM_RUN_LOCAL_MODEL_TESTS=1 pytest \\
    services/ai-api/tests/test_local_integration.py -m integration
"""

import os

import pytest
from ai_api.providers.local_model import LocalModelProvider
from ai_platform_protocol.models.inference import ChatMessage, GenerateRequest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    os.getenv("AI_PLATFORM_RUN_LOCAL_MODEL_TESTS") != "1",
    reason="Set AI_PLATFORM_RUN_LOCAL_MODEL_TESTS=1 to run local model integration tests",
)
@pytest.mark.asyncio
async def test_local_model_generate_tiny_gpt2() -> None:
    transformers = pytest.importorskip("transformers")
    torch = pytest.importorskip("torch")
    _ = (transformers, torch)

    provider = LocalModelProvider(
        model_id="sshleifer/tiny-gpt2",
        device_setting="cpu",
        dtype_setting="float32",
        max_context=512,
        generation_timeout_sec=120,
    )
    response = await provider.generate(
        GenerateRequest(
            messages=[ChatMessage(role="user", content="Hello")],
            max_tokens=8,
            temperature=0.7,
        )
    )
    assert response.content
    assert response.provider == "local_hf"
    assert response.usage.total_tokens > 0
