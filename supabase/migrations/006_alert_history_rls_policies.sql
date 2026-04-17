-- Migration 006: Add missing RLS policies for alert_history and analysis_traces
--
-- alert_history (002) was created with only a SELECT policy.
-- The app needs INSERT (backend creates alerts) and UPDATE (user marks read/dismissed).
-- analysis_traces (005) was created with no RLS at all.

-- ============================================
-- alert_history: INSERT policy
-- ============================================
-- Alerts are created by the backend acting as the authenticated user
-- (anon client + user JWT). Service role bypasses RLS automatically.
DROP POLICY IF EXISTS "Users can insert own alerts" ON public.alert_history;
CREATE POLICY "Users can insert own alerts"
    ON public.alert_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- ============================================
-- alert_history: UPDATE policy
-- ============================================
-- Users mark their own alerts as read / acknowledged / dismissed / acted.
DROP POLICY IF EXISTS "Users can update own alerts" ON public.alert_history;
CREATE POLICY "Users can update own alerts"
    ON public.alert_history FOR UPDATE
    USING (auth.uid() = user_id);

-- ============================================
-- alert_history: DELETE policy
-- ============================================
-- Users can delete their own alerts.
DROP POLICY IF EXISTS "Users can delete own alerts" ON public.alert_history;
CREATE POLICY "Users can delete own alerts"
    ON public.alert_history FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================
-- analysis_traces: RLS
-- ============================================
-- Traces are written by the backend (service role). Users should not be
-- able to read or write traces directly — backend-only via service role.
ALTER TABLE public.analysis_traces ENABLE ROW LEVEL SECURITY;

-- No user-facing policies: service role bypasses RLS and is the only writer/reader.
-- If you want to expose traces to authenticated users in the future, add a SELECT
-- policy here: CREATE POLICY "..." ON analysis_traces FOR SELECT USING (auth.uid() IS NOT NULL);

-- ============================================
-- analysis_cache: UPDATE policy (missing from 003)
-- ============================================
-- upsert(on_conflict="ticker") requires both INSERT + UPDATE policies.
-- 003 added INSERT but forgot UPDATE, so upsert falls back to insert only
-- and fails when the ticker already exists.
DROP POLICY IF EXISTS "Anyone can update analysis cache" ON analysis_cache;
CREATE POLICY "Anyone can update analysis cache" ON analysis_cache
    FOR UPDATE USING (true);

-- Verify
SELECT 'Migration 006 complete' AS status;
SELECT schemaname, tablename, policyname, cmd
FROM pg_policies
WHERE tablename IN ('alert_history', 'analysis_traces')
ORDER BY tablename, cmd;
