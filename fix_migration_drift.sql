-- LamGen PostgreSQL Migration Drift — Manual SQL Fixes
-- Run these on your Postgres server BEFORE running repair_migrations.py
-- Safe to run: all statements are IF EXISTS (no-ops if already clean)

-- ================================================================
-- 1. tools app — duplicate column / constraint conflicts
-- ================================================================

-- Add usage_count if missing (migration 0003)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='tools_tool' AND column_name='usage_count'
    ) THEN
        ALTER TABLE tools_tool ADD COLUMN usage_count bigint NOT NULL DEFAULT 0;
        RAISE NOTICE 'Added usage_count to tools_tool';
    ELSE
        RAISE NOTICE 'usage_count already exists — skipping';
    END IF;
END $$;

-- Drop duplicate unique constraint if it exists with wrong name
DROP INDEX IF EXISTS unique_user_tool_history;

-- Re-create it cleanly (only if constraint doesn't exist yet)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'unique_user_tool_history'
    ) THEN
        CREATE UNIQUE INDEX unique_user_tool_history
            ON tools_toolusagehistory (user_id, tool_id)
            WHERE user_id IS NOT NULL;
        RAISE NOTICE 'Created unique_user_tool_history index';
    ELSE
        RAISE NOTICE 'unique_user_tool_history already exists — skipping';
    END IF;
END $$;

-- ================================================================
-- 2. tools app — SEO fields (migrations 0006, 0007)
-- ================================================================

DO $$
DECLARE cols TEXT[] := ARRAY[
    'seo_intro', 'use_cases', 'faq_items', 'canonical_url',
    'content_blocks', 'examples', 'keywords', 'last_content_update',
    'og_image', 'schema_type', 'searchable_tags', 'word_count_target'
];
col TEXT;
BEGIN
    FOREACH col IN ARRAY cols LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name='tools_tool' AND column_name=col
        ) THEN
            EXECUTE format('ALTER TABLE tools_tool ADD COLUMN %I TEXT', col);
            RAISE NOTICE 'Added % to tools_tool', col;
        END IF;
    END LOOP;
END $$;

-- ================================================================
-- 3. tools app — AI/cache fields (migration 0008)
-- ================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='tools_tool' AND column_name='is_ai_powered'
    ) THEN
        ALTER TABLE tools_tool ADD COLUMN is_ai_powered boolean NOT NULL DEFAULT false;
        RAISE NOTICE 'Added is_ai_powered to tools_tool';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='tools_tool' AND column_name='cache_strategy'
    ) THEN
        ALTER TABLE tools_tool ADD COLUMN cache_strategy varchar(20) NOT NULL DEFAULT 'standard';
        RAISE NOTICE 'Added cache_strategy to tools_tool';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='tools_tool' AND column_name='is_trending'
    ) THEN
        ALTER TABLE tools_tool ADD COLUMN is_trending boolean NOT NULL DEFAULT false;
        RAISE NOTICE 'Added is_trending to tools_tool';
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='tools_tool' AND column_name='search_priority'
    ) THEN
        ALTER TABLE tools_tool ADD COLUMN search_priority integer NOT NULL DEFAULT 0;
        RAISE NOTICE 'Added search_priority to tools_tool';
    END IF;
END $$;

-- ================================================================
-- 4. tools app — registry_version (migration 0009)
-- ================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='tools_tool' AND column_name='registry_version'
    ) THEN
        ALTER TABLE tools_tool ADD COLUMN registry_version varchar(20);
        RAISE NOTICE 'Added registry_version to tools_tool';
    END IF;
END $$;

-- ================================================================
-- 5. generation app — column drift fixes
-- ================================================================

-- esl_context (added in 0002, removed in 0004)
-- If column still exists and 0004 hasn't run, remove it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='generation_assignmentbrief' AND column_name='esl_context'
    ) THEN
        RAISE NOTICE 'esl_context still present — it will be removed by migration 0004 when faked';
    END IF;
END $$;

-- assignment_type_hint (added in 0002)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='generation_assignmentbrief' AND column_name='assignment_type_hint'
    ) THEN
        ALTER TABLE generation_assignmentbrief ADD COLUMN assignment_type_hint varchar(50);
        RAISE NOTICE 'Added assignment_type_hint to generation_assignmentbrief';
    END IF;
END $$;

-- user_hints (added in 0003)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name='generation_generationjob' AND column_name='user_hints'
    ) THEN
        ALTER TABLE generation_generationjob ADD COLUMN user_hints text;
        RAISE NOTICE 'Added user_hints to generation_generationjob';
    END IF;
END $$;

-- ================================================================
-- 6. Verify final state
-- ================================================================
SELECT
    table_name,
    COUNT(*) AS column_count
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('tools_tool', 'tools_toolusagehistory', 'generation_generationjob', 'generation_assignmentbrief')
GROUP BY table_name
ORDER BY table_name;
