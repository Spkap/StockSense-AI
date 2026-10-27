-- Keep the latest debate alongside the research it belongs to. Existing rows
-- remain unchanged, and deletion of research removes its attached debate.
ALTER TABLE public.analysis_cache ADD COLUMN IF NOT EXISTS debate_result jsonb;
ALTER TABLE public.user_analysis_cache ADD COLUMN IF NOT EXISTS debate_result jsonb;
