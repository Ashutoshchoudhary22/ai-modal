# API Specification

Base URL (development): `http://localhost:8000`  
API version prefix: `/v1`

All JSON requests/responses use `Content-Type: application/json` unless noted.

---

## Authentication

| Method | Header | Use |
|--------|--------|-----|
| Bearer JWT | `Authorization: Bearer <token>` | User sessions (web/desktop) |
| API Key | `X-API-Key: <key>` | Programmatic access |

Unauthenticated endpoints: `/health`, `/ready`, `/v1/meta`.

Rate limits (default): 60 req/min per key; configurable via `AI_PLATFORM_RATE_LIMIT_RPM`.

---

## Common Types

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Human-readable message",
    "details": {}
  },
  "request_id": "uuid"
}
```

### Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid request payload |
| `UNAUTHORIZED` | 401 | Missing or invalid auth |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `MODEL_UNAVAILABLE` | 503 | Model provider offline |
| `MODEL_NOT_CONFIGURED` | 503 | Model/provider not configured |
| `MODEL_NOT_FOUND` | 404 | Model checkpoint not found |
| `MODEL_LOAD_FAILED` | 503 | Model failed to load |
| `CUDA_UNAVAILABLE` | 503 | CUDA requested but unavailable |
| `OUT_OF_MEMORY` | 503 | Insufficient memory |
| `CONTEXT_LENGTH_EXCEEDED` | 400 | Prompt exceeds context window |
| `PROVIDER_UNAVAILABLE` | 503 | Provider capability unavailable |
| `GENERATION_TIMEOUT` | 504 | Generation timed out |
| `GENERATION_CANCELLED` | 499 | Generation cancelled |

---

## Health & Meta

### `GET /health`

Liveness check. No auth required.

**Response 200:**

```json
{
  "status": "ok",
  "version": "0.1.0",
  "environment": "development"
}
```

### `GET /ready`

Readiness check including provider state. No auth required.

**Response 200:**

```json
{
  "status": "ready",
  "provider": "development_mock",
  "provider_state": "ready",
  "model_id": "development-mock-v1",
  "message": "Development/test provider — not for production use",
  "device": null
}
```

### `GET /v1/meta`

Platform metadata.

**Response 200:**

```json
{
  "api_version": "v1",
  "platform_version": "0.1.0",
  "supported_modalities": ["text"],
  "providers": ["development_mock"]
}
```

---

## Inference — AI API (`services/ai-api`)

### `GET /v1/models`

List registered models for the active provider.

### `POST /v1/chat`

Chat completion (alias of generate with message-oriented API).

**Request:** Same as `/v1/generate`.

### `POST /v1/generate`

Non-streaming text generation.

**Request:**

```json
{
  "model": "default",
  "messages": [
    {"role": "system", "content": "You are a coding assistant."},
    {"role": "user", "content": "Explain recursion."}
  ],
  "max_tokens": 1024,
  "temperature": 0.7,
  "stop": []
}
```

**Response 200:**

```json
{
  "id": "gen_uuid",
  "model": "development-mock-v1",
  "content": "...",
  "finish_reason": "stop",
  "usage": {
    "prompt_tokens": 42,
    "completion_tokens": 128,
    "total_tokens": 170
  }
}
```

### `POST /v1/chat/stream`

Server-Sent Events streaming chat completion.

**Request:** Same body as `/v1/generate`.

**Legacy alias:** `POST /v1/generate/stream`

### `POST /v1/generate/stream`

Server-Sent Events (SSE) streaming.

**Request:** Same body as `/v1/generate`.

**Response:** `Content-Type: text/event-stream`

```
data: {"type":"chunk","content":"Hello"}
data: {"type":"chunk","content":" world"}
data: {"type":"done","usage":{"prompt_tokens":10,"completion_tokens":2,"total_tokens":12}}
```

### `POST /v1/generate/structured`

JSON-schema constrained generation.

**Request:**

```json
{
  "model": "default",
  "messages": [{"role": "user", "content": "List 2 colors"}],
  "response_schema": {
    "type": "object",
    "properties": {
      "colors": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["colors"]
  }
}
```

**Response 200:**

```json
{
  "id": "gen_uuid",
  "model": "development-mock-v1",
  "parsed": {"colors": ["red", "blue"]},
  "usage": {"prompt_tokens": 20, "completion_tokens": 10, "total_tokens": 30}
}
```

### `POST /v1/embeddings`

Text embeddings.

**Legacy alias:** `POST /v1/embed`

### `POST /v1/embed`

Text embeddings.

**Request:**

```json
{
  "model": "embed-default",
  "inputs": ["def hello(): pass", "class Foo: pass"]
}
```

**Response 200:**

```json
{
  "model": "development-mock-embed-v1",
  "embeddings": [[0.1, 0.2], [0.3, 0.4]],
  "dimensions": 2,
  "usage": {"total_tokens": 15}
}
```

### `POST /v1/vision`

Multimodal input (Phase 10+). Stub in Phase 0.

**Request:**

```json
{
  "model": "vision-default",
  "messages": [{"role": "user", "content": "Describe this UI"}],
  "images": [{"url": "https://...", "detail": "high"}]
}
```

---

## Agent — Agent Service (`services/agent`)

### `POST /v1/agent/sessions`

Create agent session.

**Request:**

```json
{
  "workspace_root": "/path/to/project",
  "task": "Fix the authentication bug in login flow",
  "model": "default",
  "max_iterations": 25
}
```

**Response 201:**

```json
{
  "session_id": "sess_uuid",
  "status": "created",
  "ws_url": "ws://localhost:8001/v1/agent/sessions/sess_uuid/stream"
}
```

### `GET /v1/agent/sessions/{session_id}`

Session status and summary.

### `POST /v1/agent/sessions/{session_id}/cancel`

Cancel running session.

### `WebSocket /v1/agent/sessions/{session_id}/stream`

Agent event stream.

**Event types:**

```json
{"type": "plan", "steps": ["...", "..."]}
{"type": "tool_call", "tool": "read_file", "args": {"path": "src/auth.py"}}
{"type": "tool_result", "tool": "read_file", "output": "...", "success": true}
{"type": "message", "role": "assistant", "content": "..."}
{"type": "error", "message": "..."}
{"type": "done", "status": "completed", "summary": "..."}
```

---

## Code Indexer (`services/code-indexer`)

### `POST /v1/index`

Index or re-index a workspace.

**Request:**

```json
{
  "workspace_id": "ws_uuid",
  "root_path": "/path/to/repo",
  "force": false
}
```

### `POST /v1/search`

Hybrid code search.

**Request:**

```json
{
  "workspace_id": "ws_uuid",
  "query": "authentication middleware",
  "mode": "hybrid",
  "limit": 20
}
```

**Response 200:**

```json
{
  "results": [
    {
      "path": "src/middleware/auth.ts",
      "score": 0.92,
      "snippet": "...",
      "symbols": ["authenticate", "AuthMiddleware"]
    }
  ]
}
```

### `GET /v1/symbols/{workspace_id}`

Symbol graph export (JSON).

---

## Browser Agent (`services/browser-agent`)

### `POST /v1/browser/sessions`

**Request:**

```json
{
  "url": "http://localhost:3000",
  "viewport": {"width": 1280, "height": 720}
}
```

### `POST /v1/browser/sessions/{id}/actions`

Execute Playwright actions (click, type, scroll, screenshot).

---

## Training API (`services/training-api`)

### `POST /v1/training/jobs`

Submit training job.

**Request:**

```json
{
  "config_path": "models/configs/code_sft.yaml",
  "dataset_version": "code-v1.0.0",
  "job_type": "sft"
}
```

### `GET /v1/training/jobs/{job_id}`

Job status, logs URL, metrics.

---

## Model Management

### `GET /v1/models`

List available models and capabilities.

### `GET /v1/models/{model_id}/versions`

Version history with benchmark summaries.

---

## Usage & Billing (Phase 16)

### `GET /v1/usage`

Token and request usage for current org/billing period.

---

## WebSocket Conventions

- Client sends `{"type":"ping"}` → server `{"type":"pong"}`
- Include `request_id` in client messages for correlation
- Server closes with code 4401 on auth failure

---

## Versioning

Breaking changes increment `/v2`. Deprecation notices in `Sunset` header minimum 90 days.

---

*Last updated: Phase 0*
