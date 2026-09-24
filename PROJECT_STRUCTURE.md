# AI Platform — Project Structure

## Implementation Status

| Path | Status | Notes |
|------|--------|-------|
| `services/ai-api/` | **IMPLEMENTED** | FastAPI inference service, providers, tests |
| `packages/protocol/` | **IMPLEMENTED** | Model types + provider protocol; agent/tool/indexer stubs |
| `packages/shared/` | **IMPLEMENTED** | Config, logging, DB layer, telemetry context |
| `packages/ui/` | **PLANNED** | Placeholder package only |
| `apps/web/` | **IMPLEMENTED (dev)** | Test console UI (React + Vite) |
| `apps/desktop/`, `apps/admin/` | **PLANNED** | README + placeholder `package.json` only |
| `services/code-indexer/` | **IMPLEMENTED** | Phase 4 repository intelligence (scan, index, search, context) |
| `services/agent/` | **IMPLEMENTED** | Phase 5–9 tools, agent loop, UI generation, screenshot-to-code, browser agent |
| `browser-agent/`, `training-api/` | **PLANNED** | README placeholders only (browser logic lives in `services/agent/browser/`) |
| `training/`, `models/` | **IMPLEMENTED (Phase 2 SFT)** | Dataset pipeline + config-driven training; see `docs/TRAINING.md` |
| `tests/integration/` | **IMPLEMENTED** | Phase 0 structure checks |

Do **not** create empty service directories beyond what the roadmap requires. New services should appear when their phase begins.

---

## Root Layout

```
/
├── apps/                    # Client applications
│   ├── desktop/             # Electron IDE
│   ├── web/                 # User web application
│   └── admin/               # Admin / observability portal
│
├── services/                # Backend microservices
│   ├── ai-api/              # Inference API (generate, embed, stream)
│   ├── agent/               # Coding agent orchestration
│   ├── code-indexer/        # Repository indexing & search
│   ├── browser-agent/       # Playwright automation
│   └── training-api/        # Training job management
│
├── models/                  # Model artifacts & configs
│   ├── base/                # Base model references (not weights in git)
│   ├── finetuned/           # Fine-tuned checkpoint metadata
│   └── configs/             # Model configuration YAML
│
├── training/                # ML training pipelines
│   ├── data/                # Dataset storage (gitignored large files)
│   ├── preprocess/          # Cleaning, dedup, formatting
│   ├── sft/                 # Supervised fine-tuning scripts
│   ├── preference/          # DPO / preference optimization
│   └── evaluation/          # Benchmark runners
│
├── packages/                # Shared libraries
│   ├── shared/              # Python shared utilities
│   ├── protocol/            # Pydantic models & interfaces
│   └── ui/                  # Shared React components
│
├── infra/                   # Infrastructure as code
│   ├── docker/              # Dockerfiles per service
│   └── k8s/                 # Kubernetes manifests (future)
│
├── scripts/                 # Dev & ops scripts
├── docs/                    # Extended documentation
├── tests/                   # Cross-cutting integration tests
│
├── ARCHITECTURE.md
├── ROADMAP.md
├── DEVELOPMENT_RULES.md
├── PROJECT_STRUCTURE.md
├── README.md
│
├── pyproject.toml           # Python workspace root
├── package.json             # Node workspace root
├── docker-compose.yml       # Local dev stack
├── Makefile                 # Common dev commands
└── .env.example             # Environment template
```

---

## Applications (`apps/`)

### `apps/desktop`

Electron + React + TypeScript IDE.

| Path | Purpose |
|------|---------|
| `src/main/` | Electron main process |
| `src/renderer/` | React UI (Monaco, chat, terminal) |
| `src/preload/` | Secure IPC bridge |

### `apps/web`

Customer-facing SaaS web app (project management, settings, billing UI).

### `apps/admin`

Internal admin: model versions, benchmarks, usage dashboards.

---

## Services (`services/`)

Each service follows:

```
services/<name>/
├── pyproject.toml      # or package.json for Node services
├── src/
│   └── <name>/
│       ├── __init__.py
│       ├── main.py       # FastAPI entry
│       ├── routes/
│       ├── services/
│       └── config.py
├── tests/
└── README.md
```

| Service | Port (dev) | Description |
|---------|------------|-------------|
| ai-api | 8000 | Model inference REST/WS |
| agent | 8001 | Agent sessions & tools |
| code-indexer | 8002 | Index & search |
| browser-agent | 8003 | Playwright worker |
| training-api | 8004 | Training jobs |

---

## Packages (`packages/`)

### `packages/protocol`

**Single source of truth** for cross-service types:

- `ModelProvider` protocol (**IMPLEMENTED**)
- Request/response Pydantic models (**IMPLEMENTED**)
- `tools/` types and protocol (**IMPLEMENTED** — Phase 5)
- `agent/`, `indexer/` protocol stubs (**PLANNED** — Phase 6+)
- Error codes (**IMPLEMENTED**)

### `packages/shared`

Logging, config loading, DB layer, telemetry context (**IMPLEMENTED**).

### `packages/ui`

Shared React components (design system).

---

## Training (`training/`)

```
training/
├── sft/
│   └── train.py              # python training/sft/train.py --config ...
├── preprocess/
│   ├── deduplicate.py
│   ├── validate.py
│   └── format_instructions.py
├── evaluation/
│   └── run_benchmarks.py
└── data/
    └── manifests/            # JSON/YAML dataset manifests
```

Configs live in `models/configs/` (e.g. `code_sft.yaml`).

---

## Models (`models/`)

- **Do not commit large weight files** — use `.gitignore` + object storage references.
- `models/configs/` — architecture, LoRA rank, learning rate, etc.
- `models/base/README.md` — documented open-source base model IDs for dev.

---

## Infrastructure (`infra/`)

```
infra/docker/
├── ai-api.Dockerfile
├── agent.Dockerfile
├── mysql/
│   └── init.sql
└── ...
```

---

## Tests (`tests/`)

| Path | Scope |
|------|-------|
| `tests/integration/` | Multi-service flows |
| `tests/fixtures/` | Sample repos, mock data |
| `services/*/tests/` | Service unit tests |
| `packages/*/tests/` | Package unit tests |

---

## Naming Conventions

| Item | Convention |
|------|------------|
| Python packages | `snake_case` |
| TypeScript modules | `camelCase` files, `PascalCase` components |
| API routes | `kebab-case` URLs, `/v1/` prefix |
| Env vars | `SCREAMING_SNAKE_CASE`, prefixed `AI_PLATFORM_` |
| DB tables | `snake_case`, plural nouns |

---

## Import Rules

1. `apps/*` may import from `packages/*`, not from `services/*` internals.
2. `services/*` may import from `packages/*`, not from other services' `src` directly — use HTTP/gRPC.
3. `training/*` may import from `packages/protocol` and `packages/shared`.
4. Circular imports forbidden — extract shared code to `packages/`.

---

## Git Ignore Highlights

- `training/data/raw/**` (large datasets)
- `models/**/*.bin`, `models/**/*.safetensors`
- `.env`, `node_modules/`, `__pycache__/`, `.venv/`
- `dist/`, `build/`, `.electron/`

---

*Last updated: Phase 1 — Model Abstraction*
