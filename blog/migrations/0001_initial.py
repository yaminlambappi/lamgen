from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tools", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ContentArticle",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=200)),
                ("slug", models.SlugField(max_length=250, unique=True)),
                ("content_type", models.CharField(choices=[("tutorial", "Tutorial"), ("comparison", "Comparison"), ("use-case", "Use-Case Guide"), ("troubleshooting", "Troubleshooting Guide")], max_length=20)),
                ("body", models.TextField(help_text="Markdown content")),
                ("author", models.CharField(default="LamGen Team", max_length=100)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("meta_title", models.CharField(blank=True, max_length=70)),
                ("meta_description", models.CharField(blank=True, max_length=160)),
                ("is_published", models.BooleanField(default=False)),
                ("related_tools", models.ManyToManyField(blank=True, related_name="articles", to="tools.tool")),
            ],
            options={"ordering": ["-published_at"]},
        ),
    ]
