"""Model registry repository backed by MySQL."""

from __future__ import annotations

import uuid
from datetime import datetime

from ai_platform_protocol.models.registry import ModelRegistryRecord
from sqlalchemy import select
from sqlalchemy.orm import Session

from ai_platform_shared.db.models import ProviderModelRegistryORM


class ModelRegistryRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_models(self, provider: str | None = None) -> list[ModelRegistryRecord]:
        stmt = select(ProviderModelRegistryORM)
        if provider:
            stmt = stmt.where(ProviderModelRegistryORM.provider == provider)
        rows = self._session.scalars(
            stmt.order_by(ProviderModelRegistryORM.created_at.desc())
        ).all()
        return [self._to_record(row) for row in rows]

    def get_by_model_id(self, model_id: str) -> ModelRegistryRecord | None:
        row = self._session.scalar(
            select(ProviderModelRegistryORM).where(ProviderModelRegistryORM.model_id == model_id)
        )
        return self._to_record(row) if row else None

    def upsert(self, record: ModelRegistryRecord) -> ModelRegistryRecord:
        existing = self._session.scalar(
            select(ProviderModelRegistryORM).where(
                ProviderModelRegistryORM.model_id == record.model_id
            )
        )
        if existing:
            existing.model_name = record.model_name
            existing.version = record.version
            existing.provider = record.provider
            existing.architecture = record.architecture
            existing.capabilities = record.capabilities
            existing.context_length = record.context_length
            existing.modalities = record.modalities
            existing.status = record.status
            existing.local_path = record.local_path
            self._session.flush()
            return self._to_record(existing)

        row = ProviderModelRegistryORM(
            id=str(uuid.uuid4()),
            model_id=record.model_id,
            model_name=record.model_name,
            version=record.version,
            provider=record.provider,
            architecture=record.architecture,
            capabilities=record.capabilities,
            context_length=record.context_length,
            modalities=record.modalities,
            status=record.status,
            local_path=record.local_path,
        )
        self._session.add(row)
        self._session.flush()
        return self._to_record(row)

    @staticmethod
    def _to_record(row: ProviderModelRegistryORM) -> ModelRegistryRecord:
        return ModelRegistryRecord(
            model_id=row.model_id,
            model_name=row.model_name,
            version=row.version,
            provider=row.provider,
            architecture=row.architecture,
            capabilities=row.capabilities or {},
            context_length=row.context_length,
            modalities=row.modalities or ["text"],
            status=row.status,
            local_path=row.local_path,
            created_at=row.created_at if isinstance(row.created_at, datetime) else None,
        )
