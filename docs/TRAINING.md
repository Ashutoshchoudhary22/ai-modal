# Phase 2 — Coding Model Pipeline

This document describes the **IMPLEMENTED** supervised fine-tuning (SFT) training pipeline.

## Overview

```
Dataset (JSONL)
  ↓ manifest
Validation CLI
  ↓
Cleaning → Deduplication → Split
  ↓
Tokenizer
  ↓
Training (Transformers Trainer)
  ↓
Checkpoint + experiment metadata
  ↓
Optional MySQL model registry
  ↓
LocalModelProvider inference
```

## Dataset format (JSONL)

Instruction format:

```json
{"id": "example-1", "instruction": "Write a function", "input": "", "output": "def f(): pass"}
```

Conversational format:

```json
{"id": "example-2", "messages": [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]}
```

## Manifest format

Manifests live under `training/data/manifests/` (or project-specific paths).

Required metadata:

- dataset name, version, description
- source + **license**
- raw JSONL path
- quality rules
- preprocessing configuration
- split configuration
- provenance timestamps and hashes (filled during preprocessing)

Example: `training/data/manifests/smoke_sft.json`

## Validation CLI

```bash
python -m training.datasets.validate \
  --input training/tests/fixtures/smoke_sft.jsonl \
  --manifest training/data/manifests/smoke_sft.json
```

Reports valid/invalid/duplicate records and exits non-zero on failure.

Optional token statistics:

```bash
python -m training.datasets.validate \
  --input training/tests/fixtures/smoke_sft.jsonl \
  --manifest training/data/manifests/smoke_sft.json \
  --tokenizer-model hf-internal-testing/tiny-random-gpt2
```

## Training

Install training dependencies:

```bash
pip install -e "training[train]"
```

Run SFT:

```bash
python training/sft/train.py --config models/configs/code_sft.yaml
```

### Smoke test (SMOKE TEST ONLY)

Uses synthetic dataset + tiny HF test model on CPU:

```bash
python training/sft/train.py --config models/configs/smoke_test.yaml
```

This verifies the full pipeline but is **not** a production coding model.

## Configuration

Training configs live in `models/configs/`.

Key sections:

| Section | Purpose |
|---------|---------|
| `experiment` | name, seed, smoke_test flag |
| `model` | base model ID, trust_remote_code |
| `tokenizer` | tokenizer model ID |
| `dataset` | manifest path |
| `output` | checkpoint directory (gitignored) |
| `training` | batch size, LR, epochs, max_seq_length |
| `lora` | optional LoRA/QLoRA settings |
| `hardware` | device + precision (`auto`, `cpu`, `cuda`, `fp32`, ...) |
| `registry` | optional MySQL registration |

## LoRA / QLoRA

Configure under `lora:` in the training YAML.

- `target_modules` must match the loaded architecture
- QLoRA requires optional `training[qlora]` (`bitsandbytes`)

## Checkpoints

Written to `models/finetuned/<run>/` by default:

- `final/` model + tokenizer
- `experiment.json`
- `training_metadata.json`
- `training_config.yaml` snapshot

Large artifacts are gitignored.

## Model registry

When `registry.enabled: true`, trained models register in MySQL `provider_model_registry`.

Registration **fails clearly** if the database is unavailable.

## LocalModelProvider integration

Point the AI API to a trained checkpoint:

```env
AI_PLATFORM_MODEL_PROVIDER=local
AI_PLATFORM_MODEL_PATH=./models/finetuned/smoke-test/final
```

Inference continues through `ModelProvider` → `LocalModelProvider`.

## Hardware

- `device: auto` selects CUDA when available, otherwise CPU
- `precision: auto` selects bf16/fp16 on GPU, fp32 on CPU
- Incompatible precision/device combinations fail with a clear error

## Status

| Component | Status |
|-----------|--------|
| Manifest + validation | IMPLEMENTED |
| Cleaning / dedup / split | IMPLEMENTED |
| Config-driven SFT training | IMPLEMENTED |
| LoRA (optional deps) | IMPLEMENTED |
| QLoRA | IMPLEMENTED (optional bitsandbytes) |
| Experiment metadata | IMPLEMENTED |
| Model registry hook | IMPLEMENTED |
| Coding benchmarks | PLANNED (Phase 12) |

*Last updated: Phase 2 — Coding Model Pipeline*
