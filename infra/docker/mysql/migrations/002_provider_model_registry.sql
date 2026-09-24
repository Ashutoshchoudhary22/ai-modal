-- AI Platform — Provider Model Registry
-- Version: 002_provider_model_registry

USE aiplatform;

CREATE TABLE IF NOT EXISTS provider_model_registry (
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

CREATE INDEX IF NOT EXISTS idx_provider_model_registry_provider ON provider_model_registry(provider);
CREATE INDEX IF NOT EXISTS idx_provider_model_registry_status ON provider_model_registry(status);

INSERT INTO provider_model_registry (
    id, model_id, model_name, version, provider, architecture,
    capabilities, context_length, modalities, status
)
SELECT UUID(), 'development-mock-v1', 'Development Mock Model', '1.0.0',
       'development_mock', 'mock', JSON_OBJECT('generate', true, 'stream', true),
       4096, JSON_ARRAY('text'), 'registered'
WHERE NOT EXISTS (
    SELECT 1 FROM provider_model_registry WHERE model_id = 'development-mock-v1'
);
