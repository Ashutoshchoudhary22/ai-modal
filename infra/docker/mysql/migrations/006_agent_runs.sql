-- Phase 6: Agent run metadata persistence
CREATE TABLE IF NOT EXISTS agent_runs (
    id CHAR(36) PRIMARY KEY,
    workspace_id VARCHAR(255) NOT NULL,
    request_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    policy VARCHAR(50) NOT NULL,
    task TEXT NOT NULL,
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP NULL,
    iterations INT NOT NULL DEFAULT 0,
    tool_calls INT NOT NULL DEFAULT 0,
    model_calls INT NOT NULL DEFAULT 0,
    stop_reason VARCHAR(100) NULL,
    final_response TEXT NULL,
    error_summary TEXT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_runs_workspace (workspace_id),
    INDEX idx_agent_runs_status (status),
    INDEX idx_agent_runs_request (request_id)
);

CREATE TABLE IF NOT EXISTS agent_run_events (
    id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    run_id CHAR(36) NOT NULL,
    sequence INT NOT NULL,
    event_type VARCHAR(80) NOT NULL,
    tool_name VARCHAR(100) NULL,
    success TINYINT(1) NULL,
    duration_ms INT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_agent_run_events_run (run_id, sequence),
    CONSTRAINT fk_agent_run_events_run FOREIGN KEY (run_id) REFERENCES agent_runs(id) ON DELETE CASCADE
);
