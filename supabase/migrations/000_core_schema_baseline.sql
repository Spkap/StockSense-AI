-- Core StockSense schema baseline.
--
-- This migration intentionally precedes the existing numbered migrations.
-- Migrations 001+ assume these user/thesis tables already exist, so the
-- baseline must be replayable before stage-specific migrations on a fresh DB.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- USER PROFILES
-- ============================================
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email TEXT,
    display_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS email TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS display_name TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS avatar_url TEXT;
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.profiles (id, email, display_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', split_part(NEW.email, '@', 1))
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- ============================================
-- POSITIONS
-- ============================================
CREATE TABLE IF NOT EXISTS public.positions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
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

ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS ticker TEXT;
ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS position_type TEXT DEFAULT 'watching';
ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS entry_date DATE;
ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS entry_price DECIMAL(12, 4);
ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS current_shares DECIMAL(12, 4);
ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.positions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

DO $$
BEGIN
    ALTER TABLE public.positions
        ADD CONSTRAINT positions_position_type_check
        CHECK (position_type IN ('long', 'short', 'watching'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================
-- THESES
-- ============================================
CREATE TABLE IF NOT EXISTS public.theses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    position_id UUID REFERENCES public.positions(id) ON DELETE CASCADE,
    ticker TEXT NOT NULL,
    thesis_summary TEXT NOT NULL,
    conviction_level TEXT CHECK (conviction_level IN ('high', 'medium', 'low')) DEFAULT 'medium',
    kill_criteria TEXT[],
    origin_analysis_id INTEGER,
    origin_analysis_snapshot JSONB,
    time_horizon TEXT CHECK (time_horizon IN ('short', 'medium', 'long')) DEFAULT 'medium',
    thesis_type TEXT CHECK (thesis_type IN ('growth', 'value', 'income', 'turnaround', 'special_situation')) DEFAULT 'growth',
    status TEXT CHECK (status IN ('active', 'validated', 'invalidated', 'exited')) DEFAULT 'active',
    invalidation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS position_id UUID REFERENCES public.positions(id) ON DELETE CASCADE;
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS ticker TEXT;
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS thesis_summary TEXT;
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS conviction_level TEXT DEFAULT 'medium';
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS kill_criteria TEXT[];
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS origin_analysis_id INTEGER;
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS origin_analysis_snapshot JSONB;
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS time_horizon TEXT DEFAULT 'medium';
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS thesis_type TEXT DEFAULT 'growth';
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'active';
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS invalidation_reason TEXT;
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();
ALTER TABLE public.theses ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ DEFAULT NOW();

DO $$
BEGIN
    ALTER TABLE public.theses
        ADD CONSTRAINT theses_conviction_level_check
        CHECK (conviction_level IN ('high', 'medium', 'low'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE public.theses
        ADD CONSTRAINT theses_time_horizon_check
        CHECK (time_horizon IN ('short', 'medium', 'long'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE public.theses
        ADD CONSTRAINT theses_thesis_type_check
        CHECK (thesis_type IN ('growth', 'value', 'income', 'turnaround', 'special_situation'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

DO $$
BEGIN
    ALTER TABLE public.theses
        ADD CONSTRAINT theses_status_check
        CHECK (status IN ('active', 'validated', 'invalidated', 'exited'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================
-- THESIS HISTORY
-- ============================================
CREATE TABLE IF NOT EXISTS public.thesis_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    thesis_id UUID NOT NULL REFERENCES public.theses(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES public.profiles(id) ON DELETE CASCADE,
    thesis_summary TEXT NOT NULL,
    conviction_level TEXT,
    kill_criteria TEXT[],
    change_reason TEXT,
    change_type TEXT CHECK (change_type IN ('created', 'updated', 'conviction_changed', 'invalidated', 'exited')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.thesis_history ADD COLUMN IF NOT EXISTS thesis_summary TEXT;
ALTER TABLE public.thesis_history ADD COLUMN IF NOT EXISTS conviction_level TEXT;
ALTER TABLE public.thesis_history ADD COLUMN IF NOT EXISTS kill_criteria TEXT[];
ALTER TABLE public.thesis_history ADD COLUMN IF NOT EXISTS change_reason TEXT;
ALTER TABLE public.thesis_history ADD COLUMN IF NOT EXISTS change_type TEXT;
ALTER TABLE public.thesis_history ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT NOW();

DO $$
BEGIN
    ALTER TABLE public.thesis_history
        ADD CONSTRAINT thesis_history_change_type_check
        CHECK (change_type IN ('created', 'updated', 'conviction_changed', 'invalidated', 'exited'));
EXCEPTION
    WHEN duplicate_object THEN NULL;
END $$;

-- ============================================
-- RLS POLICIES
-- ============================================
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.theses ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.thesis_history ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own profile" ON public.profiles;
CREATE POLICY "Users can view own profile" ON public.profiles
    FOR SELECT USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON public.profiles;
CREATE POLICY "Users can update own profile" ON public.profiles
    FOR UPDATE USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can view own positions" ON public.positions;
CREATE POLICY "Users can view own positions" ON public.positions
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own positions" ON public.positions;
CREATE POLICY "Users can insert own positions" ON public.positions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own positions" ON public.positions;
CREATE POLICY "Users can update own positions" ON public.positions
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own positions" ON public.positions;
CREATE POLICY "Users can delete own positions" ON public.positions
    FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view own theses" ON public.theses;
CREATE POLICY "Users can view own theses" ON public.theses
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own theses" ON public.theses;
CREATE POLICY "Users can insert own theses" ON public.theses
    FOR INSERT WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can update own theses" ON public.theses;
CREATE POLICY "Users can update own theses" ON public.theses
    FOR UPDATE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can delete own theses" ON public.theses;
CREATE POLICY "Users can delete own theses" ON public.theses
    FOR DELETE USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can view own thesis history" ON public.thesis_history;
CREATE POLICY "Users can view own thesis history" ON public.thesis_history
    FOR SELECT USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "Users can insert own thesis history" ON public.thesis_history;
CREATE POLICY "Users can insert own thesis history" ON public.thesis_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- ============================================
-- INDEXES AND TRIGGERS
-- ============================================
CREATE INDEX IF NOT EXISTS idx_positions_user_id ON public.positions(user_id);
CREATE INDEX IF NOT EXISTS idx_positions_ticker ON public.positions(ticker);
CREATE INDEX IF NOT EXISTS idx_theses_user_id ON public.theses(user_id);
CREATE INDEX IF NOT EXISTS idx_theses_ticker ON public.theses(ticker);
CREATE INDEX IF NOT EXISTS idx_theses_status ON public.theses(status);
CREATE INDEX IF NOT EXISTS idx_thesis_history_thesis_id ON public.thesis_history(thesis_id);

CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_positions_updated_at ON public.positions;
CREATE TRIGGER update_positions_updated_at
    BEFORE UPDATE ON public.positions
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();

DROP TRIGGER IF EXISTS update_theses_updated_at ON public.theses;
CREATE TRIGGER update_theses_updated_at
    BEFORE UPDATE ON public.theses
    FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();
