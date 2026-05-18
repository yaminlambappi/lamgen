from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tools", "0008_tool_cache_strategy_tool_is_ai_powered_and_more"),
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
