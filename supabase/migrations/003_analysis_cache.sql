-- Migration: Add analysis_cache table to Supabase
-- This replaces the local SQLite cache with Supabase storage
-- Run this in Supabase SQL Editor

-- ============================================
-- ANALYSIS CACHE (replaces SQLite)
-- ============================================
-- Public cache for stock analysis results
-- No RLS - accessible by all users (cached analyses are public)

CREATE TABLE IF NOT EXISTS analysis_cache (
    id BIGSERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    analysis_summary TEXT,
    sentiment_report TEXT,
    
    -- JSON-serialized data
    price_data JSONB DEFAULT '[]'::jsonb,
    headlines JSONB DEFAULT '[]'::jsonb,
    reasoning_steps JSONB DEFAULT '[]'::jsonb,
    tools_used JSONB DEFAULT '[]'::jsonb,
    
    -- Analysis metadata
    iterations INTEGER DEFAULT 0,
    
    -- Structured sentiment analysis (Stage 1)
    overall_sentiment TEXT,
    overall_confidence DECIMAL(3, 2),
    confidence_reasoning TEXT,
    headline_analyses JSONB DEFAULT '[]'::jsonb,
    key_themes JSONB DEFAULT '[]'::jsonb,
    potential_impact TEXT,
    risks_identified JSONB DEFAULT '[]'::jsonb,
    information_gaps JSONB DEFAULT '[]'::jsonb,
    
    -- Skeptic analysis (Stage 2)
    skeptic_report TEXT,
    skeptic_sentiment TEXT,
    skeptic_confidence DECIMAL(3, 2),
    primary_disagreement TEXT,
    critiques JSONB DEFAULT '[]'::jsonb,
    bear_cases JSONB DEFAULT '[]'::jsonb,
    hidden_risks JSONB DEFAULT '[]'::jsonb,
    would_change_mind JSONB DEFAULT '[]'::jsonb,
    
    -- Fundamental data
    fundamental_data JSONB DEFAULT '{}'::jsonb,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast ticker lookups
CREATE INDEX IF NOT EXISTS idx_analysis_cache_ticker ON analysis_cache(ticker);
CREATE INDEX IF NOT EXISTS idx_analysis_cache_ticker_created ON analysis_cache(ticker, created_at DESC);

-- Updated_at trigger
CREATE TRIGGER update_analysis_cache_updated_at
    BEFORE UPDATE ON analysis_cache
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- PUBLIC ACCESS POLICY
-- ============================================
-- Analysis cache is public - anyone can read/write
-- This allows anonymous users to benefit from cached analyses

ALTER TABLE analysis_cache ENABLE ROW LEVEL SECURITY;

-- Allow anyone to read cached analyses
CREATE POLICY "Anyone can read analysis cache" ON analysis_cache
    FOR SELECT USING (true);

-- Allow backend to insert (using service key or anon key)
CREATE POLICY "Anyone can insert analysis cache" ON analysis_cache
    FOR INSERT WITH CHECK (true);

-- Allow backend to delete (using service key)
CREATE POLICY "Anyone can delete analysis cache" ON analysis_cache
    FOR DELETE USING (true);

-- Note: For production, you may want to restrict write access
-- to only authenticated service roles by checking:
-- auth.role() = 'service_role' OR auth.role() = 'authenticated'
