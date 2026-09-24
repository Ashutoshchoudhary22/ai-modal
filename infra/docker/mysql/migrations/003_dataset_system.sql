-- AI Platform — Dataset System (Phase 3)
-- Version: 003_dataset_system

USE aiplatform;

CREATE TABLE IF NOT EXISTS dataset_sources (
    id CHAR(36) PRIMARY KEY,
    dataset_id CHAR(36) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    source_type VARCHAR(50) NOT NULL DEFAULT 'internal',
    source_reference TEXT,
    license VARCHAR(100) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_dataset_sources_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dataset_sources_dataset ON dataset_sources(dataset_id);

CREATE TABLE IF NOT EXISTS dataset_processing_runs (
    id CHAR(36) PRIMARY KEY,
    dataset_version_id CHAR(36) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'completed',
    input_records INT NOT NULL DEFAULT 0,
    valid_records INT NOT NULL DEFAULT 0,
    invalid_records INT NOT NULL DEFAULT 0,
    exact_duplicates INT NOT NULL DEFAULT 0,
    normalized_duplicates INT NOT NULL DEFAULT 0,
    filtered_records INT NOT NULL DEFAULT 0,
    output_records INT NOT NULL DEFAULT 0,
    train_records INT NOT NULL DEFAULT 0,
    validation_records INT NOT NULL DEFAULT 0,
    test_records INT NOT NULL DEFAULT 0,
    raw_hash VARCHAR(64),
    normalized_hash VARCHAR(64),
    processed_hash VARCHAR(64),
    processing_config_hash VARCHAR(64),
    report_uri TEXT,
    processed_uri TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    CONSTRAINT fk_dataset_processing_runs_version FOREIGN KEY (dataset_version_id)
        REFERENCES dataset_versions(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_dataset_processing_runs_version ON dataset_processing_runs(dataset_version_id);
CREATE INDEX IF NOT EXISTS idx_dataset_processing_runs_status ON dataset_processing_runs(status);
