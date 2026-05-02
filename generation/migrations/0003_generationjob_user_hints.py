from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('generation', '0002_assignmentbrief_esl_context_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='generationjob',
            name='assignment_type_hint',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='generationjob',
            name='citation_style_hint',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='generationjob',
            name='writing_tone_hint',
            field=models.CharField(blank=True, max_length=30),
        ),
        migrations.AddField(
            model_name='generationjob',
            name='generation_mode',
            field=models.CharField(blank=True, default='standard', max_length=20),
        ),
    ]
