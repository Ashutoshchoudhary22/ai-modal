"""Multimodal supervised fine-tuning trainer."""

from __future__ import annotations

import json
import math
import random
import shutil
from pathlib import Path
from typing import Any

import numpy as np

from training.multimodal.checkpoint import (
    apply_checkpoint_retention,
    load_checkpoint_metadata,
    restore_training_state,
    save_checkpoint,
    validate_resume_compatibility,
)
from training.multimodal.collator import MultimodalDataCollator
from training.multimodal.config import MultimodalTrainingConfig, load_multimodal_config
from training.multimodal.errors import MultimodalTrainingError, MultimodalTrainingErrorCode
from training.multimodal.experiment import (
    save_experiment,
    start_experiment,
    transition_status,
    write_reproducibility_manifest,
)
from training.multimodal.metrics import MetricsTracker, TrainingMetrics
from training.multimodal.model import build_model
from training.multimodal.peft import apply_lora
from training.multimodal.processor import MultimodalTrainingProcessor, load_dataset_records
from training.multimodal.validation import fingerprint_dataset, validate_jsonl_dataset


def _require_torch():
    try:
        import torch
    except ImportError as exc:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.MODEL_UNAVAILABLE,
            "PyTorch is required for multimodal training. Install training optional deps.",
        ) from exc
    return torch


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch = _require_torch()
    torch.manual_seed(seed)


def _resolve_device(config: MultimodalTrainingConfig):
    torch = _require_torch()
    device_name = config.hardware.device
    if device_name == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    if device_name.startswith("cuda") and not torch.cuda.is_available():
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.DEVICE_UNAVAILABLE,
            "CUDA requested but unavailable",
        )
    return torch.device(device_name)


def _build_optimizer(model, config: MultimodalTrainingConfig):
    torch = _require_torch()
    params = [p for p in model.parameters() if p.requires_grad]
    if config.training.optimizer == "sgd":
        return torch.optim.SGD(
            params,
            lr=config.training.learning_rate,
            weight_decay=config.training.weight_decay,
        )
    return torch.optim.AdamW(
        params,
        lr=config.training.learning_rate,
        weight_decay=config.training.weight_decay,
    )


def _build_scheduler(optimizer, config: MultimodalTrainingConfig, total_steps: int):
    torch = _require_torch()

    warmup_steps = config.training.warmup_steps
    if warmup_steps == 0 and config.training.warmup_ratio > 0:
        warmup_steps = int(total_steps * config.training.warmup_ratio)

    def lr_lambda(step: int) -> float:
        if step < warmup_steps:
            return float(step) / float(max(1, warmup_steps))
        progress = (step - warmup_steps) / float(max(1, total_steps - warmup_steps))
        progress = min(max(progress, 0.0), 1.0)
        if config.training.scheduler == "constant":
            return 1.0
        if config.training.scheduler == "cosine":
            return 0.5 * (1.0 + math.cos(math.pi * progress))
        return 1.0 - progress

    return torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)


def build_training_plan(
    config: MultimodalTrainingConfig,
    *,
    train_count: int,
    val_count: int,
    image_count: int,
    parameter_report: dict[str, Any],
    device: str,
    total_steps: int,
) -> str:
    effective_batch = (
        config.training.per_device_train_batch_size * config.training.gradient_accumulation_steps
    )
    return (
        "Training Plan\n"
        f"Dataset:\n"
        f"  Records: {train_count + val_count}\n"
        f"  Images: {image_count}\n"
        f"  Train: {train_count}\n"
        f"  Validation: {val_count}\n"
        f"\nModel:\n"
        f"  Parameters: {parameter_report['total_parameters']}\n"
        f"  Trainable: {parameter_report['trainable_parameters']}\n"
        f"\nHardware:\n"
        f"  Device: {device}\n"
        f"  Dtype: {config.hardware.dtype}\n"
        f"\nTraining:\n"
        f"  Epochs: {config.training.num_epochs}\n"
        f"  Steps: {total_steps}\n"
        f"  Effective batch: {effective_batch}\n"
        f"  Learning rate: {config.training.learning_rate}\n"
    )


def _evaluate(
    model,
    collator: MultimodalDataCollator,
    examples,
    device,
) -> float:
    torch = _require_torch()
    if not examples:
        return 0.0
    model.eval()
    losses: list[float] = []
    batch_size = 1
    with torch.no_grad():
        for start in range(0, len(examples), batch_size):
            batch_examples = examples[start : start + batch_size]
            batch = collator(batch_examples)
            outputs = model(
                input_ids=batch.input_ids.to(device),
                attention_mask=batch.attention_mask.to(device),
                pixel_values=batch.pixel_values.to(device),
                labels=batch.labels.to(device),
            )
            if "loss" in outputs:
                losses.append(float(outputs["loss"].item()))
    model.train()
    return float(sum(losses) / len(losses)) if losses else 0.0


def run_multimodal_training(
    config_path: Path,
    *,
    dry_run: bool = False,
    resume_from_checkpoint: Path | None = None,
    cancelled: callable[[], bool] | None = None,
) -> Path:
    config = load_multimodal_config(config_path)
    set_seed(config.experiment.seed)
    device = _resolve_device(config)
    output_dir = Path(config.output.dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(config_path, output_dir / "training_config.yaml")

    dataset_root, _ = load_dataset_records(config)
    dataset_id = Path(config.dataset.path).name
    dataset_version = "1.0.0"
    records, quality_report = validate_jsonl_dataset(
        dataset_root if dataset_root.is_dir() else Path(config.dataset.path).parent,
        dataset_id=dataset_id,
        version=dataset_version,
    )

    if config.resources.max_dataset_records and len(records) > config.resources.max_dataset_records:
        raise MultimodalTrainingError(
            MultimodalTrainingErrorCode.TRAINING_CONFIG_INVALID,
            "Dataset exceeds max_dataset_records resource limit",
        )

    split_index = max(1, int(len(records) * 0.75))
    train_records = records[:split_index]
    val_records = records[split_index:] or records[:1]

    processor = MultimodalTrainingProcessor(
        config, dataset_root if dataset_root.is_dir() else dataset_root.parent
    )
    train_examples = processor.process_records(train_records)
    val_examples = processor.process_records(val_records)

    dataset_fingerprint = fingerprint_dataset(records, config.processor.model_dump(mode="json"))
    experiment = start_experiment(
        config,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
        dataset_fingerprint=dataset_fingerprint,
        device=str(device),
    )
    experiment.status = transition_status(experiment.status, "validating")
    save_experiment(output_dir, experiment)

    model = build_model(config.model, processor.tokenizer, config.processor.image.image_size)
    if config.peft.enabled:
        apply_lora(model, config.peft)

    parameter_report = model.trainable_parameters()
    collator = MultimodalDataCollator(processor.tokenizer, config)

    steps_per_epoch = max(
        1,
        math.ceil(len(train_examples) / config.training.per_device_train_batch_size),
    )
    total_steps = config.training.max_steps or (steps_per_epoch * config.training.num_epochs)
    if config.resources.max_training_steps:
        total_steps = min(total_steps, config.resources.max_training_steps)

    plan = build_training_plan(
        config,
        train_count=len(train_records),
        val_count=len(val_records),
        image_count=quality_report.image_count,
        parameter_report={
            "total_parameters": parameter_report.total_parameters,
            "trainable_parameters": parameter_report.trainable_parameters,
        },
        device=str(device),
        total_steps=total_steps,
    )
    (output_dir / "training_plan.txt").write_text(plan, encoding="utf-8")
    print(plan)

    if dry_run:
        print("Dry run complete — configuration, dataset, and model validated.")
        return output_dir

    torch = _require_torch()
    model.to(device)
    model.train()
    optimizer = _build_optimizer(model, config)
    scheduler = _build_scheduler(optimizer, config, total_steps)
    metrics_tracker = MetricsTracker()

    start_step = 0
    start_epoch = 0
    best_validation_loss: float | None = None
    if resume_from_checkpoint is not None:
        metadata = load_checkpoint_metadata(resume_from_checkpoint)
        validate_resume_compatibility(metadata, config, dataset_fingerprint)
        restored = restore_training_state(
            resume_from_checkpoint,
            model=model,
            optimizer=optimizer,
            scheduler=scheduler,
        )
        processor.tokenizer = processor.tokenizer.from_dict(restored.tokenizer_vocab)
        start_step = restored.step
        start_epoch = restored.epoch
        best_validation_loss = restored.best_validation_loss

    experiment.status = transition_status(experiment.status, "preparing")
    experiment.status = transition_status(experiment.status, "running")
    save_experiment(output_dir, experiment)
    write_reproducibility_manifest(
        output_dir, experiment, config, dataset_fingerprint=dataset_fingerprint
    )

    global_step = start_step
    accumulation_loss = 0.0
    optimizer.zero_grad()
    epoch = start_epoch

    for epoch in range(start_epoch, config.training.num_epochs):
        for batch_start in range(
            0, len(train_examples), config.training.per_device_train_batch_size
        ):
            if cancelled and cancelled():
                experiment.status = transition_status(experiment.status, "cancelled")
                save_experiment(output_dir, experiment)
                raise MultimodalTrainingError(
                    MultimodalTrainingErrorCode.TRAINING_CANCELLED,
                    "Training run was cancelled",
                )
            if global_step >= total_steps:
                break

            batch_examples = train_examples[
                batch_start : batch_start + config.training.per_device_train_batch_size
            ]
            batch = collator(batch_examples)
            outputs = model(
                input_ids=batch.input_ids.to(device),
                attention_mask=batch.attention_mask.to(device),
                pixel_values=batch.pixel_values.to(device),
                labels=batch.labels.to(device),
            )
            loss = outputs["loss"] / config.training.gradient_accumulation_steps
            loss.backward()
            accumulation_loss += float(outputs["loss"].item())

            if (global_step + 1) % config.training.gradient_accumulation_steps == 0:
                grad_norm = torch.nn.utils.clip_grad_norm_(
                    model.parameters(),
                    config.training.max_grad_norm,
                )
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()

                if (global_step + 1) % config.training.logging_steps == 0:
                    lr = scheduler.get_last_lr()[0]
                    metrics_tracker.record(
                        TrainingMetrics(
                            step=global_step + 1,
                            epoch=epoch + 1,
                            loss=accumulation_loss,
                            learning_rate=lr,
                            grad_norm=float(grad_norm),
                            image_count=sum(
                                len(example.image_metadata) for example in batch_examples
                            ),
                        )
                    )
                    print(
                        f"Epoch {epoch + 1}/{config.training.num_epochs} "
                        f"step {global_step + 1} loss={accumulation_loss:.4f}"
                    )
                    accumulation_loss = 0.0

            global_step += 1

            if (
                config.evaluation.enabled
                and val_examples
                and global_step % config.training.eval_steps == 0
            ):
                experiment.status = transition_status(experiment.status, "evaluating")
                validation_loss = _evaluate(model, collator, val_examples, device)
                experiment.status = transition_status(experiment.status, "running")
                print(f"validation_loss={validation_loss:.4f}")
                metrics_tracker.record(
                    TrainingMetrics(
                        step=global_step,
                        epoch=epoch + 1,
                        validation_loss=validation_loss,
                    )
                )
                if best_validation_loss is None or validation_loss < best_validation_loss:
                    best_validation_loss = validation_loss

            if global_step % config.training.save_steps == 0:
                experiment.status = transition_status(experiment.status, "saving")
                checkpoint_name = f"checkpoint-{global_step:06d}"
                checkpoint_dir = save_checkpoint(
                    output_dir,
                    step=global_step,
                    epoch=epoch + 1,
                    model=model,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    config=config,
                    dataset_fingerprint=dataset_fingerprint,
                    tokenizer_vocab=processor.tokenizer.to_dict(),
                    best_validation_loss=best_validation_loss,
                    name=checkpoint_name,
                )
                apply_checkpoint_retention(
                    output_dir,
                    config.output.save_total_limit,
                    checkpoint_dir,
                )
                experiment.checkpoint_path = str(checkpoint_dir)
                experiment.status = transition_status(experiment.status, "running")

        if global_step >= total_steps:
            break

    final_dir = save_checkpoint(
        output_dir,
        step=global_step,
        epoch=min(config.training.num_epochs, epoch + 1),
        model=model,
        optimizer=optimizer,
        scheduler=scheduler,
        config=config,
        dataset_fingerprint=dataset_fingerprint,
        tokenizer_vocab=processor.tokenizer.to_dict(),
        best_validation_loss=best_validation_loss,
        name="final",
    )
    experiment.metrics_summary = metrics_tracker.summary()
    experiment.status = transition_status(experiment.status, "completed")
    experiment.checkpoint_path = str(final_dir)
    save_experiment(output_dir, experiment)
    (output_dir / "metrics.json").write_text(
        json.dumps([item.to_dict() for item in metrics_tracker.history], indent=2),
        encoding="utf-8",
    )
    print(f"Status: completed\nCheckpoint: {final_dir.name}")
    return final_dir
