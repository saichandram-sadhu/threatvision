-- Per-user MISP URL + encrypted key; explorer response cache (M4).

ALTER TABLE user_integration_settings
    ADD COLUMN IF NOT EXISTS misp_base_url TEXT,
    ADD COLUMN IF NOT EXISTS misp_api_key_ciphertext TEXT;

CREATE TABLE IF NOT EXISTS misp_explorer_cache (
    user_id UUID PRIMARY KEY REFERENCES users (id) ON DELETE CASCADE,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_misp_explorer_cache_updated ON misp_explorer_cache (updated_at);
