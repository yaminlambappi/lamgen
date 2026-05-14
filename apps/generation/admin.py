from django.contrib import admin

from .models import (
    AssignmentBrief,
    DocumentOutline,
    GeneratedSection,
    GenerationJob,
    RubricProfile,
    TokenUsageLog,
)


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'user',
        'status',
        'progress_percentage',
        'target_word_count',
        'generated_word_count',
        'created_at',
        'completed_at',
    )
    list_filter = ('status',)
    search_fields = ('title', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at', 'completed_at')


@admin.register(AssignmentBrief)
class AssignmentBriefAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'topic_short',
        'subject_area',
        'assignment_type',
        'academic_level',
        'citation_style',
        'created_at',
    )
    search_fields = ('topic', 'subject_area')
    list_filter = ('assignment_type', 'academic_level', 'writing_tone')

    @admin.display(description='Topic')
    def topic_short(self, obj):
        return obj.topic[:60]


@admin.register(RubricProfile)
class RubricProfileAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'brief',
        'created_at',
    )
    search_fields = ('brief__topic',)


@admin.register(DocumentOutline)
class DocumentOutlineAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'job',
        'user_confirmed',
        'confirmed_at',
        'created_at',
    )
    list_filter = ('user_confirmed',)
    search_fields = ('job__title',)


@admin.register(GeneratedSection)
class GeneratedSectionAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'job',
        'order',
        'title',
        'word_count',
        'humanized',
        'rewritten_by_reviewer',
    )
    list_filter = ('humanized', 'rewritten_by_reviewer')
    search_fields = ('title', 'job__title')
    ordering = ('job', 'order')


@admin.register(TokenUsageLog)
class TokenUsageLogAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'job',
        'stage',
        'model',
        'input_tokens',
        'output_tokens',
        'created_at',
    )
    list_filter = ('model', 'stage')
    search_fields = ('job__title', 'stage', 'model')
    readonly_fields = ('created_at',)
