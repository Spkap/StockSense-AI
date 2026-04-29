-- Restrict shared analysis cache writes to the backend service role.
-- Public clients can still read cache rows, but cannot mutate global analysis data.

ALTER TABLE analysis_cache ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Anyone can insert analysis cache" ON analysis_cache;
DROP POLICY IF EXISTS "Anyone can update analysis cache" ON analysis_cache;
DROP POLICY IF EXISTS "Anyone can delete analysis cache" ON analysis_cache;
DROP POLICY IF EXISTS "Service role can insert analysis cache" ON analysis_cache;
DROP POLICY IF EXISTS "Service role can update analysis cache" ON analysis_cache;
DROP POLICY IF EXISTS "Service role can delete analysis cache" ON analysis_cache;

CREATE POLICY "Service role can insert analysis cache" ON analysis_cache
    FOR INSERT WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can update analysis cache" ON analysis_cache
    FOR UPDATE USING (auth.role() = 'service_role')
    WITH CHECK (auth.role() = 'service_role');

CREATE POLICY "Service role can delete analysis cache" ON analysis_cache
    FOR DELETE USING (auth.role() = 'service_role');

SELECT 'Migration 010 complete' AS status;
