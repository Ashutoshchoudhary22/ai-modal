-- AI Platform — Repository file metadata (Phase 4 GREEN)
-- Version: 005_repository_files

USE aiplatform;

CREATE TABLE IF NOT EXISTS repository_files (
    id CHAR(64) PRIMARY KEY,
    workspace_id CHAR(36) NOT NULL,
    relative_path VARCHAR(2048) NOT NULL,
    language VARCHAR(50) NULL,
    size_bytes BIGINT NOT NULL DEFAULT 0,
    sha256 CHAR(64) NOT NULL,
    line_count INT NOT NULL DEFAULT 0,
    is_binary TINYINT(1) NOT NULL DEFAULT 0,
    is_generated TINYINT(1) NOT NULL DEFAULT 0,
    is_ignored TINYINT(1) NOT NULL DEFAULT 0,
    parser_status VARCHAR(50) NOT NULL DEFAULT 'pending',
    index_version INT NOT NULL DEFAULT 1,
    parser_version VARCHAR(50) NULL,
    first_indexed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_indexed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_repository_files_workspace FOREIGN KEY (workspace_id)
        REFERENCES workspaces(id) ON DELETE CASCADE,
    CONSTRAINT uq_repository_files_workspace_path UNIQUE (workspace_id, relative_path(512))
);

CREATE INDEX IF NOT EXISTS idx_repository_files_workspace
    ON repository_files(workspace_id);
CREATE INDEX IF NOT EXISTS idx_repository_files_workspace_path
    ON repository_files(workspace_id, relative_path(191));
CREATE INDEX IF NOT EXISTS idx_repository_files_language
    ON repository_files(workspace_id, language);
CREATE INDEX IF NOT EXISTS idx_repository_files_sha256
    ON repository_files(sha256);

ALTER TABLE repository_symbols
    ADD COLUMN file_id CHAR(64) NULL AFTER workspace_id;

ALTER TABLE repository_imports
    ADD COLUMN file_id CHAR(64) NULL AFTER workspace_id;

CREATE INDEX IF NOT EXISTS idx_repository_symbols_file
    ON repository_symbols(workspace_id, file_id);
CREATE INDEX IF NOT EXISTS idx_repository_imports_file
    ON repository_imports(workspace_id, file_id);
