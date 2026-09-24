# AI Platform — Delivery Roadmap

Phased implementation plan. Each phase must pass tests and documentation updates before the next begins.

**Legend:** ✅ Complete · 🔄 In Progress · ⬜ Planned

---

## Phase 0 — Project Foundation ✅

**Goal:** Architecture, monorepo scaffold, dev environment, CI baseline.

| Deliverable | Status |
|-------------|--------|
| ARCHITECTURE.md | ✅ |
| ROADMAP.md | ✅ |
| DEVELOPMENT_RULES.md | ✅ |
| PROJECT_STRUCTURE.md | ✅ |
| README.md | ✅ |
| API specification (`docs/API.md`) | ✅ |
| Database schema (`docs/DATABASE_SCHEMA.md`) | ✅ |
| Environment config (`docs/ENVIRONMENT.md`, `.env.example`) | ✅ |
| Docker Compose dev stack | ✅ |
| Python + Node tooling, lint, tests | ✅ |
| Initial CI workflow | ✅ |

**Exit criteria:** `make test` / `npm test` / `pytest` pass; Docker services start; docs reviewed.

---

## Phase 1 — Model Abstraction ✅

**Goal:** Replaceable `ModelProvider` with mock and local implementations.

| Deliverable | Status |
|-------------|--------|
| `ModelProvider` protocol in `packages/protocol` | ✅ |
| `DevelopmentMockProvider` | ✅ |
| `LocalModelProvider` (HF Transformers) | ✅ |
| `ProprietaryModelProvider` placeholder | ✅ |
| Model registry (MySQL) | ✅ |
| Provider factory | ✅ |
| AI API integration (`/ready`, `/v1/chat`, streaming) | ✅ |
| Unit + integration tests | ✅ |
| Documentation (`docs/MODEL_PROVIDER.md`, `docs/LOCAL_MODEL_SETUP.md`) | ✅ |
| Future-compatible agent/tool/indexer protocol stubs | ✅ |

**Exit criteria:** Services call providers only through interface; no hard-coded model logic in agents. ✅

---

## Phase 2 — Coding Model Pipeline ✅

**Goal:** Configurable SFT training for code models.

| Deliverable | Status |
|-------------|--------|
| Tokenizer management | ✅ |
| Dataset loading + validation | ✅ |
| Cleaning, dedup, language detection | ✅ (language metadata; detection PLANNED Phase 3) |
| Train/val/test split | ✅ |
| `training/sft/train.py --config` | ✅ |
| LoRA/QLoRA + full FT configs | ✅ |
| Auto CUDA device detection | ✅ |
| Checkpoint + experiment tracking | ✅ |

**Exit criteria:** Training runs on mock/small dataset; checkpoints saved; config documented. ✅

See [docs/TRAINING.md](./docs/TRAINING.md).

---

## Phase 3 — Dataset System ✅

**Goal:** Versioned, governed dataset pipeline.

| Deliverable | Status |
|-------------|--------|
| Dataset manifest format | ✅ |
| Provenance, hashing, dedup | ✅ |
| License + quality metadata | ✅ |
| Instruction / conversation / completion / preference schemas | ✅ |
| Validation + processing CLI | ✅ |
| MySQL dataset metadata | ✅ |
| Quality reports + leakage checks | ✅ |

**Exit criteria:** Sample datasets validate; train/test separation enforced. ✅

See [docs/DATASETS.md](./docs/DATASETS.md).

---

## Phase 4 — Repository Intelligence ⬜

**Goal:** Index and retrieve relevant code context.

| Deliverable | Status |
|-------------|--------|
| Workspace scanner | ⬜ |
| Tree-sitter multi-language parsing | ⬜ |
| Symbol + import graph | ⬜ |
| Embeddings + vector index | ⬜ |
| Semantic + lexical search API | ⬜ |

**Exit criteria:** "Fix auth bug" retrieves auth-related files in test repo.

---

## Phase 5 — Coding Agent Tools ⬜

**Goal:** Sandboxed tool library with schemas and permissions.

| Deliverable | Status |
|-------------|--------|
| All tools (read/write/terminal/git/browser/…) | ⬜ |
| Permission rules + timeouts | ⬜ |
| Cancellation + structured logging | ⬜ |

**Exit criteria:** Each tool has unit tests; dangerous ops require approval.

---

## Phase 6 — Agent Loop ⬜

**Goal:** Planner → retrieve → act → observe → validate loop.

| Deliverable | Status |
|-------------|--------|
| Planner module | ⬜ |
| Iteration limits + cancellation | ⬜ |
| Reflection + retry | ⬜ |
| WebSocket streaming of steps | ⬜ |

**Exit criteria:** End-to-end task on fixture repo completes within iteration cap.

---

## Phase 7 — UI Generation ⬜

**Goal:** React + TS + Tailwind component generation.

| Deliverable | Status |
|-------------|--------|
| UI prompt templates | ⬜ |
| Component library conventions | ⬜ |
| Accessibility + responsive checks | ⬜ |

---

## Phase 8 — Screenshot-to-Code ⬜

**Goal:** Vision → layout → React iteration loop.

| Deliverable | Status |
|-------------|--------|
| Layout understanding pipeline | ⬜ |
| Visual diff evaluation | ⬜ |
| Iterative correction | ⬜ |

---

## Phase 9 — Browser Agent ⬜

**Goal:** Playwright integration for UI testing.

| Deliverable | Status |
|-------------|--------|
| browser-agent service | ⬜ |
| Console/network inspection | ⬜ |
| Responsive screenshot tests | ⬜ |

---

## Phase 10 — Multimodal Model Architecture ⬜

**Goal:** Decoupled text/vision/fusion interfaces.

| Deliverable | Status |
|-------------|--------|
| `VisionEncoder` protocol | ⬜ |
| `MultimodalFusion` protocol | ⬜ |
| Wiring in ModelProvider | ⬜ |

---

## Phase 11 — Training Strategy ⬜

**Goal:** Staged training configs for all 10 stages.

| Deliverable | Status |
|-------------|--------|
| Stage configs (1–10) | ⬜ |
| Pretraining path (documented, optional) | ⬜ |

---

## Phase 12 — Evaluation Framework ⬜

**Goal:** Benchmarks tied to model versions.

| Deliverable | Status |
|-------------|--------|
| Code benchmarks | ⬜ |
| UI/visual benchmarks | ⬜ |
| Agent benchmarks | ⬜ |
| Results storage + comparison | ⬜ |

---

## Phase 13 — Desktop IDE ⬜

**Goal:** Electron app with Monaco, chat, terminal.

| Deliverable | Status |
|-------------|--------|
| Layout (explorer/editor/chat/terminal) | ⬜ |
| Git, problems, diff panels | ⬜ |
| Agent mode integration | ⬜ |

---

## Phase 14 — Inline Coding ⬜

**Goal:** Low-latency completions and inline edits.

| Deliverable | Status |
|-------------|--------|
| Streaming completions | ⬜ |
| Inline edit/explain/refactor | ⬜ |

---

## Phase 15 — Security Hardening ⬜

**Goal:** Production-grade sandbox and audit.

| Deliverable | Status |
|-------------|--------|
| Command allowlist | ⬜ |
| Secrets vault integration | ⬜ |
| Audit log persistence | ⬜ |

---

## Phase 16 — Multi-Tenant SaaS ⬜

**Goal:** Orgs, billing, API keys, usage.

| Deliverable | Status |
|-------------|--------|
| Auth service | ⬜ |
| Tenant isolation | ⬜ |
| Usage metering | ⬜ |

---

## Phase 17 — Model Router ⬜

**Goal:** Task-aware model selection.

| Deliverable | Status |
|-------------|--------|
| Router rules + config | ⬜ |
| Fallback chains | ⬜ |

---

## Phase 18 — Observability ⬜

**Goal:** Metrics, tracing, admin dashboards.

| Deliverable | Status |
|-------------|--------|
| Prometheus/OpenTelemetry | ⬜ |
| Admin UI charts | ⬜ |

---

## Phase 19 — Continuous Learning ⬜

**Goal:** Governed feedback → training pipeline.

| Deliverable | Status |
|-------------|--------|
| Feedback ingestion | ⬜ |
| Quality gate + eval before train | ⬜ |

---

## Phase 20 — Developer Experience ⬜

**Goal:** Full CI/CD, integration/e2e tests, docs parity.

| Deliverable | Status |
|-------------|--------|
| E2E test suite | ⬜ |
| Release automation | ⬜ |
| Contributor guide | ⬜ |

---

## Milestone Timeline (Indicative)

| Quarter | Focus |
|---------|-------|
| Q1 | Phases 0–3 (foundation, model abstraction, training, datasets) |
| Q2 | Phases 4–6 (repo intel, agent tools, agent loop) |
| Q3 | Phases 7–12 (UI, browser, multimodal, eval) |
| Q4 | Phases 13–20 (IDE, SaaS, observability, continuous learning) |

*Timelines adjust based on team size and GPU availability.*

---

## Current Status

**Active phase:** Phase 3 — Dataset System ✅  
**Next phase:** Phase 4 — Repository Intelligence

---

*Last updated: Phase 0*
