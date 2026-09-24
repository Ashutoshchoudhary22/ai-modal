"""Local model evaluation adapter (HTTP inference API)."""

from __future__ import annotations

import httpx

from training.evaluation.adapters.base import EvaluationModelAdapter
from training.evaluation.errors import EvaluationError, EvaluationErrorCode


class LocalEvaluationAdapter(EvaluationModelAdapter):
    def __init__(
        self,
        *,
        model_id: str,
        api_url: str = "http://127.0.0.1:8000",
        timeout_sec: float = 120.0,
    ) -> None:
        self._model_id = model_id
        self._api_url = api_url.rstrip("/")
        self._timeout = timeout_sec

    @property
    def provider_id(self) -> str:
        return "local_hf"

    @property
    def model_id(self) -> str:
        return self._model_id

    async def generate(self, prompt: str, *, max_tokens: int = 256) -> str:
        payload = {
            "model": self._model_id,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.2,
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.post(f"{self._api_url}/v1/chat", json=payload)
        except httpx.HTTPError as exc:
            raise EvaluationError(
                EvaluationErrorCode.MODEL_UNAVAILABLE,
                f"REAL_MODEL_UNAVAILABLE: local evaluation API unreachable ({exc})",
            ) from exc
        if response.status_code != 200:
            raise EvaluationError(
                EvaluationErrorCode.MODEL_UNAVAILABLE,
                f"REAL_MODEL_UNAVAILABLE: local evaluation API returned {response.status_code}",
            )
        data = response.json()
        content = data.get("content", "")
        if not isinstance(content, str) or not content.strip():
            raise EvaluationError(
                EvaluationErrorCode.MODEL_UNAVAILABLE,
                "REAL_MODEL_UNAVAILABLE: empty model response",
            )
        return content
