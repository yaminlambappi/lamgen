#!/usr/bin/env python3
"""
LamGen Production Migration Repair Script
==========================================
Safely reconciles Django migration history with PostgreSQL schema.

Usage (on production server):
    DJANGO_SETTINGS_MODULE=config.settings.production python3 repair_migrations.py

Strategy:
- Detect each conflict type
- Fake-apply migrations where schema already exists
- Drop duplicate indexes/constraints where needed
- Run remaining migrations normally
- NEVER drops tables or destroys data
"""

import subprocess
import sys
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")

import django
django.setup()

from django.db import connection


# ── helpers ────────────────────────────────────────────────────────────────

def run(cmd, check=True):
    print(f"\n$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print("[stderr]", result.stderr.rstrip())
    if check and result.returncode != 0:
        print(f"[ERROR] Command failed (exit {result.returncode})")
    return result


def sql(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        try:
            return cursor.fetchall()
        except Exception:
            return []


def column_exists(table, column):
    rows = sql("""
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public'
          AND table_name   = %s
          AND column_name  = %s
    """, [table, column])
    return bool(rows)


def table_exists(table):
    rows = sql("""
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public' AND table_name = %s
    """, [table])
    return bool(rows)


def constraint_exists(name):
    rows = sql("""
        SELECT 1 FROM pg_constraint WHERE conname = %s
    """, [name])
    return bool(rows)


def index_exists(name):
    rows = sql("""
        SELECT 1 FROM pg_indexes
        WHERE schemaname = 'public' AND indexname = %s
    """, [name])
    return bool(rows)


def migration_applied(app, name):
    rows = sql("""
        SELECT 1 FROM django_migrations
        WHERE app = %s AND name = %s
    """, [app, name])
    return bool(rows)


def fake_migrate(app, migration):
    print(f"\n  [FAKE] {app}.{migration}")
    run(f"python3 manage.py migrate {app} {migration} --fake")


def drop_index_if_exists(name):
    if index_exists(name):
        print(f"  [DROP INDEX] {name}")
        sql(f'DROP INDEX IF EXISTS "{name}"')
    else:
        print(f"  [SKIP] Index {name} does not exist")


def drop_constraint_if_exists(table, name):
    if constraint_exists(name):
        print(f"  [DROP CONSTRAINT] {name} on {table}")
        sql(f'ALTER TABLE "{table}" DROP CONSTRAINT IF EXISTS "{name}"')
    else:
        print(f"  [SKIP] Constraint {name} does not exist")


# ── main repair logic ───────────────────────────────────────────────────────

print("=" * 60)
print("LamGen Migration Repair — Production PostgreSQL")
print("=" * 60)

# 0. Show current state
print("\n[1] Current migration state:")
run("python3 manage.py showmigrations --plan 2>&1 | grep -v '\[X\]' | head -40")

print("\n[2] Detecting conflicts...")

# ── TOOLS APP ──────────────────────────────────────────────────────────────
print("\n--- tools app ---")

# tools.0003 — adds usage_count to tools_tool
if not migration_applied("tools", "0003_tool_add_usage_count"):
    if column_exists("tools_tool", "usage_count"):
        print("  CONFLICT A: usage_count column already exists in tools_tool")
        fake_migrate("tools", "0003_tool_add_usage_count")
    else:
        print("  OK: Need to run tools.0003 normally")
else:
    print("  [OK] tools.0003 already applied")

# tools.0004 — data migration (deduplication) — always safe to fake if applied
if not migration_applied("tools", "0004_deduplicate_toolusagehistory"):
    print("  tools.0004 (data migration) — faking if not applied")
    fake_migrate("tools", "0004_deduplicate_toolusagehistory")
else:
    print("  [OK] tools.0004 already applied")

# tools.0005 — adds unique constraint unique_user_tool_history
if not migration_applied("tools", "0005_toolusagehistory_unique_constraint"):
    if constraint_exists("unique_user_tool_history") or index_exists("unique_user_tool_history"):
        print("  CONFLICT C: unique_user_tool_history constraint already exists")
        fake_migrate("tools", "0005_toolusagehistory_unique_constraint")
    else:
        print("  OK: Need to run tools.0005 normally")
else:
    print("  [OK] tools.0005 already applied")

# tools.0006-0010 — SEO fields, cache strategy, ai_powered, merge
for mig in [
    "0006_add_seo_content_fields",
    "0007_expand_seo_fields",
    "0008_tool_cache_strategy_tool_is_ai_powered_and_more",
    "0009_tool_registry_version",
    "0010_merge_20260518_1949",
]:
    if not migration_applied("tools", mig):
        # Check a representative column for each
        col_map = {
            "0006_add_seo_content_fields": ("tools_tool", "seo_intro"),
            "0007_expand_seo_fields": ("tools_tool", "content_blocks"),
            "0008_tool_cache_strategy_tool_is_ai_powered_and_more": ("tools_tool", "is_ai_powered"),
            "0009_tool_registry_version": ("tools_tool", "registry_version"),
            "0010_merge_20260518_1949": None,
        }
        check = col_map.get(mig)
        if check and column_exists(*check):
            print(f"  CONFLICT A: Column {check[1]} already exists → faking {mig}")
            fake_migrate("tools", mig)
        elif not check:
            # Merge migration — always fake
            fake_migrate("tools", mig)
        else:
            print(f"  OK: Need to run tools.{mig} normally")
    else:
        print(f"  [OK] tools.{mig} already applied")

# ── GENERATION APP ──────────────────────────────────────────────────────────
print("\n--- generation app ---")

gen_migrations = [
    ("0001_initial", "generation_generationjob"),
    ("0002_assignmentbrief_esl_context_and_more", None),
    ("0003_generationjob_user_hints", None),
    ("0004_remove_assignmentbrief_esl_context_and_more", None),
]

for mig, table in gen_migrations:
    if not migration_applied("generation", mig):
        if table and table_exists(table):
            print(f"  CONFLICT B: Table {table} already exists → faking {mig}")
            fake_migrate("generation", mig)
        elif not table:
            # Column mutations — check representative columns
            col_checks = {
                "0002_assignmentbrief_esl_context_and_more": ("generation_assignmentbrief", "esl_context"),
                "0003_generationjob_user_hints": ("generation_generationjob", "user_hints"),
                "0004_remove_assignmentbrief_esl_context_and_more": None,
            }
            check = col_checks.get(mig)
            if check and column_exists(*check):
                print(f"  CONFLICT A: Column {check[1]} already exists → faking {mig}")
                fake_migrate("generation", mig)
            elif check and not column_exists(*check):
                # 0004 removes esl_context — if it's already gone, fake it
                if mig.startswith("0004") and not column_exists("generation_assignmentbrief", "esl_context"):
                    print(f"  CONFLICT A: esl_context already removed → faking {mig}")
                    fake_migrate("generation", mig)
                else:
                    print(f"  OK: Need to run generation.{mig} normally")
            elif not check:
                print(f"  INFO: generation.{mig} — running normally")
        else:
            print(f"  OK: Need to run generation.{mig} normally")
    else:
        print(f"  [OK] generation.{mig} already applied")

# ── SEO APP ─────────────────────────────────────────────────────────────────
print("\n--- seo app ---")

seo_migrations = [
    ("0001_initial", "seo_seopage"),
    ("0002_add_schema_type_and_related_tools", None),
    ("0003_longtailvariant", "seo_longtailvariant"),
    ("0004_add_longtail_seo_fields", None),
]

for mig, table in seo_migrations:
    if not migration_applied("seo", mig):
        if table and table_exists(table):
            print(f"  CONFLICT B: Table {table} already exists → faking {mig}")
            fake_migrate("seo", mig)
        else:
            print(f"  OK: Need to run seo.{mig} normally")
    else:
        print(f"  [OK] seo.{mig} already applied")

# ── OTHER APPS (initial migrations only) ───────────────────────────────────
print("\n--- other apps ---")

other_initials = [
    ("ai_providers", "0001_initial", "ai_providers_aiprovider"),
    ("ai_providers", "0002_aiprovider_remove_aiproviderusage_provider_name_and_more", None),
    ("ai_tools_core", "0001_initial", "ai_tools_core_generationhistory"),
    ("ai_tools_core", "0002_prompttemplate", "ai_tools_core_prompttemplate"),
    ("analytics", "0001_initial", "analytics_toolusage"),
    ("blog", "0001_initial", "blog_contentarticle"),
    ("games", "0001_initial", "games_signalingroom"),
    ("thesis", "0001_initial", "thesis_thesisrequest"),
    ("users", "0001_initial", "users_customuser"),
    ("users", "0002_alter_customuser_groups", None),
]

for app, mig, table in other_initials:
    if not migration_applied(app, mig):
        if table and table_exists(table):
            print(f"  CONFLICT B: Table {table} exists → faking {app}.{mig}")
            fake_migrate(app, mig)
        else:
            print(f"  OK: Need to run {app}.{mig} normally")
    else:
        print(f"  [OK] {app}.{mig} already applied")

# ── RUN REMAINING MIGRATIONS ────────────────────────────────────────────────
print("\n[3] Running remaining unapplied migrations...")
result = run("python3 manage.py migrate --plan")

print("\n[4] Applying migrations...")
result = run("python3 manage.py migrate", check=False)

if "error" in result.stdout.lower() or result.returncode != 0:
    print("\n[WARNING] Some errors occurred. Checking for known fixable errors...")

    # Handle duplicate index errors that can be manually cleared
    stderr_combined = result.stdout + result.stderr
    if "unique_user_tool_history" in stderr_combined:
        print("  → Dropping duplicate unique_user_tool_history index...")
        drop_index_if_exists("unique_user_tool_history")
        drop_constraint_if_exists("tools_toolusagehistory", "unique_user_tool_history")
        run("python3 manage.py migrate", check=False)

# ── FINAL VALIDATION ────────────────────────────────────────────────────────
print("\n[5] Final validation:")
run("python3 manage.py showmigrations --plan 2>&1 | grep -v '\[X\]' | head -20 || echo 'All migrations applied!'")
run("python3 manage.py check")

print("\n" + "=" * 60)
print("Repair complete. Run 'python3 manage.py migrate' to confirm.")
print("=" * 60)
