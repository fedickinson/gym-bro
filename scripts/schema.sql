-- Gym Bro Database Schema for Supabase (Postgres)
-- Run this in Supabase SQL Editor to create tables

-- ============================================================================
-- WORKOUT LOGS
-- ============================================================================
CREATE TABLE workout_logs (
    -- Primary fields
    id TEXT PRIMARY KEY,
    date DATE NOT NULL,
    type TEXT NOT NULL,
    template_id TEXT,

    -- Nested data (JSONB preserves current JSON structure)
    exercises JSONB NOT NULL DEFAULT '[]',
    warmup JSONB,
    supplementary_work JSONB,

    -- Simple fields
    notes TEXT,
    completed BOOLEAN DEFAULT TRUE,
    session_id TEXT,

    -- Soft delete
    deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for fast queries
CREATE INDEX idx_workout_logs_date ON workout_logs(date DESC);
CREATE INDEX idx_workout_logs_type ON workout_logs(type);
CREATE INDEX idx_workout_logs_deleted ON workout_logs(deleted) WHERE deleted = FALSE;
CREATE INDEX idx_workout_logs_exercises_gin ON workout_logs USING GIN (exercises);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_workout_logs_updated_at
    BEFORE UPDATE ON workout_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- TEMPLATES
-- ============================================================================
CREATE TABLE templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    exercises JSONB NOT NULL DEFAULT '[]',
    supersets JSONB DEFAULT '[]',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_templates_type ON templates(type);

-- ============================================================================
-- WEEKLY SPLIT
-- ============================================================================
CREATE TABLE weekly_split (
    id SERIAL PRIMARY KEY,
    config JSONB NOT NULL,
    current_week JSONB NOT NULL,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TRIGGER update_weekly_split_updated_at
    BEFORE UPDATE ON weekly_split
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- EXERCISES
-- ============================================================================
CREATE TABLE exercises (
    canonical_name TEXT PRIMARY KEY,
    variations JSONB DEFAULT '[]',
    muscle_groups JSONB DEFAULT '[]',
    equipment JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_exercises_muscle_groups ON exercises USING GIN (muscle_groups);
CREATE INDEX idx_exercises_equipment ON exercises USING GIN (equipment);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these after migration to verify data:

-- SELECT COUNT(*) FROM workout_logs WHERE deleted = FALSE;
-- SELECT COUNT(*) FROM templates;
-- SELECT * FROM weekly_split;
-- SELECT COUNT(*) FROM exercises;
