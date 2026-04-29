CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS agent_runs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    run_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'running',
    ticker TEXT,
    thesis_id UUID,
    question TEXT,
    phase TEXT,
    progress NUMERIC NOT NULL DEFAULT 0,
    idempotency_key TEXT,
    input_hash TEXT,
    evidence_hash TEXT,
    cache_hit BOOLEAN NOT NULL DEFAULT false,
    final_result JSONB,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS agent_run_steps (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_id UUID NOT NULL REFERENCES agent_runs(id) ON DELETE CASCADE,
    step_name TEXT NOT NULL,
    phase TEXT NOT NULL,
    status TEXT NOT NULL,
    event_type TEXT,
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

CREATE TABLE IF NOT EXISTS source_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker TEXT NOT NULL,
    cik TEXT,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    title TEXT NOT NULL,
    url TEXT,
    accession_number TEXT,
    filing_type TEXT,
    period TEXT,
    filed_at TEXT,
    published_at TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    raw_text TEXT,
    raw_json JSONB,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS evidence_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_document_id UUID REFERENCES source_documents(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    local_id TEXT NOT NULL,
    chunk_index INT NOT NULL,
    text TEXT NOT NULL,
    fts TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', text)) STORED,
    embedding vector(1536),
    reliability_tier TEXT NOT NULL DEFAULT 'medium',
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS agent_runs_user_created_idx ON agent_runs(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS agent_runs_type_status_idx ON agent_runs(run_type, status);
CREATE INDEX IF NOT EXISTS agent_run_steps_run_id_idx ON agent_run_steps(run_id);
CREATE INDEX IF NOT EXISTS source_documents_ticker_idx ON source_documents(ticker);
CREATE INDEX IF NOT EXISTS evidence_chunks_ticker_idx ON evidence_chunks(ticker);
CREATE INDEX IF NOT EXISTS evidence_chunks_fts_idx ON evidence_chunks USING GIN (fts);
CREATE UNIQUE INDEX IF NOT EXISTS evidence_chunks_source_local_idx ON evidence_chunks(source_document_id, local_id);

ALTER TABLE agent_runs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_run_steps ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE evidence_chunks ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS agent_runs_select_own ON agent_runs;
CREATE POLICY agent_runs_select_own
    ON agent_runs FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS agent_run_steps_select_own ON agent_run_steps;
CREATE POLICY agent_run_steps_select_own
    ON agent_run_steps FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM agent_runs
            WHERE agent_runs.id = agent_run_steps.run_id
              AND agent_runs.user_id = auth.uid()
        )
    );
