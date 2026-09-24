# AI Platform

A proprietary AI development platform for software engineering — code generation, repository reasoning, autonomous agents, UI generation, and multimodal coding assistance.

> **Long-term goal:** Own model weights and full training/evaluation stack.  
> **Near-term:** Open-source base models behind a replaceable `ModelProvider` abstraction.

---

## Features (Roadmap)

| Capability | Phase |
|------------|-------|
| Replaceable model providers | 1 ✅ |
| Code model fine-tuning | 2–3 |
| Repository indexing & search | 4 |
| Autonomous coding agent | 5–6 |
| UI generation (React/Tailwind) | 7 |
| Screenshot-to-code | 8 |
| Browser-based UI testing | 9 |
| Multimodal architecture | 10 |
| Evaluation & benchmarks | 12 |
| Desktop IDE (Electron) | 13 |
| Multi-tenant SaaS | 16 |

See [ROADMAP.md](./ROADMAP.md) for the full phased plan.

---

## Platform Structure

```
AI Platform
│
├── 🖥️ Frontend
│   ├── Web App
│   ├── Desktop IDE (Electron)
│   └── Admin Panel
│
├── ⚙️ Backend
│   ├── API Gateway
│   ├── AI API
│   ├── Agent Service
│   ├── Code Indexer
│   ├── Browser Agent
│   └── Training API
│
├── 🤖 AI / Model
│   ├── ModelProvider abstraction
│   ├── DevelopmentMockProvider
│   ├── LocalModelProvider
│   ├── ProprietaryModelProvider (placeholder)
│   ├── SFT (planned)
│   ├── Agent Training (planned)
│   ├── UI Training (planned)
│   └── Vision/Multimodal (planned)
│
└── 🗄️ Infrastructure
    ├── MySQL
    ├── Redis
    ├── Vector DB (planned)
    └── Object Storage (planned)
```

---

## Architecture

```
Desktop / Web / Admin  →  API Gateway  →  AI API · Agent · Indexer · Browser Agent
                                              ↓
                                    Model Provider Layer (mock / local / proprietary)
                                              ↓
                              MySQL · Redis · Vector DB · GPU Workers
```

Full details: [ARCHITECTURE.md](./ARCHITECTURE.md)

---

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+ (for web test console and workspace scripts)
- Docker & Docker Compose (**optional** — only required for MySQL/Redis or local HF stack)
- (Optional) NVIDIA GPU + CUDA for `LocalModelProvider`

**Minimal dev (no Docker):** set `AI_PLATFORM_MODEL_PROVIDER=development_mock` and run the AI API directly.

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env with your settings
```

### 2. Start infrastructure

```bash
docker compose up -d mysql redis
```

### 3. Python environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -e "packages/protocol[dev]" -e "packages/shared[dev]" -e "services/ai-api[dev]"
```

### 4. Node environment

```bash
npm install
```

### 5. Run tests

```bash
# All tests via Makefile
make test

# Or individually
pytest
npm run test
```

### 6. Start AI API (development)

```bash
make dev-ai-api
# Health: http://localhost:8000/health
```

### 7. Start Test UI (browser console)

```bash
npm install
npm run dev:web
# Open: http://localhost:5173
```

See [apps/web/README.md](./apps/web/README.md) for details.

---

## Project Structure

```
apps/          # desktop, web, admin
services/      # ai-api, agent, code-indexer, browser-agent, training-api
packages/      # protocol, shared, ui
training/      # SFT, evaluation, preprocess
models/        # configs, checkpoint metadata
infra/         # Docker, k8s
docs/          # API, schema, environment
```

Details: [PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)

---

## Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](./ARCHITECTURE.md) | System design |
| [ROADMAP.md](./ROADMAP.md) | Phased delivery |
| [DEVELOPMENT_RULES.md](./DEVELOPMENT_RULES.md) | Engineering standards |
| [docs/API.md](./docs/API.md) | REST/WebSocket API |
| [docs/DATABASE_SCHEMA.md](./docs/DATABASE_SCHEMA.md) | MySQL schema |
| [docs/ENVIRONMENT.md](./docs/ENVIRONMENT.md) | Configuration |
| [docs/MODEL_PROVIDER.md](./docs/MODEL_PROVIDER.md) | Model provider architecture |
| [docs/LOCAL_MODEL_SETUP.md](./docs/LOCAL_MODEL_SETUP.md) | Local HF model setup |

---

## Development Rules (Summary)

- No fake AI or benchmark scores in production paths
- Model access only through `ModelProvider` interfaces
- Sandboxed agent tools with approval for dangerous commands
- Licensed datasets only; governed continuous learning
- Tests and docs required for major features

Full rules: [DEVELOPMENT_RULES.md](./DEVELOPMENT_RULES.md)

---

## Current Status

**Phase 1 — Model Abstraction** ✅  
**Next: Phase 2 — Coding Model Pipeline**

---

## License

Proprietary — all rights reserved. Third-party open-source components retain their respective licenses.
