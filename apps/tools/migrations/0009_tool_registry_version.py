"""
Migration 0009: Add registry_version to tools_tool.

Uses RunSQL with ADD COLUMN IF NOT EXISTS so it is safe to apply:
  - on the server (which may not have migration 0008 yet)
  - locally (where the column may already exist from a previous attempt)

Depends on 0007 (the last migration present on all environments).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        # 0007 is the last migration guaranteed to exist in all environments.
        # 0008 was created locally but never pushed; it can be committed
        # separately and will chain correctly after this migration.
        ("tools", "0007_expand_seo_fields"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="tool",
                    name="registry_version",
                    field=models.CharField(
                        default="1.0",
                        help_text="Registry version string; auto-updated by seed_tools.",
                        max_length=20,
                    ),
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql="""
                        ALTER TABLE tools_tool
                        ADD COLUMN IF NOT EXISTS registry_version VARCHAR(20) NOT NULL DEFAULT '1.0';
                    """,
                    reverse_sql="""
                        ALTER TABLE tools_tool
                        DROP COLUMN IF EXISTS registry_version;
                    """,
                ),
            ]
        )
    ]
