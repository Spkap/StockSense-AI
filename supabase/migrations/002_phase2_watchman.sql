-- Create alert_history table for Phase 2: The Watchman Update
CREATE TABLE IF NOT EXISTS public.alert_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id),
    thesis_id UUID NOT NULL REFERENCES public.theses(id),
    ticker TEXT NOT NULL,
    alert_type TEXT NOT NULL DEFAULT 'kill_criteria', -- 'kill_criteria', 'price_movement', 'news_sentiment'
    message TEXT NOT NULL,
    data JSONB DEFAULT '{}'::jsonb, -- Stores full context (triggered criteria, signal, confidence)
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.alert_history ENABLE ROW LEVEL SECURITY;

-- Policy: Users can see their own alerts
CREATE POLICY "Users can view their own alerts" 
    ON public.alert_history FOR SELECT 
    USING (auth.uid() = user_id);

-- Policy: Service role can insert alerts (for background jobs)
-- Note: In Supabase, the service role bypasses RLS, so explicit insert policy for users isn't strictly needed for background jobs,
-- but if we want users to create alerts (e.g. manual trigger), we might need it. 
-- For now, we assume alerts are system-generated or background-generated.
