-- AI Platform — Initial MySQL Schema
-- Version: 001_initial
-- MySQL 8.0+

USE aiplatform;

-- Organizations & Users
CREATE TABLE organizations (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(255) NOT NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    plan VARCHAR(50) NOT NULL DEFAULT 'free',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

CREATE TABLE users (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255),
    display_name VARCHAR(255),
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE organization_members (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    organization_id CHAR(36) NOT NULL,
    user_id CHAR(36) NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    UNIQUE KEY uq_org_user (organization_id, user_id),
    CONSTRAINT fk_org_members_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_org_members_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE teams (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    organization_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    CONSTRAINT fk_teams_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE workspaces (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    team_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    root_path TEXT,
    settings JSON NOT NULL DEFAULT (JSON_OBJECT()),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_workspaces_team FOREIGN KEY (team_id) REFERENCES teams(id) ON DELETE CASCADE
);

CREATE TABLE projects (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    workspace_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    metadata JSON NOT NULL DEFAULT (JSON_OBJECT()),
    CONSTRAINT fk_projects_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

-- Agent Sessions
CREATE TABLE agent_sessions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    project_id CHAR(36) NULL,
    workspace_id CHAR(36) NULL,
    user_id CHAR(36) NULL,
    task TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'created',
    model_id VARCHAR(100) NOT NULL,
    max_iterations INT NOT NULL DEFAULT 25,
    iteration_count INT NOT NULL DEFAULT 0,
    summary TEXT,
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agent_sessions_project FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL,
    CONSTRAINT fk_agent_sessions_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE SET NULL,
    CONSTRAINT fk_agent_sessions_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX idx_agent_sessions_workspace_status ON agent_sessions(workspace_id, status);

CREATE TABLE agent_events (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    session_id CHAR(36) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    payload JSON NOT NULL DEFAULT (JSON_OBJECT()),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_agent_events_session FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE CASCADE
);

CREATE INDEX idx_agent_events_session_created ON agent_events(session_id, created_at);

-- Code Indexing
CREATE TABLE code_indices (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    workspace_id CHAR(36) NOT NULL UNIQUE,
    status VARCHAR(50) NOT NULL DEFAULT 'indexing',
    file_count INT NOT NULL DEFAULT 0,
    symbol_count INT NOT NULL DEFAULT 0,
    index_hash VARCHAR(64),
    indexed_at TIMESTAMP NULL,
    CONSTRAINT fk_code_indices_workspace FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE indexed_files (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    index_id CHAR(36) NOT NULL,
    path TEXT NOT NULL,
    language VARCHAR(50),
    content_hash VARCHAR(64),
    size_bytes INT NOT NULL DEFAULT 0,
    CONSTRAINT fk_indexed_files_index FOREIGN KEY (index_id) REFERENCES code_indices(id) ON DELETE CASCADE
);

-- Models & Training
CREATE TABLE models (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(100) NOT NULL UNIQUE,
    modality VARCHAR(50) NOT NULL DEFAULT 'text',
    description TEXT
);

CREATE TABLE datasets (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    license VARCHAR(100) NOT NULL,
    description TEXT
);

CREATE TABLE dataset_versions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    dataset_id CHAR(36) NOT NULL,
    version VARCHAR(50) NOT NULL,
    manifest_uri TEXT,
    entry_count INT NOT NULL DEFAULT 0,
    content_hash VARCHAR(64),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_dataset_version (dataset_id, version),
    CONSTRAINT fk_dataset_versions_dataset FOREIGN KEY (dataset_id) REFERENCES datasets(id) ON DELETE CASCADE
);

CREATE TABLE model_versions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    model_id CHAR(36) NOT NULL,
    version VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    artifact_uri TEXT,
    config_hash VARCHAR(64),
    dataset_version_id CHAR(36) NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_model_version (model_id, version),
    CONSTRAINT fk_model_versions_model FOREIGN KEY (model_id) REFERENCES models(id) ON DELETE CASCADE,
    CONSTRAINT fk_model_versions_dataset FOREIGN KEY (dataset_version_id) REFERENCES dataset_versions(id) ON DELETE SET NULL
);

CREATE TABLE training_jobs (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    job_type VARCHAR(50) NOT NULL,
    config_path TEXT NOT NULL,
    dataset_version_id CHAR(36) NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'queued',
    output_model_version_id CHAR(36) NULL,
    metrics JSON NOT NULL DEFAULT (JSON_OBJECT()),
    started_at TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_training_jobs_dataset FOREIGN KEY (dataset_version_id) REFERENCES dataset_versions(id) ON DELETE SET NULL,
    CONSTRAINT fk_training_jobs_model_version FOREIGN KEY (output_model_version_id) REFERENCES model_versions(id) ON DELETE SET NULL
);

CREATE TABLE benchmark_runs (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    model_version_id CHAR(36) NOT NULL,
    benchmark_name VARCHAR(100) NOT NULL,
    dataset_version_id CHAR(36) NULL,
    config JSON NOT NULL DEFAULT (JSON_OBJECT()),
    results JSON NOT NULL DEFAULT (JSON_OBJECT()),
    run_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_benchmark_runs_model_version FOREIGN KEY (model_version_id) REFERENCES model_versions(id) ON DELETE CASCADE,
    CONSTRAINT fk_benchmark_runs_dataset FOREIGN KEY (dataset_version_id) REFERENCES dataset_versions(id) ON DELETE SET NULL
);

-- Auth & Billing
CREATE TABLE api_keys (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    organization_id CHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    key_prefix VARCHAR(12) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    scopes JSON NOT NULL DEFAULT (JSON_ARRAY()),
    expires_at TIMESTAMP NULL,
    revoked_at TIMESTAMP NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_api_keys_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

CREATE TABLE usage_records (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    organization_id CHAR(36) NOT NULL,
    user_id CHAR(36) NULL,
    session_id CHAR(36) NULL,
    model_id VARCHAR(100) NOT NULL,
    prompt_tokens INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    tool_calls INT NOT NULL DEFAULT 0,
    recorded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_usage_records_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_usage_records_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    CONSTRAINT fk_usage_records_session FOREIGN KEY (session_id) REFERENCES agent_sessions(id) ON DELETE SET NULL
);

CREATE INDEX idx_usage_records_org_recorded ON usage_records(organization_id, recorded_at);

CREATE TABLE subscriptions (
    id CHAR(36) PRIMARY KEY DEFAULT (UUID()),
    organization_id CHAR(36) NOT NULL UNIQUE,
    plan VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    external_id VARCHAR(255),
    current_period_start TIMESTAMP NULL,
    current_period_end TIMESTAMP NULL,
    CONSTRAINT fk_subscriptions_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE
);

-- Audit
CREATE TABLE audit_logs (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    organization_id CHAR(36) NULL,
    user_id CHAR(36) NULL,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(255),
    metadata JSON NOT NULL DEFAULT (JSON_OBJECT()),
    ip_address VARCHAR(45),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_audit_logs_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL,
    CONSTRAINT fk_audit_logs_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Seed development data
INSERT INTO organizations (name, slug, plan) VALUES ('Development Org', 'dev-org', 'free');
INSERT INTO models (name, modality, description)
VALUES ('code-assistant', 'text', 'Default coding assistant model placeholder');

-- Provider model registry (Phase 1)
CREATE TABLE provider_model_registry (
    id CHAR(36) PRIMARY KEY,
    model_id VARCHAR(100) NOT NULL UNIQUE,
    model_name VARCHAR(255) NOT NULL,
    version VARCHAR(50) NOT NULL,
    provider VARCHAR(50) NOT NULL,
    architecture VARCHAR(100),
    capabilities JSON NOT NULL DEFAULT (JSON_OBJECT()),
    context_length INT,
    modalities JSON NOT NULL DEFAULT (JSON_ARRAY('text')),
    status VARCHAR(50) NOT NULL DEFAULT 'registered',
    local_path TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_provider_model_registry_provider ON provider_model_registry(provider);
CREATE INDEX idx_provider_model_registry_status ON provider_model_registry(status);

INSERT INTO provider_model_registry (
    id, model_id, model_name, version, provider, architecture,
    capabilities, context_length, modalities, status
) VALUES (
    UUID(), 'development-mock-v1', 'Development Mock Model', '1.0.0',
    'development_mock', 'mock', JSON_OBJECT('generate', true, 'stream', true),
    4096, JSON_ARRAY('text'), 'registered'
);
