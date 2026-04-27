-- Per-IP and per-email registration attempt limits (rolling UTC hour buckets).

CREATE TABLE registration_throttle (
    bucket TEXT NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    hit_count INTEGER NOT NULL DEFAULT 0 CHECK (hit_count >= 0),
    PRIMARY KEY (bucket, window_start)
);

CREATE INDEX idx_registration_throttle_prune ON registration_throttle (window_start);
