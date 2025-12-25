-- ============================================
-- StockSense Migration: Stage 4 Features
-- Run this in Supabase SQL Editor
-- ============================================

-- 1. Add origin_analysis columns to theses table (Feature 2)
ALTER TABLE theses 
ADD COLUMN IF NOT EXISTS origin_analysis_id INTEGER,
ADD COLUMN IF NOT EXISTS origin_analysis_snapshot JSONB;

-- Add comment for documentation
COMMENT ON COLUMN theses.origin_analysis_id IS 'SQLite cache ID when thesis was created';
COMMENT ON COLUMN theses.origin_analysis_snapshot IS 'Snapshot of key metrics at thesis creation: {sentiment, confidence, key_themes, skeptic_verdict, timestamp}';


-- 2. Create kill_alerts table (Feature 1)
CREATE TABLE IF NOT EXISTS kill_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thesis_id UUID NOT NULL REFERENCES theses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    
    -- What triggered the alert
    triggered_criteria TEXT NOT NULL,
    triggering_signal TEXT NOT NULL,
    match_confidence DECIMAL(3, 2),
    
    -- Analysis context
    analysis_sentiment TEXT,
    analysis_confidence DECIMAL(3, 2),
    analysis_summary TEXT,
    
    -- Alert status
    status TEXT CHECK (status IN ('pending', 'dismissed', 'acknowledged', 'acted')) DEFAULT 'pending',
    user_action TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);


-- 3. Enable RLS on kill_alerts
ALTER TABLE kill_alerts ENABLE ROW LEVEL SECURITY;


-- 4. Create RLS policies for kill_alerts (idempotent)
DROP POLICY IF EXISTS "Users can view own kill alerts" ON kill_alerts;
CREATE POLICY "Users can view own kill alerts" ON kill_alerts
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own kill alerts" ON kill_alerts;
CREATE POLICY "Users can insert own kill alerts" ON kill_alerts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own kill alerts" ON kill_alerts;
CREATE POLICY "Users can update own kill alerts" ON kill_alerts
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own kill alerts" ON kill_alerts;
CREATE POLICY "Users can delete own kill alerts" ON kill_alerts
    FOR DELETE USING (auth.uid() = user_id);


-- 5. Create indexes for kill_alerts
CREATE INDEX IF NOT EXISTS idx_kill_alerts_user_id ON kill_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_kill_alerts_thesis_id ON kill_alerts(thesis_id);
CREATE INDEX IF NOT EXISTS idx_kill_alerts_ticker ON kill_alerts(ticker);
CREATE INDEX IF NOT EXISTS idx_kill_alerts_status ON kill_alerts(status);


-- Verify migration
SELECT 'Migration complete!' as status;
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'theses' 
AND column_name IN ('origin_analysis_id', 'origin_analysis_snapshot');
