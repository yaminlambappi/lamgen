"""
Celery tasks for the LamGen generation pipeline.

run_generation_pipeline      — Stages 1+2 (combined analysis) and Stage 3 (outline).
                               Pauses at AWAITING_OUTLINE_REVIEW for user review.
continue_generation_pipeline — Stage 6 (section-by-section generation).
                               Stages 4 and 5 are handled inline during generation.
cleanup_old_generation_uploads — Hourly cleanup of source files for completed jobs.
"""

import logging
import os
import time
from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from generation.models import GenerationJob
from generation.services.generation_config import GenerationConfig
from generation.services.orchestrator import GenerationPipelineOrchestrator
from generation.services.section_memory import SectionMemoryService
from generation.services.assignment_intelligence import AssignmentIntelligenceEngine

logger = logging.getLogger(__name__)


@shared_task
def run_generation_pipeline(job_id: str) -> None:
    """
    Execute Stages 1+2 (combined assignment analysis) and Stage 3 (outline generation).

    Pauses at AWAITING_OUTLINE_REVIEW once the outline is ready for user review.
    The pipeline resumes via continue_generation_pipeline() after outline confirmation.
    """
    try:
        job = GenerationJob.objects.get(id=job_id)
    except GenerationJob.DoesNotExist:
        logger.error("generation.pipeline | job=%s status=not_found stage=analysis", job_id)
        return

    config = GenerationConfig()
    orchestrator = GenerationPipelineOrchestrator()
    pipeline_start = time.monotonic()

    logger.info(
        "generation.pipeline | job=%s status=started stage=analysis mode=%s",
        job.id, config.mode,
    )

    job.status = GenerationJob.Status.PROCESSING
    job.save(update_fields=["status"])
    SectionMemoryService.initialise(str(job.id))

    # ------------------------------------------------------------------
    # Stages 1 + 2 — combined analysis (single API call)
    # ------------------------------------------------------------------
    try:
        if job.input_file:
            try:
                from generation.services.document_parser import DocumentParserService
                import mimetypes
                file_path = job.input_file.path
                mime_type, _ = mimetypes.guess_type(file_path)
                text = DocumentParserService().parse(file_path, mime_type or "")
                text_chunks = DocumentParserService().chunk_text(text)
                logger.info(
                    "generation.pipeline | job=%s stage=document_parse "
                    "chunks=%d source=file",
                    job.id, len(text_chunks),
                )
            except Exception as parse_exc:
                logger.warning(
                    "generation.pipeline | job=%s stage=document_parse "
                    "status=parse_failed source=file fallback=prompt_text error=%s",
                    job.id, parse_exc,
                )
                text_chunks = [job.prompt_text] if job.prompt_text else [""]
        else:
            text_chunks = [job.prompt_text] if job.prompt_text else [""]
            logger.info(
                "generation.pipeline | job=%s stage=document_parse source=prompt_text",
                job.id,
            )

        brief = AssignmentIntelligenceEngine(config=config).analyse(text_chunks, job)
        orchestrator.update_progress(job, "instruction_analysis")
        orchestrator.update_progress(job, "rubric_extraction")

        logger.info(
            "generation.pipeline | job=%s stage=analysis status=complete "
            "assignment_type=%s academic_level=%s has_rubric=%s",
            job.id,
            brief.assignment_type,
            brief.academic_level,
            hasattr(brief, 'rubric') and bool(getattr(brief, 'rubric', None)),
        )
    except Exception as exc:
        logger.error(
            "generation.pipeline | job=%s stage=analysis status=failed error=%s",
            job.id, exc,
        )
        orchestrator.fail_job(job, "instruction_analysis", str(exc))
        return

    # ------------------------------------------------------------------
    # Stage 3 — outline generation
    # ------------------------------------------------------------------
    try:
        from generation.services.outline_generator import OutlineGenerationService
        outline = OutlineGenerationService(config=config).generate(job, brief)
        orchestrator.update_progress(job, "outline_generation")
        job.status = GenerationJob.Status.AWAITING_OUTLINE_REVIEW
        job.save(update_fields=["status"])

        duration = time.monotonic() - pipeline_start
        logger.info(
            "generation.pipeline | job=%s stage=outline status=complete "
            "sections=%d duration=%.2fs awaiting_review=true",
            job.id, len(outline.sections), duration,
        )
    except Exception as exc:
        logger.error(
            "generation.pipeline | job=%s stage=outline status=failed error=%s",
            job.id, exc,
        )
        orchestrator.fail_job(job, "outline_generation", str(exc))
        return


@shared_task
def continue_generation_pipeline(job_id: str) -> None:
    """
    Execute Stage 6 (section-by-section generation) after outline confirmation.

    Emits a structured completion log with total tokens, estimated cost, and
    section count on success.
    """
    try:
        job = GenerationJob.objects.get(id=job_id)
    except GenerationJob.DoesNotExist:
        logger.error(
            "generation.pipeline | job=%s status=not_found stage=generation", job_id
        )
        return

    config = GenerationConfig()
    orchestrator = GenerationPipelineOrchestrator()
    generation_start = time.monotonic()

    logger.info(
        "generation.pipeline | job=%s status=started stage=generation mode=%s",
        job.id, config.mode,
    )

    job.status = GenerationJob.Status.PROCESSING
    job.save(update_fields=["status"])

    brief = job.brief
    outline = job.outline

    try:
        memory = SectionMemoryService.get(str(job.id))
    except Exception:
        logger.warning(
            "generation.pipeline | job=%s stage=generation "
            "status=memory_missing action=reinitialise",
            job.id,
        )
        memory = SectionMemoryService.initialise(str(job.id))

    # ------------------------------------------------------------------
    # Stage 6 — section generation
    # ------------------------------------------------------------------
    try:
        from generation.services.section_generator import SectionGenerationService
        sections = SectionGenerationService(config=config).generate_all(
            job, brief, outline, memory
        )
        orchestrator.update_progress(job, "section_generation")
    except Exception as exc:
        logger.error(
            "generation.pipeline | job=%s stage=generation status=failed error=%s",
            job.id, exc,
        )
        orchestrator.fail_job(job, "section_generation", str(exc))
        return

    job.status = GenerationJob.Status.COMPLETED
    job.completed_at = timezone.now()
    job.save(update_fields=["status", "completed_at"])
    SectionMemoryService.delete(str(job.id))

    # Structured completion log
    duration = time.monotonic() - generation_start
    job.refresh_from_db()
    total_words = sum(s.word_count for s in sections)
    from generation.services.claude_service import _estimate_cost_cents
    cost_cents = _estimate_cost_cents(job.total_input_tokens, job.total_output_tokens)

    logger.info(
        "generation.pipeline | job=%s status=completed "
        "sections=%d total_words=%d "
        "total_input_tokens=%d total_output_tokens=%d "
        "estimated_cost_cents=%.4f duration=%.2fs",
        job.id,
        len(sections), total_words,
        job.total_input_tokens, job.total_output_tokens,
        cost_cents, duration,
    )


@shared_task
def cleanup_old_generation_uploads() -> int:
    """
    Delete source files from disk for GenerationJob records that are older than
    24 hours and have reached a terminal status (COMPLETED or FAILED).

    Returns the number of files removed.
    """
    cutoff = timezone.now() - timedelta(hours=24)
    terminal_statuses = [GenerationJob.Status.COMPLETED, GenerationJob.Status.FAILED]

    jobs = GenerationJob.objects.filter(
        created_at__lt=cutoff,
        status__in=terminal_statuses,
    ).exclude(input_file='')

    cleaned = 0
    for job in jobs:
        try:
            if os.path.exists(job.input_file.path):
                os.remove(job.input_file.path)
            job.input_file = None
            job.save(update_fields=['input_file'])
            cleaned += 1
        except Exception as exc:
            logger.warning(
                "generation.cleanup | job=%s status=cleanup_failed error=%s",
                job.id, exc,
            )

    if cleaned:
        logger.info("generation.cleanup | removed_files=%d", cleaned)
    return cleaned
