# Multimodal Model Architecture — Phase 10

Modular, provider-independent architecture for text + image inference.

## Architecture

```
MultimodalRequest
        ↓
ImageProcessor (optional per image)
        ↓
VisionEncoder → MultimodalProjector
        ↓
MultimodalFusion
        ↓
Language Model / End-to-End MultimodalModel
        ↓
MultimodalResponse
```

End-to-end VLM providers can implement `MultimodalModel` directly without exposing internal components.

## Protocol

`packages/protocol/src/ai_platform_protocol/multimodal/`:

- `MultimodalMessage`, `TextContent`, `ImageContent`, `ImageReference`
- `MultimodalRequest`, `MultimodalResponse`, `MultimodalStreamChunk`
- `MultimodalCapabilities`, `MultimodalUsage`, `ContextBudget`
- `VisionEncoderOutput`, `VisualEmbedding`, `ProcessedImage`

## Providers

| Provider | Value | Notes |
|----------|-------|-------|
| Mock | `development_mock` | Deterministic modular pipeline (default) |
| Local | `local` | Explicit unavailable unless configured |
| Proprietary | `proprietary` | Placeholder |

Factory: `create_multimodal_model()` in `ai_api.multimodal.factory`.

## API

- `POST /v1/multimodal/generate`
- `POST /v1/multimodal/generate/stream`
- `GET /v1/models` — includes `multimodal.capabilities`

## Phase 8 Integration

Set `AI_PLATFORM_VISION_USE_MULTIMODAL=true` to route `VisionProvider` through `MultimodalVisionProvider`.

Existing screenshot-to-code API remains backward compatible.

## Phase 9 Integration

`browser_observation_to_request()` adapts `BrowserObservation` to `MultimodalRequest`.

## Security

- Images are untrusted input (visual prompt injection)
- `ImageReference` uses `temp://` storage references — no filesystem paths
- Reuses Phase 8 `ImageValidator`
- Tool/agent/browser policies remain authoritative

## Database

No new migration required. Multimodal models use existing `provider_model_registry` with `modalities` metadata.

## Phase 11 Boundary

Phase 10 = architecture + inference interfaces.

Phase 11 = multimodal training strategy, datasets, SFT, checkpointing.
