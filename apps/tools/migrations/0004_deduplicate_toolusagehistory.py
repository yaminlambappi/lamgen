# Data migration: Deduplicate ToolUsageHistory records
# Keeps the most recent record per (user, tool) pair where user is not null.
# This must run BEFORE the UniqueConstraint is added in the next migration.
# Generated manually for LamGen Tools Ecosystem - Task 1.2

from django.db import migrations


def deduplicate_tool_usage_history(apps, schema_editor):
    """
    For each (user, tool) pair with user IS NOT NULL, keep only the most
    recently used record (highest used_at) and delete the rest.
    """
    ToolUsageHistory = apps.get_model('tools', 'ToolUsageHistory')

    # Find all (user_id, tool_id) pairs that have duplicates (user not null)
    seen = {}
    # Order by used_at descending so the first one we see is the most recent
    for record in ToolUsageHistory.objects.filter(
        user__isnull=False
    ).order_by('-used_at'):
        key = (record.user_id, record.tool_id)
        if key in seen:
            # This is a duplicate — delete it
            record.delete()
        else:
            seen[key] = record.pk


def reverse_deduplicate(apps, schema_editor):
    # Deduplication is not reversible (deleted records cannot be restored)
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0003_tool_add_usage_count'),
    ]

    operations = [
        migrations.RunPython(
            deduplicate_tool_usage_history,
            reverse_deduplicate,
        ),
    ]
