import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from generation.models import (
    AssignmentBrief, DocumentOutline, GeneratedSection, GenerationJob, RubricProfile
)
from thesis.models import StatusChoices, ThesisChunk, ThesisRequest

User = get_user_model()


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f'user{n}')
    email = factory.Sequence(lambda n: f'user{n}@example.com')
    password = factory.PostGenerationMethodCall('set_password', 'testpass123')
    university = 'Test University'
    bio = 'Test bio'
    is_active = True


class ThesisRequestFactory(DjangoModelFactory):
    class Meta:
        model = ThesisRequest

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f'Test Thesis {n}')
    status = StatusChoices.PENDING
    generated_thesis = ''
    error_message = ''


class CompletedThesisRequestFactory(ThesisRequestFactory):
    status = StatusChoices.COMPLETED
    generated_thesis = '# Abstract\n\nThis is a test thesis.\n\n# Introduction\n\nTest content.'


class ThesisChunkFactory(DjangoModelFactory):
    class Meta:
        model = ThesisChunk

    thesis_request = factory.SubFactory(ThesisRequestFactory)
    order = factory.Sequence(lambda n: n)
    content = factory.Sequence(lambda n: f'Chunk content {n}')
    token_count = 100


class GenerationJobFactory(DjangoModelFactory):
    class Meta:
        model = GenerationJob

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda n: f'Test Generation Job {n}')
    status = GenerationJob.Status.PENDING
    target_word_count = 3000
    prompt_text = 'This is a test assignment prompt for generation testing purposes.'


class AssignmentBriefFactory(DjangoModelFactory):
    class Meta:
        model = AssignmentBrief

    job = factory.SubFactory(GenerationJobFactory)
    topic = 'Test Assignment Topic'
    subject_area = 'Computer Science'
    assignment_type = AssignmentBrief.AssignmentType.ESSAY
    academic_level = AssignmentBrief.AcademicLevel.POSTGRADUATE
    citation_style = 'APA'
    writing_tone = AssignmentBrief.WritingTone.CRITICAL_ANALYTICAL
    required_sections = ['Introduction', 'Body', 'Conclusion']
    required_frameworks = []
    organisational_context = ''
    academic_level_inferred = False


class RubricProfileFactory(DjangoModelFactory):
    class Meta:
        model = RubricProfile

    brief = factory.SubFactory(AssignmentBriefFactory)
    criteria = [
        {'name': 'Critical Analysis', 'weight': 0.4, 'distinction_descriptor': 'Demonstrates sophisticated critical analysis'},
        {'name': 'Research Depth', 'weight': 0.3, 'distinction_descriptor': 'Engages with multiple theoretical positions'},
        {'name': 'Writing Quality', 'weight': 0.3, 'distinction_descriptor': 'Clear, well-structured academic prose'},
    ]


class DocumentOutlineFactory(DjangoModelFactory):
    class Meta:
        model = DocumentOutline

    job = factory.SubFactory(GenerationJobFactory)
    sections = [
        {'title': 'Introduction', 'target_word_count': 500, 'key_points': ['Background', 'Thesis statement']},
        {'title': 'Main Body', 'target_word_count': 2000, 'key_points': ['Analysis', 'Evidence']},
        {'title': 'Conclusion', 'target_word_count': 500, 'key_points': ['Summary', 'Implications']},
    ]
    user_confirmed = False
    research_context = {}


class GeneratedSectionFactory(DjangoModelFactory):
    class Meta:
        model = GeneratedSection

    job = factory.SubFactory(GenerationJobFactory)
    order = factory.Sequence(lambda n: n)
    title = factory.Sequence(lambda n: f'Section {n}')
    content = 'This is test section content for testing purposes.'
    word_count = 10
    humanized = False
    rewritten_by_reviewer = False
