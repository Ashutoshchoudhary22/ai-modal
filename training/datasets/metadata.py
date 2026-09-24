"""Persist dataset metadata to MySQL."""

from __future__ import annotations

from pathlib import Path

from training.datasets.ingest import IngestResult
from training.datasets.manifest import DatasetManifest


def persist_dataset_metadata(
    manifest: DatasetManifest,
    result: IngestResult,
) -> str | None:
    """Persist dataset version and processing run. Returns dataset_version_id or None."""
    try:
        from ai_platform_shared.db import session_scope
        from ai_platform_shared.db.dataset_repository import DatasetRepository
    except ImportError:
        return None

    try:
        with session_scope() as session:
            repo = DatasetRepository(session)
            dataset = repo.get_or_create_dataset(
                name=manifest.dataset.name,
                category=manifest.dataset.task,
                license=manifest.source.license,
                description=manifest.dataset.description,
            )
            version = repo.upsert_version(
                dataset_id=dataset.id,
                version=manifest.dataset.version,
                manifest_uri=str(result.processed.processed_manifest_path),
                entry_count=result.quality_report.output_records,
                content_hash=result.quality_report.processed_hash,
            )
            repo.create_processing_run(
                dataset_version_id=version.id,
                status="completed",
                counts={
                    "input_records": result.quality_report.input_records,
                    "valid_records": result.quality_report.valid_records,
                    "invalid_records": result.quality_report.invalid_records,
                    "exact_duplicates": result.quality_report.exact_duplicates,
                    "normalized_duplicates": result.quality_report.normalized_duplicates,
                    "filtered_records": result.quality_report.filtered_records,
                    "output_records": result.quality_report.output_records,
                    "train_records": result.quality_report.train_records,
                    "validation_records": result.quality_report.validation_records,
                    "test_records": result.quality_report.test_records,
                },
                hashes={
                    "raw_hash": result.quality_report.raw_hash,
                    "normalized_hash": result.quality_report.normalized_hash,
                    "processed_hash": result.quality_report.processed_hash,
                    "processing_config_hash": result.quality_report.configuration_hash,
                },
                report_uri=str(
                    Path(result.processed.processed_dir) / "quality_report.json"
                ),
                processed_uri=str(result.processed.processed_dir),
            )
            return version.id
    except Exception:
        return None
