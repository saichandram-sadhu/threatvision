-- ThreatVision initial schema (M1)
-- Requires PostgreSQL 14+ (gen_random_uuid in core).

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TYPE user_role AS ENUM ('USER', 'ADMIN', 'SUPERADMIN');

CREATE TYPE ioc_job_status AS ENUM ('pending', 'processing', 'complete', 'failed');

CREATE TYPE ioc_job_item_status AS ENUM ('pending', 'done', 'error');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(320) NOT NULL UNIQUE,
    password_hash TEXT,
    name VARCHAR(255),
    image_url TEXT,
    role user_role NOT NULL DEFAULT 'USER',
    api_key_hash TEXT,
    api_key_prefix VARCHAR(16),
    daily_limit INTEGER NOT NULL DEFAULT 100 CHECK (daily_limit > 0),
    unlimited BOOLEAN NOT NULL DEFAULT FALSE,
    banned BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);

CREATE TABLE user_integration_settings (
    user_id UUID PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    source_toggles JSONB NOT NULL DEFAULT '{}',
    secrets_ciphertext TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE platform_settings (
    id SMALLINT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    misp_fallback_url TEXT,
    misp_fallback_api_key_ciphertext TEXT,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO platform_settings (id) VALUES (1) ON CONFLICT (id) DO NOTHING;

CREATE TABLE usage_counters (
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    usage_day DATE NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 0 CHECK (request_count >= 0),
    PRIMARY KEY (user_id, usage_day)
);

CREATE INDEX idx_usage_counters_user_day ON usage_counters (user_id, usage_day);

CREATE TABLE ioc_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    status ioc_job_status NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ioc_jobs_user ON ioc_jobs (user_id);

CREATE TABLE ioc_job_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES ioc_jobs (id) ON DELETE CASCADE,
    ioc_raw TEXT NOT NULL,
    ioc_type VARCHAR(64),
    aggregate JSONB,
    sources JSONB,
    item_status ioc_job_item_status NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_ioc_job_items_job ON ioc_job_items (job_id);

CREATE TABLE activity_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    ioc_snippet VARCHAR(512) NOT NULL,
    verdict VARCHAR(32) NOT NULL,
    flagged_by JSONB NOT NULL DEFAULT '[]',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_activity_log_user_created ON activity_log (user_id, created_at DESC);

CREATE TABLE webhook_secrets (
    user_id UUID PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    secret_hash TEXT NOT NULL,
    hmac_optional BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
