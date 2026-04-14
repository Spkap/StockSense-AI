-- Migration: Audit trail for every agent step in every analysis run (P3-M)
--
-- run_id matches X-Correlation-ID header on the originating request.
-- Rows are append-only — never updated, never deleted by application code.

CREATE TABLE IF NOT EXISTS analysis_traces (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    ticker      TEXT        NOT NULL,
    run_id      TEXT        NOT NULL,
    step_name   TEXT        NOT NULL,   -- "bull_analyst" | "bear_analyst" | "synthesizer" | "skeptic"
    prompt_snapshot  TEXT,              -- exact prompt text sent to LLM
    response_snapshot TEXT,             -- exact LLM response text
    token_count INT,
    duration_ms INT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS analysis_traces_run_id_idx ON analysis_traces(run_id);
CREATE INDEX IF NOT EXISTS analysis_traces_ticker_idx ON analysis_traces(ticker);
