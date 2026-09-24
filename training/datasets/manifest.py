"""Dataset manifest schema."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class DatasetInfo(BaseModel):
    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str = Field(min_length=1)
    language: str = "en"
    format: Literal["jsonl"] = "jsonl"
    task: Literal[
        "code_sft",
        "code_completion",
        "instruction",
        "conversation",
        "preference",
    ] = "code_sft"
    dataset_type: Literal[
        "instruction",
        "conversation",
        "completion",
        "preference",
        "mixed",
    ] = "instruction"
    synthetic: bool = False
    parent_version: str | None = None


class SourceInfo(BaseModel):
    name: str = Field(min_length=1)
    type: Literal["internal", "synthetic", "external", "huggingface"] = "internal"
    url: str | None = None
    license: str = Field(min_length=1)
    license_url: str | None = None


class RecordsInfo(BaseModel):
    raw_path: str = Field(min_length=1)
    processed_dir: str | None = None
    count: int | None = Field(default=None, ge=0)
    train: int | None = Field(default=None, ge=0)
    validation: int | None = Field(default=None, ge=0)
    test: int | None = Field(default=None, ge=0)


class QualityRules(BaseModel):
    min_chars: int = Field(default=1, ge=0)
    max_chars: int = Field(default=50000, ge=1)
    min_output_chars: int = Field(default=1, ge=0)
    require_license: bool = True
    allow_duplicates: bool = False
    reject_empty: bool = True


class DeduplicationConfig(BaseModel):
    exact: bool = True
    normalized: bool = True


class ValidationConfig(BaseModel):
    strict: bool = True
    allow_empty_lines: bool = False


class PreprocessingConfig(BaseModel):
    version: str = "1.0"
    unicode_normalize: Literal["NFC", "NFD", "none"] = "NFC"
    strip_outer_whitespace: bool = True
    remove_empty: bool = True
    max_chars: int | None = Field(default=None, ge=1)
    normalize_newlines: bool = True


class SplitConfig(BaseModel):
    train: float = Field(default=0.9, gt=0, lt=1)
    validation: float = Field(default=0.05, ge=0, lt=1)
    test: float = Field(default=0.05, ge=0, lt=1)
    seed: int = 42

    @model_validator(mode="after")
    def validate_split_sum(self) -> SplitConfig:
        total = self.train + self.validation + self.test
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Split fractions must sum to 1.0, got {total}")
        return self


class TokenizerRef(BaseModel):
    model_id: str | None = None
    use_fast: bool = True


class ProvenanceInfo(BaseModel):
    created_at: str = Field(min_length=1)
    created_by: str = "ai-platform"
    source_reference: str | None = None
    raw_sha256: str | None = None
    normalized_sha256: str | None = None
    processed_sha256: str | None = None
    processing_config_hash: str | None = None
    processing_version: str = "1.0"
    parent_version: str | None = None


class DatasetManifest(BaseModel):
    schema_version: Literal["1.0"] = "1.0"
    dataset: DatasetInfo
    source: SourceInfo
    records: RecordsInfo
    quality: QualityRules = Field(default_factory=QualityRules)
    validation: ValidationConfig = Field(default_factory=ValidationConfig)
    preprocessing: PreprocessingConfig = Field(default_factory=PreprocessingConfig)
    deduplication: DeduplicationConfig = Field(default_factory=DeduplicationConfig)
    split: SplitConfig = Field(default_factory=SplitConfig)
    tokenizer: TokenizerRef | None = None
    provenance: ProvenanceInfo

    @field_validator("source")
    @classmethod
    def validate_license_present(cls, value: SourceInfo) -> SourceInfo:
        if not value.license.strip():
            raise ValueError("source.license is required")
        return value


def load_manifest(path: str | Path) -> DatasetManifest:
    manifest_path = Path(path)
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    return DatasetManifest.model_validate(raw)


def save_manifest(manifest: DatasetManifest, path: str | Path) -> None:
    manifest_path = Path(path)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        manifest.model_dump_json(indent=2),
        encoding="utf-8",
    )
