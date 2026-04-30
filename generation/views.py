import json
import logging

import magic
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from generation.models import GenerationJob, DocumentOutline
from generation.services.generation_config import GenerationConfig
from generation.tasks import run_generation_pipeline, continue_generation_pipeline

logger = logging.getLogger(__name__)

MAX_FILE_SIZE = 20 * 1024 * 1024  # 20 MB
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
}

# ---------------------------------------------------------------------------
# Choices exposed to the template — must stay in sync with backend constants
# ---------------------------------------------------------------------------

ASSIGNMENT_TYPE_CHOICES = [
    ('essay',             'Essay'),
    ('report',            'Report'),
    ('case_study',        'Case Study'),
    ('literature_review', 'Literature Review'),
    ('thesis_chapter',    'Thesis Chapter'),
    ('other',             'Other'),
]

CITATION_STYLE_CHOICES = [
    ('APA',       'APA'),
    ('Harvard',   'Harvard'),
    ('Chicago',   'Chicago'),
    ('Vancouver', 'Vancouver'),
    ('other',     'Other'),
]

WRITING_TONE_CHOICES = [
    ('critical_analytical',      'Analytical'),
    ('professional_report',      'Professional'),
    ('descriptive_explanatory',  'Descriptive'),
    ('reflective',               'Reflective'),
]

GENERATION_MODE_CHOICES = [
    ('economy',  'Fast & Cheap',      'Lowest cost — good for drafts and shorter assignments'),
    ('standard', 'Balanced',          'Recommended — strong quality at reasonable cost'),
    ('quality',  'Premium Quality',   'Strongest analysis — higher token usage'),
]

WORD_COUNT_PRESETS = [1000, 1500, 2000, 2500, 3000, 4000, 5000]

# Section defaults per assignment type — used when section_mode is 'fixed'
SECTION_DEFAULTS = {
    'essay':             ['Introduction', 'Literature Review', 'Analysis', 'Discussion', 'Conclusion'],
    'report':            ['Executive Summary', 'Introduction', 'Methodology', 'Findings', 'Recommendations', 'Conclusion'],
    'case_study':        ['Introduction', 'Background', 'Analysis', 'Discussion', 'Conclusion'],
    'literature_review': ['Introduction', 'Thematic Review', 'Critical Analysis', 'Synthesis', 'Conclusion'],
    'thesis_chapter':    ['Introduction', 'Literature Review', 'Methodology', 'Results', 'Discussion', 'Conclusion'],
    'other':             ['Introduction', 'Main Body', 'Analysis', 'Conclusion'],
}


def _get_submit_context(overrides: dict | None = None) -> dict:
    """
    Build the context dict for the submit form, pulling defaults from settings
    so the frontend always reflects the current backend configuration.
    """
    config = GenerationConfig()
    ctx = {
        'assignment_type_choices': ASSIGNMENT_TYPE_CHOICES,
        'citation_style_choices':  CITATION_STYLE_CHOICES,
        'writing_tone_choices':    WRITING_TONE_CHOICES,
        'generation_mode_choices': GENERATION_MODE_CHOICES,
        'word_count_presets':      WORD_COUNT_PRESETS,
        'section_defaults_json':   json.dumps(SECTION_DEFAULTS),
        # Backend defaults — template uses these as initial values
        'default_assignment_type':  config.assignment_type_default,
        'default_citation_style':   config.citation_style_default,
        'default_writing_tone':     config.writing_tone_default,
        'default_generation_mode':  config.mode,
        'default_section_mode':     config.section_mode,
        'default_word_count':       3000,
        'max_budget_cents':         config.max_budget_cents,
        # Cost estimate hint (cents per 3000-word, 5-section assignment)
        'estimated_cost_cents': round(config.estimate_assignment_cost_cents(3000, 5), 2),
    }
    if overrides:
        ctx.update(overrides)
    return ctx


@login_required
def submit_job(request):
    """
    GET:  Render the assignment submission form with backend-aligned defaults.
    POST: Validate, create GenerationJob, enqueue pipeline, redirect to status.
    """
    if request.method == 'GET':
        return render(request, 'generation/submit.html', _get_submit_context())

    # --- POST ---
    errors = []
    title              = request.POST.get('title', '').strip()
    prompt_text        = request.POST.get('prompt_text', '').strip()
    target_word_count_raw = request.POST.get('target_word_count', '').strip()
    uploaded_file      = request.FILES.get('input_file')

    # Generation settings from form
    assignment_type   = request.POST.get('assignment_type', 'essay').strip()
    citation_style    = request.POST.get('citation_style', 'APA').strip()
    writing_tone      = request.POST.get('writing_tone', 'critical_analytical').strip()
    generation_mode   = request.POST.get('generation_mode', 'standard').strip()
    section_mode      = request.POST.get('section_mode', 'auto').strip()

    if not title:
        errors.append('A title is required.')

    target_word_count = None
    try:
        target_word_count = int(target_word_count_raw)
        if not (500 <= target_word_count <= 15000):
            errors.append('Word count must be between 500 and 15,000.')
    except (ValueError, TypeError):
        errors.append('Word count must be a valid number.')

    if uploaded_file:
        header = uploaded_file.read(2048)
        uploaded_file.seek(0)
        mime_type = magic.from_buffer(header, mime=True)
        if mime_type not in ALLOWED_MIME_TYPES:
            errors.append(
                f'Unsupported file type ({mime_type}). Upload a PDF or DOCX file.'
            )
        if uploaded_file.size > MAX_FILE_SIZE:
            errors.append('File exceeds the 20 MB size limit.')
    elif prompt_text:
        if not (50 <= len(prompt_text) <= 10000):
            errors.append('Prompt must be between 50 and 10,000 characters.')
    else:
        errors.append('Upload a file or paste an assignment prompt.')

    if errors:
        return render(request, 'generation/submit.html', _get_submit_context({
            'errors':            errors,
            'title':             title,
            'prompt_text':       prompt_text,
            'target_word_count': target_word_count_raw,
            # Preserve user selections on error
            'default_assignment_type': assignment_type,
            'default_citation_style':  citation_style,
            'default_writing_tone':    writing_tone,
            'default_generation_mode': generation_mode,
            'default_section_mode':    section_mode,
        }))

    job = GenerationJob(
        user=request.user,
        title=title,
        target_word_count=target_word_count,
        status=GenerationJob.Status.PENDING,
    )
    if uploaded_file:
        job.input_file = uploaded_file
    elif prompt_text:
        job.prompt_text = prompt_text
    job.save()

    logger.info(
        "generation.views | job=%s user=%s action=submitted "
        "assignment_type=%s generation_mode=%s word_count=%d",
        job.id, request.user.id, assignment_type, generation_mode, target_word_count,
    )

    run_generation_pipeline.delay(str(job.id))
    return redirect('generation:job_status', pk=job.id)


@login_required
def job_status(request, pk):
    """Render the job status page for the authenticated owner."""
    job = get_object_or_404(GenerationJob, pk=pk)
    if job.user != request.user:
        return HttpResponseForbidden('You do not have permission to view this job.')

    outline = None
    try:
        outline = job.outline
    except DocumentOutline.DoesNotExist:
        pass

    # Cost summary for completed jobs
    cost_cents = None
    if job.status == GenerationJob.Status.COMPLETED:
        from generation.services.claude_service import _estimate_cost_cents
        cost_cents = _estimate_cost_cents(job.total_input_tokens, job.total_output_tokens)

    return render(request, 'generation/status.html', {
        'job':        job,
        'outline':    outline,
        'cost_cents': cost_cents,
    })


@login_required
def job_status_json(request, pk):
    """JSON polling endpoint — returns stage, progress_percentage, and status."""
    job = get_object_or_404(GenerationJob, pk=pk)
    if job.user != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    return JsonResponse({
        'stage':              job.current_stage,
        'progress_percentage': job.progress_percentage,
        'status':             job.status,
    })


@login_required
@require_http_methods(['POST'])
def confirm_outline(request, pk):
    """Confirm the generated outline and resume section generation."""
    job = get_object_or_404(GenerationJob, pk=pk)
    if job.user != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    try:
        outline = job.outline
    except DocumentOutline.DoesNotExist:
        return JsonResponse({'error': 'Outline not found'}, status=404)

    outline.user_confirmed = True
    outline.confirmed_at = timezone.now()
    outline.save()

    continue_generation_pipeline.delay(str(job.id))
    return JsonResponse({'success': True})


@login_required
@require_http_methods(['POST'])
def edit_outline(request, pk):
    """Update outline sections while the job is awaiting review."""
    job = get_object_or_404(GenerationJob, pk=pk)
    if job.user != request.user:
        return JsonResponse({'error': 'Forbidden'}, status=403)

    if job.status != GenerationJob.Status.AWAITING_OUTLINE_REVIEW:
        return JsonResponse(
            {'error': 'Outline can only be edited while awaiting review.'},
            status=400,
        )

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    try:
        outline = job.outline
    except DocumentOutline.DoesNotExist:
        return JsonResponse({'error': 'Outline not found'}, status=404)

    outline.sections = data.get('sections', outline.sections)
    outline.save(update_fields=['sections'])
    return JsonResponse({'success': True})
