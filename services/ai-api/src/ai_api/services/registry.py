"""Registry service."""

from __future__ import annotations

from ai_platform_protocol.models.registry import ModelRegistryRecord
from ai_platform_shared.db import session_scope
from ai_platform_shared.db.repository import ModelRegistryRepository


class RegistryService:
    def list_models(self, provider: str | None = None) -> list[ModelRegistryRecord]:
        with session_scope() as session:
            repository = ModelRegistryRepository(session)
            return repository.list_models(provider=provider)

    def get_model(self, model_id: str) -> ModelRegistryRecord | None:
        with session_scope() as session:
            repository = ModelRegistryRepository(session)
            return repository.get_by_model_id(model_id)

    def register_model(self, record: ModelRegistryRecord) -> ModelRegistryRecord:
        with session_scope() as session:
            repository = ModelRegistryRepository(session)
            return repository.upsert(record)
