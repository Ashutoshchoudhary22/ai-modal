"""Dataset metadata repository backed by MySQL."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform_shared.db.models import (
    DatasetORM,
    DatasetProcessingRunORM,
    DatasetVersionORM,
)


class DatasetRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create_dataset(
        self,
        *,
        name: str,
        category: str,
        license: str,
        description: str | None = None,
    ) -> DatasetORM:
        existing = self._session.scalar(select(DatasetORM).where(DatasetORM.name == name))
        if existing:
            return existing
        row = DatasetORM(
            id=str(uuid.uuid4()),
            name=name,
            category=category,
            license=license,
            description=description,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def get_version(self, dataset_id: str, version: str) -> DatasetVersionORM | None:
        return self._session.scalar(
            select(DatasetVersionORM).where(
                DatasetVersionORM.dataset_id == dataset_id,
                DatasetVersionORM.version == version,
            )
        )

    def upsert_version(
        self,
        *,
        dataset_id: str,
        version: str,
        manifest_uri: str | None,
        entry_count: int,
        content_hash: str | None,
    ) -> DatasetVersionORM:
        existing = self.get_version(dataset_id, version)
        if existing:
            existing.manifest_uri = manifest_uri
            existing.entry_count = entry_count
            existing.content_hash = content_hash
            self._session.flush()
            return existing
        row = DatasetVersionORM(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            version=version,
            manifest_uri=manifest_uri,
            entry_count=entry_count,
            content_hash=content_hash,
        )
        self._session.add(row)
        self._session.flush()
        return row

    def create_processing_run(
        self,
        *,
        dataset_version_id: str,
        status: str,
        counts: dict[str, int],
        hashes: dict[str, str | None],
        report_uri: str | None,
        processed_uri: str | None,
    ) -> DatasetProcessingRunORM:
        row = DatasetProcessingRunORM(
            id=str(uuid.uuid4()),
            dataset_version_id=dataset_version_id,
            status=status,
            input_records=counts.get("input_records", 0),
            valid_records=counts.get("valid_records", 0),
            invalid_records=counts.get("invalid_records", 0),
            exact_duplicates=counts.get("exact_duplicates", 0),
            normalized_duplicates=counts.get("normalized_duplicates", 0),
            filtered_records=counts.get("filtered_records", 0),
            output_records=counts.get("output_records", 0),
            train_records=counts.get("train_records", 0),
            validation_records=counts.get("validation_records", 0),
            test_records=counts.get("test_records", 0),
            raw_hash=hashes.get("raw_hash"),
            normalized_hash=hashes.get("normalized_hash"),
            processed_hash=hashes.get("processed_hash"),
            processing_config_hash=hashes.get("processing_config_hash"),
            report_uri=report_uri,
            processed_uri=processed_uri,
            completed_at=datetime.now(UTC),
        )
        self._session.add(row)
        self._session.flush()
        return row
