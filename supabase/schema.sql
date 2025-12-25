-- StockSense Database Schema
-- Stage 3: User Belief System
-- Run this in Supabase SQL Editor

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USER PROFILES
-- ============================================
-- Extends Supabase auth.users with app-specific data
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Auto-create profile when user signs up
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger for new user signup
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- ============================================
-- POSITIONS (Watchlist with context)
-- ============================================
CREATE TABLE IF NOT EXISTS positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    position_type TEXT CHECK (position_type IN ('long', 'short', 'watching')) DEFAULT 'watching',
    entry_date DATE,
    entry_price DECIMAL(12, 4),
    current_shares DECIMAL(12, 4),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(user_id, ticker)
);

-- ============================================
-- THESES (Investment theses with kill criteria)
-- ============================================
CREATE TABLE IF NOT EXISTS theses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    position_id UUID REFERENCES positions(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    
    -- Core thesis
    thesis_summary TEXT NOT NULL,  -- "Why I own this"
    conviction_level TEXT CHECK (conviction_level IN ('high', 'medium', 'low')) DEFAULT 'medium',
    
    -- Kill criteria (Stage 3 core feature)
    kill_criteria TEXT[],  -- Array of conditions that would trigger exit
    
    -- Analysis-Thesis Linkage (Stage 4)
    origin_analysis_id INTEGER,               -- SQLite cache ID when thesis was created
    origin_analysis_snapshot JSONB,           -- Snapshot of key metrics at thesis creation
    -- Snapshot includes: {sentiment, confidence, key_themes, skeptic_verdict, timestamp}
    
    -- Thesis metadata
    time_horizon TEXT CHECK (time_horizon IN ('short', 'medium', 'long')) DEFAULT 'medium',
    thesis_type TEXT CHECK (thesis_type IN ('growth', 'value', 'income', 'turnaround', 'special_situation')) DEFAULT 'growth',
    
    -- Status tracking
    status TEXT CHECK (status IN ('active', 'validated', 'invalidated', 'exited')) DEFAULT 'active',
    invalidation_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- THESIS HISTORY (Track belief evolution)
-- ============================================
CREATE TABLE IF NOT EXISTS thesis_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thesis_id UUID NOT NULL REFERENCES theses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    
    -- Snapshot of thesis at this point
    thesis_summary TEXT NOT NULL,
    conviction_level TEXT,
    kill_criteria TEXT[],
    
    -- What changed
    change_reason TEXT,
    change_type TEXT CHECK (change_type IN ('created', 'updated', 'conviction_changed', 'invalidated', 'exited')),
    
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- KILL ALERTS (Kill criteria monitoring - Stage 4)
-- ============================================
-- Alerts generated when analysis results may trigger kill criteria
CREATE TABLE IF NOT EXISTS kill_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thesis_id UUID NOT NULL REFERENCES theses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    
    -- What triggered the alert
    triggered_criteria TEXT NOT NULL,           -- The kill criteria text that was matched
    triggering_signal TEXT NOT NULL,            -- The signal from analysis that matched
    match_confidence DECIMAL(3, 2),             -- 0.00-1.00 confidence in the match
    
    -- Analysis context
    analysis_sentiment TEXT,                    -- Sentiment at time of alert
    analysis_confidence DECIMAL(3, 2),          -- Confidence at time of alert
    analysis_summary TEXT,                      -- Brief summary for context
    
    -- Alert status
    status TEXT CHECK (status IN ('pending', 'dismissed', 'acknowledged', 'acted')) DEFAULT 'pending',
    user_action TEXT,                           -- What action user took (if any)
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);

-- ============================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================
-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE theses ENABLE ROW LEVEL SECURITY;
ALTER TABLE thesis_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE kill_alerts ENABLE ROW LEVEL SECURITY;

-- Profiles: Users can only see/edit their own profile
CREATE POLICY "Users can view own profile" ON profiles
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON profiles
    FOR UPDATE USING (auth.uid() = id);

-- Positions: Users can only see/edit their own positions
CREATE POLICY "Users can view own positions" ON positions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own positions" ON positions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own positions" ON positions
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own positions" ON positions
    FOR DELETE USING (auth.uid() = user_id);

-- Theses: Users can only see/edit their own theses
CREATE POLICY "Users can view own theses" ON theses
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own theses" ON theses
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own theses" ON theses
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own theses" ON theses
    FOR DELETE USING (auth.uid() = user_id);

-- Thesis History: Users can only see their own history
CREATE POLICY "Users can view own thesis history" ON thesis_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own thesis history" ON thesis_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Kill Alerts: Users can see/manage their own alerts
CREATE POLICY "Users can view own kill alerts" ON kill_alerts
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own kill alerts" ON kill_alerts
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own kill alerts" ON kill_alerts
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own kill alerts" ON kill_alerts
    FOR DELETE USING (auth.uid() = user_id);

-- ============================================
-- INDEXES for performance
-- ============================================
CREATE INDEX IF NOT EXISTS idx_positions_user_id ON positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_ticker ON positions(ticker);
CREATE INDEX IF NOT EXISTS idx_theses_user_id ON theses(user_id);
CREATE INDEX IF NOT EXISTS idx_theses_ticker ON theses(ticker);
CREATE INDEX IF NOT EXISTS idx_theses_status ON theses(status);
CREATE INDEX IF NOT EXISTS idx_thesis_history_thesis_id ON thesis_history(thesis_id);
CREATE INDEX IF NOT EXISTS idx_kill_alerts_user_id ON kill_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_kill_alerts_thesis_id ON kill_alerts(thesis_id);
CREATE INDEX IF NOT EXISTS idx_kill_alerts_ticker ON kill_alerts(ticker);
CREATE INDEX IF NOT EXISTS idx_kill_alerts_status ON kill_alerts(status);

-- ============================================
-- UPDATED_AT TRIGGER
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON positions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_theses_updated_at
    BEFORE UPDATE ON theses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
