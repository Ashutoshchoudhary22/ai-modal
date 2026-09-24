# Local Model Setup

Guide for running `LocalModelProvider` with Hugging Face Transformers.

## Prerequisites

- Python 3.12+
- Optional NVIDIA GPU + CUDA for faster inference
- Sufficient disk space for model weights

## Install Local Inference Dependencies

```bash
pip install -e "services/ai-api[local]"
```

This installs:

- PyTorch
- Transformers
- Accelerate

## Configure Environment

```env
AI_PLATFORM_ENV=development
AI_PLATFORM_MODEL_PROVIDER=local
AI_PLATFORM_MODEL_ID=sshleifer/tiny-gpt2
AI_PLATFORM_MODEL_DEVICE=auto
AI_PLATFORM_MODEL_DTYPE=auto
AI_PLATFORM_MODEL_MAX_CONTEXT=4096
AI_PLATFORM_MODEL_TRUST_REMOTE_CODE=false
```

Use either:

- `AI_PLATFORM_MODEL_ID` for a Hugging Face model ID
- `AI_PLATFORM_MODEL_PATH` for a local checkpoint directory

Do not set both unless `MODEL_PATH` should take precedence.

## Device Selection

| Setting | Behavior |
|---------|----------|
| `auto` | Use CUDA if available, otherwise CPU |
| `cpu` | Force CPU |
| `cuda` | Use default CUDA device if available |
| `cuda:0` | Use specific CUDA device |

CPU inference remains supported for small models.

## Dtype Selection

| Setting | Behavior |
|---------|----------|
| `auto` | `float16` on CUDA, `float32` on CPU |
| `float32` | Full precision |
| `float16` | Half precision (CUDA only) |
| `bfloat16` | BF16 (CUDA only) |

Unsupported dtype/device combinations return a clear configuration error.

## Start AI API

```bash
make dev-ai-api
```

Check readiness:

```bash
curl http://localhost:8000/ready
```

First inference request triggers lazy model loading.

## Example Requests

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Write a Python hello world function"}]}'
```

Streaming:

```bash
curl -N -X POST http://localhost:8000/v1/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"Count to five"}]}'
```

## Recommended Test Model

For development and smoke tests:

```text
sshleifer/tiny-gpt2
```

This model is small and suitable for CPU testing.

## Limitations (Phase 1)

- Embeddings are not supported for causal LM checkpoints
- Vision/multimodal inference is not implemented
- vLLM serving is not integrated yet
- Proprietary weights are not available yet

## Troubleshooting

| Symptom | Likely Cause |
|---------|--------------|
| `MODEL_NOT_CONFIGURED` | Missing `MODEL_ID` / `MODEL_PATH` |
| `MODEL_NOT_FOUND` | Invalid model ID/path |
| `OUT_OF_MEMORY` | Model too large for available GPU/RAM |
| `CONTEXT_LENGTH_EXCEEDED` | Prompt + max tokens exceeds configured context |
| `GENERATION_TIMEOUT` | Increase `AI_PLATFORM_MODEL_GENERATION_TIMEOUT_SEC` |

Check server logs with the `X-Request-ID` response header for correlation.
