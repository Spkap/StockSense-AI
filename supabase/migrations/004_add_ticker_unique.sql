-- Migration: Add unique constraint on ticker for upsert support (P2-E)
--
-- Required for: database.py save_analysis .upsert(data, on_conflict="ticker")
-- Without this constraint, upsert falls back to insert behaviour.

ALTER TABLE analysis_cache DROP CONSTRAINT IF EXISTS analysis_cache_ticker_key;
ALTER TABLE analysis_cache ADD CONSTRAINT analysis_cache_ticker_key UNIQUE (ticker);
