"""
Migration 0009: Add registry_version to tools_tool.

Depends on 0007 (the last migration present on all environments).
"""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0007_expand_seo_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="tool",
            name="registry_version",
            field=models.CharField(
                default="1.0",
                help_text="Registry version string; auto-updated by seed_tools.",
                max_length=20,
            ),
        ),
    ]
