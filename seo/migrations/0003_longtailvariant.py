from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("seo", "0002_add_schema_type_and_related_tools"),
        ("tools", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LongTailVariant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("variant_slug", models.SlugField(max_length=100)),
                ("keyword_intent", models.CharField(choices=[("online", "Online / Free"), ("use_case", "For Use Case"), ("without", "Without Limitation"), ("vs", "Comparison / VS"), ("how_to", "How To"), ("best", "Best / Top")], max_length=20)),
                ("unique_intro", models.TextField()),
                ("meta_title", models.CharField(max_length=70)),
                ("meta_description", models.CharField(max_length=160)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("tool", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="longtail_variants", to="tools.tool")),
            ],
            options={"ordering": ["tool", "variant_slug"]},
        ),
        migrations.AlterUniqueTogether(
            name="longtailvariant",
            unique_together={("tool", "variant_slug")},
        ),
    ]
