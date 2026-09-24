# Environment Configuration

All configuration via environment variables. Prefix: `AI_PLATFORM_` (required for platform settings).

Copy `.env.example` to `.env` for local development.

### Development without Docker

For **mock inference only**, Docker is not required:

```bash
AI_PLATFORM_MODEL_PROVIDER=development_mock
uvicorn ai_api.main:app --reload --port 8000
```

MySQL and Redis are optional until you need the model registry, caching, or agent queues.

---

## Application

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PLATFORM_ENV` | `development` | `development`, `staging`, `production` |
| `AI_PLATFORM_DEBUG` | `true` | Enable debug mode (dev only) |
| `AI_PLATFORM_LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR |
| `AI_PLATFORM_SECRET_KEY` | — | JWT signing secret (required in prod) |

---

## Services — Ports

| Variable | Default | Service |
|----------|---------|---------|
| `AI_PLATFORM_AI_API_HOST` | `0.0.0.0` | AI API bind |
| `AI_PLATFORM_AI_API_PORT` | `8000` | AI API port |
| `AI_PLATFORM_AGENT_HOST` | `0.0.0.0` | Agent service |
| `AI_PLATFORM_AGENT_PORT` | `8001` | Agent port |
| `AI_PLATFORM_INDEXER_PORT` | `8002` | Code indexer |
| `AI_PLATFORM_BROWSER_AGENT_PORT` | `8003` | Browser agent |
| `AI_PLATFORM_TRAINING_API_PORT` | `8004` | Training API |

---

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PLATFORM_DATABASE_URL` | `mysql+pymysql://aiplatform:aiplatform@localhost:3306/aiplatform` | MySQL DSN (SQLAlchemy-style) |
| `AI_PLATFORM_DATABASE_POOL_SIZE` | `10` | Connection pool |

---

## Redis

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PLATFORM_REDIS_URL` | `redis://localhost:6379/0` | Cache, sessions, job queue |

---

## Model Provider

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PLATFORM_MODEL_PROVIDER` | `development_mock` | `development_mock`, `mock`, `local`, `proprietary` |
| `AI_PLATFORM_DEFAULT_MODEL` | `development-mock-v1` | Default model ID |
| `AI_PLATFORM_MODEL_ID` | — | Hugging Face model ID for local provider |
| `AI_PLATFORM_MODEL_PATH` | — | Local checkpoint path (takes precedence over model ID) |
| `AI_PLATFORM_MODEL_DEVICE` | `auto` | `auto`, `cpu`, `cuda`, `cuda:0` |
| `AI_PLATFORM_MODEL_DTYPE` | `auto` | `auto`, `float32`, `float16`, `bfloat16` |
| `AI_PLATFORM_MODEL_MAX_CONTEXT` | `4096` | Max context length |
| `AI_PLATFORM_MODEL_TRUST_REMOTE_CODE` | `false` | Allow HF remote code |
| `AI_PLATFORM_MODEL_GENERATION_TIMEOUT_SEC` | `120` | Generation timeout |
| `AI_PLATFORM_MODEL_GENERATION_MAX_TOKENS` | `1024` | Default max tokens |
| `AI_PLATFORM_MODEL_GENERATION_TEMPERATURE` | `0.7` | Default temperature |
| `AI_PLATFORM_MODEL_GENERATION_TOP_P` | `1.0` | Default top-p |
| `AI_PLATFORM_VLLM_ENABLED` | `false` | Use vLLM for inference (future) |
| `AI_PLATFORM_VLLM_HOST` | `http://localhost:8080` | vLLM server URL |
| `AI_PLATFORM_CUDA_VISIBLE_DEVICES` | — | GPU selection (optional) |

See also: [MODEL_PROVIDER.md](./MODEL_PROVIDER.md), [LOCAL_MODEL_SETUP.md](./LOCAL_MODEL_SETUP.md)

**Production rule:** `development_mock` is rejected when `AI_PLATFORM_ENV=production`.

---

## Agent

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PLATFORM_AGENT_MAX_ITERATIONS` | `25` | Default max agent loop iterations |
| `AI_PLATFORM_AGENT_TOOL_TIMEOUT_SEC` | `120` | Per-tool timeout |
| `AI_PLATFORM_AGENT_SANDBOX_ROOT` | — | Workspace sandbox root (required for agent) |
| `AI_PLATFORM_AGENT_SHELL_ALLOWLIST` | `npm,pnpm,yarn,python,pip,pytest,git,cargo,go` | Allowed command prefixes |

---

## Security

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PLATFORM_RATE_LIMIT_RPM` | `60` | Requests per minute per API key |
| `AI_PLATFORM_JWT_EXPIRY_MINUTES` | `60` | Access token TTL |
| `AI_PLATFORM_CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated |

---

## Training

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PLATFORM_TRAINING_OUTPUT_DIR` | `./models/finetuned` | Checkpoint output |
| `AI_PLATFORM_WANDB_ENABLED` | `false` | Weights & Biases logging |
| `AI_PLATFORM_WANDB_PROJECT` | `ai-platform` | W&B project name |

---

## Object Storage (Future)

| Variable | Default | Description |
|----------|---------|-------------|
| `AI_PLATFORM_S3_BUCKET` | — | Model/dataset artifacts |
| `AI_PLATFORM_S3_REGION` | — | AWS region |

---

## Docker Compose Overrides

When using `docker compose`, service hostnames replace `localhost`:

```
AI_PLATFORM_DATABASE_URL=mysql+pymysql://aiplatform:aiplatform@mysql:3306/aiplatform
AI_PLATFORM_REDIS_URL=redis://redis:6379/0
```

See `docker-compose.yml` for service definitions.

---

## Validation Rules

- `AI_PLATFORM_SECRET_KEY` must be ≥ 32 characters in production
- `AI_PLATFORM_ENV=production` requires `AI_PLATFORM_DEBUG=false`
- Database URL must use TLS in production (e.g. `?ssl=true` for MySQL)

---

*Last updated: Phase 1 — Model Abstraction*
