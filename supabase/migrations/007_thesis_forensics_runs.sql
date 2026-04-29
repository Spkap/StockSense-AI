CREATE TABLE IF NOT EXISTS thesis_check_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    thesis_id UUID NOT NULL,
    ticker TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    run_mode TEXT NOT NULL DEFAULT 'normal',
    idempotency_key TEXT,
    thesis_hash TEXT,
    evidence_hash TEXT,
    cache_hit BOOLEAN NOT NULL DEFAULT false,
    final_verdict TEXT,
    final_confidence TEXT,
    final_summary TEXT,
    final_result JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

ALTER TABLE thesis_check_runs ADD COLUMN IF NOT EXISTS run_mode TEXT NOT NULL DEFAULT 'normal';
ALTER TABLE thesis_check_runs ADD COLUMN IF NOT EXISTS idempotency_key TEXT;
ALTER TABLE thesis_check_runs ADD COLUMN IF NOT EXISTS thesis_hash TEXT;
ALTER TABLE thesis_check_runs ADD COLUMN IF NOT EXISTS cache_hit BOOLEAN NOT NULL DEFAULT false;

CREATE INDEX IF NOT EXISTS thesis_check_runs_user_id_idx ON thesis_check_runs(user_id);
CREATE INDEX IF NOT EXISTS thesis_check_runs_thesis_id_idx ON thesis_check_runs(thesis_id);
CREATE INDEX IF NOT EXISTS thesis_check_runs_created_at_idx ON thesis_check_runs(created_at DESC);
CREATE INDEX IF NOT EXISTS thesis_check_runs_idempotency_key_idx ON thesis_check_runs(idempotency_key);
CREATE INDEX IF NOT EXISTS thesis_check_runs_thesis_hash_idx ON thesis_check_runs(thesis_hash);

CREATE TABLE IF NOT EXISTS thesis_check_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES thesis_check_runs(id) ON DELETE CASCADE,
    step_name TEXT NOT NULL,
    status TEXT NOT NULL,
    latency_ms INT NOT NULL DEFAULT 0,
    data JSONB NOT NULL DEFAULT '{}'::jsonb,
    error_message TEXT,
    retry_count INT NOT NULL DEFAULT 0,
    model TEXT,
    prompt_version TEXT,
    input_token_estimate INT,
    output_token_estimate INT,
    cost_estimate_usd NUMERIC,
    validation_errors JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS thesis_check_steps_run_id_idx ON thesis_check_steps(run_id);

ALTER TABLE thesis_check_steps ADD COLUMN IF NOT EXISTS retry_count INT NOT NULL DEFAULT 0;
ALTER TABLE thesis_check_steps ADD COLUMN IF NOT EXISTS model TEXT;
ALTER TABLE thesis_check_steps ADD COLUMN IF NOT EXISTS prompt_version TEXT;
ALTER TABLE thesis_check_steps ADD COLUMN IF NOT EXISTS input_token_estimate INT;
ALTER TABLE thesis_check_steps ADD COLUMN IF NOT EXISTS output_token_estimate INT;
ALTER TABLE thesis_check_steps ADD COLUMN IF NOT EXISTS cost_estimate_usd NUMERIC;
ALTER TABLE thesis_check_steps ADD COLUMN IF NOT EXISTS validation_errors JSONB NOT NULL DEFAULT '[]'::jsonb;

CREATE TABLE IF NOT EXISTS thesis_evidence_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES thesis_check_runs(id) ON DELETE CASCADE,
    thesis_id UUID NOT NULL,
    ticker TEXT NOT NULL,
    local_id TEXT,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    text TEXT NOT NULL,
    url TEXT,
    published_at TEXT,
    reliability_tier TEXT NOT NULL DEFAULT 'medium',
    evidence_hash TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE thesis_evidence_items ADD COLUMN IF NOT EXISTS local_id TEXT;

CREATE INDEX IF NOT EXISTS thesis_evidence_items_run_id_idx ON thesis_evidence_items(run_id);
CREATE INDEX IF NOT EXISTS thesis_evidence_items_thesis_id_idx ON thesis_evidence_items(thesis_id);
CREATE INDEX IF NOT EXISTS thesis_evidence_items_hash_idx ON thesis_evidence_items(evidence_hash);
CREATE INDEX IF NOT EXISTS thesis_evidence_items_local_id_idx ON thesis_evidence_items(run_id, local_id);

CREATE TABLE IF NOT EXISTS thesis_corrections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    thesis_id UUID NOT NULL,
    run_id UUID REFERENCES thesis_check_runs(id) ON DELETE SET NULL,
    evidence_local_id TEXT,
    claim TEXT,
    correction_type TEXT NOT NULL,
    correction_text TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS thesis_corrections_user_id_idx ON thesis_corrections(user_id);
CREATE INDEX IF NOT EXISTS thesis_corrections_thesis_id_idx ON thesis_corrections(thesis_id);

ALTER TABLE thesis_check_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE thesis_check_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE thesis_evidence_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE thesis_corrections ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can read own thesis check runs" ON thesis_check_runs;
CREATE POLICY "Users can read own thesis check runs"
ON thesis_check_runs FOR SELECT
USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can read own thesis check steps" ON thesis_check_steps;
CREATE POLICY "Users can read own thesis check steps"
ON thesis_check_steps FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM thesis_check_runs
        WHERE thesis_check_runs.id = thesis_check_steps.run_id
        AND thesis_check_runs.user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can read own thesis evidence" ON thesis_evidence_items;
CREATE POLICY "Users can read own thesis evidence"
ON thesis_evidence_items FOR SELECT
USING (
    EXISTS (
        SELECT 1 FROM thesis_check_runs
        WHERE thesis_check_runs.id = thesis_evidence_items.run_id
        AND thesis_check_runs.user_id = auth.uid()
    )
);

DROP POLICY IF EXISTS "Users can read own thesis corrections" ON thesis_corrections;
CREATE POLICY "Users can read own thesis corrections"
ON thesis_corrections FOR SELECT
USING (auth.uid() = user_id);
