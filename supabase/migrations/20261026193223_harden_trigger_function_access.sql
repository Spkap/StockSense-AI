-- Trigger functions do not need direct execution by API clients.
-- Both functions use public-qualified relations or pg_catalog built-ins.
BEGIN;
ALTER FUNCTION public.handle_new_user() SET search_path = '';
ALTER FUNCTION public.update_updated_at_column() SET search_path = '';
REVOKE EXECUTE ON FUNCTION public.handle_new_user() FROM PUBLIC, anon, authenticated;

-- The scheduler uses the service role, which bypasses RLS. Its old permissive
-- policy also let anonymous callers insert alerts for any user. Keep the
-- existing ownership policy for normal user inserts.
DROP POLICY IF EXISTS "Service can insert alerts" ON public.alert_history;
COMMIT;
