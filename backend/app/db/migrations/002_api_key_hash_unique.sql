-- Partial unique index: at most one row per API key hash when set.

CREATE UNIQUE INDEX idx_users_api_key_hash_unique ON users (api_key_hash)
WHERE api_key_hash IS NOT NULL;
