"""SQLAlchemy ORM models."""

from datetime import datetime

from sqlalchemy import JSON, DateTime, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class OrganizationORM(Base):
    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    plan: Mapped[str] = mapped_column(String(50), default="free")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class TeamORM(Base):
    __tablename__ = "teams"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


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


class WorkspaceORM(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    team_id: Mapped[str] = mapped_column(String(36), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    root_path: Mapped[str | None] = mapped_column(Text)
    settings: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RepositoryIndexRunORM(Base):
    __tablename__ = "repository_index_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="running")
    index_version: Mapped[int] = mapped_column(Integer, default=1)
    parser_version: Mapped[str | None] = mapped_column(String(50))
    schema_version: Mapped[str] = mapped_column(String(50), default="1.0")
    files_seen: Mapped[int] = mapped_column(Integer, default=0)
    files_indexed: Mapped[int] = mapped_column(Integer, default=0)
    files_skipped: Mapped[int] = mapped_column(Integer, default=0)
    files_failed: Mapped[int] = mapped_column(Integer, default=0)
    symbols_extracted: Mapped[int] = mapped_column(Integer, default=0)
    imports_extracted: Mapped[int] = mapped_column(Integer, default=0)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_summary: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)


class RepositoryFileORM(Base):
    __tablename__ = "repository_files"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    relative_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    language: Mapped[str | None] = mapped_column(String(50))
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    line_count: Mapped[int] = mapped_column(Integer, default=0)
    is_binary: Mapped[int] = mapped_column(Integer, default=0)
    is_generated: Mapped[int] = mapped_column(Integer, default=0)
    is_ignored: Mapped[int] = mapped_column(Integer, default=0)
    parser_status: Mapped[str] = mapped_column(String(50), default="pending")
    index_version: Mapped[int] = mapped_column(Integer, default=1)
    parser_version: Mapped[str | None] = mapped_column(String(50))
    first_indexed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_indexed_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RepositorySymbolORM(Base):
    __tablename__ = "repository_symbols"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    file_id: Mapped[str | None] = mapped_column(String(64))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(512), nullable=False)
    qualified_name: Mapped[str] = mapped_column(Text, nullable=False)
    parent_symbol_id: Mapped[str | None] = mapped_column(String(64))
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    end_line: Mapped[int] = mapped_column(Integer, nullable=False)
    start_byte: Mapped[int] = mapped_column(Integer, default=0)
    end_byte: Mapped[int] = mapped_column(Integer, default=0)
    signature: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)


class RepositoryImportORM(Base):
    __tablename__ = "repository_imports"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    file_id: Mapped[str | None] = mapped_column(String(64))
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    module_path: Mapped[str] = mapped_column(Text, nullable=False)
    imported_name: Mapped[str | None] = mapped_column(String(512))
    alias: Mapped[str | None] = mapped_column(String(512))
    start_line: Mapped[int] = mapped_column(Integer, nullable=False)
    resolution_status: Mapped[str] = mapped_column(String(50), default="unknown")
    resolved_path: Mapped[str | None] = mapped_column(Text)


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
