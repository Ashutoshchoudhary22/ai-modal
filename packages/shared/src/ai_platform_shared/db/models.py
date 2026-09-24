"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DatasetORM(Base):
    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    license: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)


class DatasetVersionORM(Base):
    __tablename__ = "dataset_versions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    manifest_uri: Mapped[str | None] = mapped_column(Text)
    entry_count: Mapped[int] = mapped_column(Integer, default=0)
    content_hash: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DatasetProcessingRunORM(Base):
    __tablename__ = "dataset_processing_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="completed")
    input_records: Mapped[int] = mapped_column(Integer, default=0)
    valid_records: Mapped[int] = mapped_column(Integer, default=0)
    invalid_records: Mapped[int] = mapped_column(Integer, default=0)
    exact_duplicates: Mapped[int] = mapped_column(Integer, default=0)
    normalized_duplicates: Mapped[int] = mapped_column(Integer, default=0)
    filtered_records: Mapped[int] = mapped_column(Integer, default=0)
    output_records: Mapped[int] = mapped_column(Integer, default=0)
    train_records: Mapped[int] = mapped_column(Integer, default=0)
    validation_records: Mapped[int] = mapped_column(Integer, default=0)
    test_records: Mapped[int] = mapped_column(Integer, default=0)
    raw_hash: Mapped[str | None] = mapped_column(String(64))
    normalized_hash: Mapped[str | None] = mapped_column(String(64))
    processed_hash: Mapped[str | None] = mapped_column(String(64))
    processing_config_hash: Mapped[str | None] = mapped_column(String(64))
    report_uri: Mapped[str | None] = mapped_column(Text)
    processed_uri: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class ProviderModelRegistryORM(Base):
    __tablename__ = "provider_model_registry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    architecture: Mapped[str | None] = mapped_column(String(100))
    capabilities: Mapped[dict] = mapped_column(JSON, default=dict)
    context_length: Mapped[int | None] = mapped_column(Integer)
    modalities: Mapped[list] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(50), default="registered")
    local_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
