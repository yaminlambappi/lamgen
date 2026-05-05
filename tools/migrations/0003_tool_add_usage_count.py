# Migration: Add usage_count field to Tool model
# Generated manually for LamGen Tools Ecosystem - Task 1.1

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tools', '0002_alter_toolusagehistory_used_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='tool',
            name='usage_count',
            field=models.BigIntegerField(default=0),
        ),
    ]
