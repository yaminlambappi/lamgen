import uuid

from django.conf import settings
from django.db import models


class GenerationJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING'
        ANALYSING = 'ANALYSING'
        AWAITING_OUTLINE_REVIEW = 'AWAITING_OUTLINE_REVIEW'
        PROCESSING = 'PROCESSING'
        COMPLETED = 'COMPLETED'
        FAILED = 'FAILED'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generation_jobs',
    )
    title = models.CharField(max_length=500)
    input_file = models.FileField(upload_to='uploads/', blank=True)
    prompt_text = models.TextField(blank=True)
    target_word_count = models.PositiveIntegerField(default=3000)
    # User-selected generation settings — saved from the submit form
    assignment_type_hint = models.CharField(max_length=30, blank=True)
    citation_style_hint = models.CharField(max_length=50, blank=True)
    writing_tone_hint = models.CharField(max_length=30, blank=True)
    generation_mode = models.CharField(max_length=20, blank=True, default='standard')
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    current_stage = models.CharField(max_length=100, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    output_docx = models.FileField(upload_to='outputs/', blank=True)
    output_pdf = models.FileField(upload_to='outputs/', blank=True)
    generated_word_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    total_input_tokens = models.PositiveIntegerField(default=0)
    total_output_tokens = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} ({self.status})"


class AssignmentBrief(models.Model):
    class AssignmentType(models.TextChoices):
        ESSAY = 'essay'
        REPORT = 'report'
        CASE_STUDY = 'case_study'
        LITERATURE_REVIEW = 'literature_review'
        THESIS_CHAPTER = 'thesis_chapter'
        OTHER = 'other'

    class AcademicLevel(models.TextChoices):
        UNDERGRADUATE = 'undergraduate'
        POSTGRADUATE = 'postgraduate'
        DOCTORAL = 'doctoral'

    class WritingTone(models.TextChoices):
        CRITICAL_ANALYTICAL = 'critical_analytical'
        DESCRIPTIVE_EXPLANATORY = 'descriptive_explanatory'
        REFLECTIVE = 'reflective'
        PROFESSIONAL_REPORT = 'professional_report'

    job = models.OneToOneField(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='brief',
    )
    topic = models.TextField()
    subject_area = models.CharField(max_length=255)
    assignment_type = models.CharField(max_length=30, choices=AssignmentType.choices)
    academic_level = models.CharField(max_length=20, choices=AcademicLevel.choices)
    academic_level_inferred = models.BooleanField(default=False)
    required_sections = models.JSONField(default=list)
    citation_style = models.CharField(max_length=50)
    formatting_instructions = models.TextField(blank=True)
    required_frameworks = models.JSONField(default=list)
    writing_tone = models.CharField(max_length=30, choices=WritingTone.choices)
    organisational_context = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.topic[:60]} ({self.assignment_type})"


class RubricProfile(models.Model):
    brief = models.OneToOneField(
        AssignmentBrief,
        on_delete=models.CASCADE,
        related_name='rubric',
    )
    # criteria schema: [{"name": str, "weight": float, "distinction_descriptor": str}]
    criteria = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rubric for {self.brief}"


class DocumentOutline(models.Model):
    job = models.OneToOneField(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='outline',
    )
    # sections schema: [{"title": str, "target_word_count": int, "key_points": [str]}]
    sections = models.JSONField(default=list)
    research_context = models.JSONField(default=dict)
    user_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Outline for {self.job}"


class GeneratedSection(models.Model):
    job = models.ForeignKey(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='sections',
    )
    order = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField()
    word_count = models.PositiveIntegerField(default=0)
    humanized = models.BooleanField(default=False)
    # reviewer_score schema: {"criterion_name": float, ...}
    reviewer_score = models.JSONField(null=True, blank=True)
    rewritten_by_reviewer = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        unique_together = [('job', 'order')]

    def __str__(self):
        return f"{self.title} (order={self.order})"


class TokenUsageLog(models.Model):
    job = models.ForeignKey(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='token_logs',
    )
    stage = models.CharField(max_length=100)
    input_tokens = models.PositiveIntegerField()
    output_tokens = models.PositiveIntegerField()
    model = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stage} — in:{self.input_tokens} out:{self.output_tokens}"
