# Real Local Chat Model

This guide explains how to replace `DevelopmentMockProvider` responses like `[development-mock] stream: hiee` with **real** Hugging Face inference on CPU.

## Recommended model (16 GB RAM, CPU only)

| Setting | Value |
|---------|-------|
| Model | `Qwen/Qwen2.5-0.5B-Instruct` |
| Size | ~0.5B parameters (~1 GB RAM) |
| Device | `cpu` |
| Dtype | `float32` |

Larger models (1.5B–7B+) may load on 16 GB RAM but are slow or OOM-prone on CPU-only machines.

## Install inference dependencies

```bash
pip install -e "packages/protocol[dev]" -e "packages/shared[dev]" -e "services/ai-api[local]"
```

Requires: `torch`, `transformers>=4.46`, `accelerate`.

## Configure `.env`

Copy from `.env.example` and set:

```env
AI_PLATFORM_MODEL_PROVIDER=local
AI_PLATFORM_DEFAULT_MODEL=Qwen/Qwen2.5-0.5B-Instruct
AI_PLATFORM_MODEL_ID=Qwen/Qwen2.5-0.5B-Instruct
AI_PLATFORM_MODEL_DEVICE=cpu
AI_PLATFORM_MODEL_DTYPE=float32
AI_PLATFORM_MODEL_MAX_CONTEXT=2048
AI_PLATFORM_MODEL_GENERATION_MAX_TOKENS=256
AI_PLATFORM_MODEL_GENERATION_TEMPERATURE=0.7
```

Optional:

```env
AI_PLATFORM_MODEL_PRELOAD=true
AI_PLATFORM_CHAT_RAG_ENABLED=true
AI_PLATFORM_INDEXER_URL=http://127.0.0.1:8002
```

**Do not** set `AI_PLATFORM_MODEL_PROVIDER=development_mock` for real chat.

## Start AI API

```bash
cd services/ai-api
uvicorn ai_api.main:app --port 8000
```

Verify:

```bash
curl http://127.0.0.1:8000/ready
curl -X POST http://127.0.0.1:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"hiee"}],"max_tokens":64}'
```

First request downloads weights from Hugging Face (may take several minutes).

## Desktop IDE

1. Start AI API with `local` provider (above).
2. Run desktop: `npm run dev:desktop`
3. Open **Assistant → Chat** and send messages.

The desktop sends full conversation history to `POST /v1/chat/stream`. Responses stream real generated tokens.

## Architecture

```text
Desktop Assistant
      ↓ POST /v1/chat/stream
InferenceService
      ↓ system prompt + history trim + optional RAG
LocalModelProvider (lazy load, cached)
      ↓ Transformers generate / stream
Real model weights
```

## No silent mock fallback

If the local model is misconfigured or fails to load, the API returns:

```text
REAL_MODEL_UNAVAILABLE
```

It does **not** fall back to `DevelopmentMockProvider`.

## Training (text SFT)

Phase 3 datasets support conversational JSONL:

```json
{"messages": [
  {"role": "system", "content": "You are a coding assistant."},
  {"role": "user", "content": "What is an API?"},
  {"role": "assistant", "content": "An API is ..."}
]}
```

Process and train:

```bash
python -m training.datasets process --manifest training/data/manifests/smoke_sft.json
python -m training.sft.train --config training/configs/sft/smoke.yaml
```

## RAG / knowledge

`AI_PLATFORM_CHAT_RAG_ENABLED=true` uses the code indexer (`AI_PLATFORM_INDEXER_URL`) to retrieve bounded symbol/file context. Vector DB integration is interface-only for future phases.

## Evaluation

```bash
AI_PLATFORM_EVAL_API_URL=http://127.0.0.1:8000 \
python -m training.evaluation run --benchmark conversation-mini --provider local --model Qwen/Qwen2.5-0.5B-Instruct
```

## Known limitations

- CPU inference is slow (seconds per reply for 0.5B).
- Small models are not ChatGPT-equivalent; quality is limited by model size.
- Embeddings and vision remain separate provider stacks.
- No `/v1/completions/stream` (completion uses non-streaming API).
- Agent structured tool JSON may be unreliable on very small models.
