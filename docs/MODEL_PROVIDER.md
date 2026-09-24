# Model Provider Architecture

Phase 1 introduces a replaceable model provider layer.

## Dependency Direction

```text
Application / AI API
        ↓
ModelProvider Protocol (packages/protocol)
        ↓
Provider Factory (services/ai-api/providers/factory.py)
        ↓
Provider Implementation
        ↓
Transformers / PyTorch / future vLLM / proprietary runtime
```

Application and agent code must never import vendor libraries directly.

## Supported Providers

| Provider ID | Class | Purpose |
|-------------|-------|---------|
| `development_mock` | `DevelopmentMockProvider` | Dev/test/CI only |
| `local_hf` | `LocalModelProvider` | Local Hugging Face inference |
| `proprietary` | `ProprietaryModelProvider` | Future internal weights (placeholder) |

Configure with:

```env
AI_PLATFORM_MODEL_PROVIDER=development_mock
```

For **real local chat** on CPU, see [REAL_CHAT_MODEL.md](./REAL_CHAT_MODEL.md) (`AI_PLATFORM_MODEL_PROVIDER=local`).

Aliases:

- `mock` → `development_mock`
- `local` → `LocalModelProvider`

## ModelProvider Interface

Located in `packages/protocol/src/ai_platform_protocol/providers/base.py`.

Required capabilities:

- `generate`
- `stream`
- `generate_structured`
- `embed`
- `vision` (abstraction only until multimodal provider exists)
- `count_tokens`
- `get_status`

## Provider States

| State | Meaning |
|-------|---------|
| `configured` | Provider configured, model not loaded yet |
| `loading` | Model load in progress |
| `ready` | Provider ready for inference |
| `unavailable` | Provider cannot serve requests |

Check via:

```http
GET /ready
```

## Production Rule

`DevelopmentMockProvider` is blocked in production:

```python
settings.validate_production_provider()
```

Use `local` or future `proprietary` in production environments.

## Model Registry

MySQL table: `provider_model_registry`

Managed through `RegistryService` and exposed via:

```http
GET /v1/models
```

Registry records include model ID, version, provider, capabilities, context length, modalities, and status.

## Error Codes

Provider failures use structured codes such as:

- `MODEL_NOT_CONFIGURED`
- `MODEL_NOT_FOUND`
- `MODEL_LOAD_FAILED`
- `CUDA_UNAVAILABLE`
- `OUT_OF_MEMORY`
- `CONTEXT_LENGTH_EXCEEDED`
- `PROVIDER_UNAVAILABLE`
- `GENERATION_TIMEOUT`

## Observability

Inference requests log:

- correlation/request ID
- provider ID
- model ID
- latency
- token counts

Prompts and secrets are not logged.

## Future Extension

Add a new provider by:

1. Implementing `ModelProvider`
2. Registering it in `create_provider`
3. Adding tests and documentation
4. Registering supported models in MySQL

No agent or business logic changes required.
