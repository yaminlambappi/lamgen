# Migration: Add UniqueConstraint to ToolUsageHistory for (user, tool) where user is not null
# Must run AFTER the deduplication data migration (0004).
# Generated manually for LamGen Tools Ecosystem - Task 1.2

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0004_deduplicate_toolusagehistory'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='toolusagehistory',
            constraint=models.UniqueConstraint(
                condition=models.Q(user__isnull=False),
                fields=('user', 'tool'),
                name='unique_user_tool_history',
            ),
        ),
    ]
