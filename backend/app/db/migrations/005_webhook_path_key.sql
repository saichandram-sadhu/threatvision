-- SIEM webhook routing: public path slug + optional bearer (M9).

ALTER TABLE webhook_secrets
    ADD COLUMN IF NOT EXISTS path_key VARCHAR(80) UNIQUE;

ALTER TABLE webhook_secrets
    ALTER COLUMN secret_hash DROP NOT NULL;

CREATE INDEX IF NOT EXISTS idx_webhook_secrets_path_key ON webhook_secrets (path_key)
    WHERE path_key IS NOT NULL;
