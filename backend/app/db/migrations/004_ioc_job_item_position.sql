-- Stable ordering for bulk job rows (M7 SSE + UI).

ALTER TABLE ioc_job_items
    ADD COLUMN IF NOT EXISTS position INTEGER NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_ioc_job_items_job_position ON ioc_job_items (job_id, position);
