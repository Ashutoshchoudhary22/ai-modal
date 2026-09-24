# AI Platform — System Architecture

> Proprietary AI development platform for software engineering, code intelligence, UI generation, and autonomous coding agents.

## 1. Vision

Build a **replaceable-model AI platform** that eventually runs on **our own model weights**, while using open-source base models during development. The system is not a thin wrapper around a third-party API — it is a full stack: training, evaluation, inference, agents, IDE, and SaaS infrastructure.

### Design Principles

| Principle | Description |
|-----------|-------------|
| **Model replaceability** | All product code depends on `ModelProvider` interfaces, not specific weights |
| **Evidence-based claims** | Benchmark results required before claiming model improvements |
| **Security by default** | Sandboxed tools, command approval, audit logs |
| **Modular monorepo** | Independent services with shared protocols |
| **Data governance** | Licensed data only; explicit consent for user feedback loops |
| **Observable everything** | Metrics, traces, and versioned artifacts |

---

## Implementation Status (as of Phase 5)

| Area | Status | Location |
|------|--------|----------|
| Model provider abstraction | **IMPLEMENTED** | `packages/protocol`, `services/ai-api/providers/` |
| AI inference API | **IMPLEMENTED** | `services/ai-api` (`/health`, `/ready`, `/v1/chat`, streaming, embeddings) |
| MySQL model registry | **IMPLEMENTED** | `packages/shared/db`, `provider_model_registry` table |
| Centralized config | **IMPLEMENTED** | `packages/shared/config.py`, `.env.example` |
| Request ID middleware | **IMPLEMENTED** | `services/ai-api/middleware/request_id.py` |
| Telemetry context (lightweight) | **IMPLEMENTED** | `packages/shared/telemetry/` |
| Tool protocols + types | **IMPLEMENTED** | `packages/protocol/tools` |
| Repository intelligence | **IMPLEMENTED** | `services/code-indexer`, `docs/REPOSITORY_INTELLIGENCE.md` |
| Coding agent tools | **IMPLEMENTED** | `services/agent`, `docs/CODING_AGENT_TOOLS.md` |
| Agent loop (bounded orchestration) | **IMPLEMENTED** | `services/agent/loop`, `docs/AGENT_LOOP.md` |
| UI generation | **IMPLEMENTED** | `services/agent/ui`, `docs/UI_GENERATION.md` |
| Training pipeline (SFT) | **IMPLEMENTED** | `training/`, `docs/TRAINING.md` |
| Vector DB / object storage | **FUTURE** | Not implemented; Redis/MySQL only in dev stack |
| API gateway / auth / multi-tenant | **FUTURE** | Phase 15–16 |
| Desktop IDE | **FUTURE** | Phase 13 |

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                       │
│  │ Desktop IDE  │  │  Web App     │  │ Admin Portal │                       │
│  │ (Electron)   │  │  (React)     │  │  (React)     │                       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                       │
└─────────┼─────────────────┼─────────────────┼───────────────────────────────┘
          │                 │                 │
          └─────────────────┼─────────────────┘
                            │ HTTPS / WSS
┌───────────────────────────▼─────────────────────────────────────────────────┐
│                         API GATEWAY / AUTH                                     │
│              JWT · API Keys · Rate Limiting · Tenant Routing                 │
└───────────────────────────┬─────────────────────────────────────────────────┘
                            │
     ┌──────────────────────┼──────────────────────┐
     │                      │                      │
┌────▼─────┐  ┌─────────────▼──────────┐  ┌────────▼────────┐
│ AI API   │  │ Agent Service          │  │ Training API    │
│ Inference│  │ Planner · Tools · Loop │  │ Jobs · Models   │
└────┬─────┘  └─────────────┬──────────┘  └────────┬────────┘
     │                      │                      │
     │         ┌────────────┼────────────┐         │
     │         │            │            │         │
┌────▼─────┐ ┌─▼──────────┐ ┌▼─────────┐ ┌▼──────────────┐
│ Model    │ │ Code       │ │ Browser  │ │ Evaluation    │
│ Router   │ │ Indexer    │ │ Agent    │ │ Service       │
└────┬─────┘ └─┬──────────┘ └┬─────────┘ └───────────────┘
     │         │             │
┌────▼─────────▼─────────────▼────────────────────────────────────────────────┐
│                        MODEL PROVIDER LAYER                                    │
│  ┌─────────────────┐  ┌──────────────────┐  ┌─────────────────────────┐   │
│  │ LocalModel      │  │ DevelopmentMock  │  │ Future: ProprietaryModel│   │
│  │ (vLLM/HF)       │  │ Provider         │  │ Provider                │   │
│  └─────────────────┘  └──────────────────┘  └─────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────────────┐
│                        DATA & INFRASTRUCTURE                                 │
│  MySQL · Redis · Vector DB · Object Storage · GPU Workers · CI/CD      │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Core Components

### A. Model Provider Abstraction (Phase 1) ✅

Implemented in `packages/protocol` and `services/ai-api/providers/`:

- `ModelProvider` protocol
- `DevelopmentMockProvider` (dev/test/CI only)
- `LocalModelProvider` (Hugging Face Transformers, lazy load, streaming)
- `ProprietaryModelProvider` (placeholder)
- Provider factory + MySQL model registry
- AI API endpoints: `/ready`, `/v1/chat`, `/v1/chat/stream`, `/v1/embeddings`

```python
# Conceptual interface — packages/protocol
class ModelProvider(Protocol):
    async def generate(self, request: GenerateRequest) -> GenerateResponse: ...
    async def stream(self, request: GenerateRequest) -> AsyncIterator[StreamChunk]: ...
    async def generate_structured(self, request: StructuredRequest) -> StructuredResponse: ...
    async def embed(self, request: EmbedRequest) -> EmbedResponse: ...
    async def vision(self, request: VisionRequest) -> VisionResponse: ...
    def count_tokens(self, text: str, model_id: str | None = None) -> int: ...
```

**Implementations:**
- `DevelopmentMockProvider` — deterministic responses for CI/dev without GPU
- `LocalModelProvider` — Hugging Face Transformers / vLLM for open-source weights
- `ProprietaryModelProvider` — future internal weights (same interface)

### B. Model Router (Phase 17)

Routes requests by task type, latency budget, context size, and modality:

| Task | Route |
|------|-------|
| Inline completion | Fast coding model |
| Multi-file refactor | Strong coding model + repo context |
| Screenshot-to-code | Multimodal vision model |
| Simple Q&A | Small/fast model |

### C. Repository Context Engine (Phase 4)

```
Workspace Scan → Language Detection → Tree-sitter Parse → Symbol Graph
     → Dependency Graph → Embeddings → Vector + Lexical Index → Retrieval
```

Retrieval combines:
- Semantic search (embeddings)
- Lexical search (ripgrep-style)
- Symbol/reference graph traversal
- File relationship heuristics (imports, co-change)

### D. Coding Agent (Phases 5–6)

**Agent loop:**

```
User Request → Planner → Context Retrieval → Model → Tool Selection
    → Tool Execution → Observation → Model → Validation → Correction → Response
```

**Tool categories:**
- Filesystem (read/write/edit/delete/list) — sandboxed to workspace
- Code intelligence (search_code, search_symbol, find_references)
- Terminal (run_terminal, run_tests) — allowlist + approval
- Git (diff, status, log, branch)
- Dev server (start/stop)
- Browser (open_browser, take_screenshot)

Each tool: JSON schema, permissions, timeout, cancellation, structured logging.

### E. Browser / UI Agent (Phases 7–9)

Playwright-based automation for:
- DOM inspection, console/network errors
- Responsive viewport testing
- Screenshot capture for visual evaluation
- Iterative UI correction loop

### F. Training Pipeline (Phases 2–3, 11)

Staged training path (not from scratch unless compute permits):

1. Base model evaluation
2. Code SFT (supervised fine-tuning)
3. Instruction tuning
4. Tool-use training
5. Repository-level tasks
6. UI generation
7. Screenshot-to-code
8. Browser trajectories
9. Preference optimization (DPO/ORPO)
10. Continuous evaluation

**Stack:** PyTorch, Transformers, Datasets, PEFT, TRL, Accelerate, DeepSpeed (optional), vLLM (inference).

### G. Evaluation Framework (Phase 12)

Every model version records:
- `model_version`, `dataset_version`, `config_hash`, `benchmark_results`

Benchmark categories: code generation, bug fix, repo edit, UI/visual, agent task completion.

### H. Multimodal Architecture (Phase 10)

Separate interfaces — not coupled to one vision model:

```
TextEncoder/Decoder ──┐
                      ├── MultimodalFusion → Unified Generate/Vision API
VisionEncoder ────────┘
```

### I. SaaS & Multi-Tenancy (Phase 16)

```
Organization → Team → Workspace → Project → Sessions/Tasks
```

Billing, API keys, usage metering, model version pinning per org.

---

## 4. Service Boundaries

| Service | Responsibility | Tech |
|---------|----------------|------|
| `ai-api` | Inference, embeddings, streaming | FastAPI, Python |
| `agent` | Agent loop, tool orchestration | FastAPI, Python |
| `code-indexer` | Repo scan, index, search | Python, Tree-sitter |
| `browser-agent` | Playwright automation | Python |
| `training-api` | Training job management | FastAPI, Python |
| `web` | User-facing web app | React, TypeScript |
| `desktop` | Electron IDE | Electron, React, Monaco |
| `admin` | Observability, model mgmt | React, TypeScript |

Inter-service communication: REST + WebSockets; shared types in `packages/protocol`.

---

## 5. Data Flow — End-to-End Task

**Example:** *"Build a SaaS dashboard with auth, PostgreSQL, React"*

1. Desktop/web sends task to **Agent Service**
2. **Planner** decomposes into milestones
3. **Code Indexer** retrieves relevant patterns (if existing repo)
4. **Model Router** selects coding + UI models
5. **Agent** creates files via tools, installs deps, runs tests
6. **Browser Agent** starts dev server, opens page, screenshots
7. **Vision evaluation** compares layout; agent iterates
8. **Validation** runs tests + lint
9. Results streamed to client with diffs
10. Optional: successful trajectory → feedback pipeline (governed)

---

## 6. Security Architecture (Phase 15)

| Layer | Control |
|-------|---------|
| Workspace | Path sandbox; deny traversal outside root |
| Shell | Allowlist categories; user approval for destructive ops |
| Secrets | Server-side vault; never embed in client |
| API | JWT + API keys; rate limits per tenant |
| Audit | Immutable action log per session |
| Isolation | Optional container per agent session (future) |

---

## 7. Observability (Phase 18)

**Metrics:** request latency, tokens, model ID, tool calls, retries, GPU util, task completion rate.

**Tracing:** OpenTelemetry-compatible spans across agent steps.

**Admin dashboards:** model versions, benchmark trends, usage/billing.

---

## 8. Continuous Learning (Phase 19)

```
User Task → Success + Optional Feedback → Quality Filter → Eval Gate
    → Dataset Candidate → Training → Benchmark → Deploy if Improved
```

**Not** automatic training on all conversations — explicit governance and opt-in.

---

## 9. Technology Stack Summary

| Layer | Technologies |
|-------|--------------|
| ML | Python 3.12+, PyTorch, HF ecosystem, PEFT, TRL, vLLM, CUDA |
| Backend | FastAPI, Pydantic, MySQL, Redis, WebSockets |
| Frontend | React, TypeScript, Tailwind, Monaco |
| Desktop | Electron |
| Automation | Playwright |
| Code Intel | Tree-sitter, AST, embeddings, vector DB |
| Infra | Docker, Docker Compose, Linux, CI/CD |

---

## 10. Deployment Topology (Development → Production)

**Development:** Docker Compose — MySQL, Redis, mock AI API, agent stub.

**Staging:** GPU node for inference; shared MySQL/Redis.

**Production:** K8s (future) — horizontal API replicas, dedicated GPU inference pool, managed MySQL.

---

## 11. Extension Points

| Component | Replaceable Via |
|-----------|-----------------|
| Base LLM | `ModelProvider` registration |
| Vision model | `VisionEncoder` interface |
| Vector store | `VectorIndex` interface |
| Auth | `AuthProvider` interface |
| Billing | `BillingProvider` interface |

---

## 12. Document Map

| Document | Purpose |
|----------|---------|
| `ROADMAP.md` | Phased delivery plan |
| `PROJECT_STRUCTURE.md` | Monorepo layout |
| `DEVELOPMENT_RULES.md` | Engineering standards |
| `docs/API.md` | REST/WebSocket API specification |
| `docs/DATABASE_SCHEMA.md` | MySQL schema |
| `docs/ENVIRONMENT.md` | Configuration reference |

---

*Last updated: Phase 1 — Model Abstraction*
