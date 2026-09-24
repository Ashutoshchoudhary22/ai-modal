-- AI Platform — Repository Intelligence (Phase 4)
-- Version: 004_repository_intelligence

USE aiplatform;

CREATE TABLE IF NOT EXISTS repository_index_runs (
    id CHAR(36) PRIMARY KEY,
    workspace_id CHAR(36) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    index_version INT NOT NULL DEFAULT 1,
    parser_version VARCHAR(50),
    schema_version VARCHAR(50) NOT NULL DEFAULT '1.0',
    files_seen INT NOT NULL DEFAULT 0,
    files_indexed INT NOT NULL DEFAULT 0,
    files_skipped INT NOT NULL DEFAULT 0,
    files_failed INT NOT NULL DEFAULT 0,
    symbols_extracted INT NOT NULL DEFAULT 0,
    imports_extracted INT NOT NULL DEFAULT 0,
    duration_ms INT,
    error_summary TEXT,
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP NULL,
    CONSTRAINT fk_repository_index_runs_workspace FOREIGN KEY (workspace_id)
        REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_repository_index_runs_workspace
    ON repository_index_runs(workspace_id);

CREATE TABLE IF NOT EXISTS repository_symbols (
    id CHAR(64) PRIMARY KEY,
    workspace_id CHAR(36) NOT NULL,
    file_path TEXT NOT NULL,
    kind VARCHAR(50) NOT NULL,
    name VARCHAR(512) NOT NULL,
    qualified_name TEXT NOT NULL,
    parent_symbol_id CHAR(64) NULL,
    start_line INT NOT NULL,
    end_line INT NOT NULL,
    start_byte INT NOT NULL DEFAULT 0,
    end_byte INT NOT NULL DEFAULT 0,
    signature TEXT,
    metadata JSON NOT NULL DEFAULT (JSON_OBJECT()),
    CONSTRAINT fk_repository_symbols_workspace FOREIGN KEY (workspace_id)
        REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_repository_symbols_workspace
    ON repository_symbols(workspace_id);
CREATE INDEX IF NOT EXISTS idx_repository_symbols_name
    ON repository_symbols(name(191));

CREATE TABLE IF NOT EXISTS repository_imports (
    id CHAR(64) PRIMARY KEY,
    workspace_id CHAR(36) NOT NULL,
    file_path TEXT NOT NULL,
    module_path TEXT NOT NULL,
    imported_name VARCHAR(512),
    alias VARCHAR(512),
    start_line INT NOT NULL,
    resolution_status VARCHAR(50) NOT NULL DEFAULT 'unknown',
    resolved_path TEXT,
    CONSTRAINT fk_repository_imports_workspace FOREIGN KEY (workspace_id)
        REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_repository_imports_workspace
    ON repository_imports(workspace_id);
