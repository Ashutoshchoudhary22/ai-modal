# Multimodal Training Strategy (Phase 11)

Phase 11 adds a reproducible multimodal supervised fine-tuning pipeline on top of the existing Phase 2 training infrastructure and Phase 3 dataset system.

## Architecture

```text
Dataset (JSONL + image refs)
   ↓
Validation / fingerprint / leakage checks
   ↓
MultimodalTrainingProcessor
   ↓
MultimodalDataCollator
   ↓
TinyMultimodalModel (development) or future HF models
   ↓
Loss (masked causal LM)
   ↓
Optimizer / scheduler
   ↓
Checkpoint + experiment metadata
   ↓
Model registry (optional)
```

## Dataset format

Multimodal records extend Phase 3 JSONL with structured message content:

```json
{
  "id": "mm-001",
  "messages": [
    {
      "role": "user",
      "content": [
        {"type": "text", "text": "Describe this interface."},
        {"type": "image", "image": "images/sample-001.png"}
      ]
    },
    {
      "role": "assistant",
      "content": [{"type": "text", "text": "A red dashboard panel."}]
    }
  ],
  "metadata": {"task_type": "screenshot_analysis"}
}
```

Images are referenced relative to the dataset root. Path traversal, absolute paths, and remote URLs are rejected.

## Development dataset

`data/examples/multimodal-mini` contains 8 tiny 16×16 PNG samples for validation, preprocessing, and CPU smoke training.

## Configuration

Example config: `training/configs/multimodal/sft.yaml`

Key sections:

- `dataset` — local dataset path and limits
- `model` — vision encoder, projector, language model, freezing
- `processor` — chat template, image token, image size
- `training` — SFT hyperparameters, gradient accumulation, clipping
- `peft` — optional LoRA
- `resources` — development safety limits

## CLI

Dry run:

```bash
python -m training.multimodal.train --config training/configs/multimodal/sft.yaml --dry-run
```

CPU smoke training:

```bash
python -m training.multimodal.train --config training/configs/multimodal/sft.yaml
```

Inspect samples:

```bash
python -m training.multimodal.inspect --dataset data/examples/multimodal-mini --preview 2
```

Resume:

```bash
python -m training.multimodal.train \
  --config training/configs/multimodal/sft.yaml \
  --resume-from-checkpoint training/output/multimodal-mini-sft/checkpoint-000002
```

## Training outputs

Each run writes:

- `training_plan.txt`
- `experiment.json`
- `reproducibility.json`
- `metrics.json`
- `checkpoint-*/` and `final/`

## API (minimal)

In-process routes in `training/multimodal/api.py`:

- `POST /v1/training/multimodal/runs`
- `GET /v1/training/multimodal/runs/{run_id}`
- `POST /v1/training/multimodal/runs/{run_id}/cancel`

## Security

- Image validation via MIME, extension, size, and dimensions
- Dataset image paths constrained to dataset root
- `trust_remote_code` defaults to `false`
- Resource limits for steps, records, images, and disk space

## Phase 12 boundary

Phase 11 implements training-time validation loss only. Comprehensive multimodal benchmarks and evaluation suites belong to Phase 12.

## Limitations

- No distributed training (DDP/FSDP/DeepSpeed)
- No preference optimization (DPO/RLHF/PPO)
- Development model is a tiny deterministic PyTorch module for CPU smoke runs
- No automatic model/dataset downloads
