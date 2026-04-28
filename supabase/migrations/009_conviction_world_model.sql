CREATE TABLE IF NOT EXISTS thesis_claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thesis_id UUID NOT NULL REFERENCES theses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    claim_text TEXT NOT NULL,
    claim_type TEXT NOT NULL,
    metric_hint TEXT,
    time_horizon TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    confidence TEXT NOT NULL DEFAULT 'medium',
    evidence_needed TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS claim_observables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES thesis_claims(id) ON DELETE CASCADE,
    observable_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    metric_key TEXT,
    threshold_operator TEXT,
    threshold_value NUMERIC,
    period TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS forecast_questions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thesis_id UUID NOT NULL REFERENCES theses(id) ON DELETE CASCADE,
    claim_id UUID REFERENCES thesis_claims(id) ON DELETE SET NULL,
    user_id UUID NOT NULL,
    question TEXT NOT NULL,
    resolution_criteria TEXT NOT NULL,
    due_date DATE,
    probability NUMERIC,
    status TEXT NOT NULL DEFAULT 'open',
    resolved_outcome BOOLEAN,
    resolved_at TIMESTAMPTZ,
    brier_score NUMERIC,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scenario_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thesis_id UUID NOT NULL REFERENCES theses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL,
    run_id UUID REFERENCES agent_runs(id) ON DELETE SET NULL,
    final_result JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS thesis_claims_thesis_idx ON thesis_claims(thesis_id, created_at DESC);
CREATE INDEX IF NOT EXISTS claim_observables_claim_idx ON claim_observables(claim_id);
CREATE INDEX IF NOT EXISTS forecast_questions_thesis_idx ON forecast_questions(thesis_id, status);
CREATE INDEX IF NOT EXISTS scenario_runs_thesis_idx ON scenario_runs(thesis_id, created_at DESC);

ALTER TABLE thesis_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE claim_observables ENABLE ROW LEVEL SECURITY;
ALTER TABLE forecast_questions ENABLE ROW LEVEL SECURITY;
ALTER TABLE scenario_runs ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS thesis_claims_select_own ON thesis_claims;
CREATE POLICY thesis_claims_select_own
    ON thesis_claims FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS claim_observables_select_own ON claim_observables;
CREATE POLICY claim_observables_select_own
    ON claim_observables FOR SELECT
    USING (
        EXISTS (
            SELECT 1
            FROM thesis_claims
            WHERE thesis_claims.id = claim_observables.claim_id
              AND thesis_claims.user_id = auth.uid()
        )
    );

DROP POLICY IF EXISTS forecast_questions_select_own ON forecast_questions;
CREATE POLICY forecast_questions_select_own
    ON forecast_questions FOR SELECT
    USING (auth.uid() = user_id);

DROP POLICY IF EXISTS scenario_runs_select_own ON scenario_runs;
CREATE POLICY scenario_runs_select_own
    ON scenario_runs FOR SELECT
    USING (auth.uid() = user_id);
