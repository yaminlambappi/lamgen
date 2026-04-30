"""
GenerationPipelineOrchestrator — progress tracking and failure handling.

Writes monotonically increasing progress updates to both the database and
Redis so the frontend polling endpoint always reflects the current pipeline state.
"""

import json
import logging

import redis
from django.conf import settings

from generation.models import GenerationJob
from generation.services.section_memory import SectionMemoryService

logger = logging.getLogger(__name__)


class GenerationPipelineOrchestrator:
    """
    Coordinates progress reporting and error handling across all pipeline stages.

    Progress is monotonically increasing: a stage update is only applied when
    its weight is strictly greater than the job's current progress_percentage.
    """

    # Percentage milestones per stage.
    # Stages 7–10 (humanization, review, coherence, export) are reserved for
    # future pipeline phases and currently map to 75–100.
    STAGE_WEIGHTS = {
        'instruction_analysis': 5,
        'rubric_extraction': 10,
        'outline_generation': 15,
        'section_planning': 20,
        'research_context_preparation': 25,
        'section_generation': 60,
        'humanization_pass': 75,
        'academic_reviewer_pass': 85,
        'coherence_pass': 92,
        'export_formatting': 100,
    }

    def update_progress(self, job: GenerationJob, stage: str) -> None:
        """
        Advance the job's progress to the weight for the given stage.

        Skipped silently if the new percentage is not strictly greater than
        the current value (ensures monotonic progression).
        Also writes the progress state to Redis under ``progress:{job.id}``.
        """
        percentage = self.STAGE_WEIGHTS[stage]

        if percentage <= job.progress_percentage:
            return

        job.current_stage = stage
        job.progress_percentage = percentage
        job.save(update_fields=['current_stage', 'progress_percentage'])

        r = redis.Redis.from_url(settings.REDIS_URL)
        r.setex(
            f"progress:{job.id}",
            86400,
            json.dumps({
                "stage": stage,
                "progress_percentage": percentage,
                "status": job.status,
            }),
        )

        logger.debug(
            "generation.orchestrator | job=%s stage=%s progress=%d%%",
            job.id, stage, percentage,
        )

    def fail_job(self, job: GenerationJob, stage: str, error: str) -> None:
        """
        Mark the job as FAILED, record the error, clean up Redis section memory,
        and write the failed status to the progress key.
        """
        job.status = GenerationJob.Status.FAILED
        job.error_message = f"[{stage}] {error}"
        job.save(update_fields=['status', 'error_message'])

        SectionMemoryService.delete(str(job.id))

        r = redis.Redis.from_url(settings.REDIS_URL)
        r.setex(
            f"progress:{job.id}",
            86400,
            json.dumps({
                "stage": stage,
                "progress_percentage": job.progress_percentage,
                "status": job.status,
            }),
        )

        logger.error(
            "generation.orchestrator | job=%s stage=%s status=failed error=%s",
            job.id, stage, error,
        )
