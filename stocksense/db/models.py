"""
Database models for StockSense.

Note: With Supabase migration, SQLAlchemy models are no longer used.
This file is kept for reference and potential future local testing.

The actual schema is defined in supabase/schema.sql and migrations.
"""

# Legacy SQLAlchemy model - kept for reference only
# The actual table is now in Supabase (see supabase/migrations/003_analysis_cache.sql)

ANALYSIS_CACHE_SCHEMA = """
-- Supabase table: analysis_cache
-- 
-- Columns:
--   id: BIGSERIAL PRIMARY KEY
--   ticker: TEXT NOT NULL
--   analysis_summary: TEXT
--   sentiment_report: TEXT
--   price_data: JSONB
--   headlines: JSONB
--   reasoning_steps: JSONB
--   tools_used: JSONB
--   iterations: INTEGER
--   overall_sentiment: TEXT
--   overall_confidence: DECIMAL(3,2)
--   confidence_reasoning: TEXT
--   headline_analyses: JSONB
--   key_themes: JSONB
--   potential_impact: TEXT
--   risks_identified: JSONB
--   information_gaps: JSONB
--   skeptic_report: TEXT
--   skeptic_sentiment: TEXT
--   skeptic_confidence: DECIMAL(3,2)
--   primary_disagreement: TEXT
--   critiques: JSONB
--   bear_cases: JSONB
--   hidden_risks: JSONB
--   would_change_mind: JSONB
--   fundamental_data: JSONB
--   created_at: TIMESTAMPTZ
--   updated_at: TIMESTAMPTZ
"""