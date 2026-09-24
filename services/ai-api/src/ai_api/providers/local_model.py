"""Local Hugging Face Transformers model provider."""

from __future__ import annotations

import asyncio
import json
import threading
import uuid
from collections.abc import AsyncIterator
from typing import Any

from ai_platform_protocol.models.common import TokenUsage
from ai_platform_protocol.models.errors import ProviderErrorCode
from ai_platform_protocol.models.inference import (
    ChatMessage,
    EmbedRequest,
    EmbedResponse,
    GenerateRequest,
    GenerateResponse,
    StreamChunk,
    StructuredGenerateRequest,
    StructuredGenerateResponse,
    VisionRequest,
    VisionResponse,
)
from ai_platform_protocol.models.provider import ProviderCapabilities, ProviderState, ProviderStatus

from ai_api.providers.device import detect_device, resolve_dtype, to_device_info
from ai_api.providers.errors import ProviderError


class LocalModelProvider:
    provider_id = "local_hf"
    provider_name = "Local Hugging Face Provider"

    def __init__(
        self,
        *,
        model_id: str = "",
        model_path: str = "",
        default_model: str = "default",
        device_setting: str = "auto",
        dtype_setting: str = "auto",
        max_context: int = 4096,
        trust_remote_code: bool = False,
        generation_timeout_sec: int = 120,
    ) -> None:
        self._model_ref = model_path or model_id
        self._default_model = default_model
        self._device_setting = device_setting
        self._dtype_setting = dtype_setting
        self._max_context = max_context
        self._trust_remote_code = trust_remote_code
        self._generation_timeout_sec = generation_timeout_sec

        self._device = detect_device(device_setting)
        self._dtype_name = resolve_dtype(dtype_setting, self._device)
        self._load_lock = threading.Lock()
        self._model: Any | None = None
        self._tokenizer: Any | None = None
        self._loading = False
        self._load_error: ProviderError | None = None

    async def get_status(self) -> ProviderStatus:
        if not self._model_ref:
            return ProviderStatus(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                state=ProviderState.UNAVAILABLE,
                message=(
                    "Local model is not configured. "
                    "Set AI_PLATFORM_MODEL_ID or AI_PLATFORM_MODEL_PATH."
                ),
                device=to_device_info(self._device),
                capabilities=ProviderCapabilities(
                    generate=True,
                    stream=True,
                    structured=True,
                    embed=False,
                    vision=False,
                ),
            )
        if self._load_error is not None:
            return ProviderStatus(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                state=ProviderState.UNAVAILABLE,
                model_id=self._model_ref,
                message=self._load_error.message,
                device=to_device_info(self._device),
            )
        if self._model is None:
            return ProviderStatus(
                provider_id=self.provider_id,
                provider_name=self.provider_name,
                state=ProviderState.CONFIGURED if not self._loading else ProviderState.LOADING,
                model_id=self._model_ref,
                message="Model configured but not loaded yet",
                device=to_device_info(self._device),
            )
        return ProviderStatus(
            provider_id=self.provider_id,
            provider_name=self.provider_name,
            state=ProviderState.READY,
            model_id=self._model_ref,
            message="Local model loaded",
            device=to_device_info(self._device),
            capabilities=ProviderCapabilities(
                generate=True,
                stream=True,
                structured=True,
                embed=False,
                vision=False,
            ),
            diagnostics={
                "dtype": self._dtype_name,
                "max_context": self._max_context,
            },
        )

    async def generate(self, request: GenerateRequest) -> GenerateResponse:
        model, tokenizer = await self._ensure_loaded()
        prompt = self._format_prompt(request.resolved_messages(), tokenizer)
        prompt_tokens = len(tokenizer.encode(prompt))
        self._validate_context(prompt_tokens, request.max_tokens)
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {key: value.to(model.device) for key, value in inputs.items()}

        def _run_generate() -> Any:
            return model.generate(
                **inputs,
                max_new_tokens=request.max_tokens,
                temperature=max(request.temperature, 1e-5),
                top_p=request.top_p,
                do_sample=request.temperature > 0,
                pad_token_id=tokenizer.eos_token_id,
            )

        try:
            output = await asyncio.wait_for(
                asyncio.to_thread(_run_generate),
                timeout=self._generation_timeout_sec,
            )
        except TimeoutError as exc:
            raise ProviderError(
                ProviderErrorCode.GENERATION_TIMEOUT,
                "Generation timed out",
                status_code=504,
            ) from exc
        except RuntimeError as exc:
            message = str(exc).lower()
            if "out of memory" in message or "cuda" in message and "memory" in message:
                raise ProviderError(
                    ProviderErrorCode.OUT_OF_MEMORY,
                    "Insufficient memory for generation",
                    status_code=503,
                ) from exc
            raise ProviderError(
                ProviderErrorCode.INTERNAL_ERROR,
                "Generation failed",
                status_code=500,
            ) from exc

        generated = tokenizer.decode(
            output[0][inputs["input_ids"].shape[-1] :], skip_special_tokens=True
        )
        completion_tokens = len(tokenizer.encode(generated))
        return GenerateResponse(
            id=f"gen_{uuid.uuid4().hex[:12]}",
            model=request.model if request.model != "default" else self._model_ref,
            content=generated.strip(),
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            provider=self.provider_id,
        )

    async def stream(self, request: GenerateRequest) -> AsyncIterator[StreamChunk]:
        model, tokenizer = await self._ensure_loaded()
        prompt = self._format_prompt(request.resolved_messages(), tokenizer)
        prompt_tokens = len(tokenizer.encode(prompt))
        self._validate_context(prompt_tokens, request.max_tokens)
        inputs = tokenizer(prompt, return_tensors="pt")
        inputs = {key: value.to(model.device) for key, value in inputs.items()}

        from transformers import TextIteratorStreamer

        streamer = TextIteratorStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
        generation_kwargs = {
            **inputs,
            "max_new_tokens": request.max_tokens,
            "temperature": max(request.temperature, 1e-5),
            "top_p": request.top_p,
            "do_sample": request.temperature > 0,
            "pad_token_id": tokenizer.eos_token_id,
            "streamer": streamer,
        }

        thread = threading.Thread(target=model.generate, kwargs=generation_kwargs, daemon=True)
        thread.start()

        completion_parts: list[str] = []
        try:
            for text in streamer:
                if text:
                    completion_parts.append(text)
                    await asyncio.sleep(0)
                    yield StreamChunk(type="chunk", content=text, provider=self.provider_id)
        except Exception as exc:
            yield StreamChunk(
                type="error",
                message="Streaming failed",
                provider=self.provider_id,
            )
            raise ProviderError(
                ProviderErrorCode.INTERNAL_ERROR,
                "Streaming failed",
                status_code=500,
            ) from exc
        finally:
            thread.join(timeout=self._generation_timeout_sec)

        completion_text = "".join(completion_parts)
        completion_tokens = len(tokenizer.encode(completion_text)) if completion_text else 0
        yield StreamChunk(
            type="done",
            usage=TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            provider=self.provider_id,
        )

    async def generate_structured(
        self, request: StructuredGenerateRequest
    ) -> StructuredGenerateResponse:
        schema_prompt = (
            "Respond with valid JSON only that matches this schema:\n"
            f"{json.dumps(request.response_schema)}"
        )
        structured_request = GenerateRequest(
            model=request.model,
            messages=[
                *request.resolved_messages(),
                ChatMessage(role="user", content=schema_prompt),
            ],
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
            metadata=request.metadata,
        )
        response = await self.generate(structured_request)
        try:
            parsed = json.loads(response.content)
        except json.JSONDecodeError as exc:
            raise ProviderError(
                ProviderErrorCode.INVALID_REQUEST,
                "Model did not return valid JSON for structured generation",
                status_code=422,
            ) from exc
        if not isinstance(parsed, dict):
            raise ProviderError(
                ProviderErrorCode.INVALID_REQUEST,
                "Structured generation must return a JSON object",
                status_code=422,
            )
        return StructuredGenerateResponse(
            id=response.id,
            model=response.model,
            parsed=parsed,
            usage=response.usage,
            provider=self.provider_id,
        )

    async def embed(self, request: EmbedRequest) -> EmbedResponse:
        raise ProviderError(
            ProviderErrorCode.PROVIDER_UNAVAILABLE,
            "Embedding is not supported by the configured local causal model",
            status_code=503,
        )

    async def vision(self, request: VisionRequest) -> VisionResponse:
        raise ProviderError(
            ProviderErrorCode.PROVIDER_UNAVAILABLE,
            "Vision is not implemented for LocalModelProvider",
            status_code=503,
        )

    def count_tokens(self, text: str, model_id: str | None = None) -> int:
        _ = model_id
        if self._tokenizer is not None:
            return len(self._tokenizer.encode(text))
        if self._model_ref:
            try:
                from transformers import AutoTokenizer

                tokenizer = AutoTokenizer.from_pretrained(
                    self._model_ref,
                    trust_remote_code=self._trust_remote_code,
                )
                return len(tokenizer.encode(text))
            except Exception:
                pass
        raise ProviderError(
            ProviderErrorCode.MODEL_NOT_CONFIGURED,
            "Tokenizer is unavailable until the local model is configured/loaded",
            status_code=503,
        )

    async def _ensure_loaded(self) -> tuple[Any, Any]:
        if self._model is not None and self._tokenizer is not None:
            return self._model, self._tokenizer
        if not self._model_ref:
            raise ProviderError(
                ProviderErrorCode.MODEL_NOT_CONFIGURED,
                "Local model is not configured",
                status_code=503,
            )
        if self._load_error is not None:
            raise self._load_error
        await asyncio.to_thread(self._load_model_sync)
        if self._model is None or self._tokenizer is None:
            raise ProviderError(
                ProviderErrorCode.MODEL_LOAD_FAILED,
                "Local model failed to load",
                status_code=503,
            )
        return self._model, self._tokenizer

    def _load_model_sync(self) -> None:
        with self._load_lock:
            if self._model is not None and self._tokenizer is not None:
                return
            self._loading = True
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer

                tokenizer = AutoTokenizer.from_pretrained(
                    self._model_ref,
                    trust_remote_code=self._trust_remote_code,
                )
                if tokenizer.pad_token is None and tokenizer.eos_token is not None:
                    tokenizer.pad_token = tokenizer.eos_token

                torch_dtype = {
                    "float32": torch.float32,
                    "float16": torch.float16,
                    "bfloat16": torch.bfloat16,
                }[self._dtype_name]

                model = AutoModelForCausalLM.from_pretrained(
                    self._model_ref,
                    trust_remote_code=self._trust_remote_code,
                    torch_dtype=torch_dtype,
                )
                model.to(self._device.torch_device)
                model.eval()
                self._tokenizer = tokenizer
                self._model = model
                self._load_error = None
            except FileNotFoundError as exc:
                self._load_error = ProviderError(
                    ProviderErrorCode.MODEL_NOT_FOUND,
                    "Configured local model was not found",
                    status_code=404,
                )
                raise self._load_error from exc
            except OSError as exc:
                self._load_error = ProviderError(
                    ProviderErrorCode.MODEL_NOT_FOUND,
                    "Configured local model could not be loaded",
                    status_code=404,
                )
                raise self._load_error from exc
            except RuntimeError as exc:
                message = str(exc).lower()
                if "out of memory" in message:
                    self._load_error = ProviderError(
                        ProviderErrorCode.OUT_OF_MEMORY,
                        "Insufficient memory to load local model",
                        status_code=503,
                    )
                else:
                    self._load_error = ProviderError(
                        ProviderErrorCode.MODEL_LOAD_FAILED,
                        "Failed to load local model",
                        status_code=503,
                    )
                raise self._load_error from exc
            except Exception as exc:
                self._load_error = ProviderError(
                    ProviderErrorCode.MODEL_LOAD_FAILED,
                    "Failed to load local model",
                    status_code=503,
                )
                raise self._load_error from exc
            finally:
                self._loading = False

    def _validate_context(self, prompt_tokens: int, max_new_tokens: int) -> None:
        if prompt_tokens + max_new_tokens > self._max_context:
            raise ProviderError(
                ProviderErrorCode.CONTEXT_LENGTH_EXCEEDED,
                "Request exceeds configured model context length",
                details={
                    "prompt_tokens": prompt_tokens,
                    "max_new_tokens": max_new_tokens,
                    "max_context": self._max_context,
                },
                status_code=400,
            )

    @staticmethod
    def _format_prompt(messages: list[Any], tokenizer: Any) -> str:
        if hasattr(tokenizer, "apply_chat_template"):
            try:
                return tokenizer.apply_chat_template(
                    [{"role": m.role, "content": m.content} for m in messages],
                    tokenize=False,
                    add_generation_prompt=True,
                )
            except Exception:
                pass
        return "\n".join(f"{message.role}: {message.content}" for message in messages)
