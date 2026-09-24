"""Supervised fine-tuning trainer."""

from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import numpy as np

from training.core.checkpoint import (
    copy_config_snapshot,
    prepare_output_dir,
    write_training_metadata,
)
from training.core.config import (
    TrainingConfig,
    TrainingParams,
    load_training_config,
    resolve_repo_path,
)
from training.core.errors import TrainingConfigError, TrainingDependencyError
from training.core.experiment import finalize_experiment, save_experiment_metadata, start_experiment
from training.core.hardware import detect_training_hardware, resolve_training_precision
from training.core.registry import register_trained_model
from training.core.tokenizer import TokenizerAdapter
from training.datasets.manifest import load_manifest
from training.datasets.pipeline import ProcessedDataset, load_split_records, preprocess_dataset
from training.datasets.records import ParsedRecord
from training.datasets.validation import validate_manifest_and_dataset


def _require_training_deps() -> None:
    try:
        import torch  # noqa: F401
        import transformers  # noqa: F401
    except ImportError as exc:
        raise TrainingDependencyError(
            "Training dependencies missing. Install with: pip install -e \"training[train]\""
        ) from exc


def _resolve_warmup_steps(train_dataset_size: int, training: TrainingParams) -> int:
    if training.warmup_ratio <= 0:
        return 0
    steps_per_epoch = max(
        1,
        train_dataset_size
        // (training.per_device_train_batch_size * training.gradient_accumulation_steps),
    )
    total_steps = steps_per_epoch * training.num_epochs
    return int(total_steps * training.warmup_ratio)


def _set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch

        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass


def format_record(record: ParsedRecord, config: TrainingConfig) -> str:
    template = config.prompt_template
    parts: list[str] = []
    if record.instruction.strip():
        parts.append(template.instruction.format(instruction=record.instruction))
    if record.input_text.strip():
        parts.append(template.input.format(input=record.input_text))
    parts.append(template.response.format(output=record.output))
    return "\n\n".join(parts)


def _validate_lora_targets(model, target_modules: list[str]) -> None:
    available = {name for name, _ in model.named_modules()}
    missing = [module for module in target_modules if module not in available]
    if missing:
        raise TrainingConfigError(
            "LoRA target_modules not found in model: " + ", ".join(missing)
        )


def _build_model(config: TrainingConfig, hardware, precision: str):
    import torch
    from transformers import AutoModelForCausalLM

    torch_dtype = {
        "fp32": torch.float32,
        "fp16": torch.float16,
        "bf16": torch.bfloat16,
    }[precision]

    model_kwargs: dict[str, Any] = {
        "trust_remote_code": config.model.trust_remote_code,
        "torch_dtype": torch_dtype,
    }

    if config.lora.enabled and config.lora.quantization != "none":
        try:
            from transformers import BitsAndBytesConfig
        except ImportError as exc:
            raise TrainingDependencyError(
                "QLoRA requires bitsandbytes. Install training[qlora]."
            ) from exc
        if config.lora.quantization == "4bit":
            model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
        elif config.lora.quantization == "8bit":
            model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)

    model = AutoModelForCausalLM.from_pretrained(config.model.base_model_id, **model_kwargs)

    if config.lora.enabled:
        if not config.lora.target_modules:
            raise TrainingConfigError("LoRA enabled but target_modules is empty")
        _validate_lora_targets(model, config.lora.target_modules)
        try:
            from peft import LoraConfig, get_peft_model
        except ImportError as exc:
            raise TrainingDependencyError("LoRA requires peft. Install training[train].") from exc
        lora_config = LoraConfig(
            r=config.lora.rank,
            lora_alpha=config.lora.alpha,
            lora_dropout=config.lora.dropout,
            target_modules=config.lora.target_modules,
            task_type="CAUSAL_LM",
        )
        model = get_peft_model(model, lora_config)

    if config.training.gradient_checkpointing:
        model.gradient_checkpointing_enable()

    return model


def _records_to_dataset(records: list[ParsedRecord], config: TrainingConfig, tokenizer_adapter):
    from datasets import Dataset

    texts = [format_record(record, config) for record in records]

    def tokenize_batch(batch):
        return tokenizer_adapter.tokenizer(
            batch["text"],
            truncation=True,
            max_length=config.training.max_seq_length,
            padding=False,
        )

    dataset = Dataset.from_dict({"text": texts})
    tokenized = dataset.map(
        tokenize_batch,
        batched=True,
        remove_columns=["text"],
    )

    def add_labels(example):
        example["labels"] = example["input_ids"].copy()
        return example

    return tokenized.map(add_labels)


def run_training(config_path: Path) -> Path:
    _require_training_deps()
    config = load_training_config(config_path)
    _set_seed(config.experiment.seed)

    hardware = detect_training_hardware(config.hardware.device)
    precision = resolve_training_precision(config.hardware.precision, hardware)

    manifest_path = resolve_repo_path(config.dataset.manifest)
    manifest = load_manifest(manifest_path)
    validation = validate_manifest_and_dataset(manifest, manifest_path)
    if not validation.passed:
        raise TrainingConfigError("Dataset validation failed:\n" + validation.summary())

    if config.dataset.processed_dir:
        processed_dir = resolve_repo_path(config.dataset.processed_dir)
    else:
        processed_dir = None
    if processed_dir is None and manifest.records.processed_dir:
        processed_dir = Path(manifest.records.processed_dir)
    processed_manifest_path = (
        (processed_dir / "manifest.json") if processed_dir is not None else None
    )

    if (
        config.dataset.reuse_processed
        and processed_manifest_path is not None
        and processed_manifest_path.exists()
    ):
        from training.datasets.manifest import load_manifest as reload_manifest

        processed_manifest = reload_manifest(processed_manifest_path)
        processed = ProcessedDataset(
            manifest=processed_manifest,
            processed_dir=processed_manifest_path.parent,
            train_path=processed_manifest_path.parent / "train.jsonl",
            validation_path=processed_manifest_path.parent / "validation.jsonl",
            test_path=processed_manifest_path.parent / "test.jsonl",
            train_count=processed_manifest.records.train or 0,
            validation_count=processed_manifest.records.validation or 0,
            test_count=processed_manifest.records.test or 0,
            raw_sha256=processed_manifest.provenance.raw_sha256 or "",
            processed_manifest_path=processed_manifest_path,
        )
    else:
        processed = preprocess_dataset(
            manifest,
            manifest_path,
            processed_dir=processed_dir,
        )

    experiment = start_experiment(
        config,
        config_path,
        dataset_name=manifest.dataset.name,
        dataset_version=manifest.dataset.version,
        dataset_hash=processed.raw_sha256,
        hardware=hardware,
    )

    tokenizer_model = config.tokenizer.model_id or config.model.base_model_id
    tokenizer_adapter = TokenizerAdapter(
        model_id=tokenizer_model,
        max_length=config.training.max_seq_length,
        use_fast=config.tokenizer.use_fast,
        trust_remote_code=config.model.trust_remote_code,
    )

    train_records = load_split_records(processed.train_path)
    val_records = load_split_records(processed.validation_path)
    if not train_records:
        raise TrainingConfigError("Training split is empty after preprocessing")

    train_dataset = _records_to_dataset(train_records, config, tokenizer_adapter)
    eval_dataset = (
        _records_to_dataset(val_records, config, tokenizer_adapter) if val_records else None
    )

    output_dir = prepare_output_dir(config)
    copy_config_snapshot(config_path, output_dir)

    from transformers import DataCollatorForLanguageModeling, Trainer, TrainingArguments

    model = _build_model(config, hardware, precision)

    training_args = TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=config.training.num_epochs,
        per_device_train_batch_size=config.training.per_device_train_batch_size,
        per_device_eval_batch_size=config.training.per_device_eval_batch_size,
        gradient_accumulation_steps=config.training.gradient_accumulation_steps,
        learning_rate=config.training.learning_rate,
        warmup_steps=_resolve_warmup_steps(len(train_dataset), config.training),
        weight_decay=config.training.weight_decay,
        logging_steps=config.training.logging_steps,
        save_strategy=config.training.save_strategy,
        eval_strategy=config.training.eval_strategy if eval_dataset is not None else "no",
        save_steps=config.training.save_steps,
        eval_steps=config.training.eval_steps,
        save_total_limit=config.output.save_total_limit,
        report_to=["wandb"] if config.wandb.enabled else [],
        run_name=config.wandb.run_name or config.experiment.name,
        seed=config.experiment.seed,
        fp16=precision == "fp16",
        bf16=precision == "bf16",
        use_cpu=hardware.device_type != "cuda",
    )

    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer_adapter.tokenizer,
        mlm=False,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        data_collator=data_collator,
    )

    train_result = trainer.train()
    eval_metrics: dict[str, Any] = {}
    if eval_dataset is not None:
        eval_metrics = trainer.evaluate()

    final_dir = output_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final_dir))
    tokenizer_adapter.tokenizer.save_pretrained(str(final_dir))

    training_metrics = {
        "train_loss": train_result.training_loss,
        "train_runtime_sec": train_result.metrics.get("train_runtime"),
        "train_samples": len(train_records),
        "token_count_estimate": sum(
            tokenizer_adapter.count_tokens(format_record(record, config))
            for record in train_records
        ),
    }
    validation_metrics = {
        "eval_loss": eval_metrics.get("eval_loss"),
        "eval_samples": len(val_records),
    }

    experiment = finalize_experiment(
        experiment,
        checkpoint_path=final_dir,
        training_metrics=training_metrics,
        validation_metrics=validation_metrics,
    )
    save_experiment_metadata(experiment, output_dir)
    write_training_metadata(
        output_dir,
        config=config,
        experiment=experiment,
        dataset_manifest_path=processed.processed_manifest_path,
        dataset_hash=processed.raw_sha256,
        dataset_id=config.dataset.dataset_id or manifest.dataset.name,
        dataset_version=config.dataset.dataset_version or manifest.dataset.version,
        processing_config_hash=processed.manifest.provenance.processing_config_hash,
    )

    if config.registry.enabled:
        register_trained_model(
            config,
            experiment,
            checkpoint_path=str(final_dir),
            context_length=config.training.max_seq_length,
        )

    return final_dir
