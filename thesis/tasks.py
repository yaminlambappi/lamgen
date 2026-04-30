import logging
import os
import uuid
from datetime import timedelta

import django
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Stage constants for Redis progress tracking
STAGE_PROCESSING = 'processing'
STAGE_EXTRACTED = 'extracted'
STAGE_CHUNKED = 'chunked'
STAGE_LLM_DONE = 'llm_done'
STAGE_PDF_RENDERED = 'pdf_rendered'
STAGE_COMPLETED = 'completed'
STAGE_FAILED = 'failed'

STAGE_PROGRESS = {
    STAGE_PROCESSING: 10,
    STAGE_EXTRACTED: 30,
    STAGE_CHUNKED: 50,
    STAGE_LLM_DONE: 75,
    STAGE_PDF_RENDERED: 90,
    STAGE_COMPLETED: 100,
    STAGE_FAILED: 0,
}


def _get_redis_client():
    """Get a Redis client using the broker URL from settings."""
    import redis
    return redis.from_url(settings.CELERY_BROKER_URL)


def set_stage(thesis_id: int, stage: str):
    """Store the current pipeline stage in Redis."""
    try:
        r = _get_redis_client()
        r.setex(f'thesis:{thesis_id}:stage', 3600, stage)  # expire after 1 hour
    except Exception as e:
        logger.warning('Failed to set Redis stage for thesis %d: %s', thesis_id, e)


def get_stage(thesis_id: int) -> str:
    """Retrieve the current pipeline stage from Redis."""
    try:
        r = _get_redis_client()
        val = r.get(f'thesis:{thesis_id}:stage')
        return val.decode() if val else ''
    except Exception as e:
        logger.warning('Failed to get Redis stage for thesis %d: %s', thesis_id, e)
        return ''


@shared_task(bind=True, max_retries=0, acks_late=True)
def process_thesis_task(self, thesis_id: int) -> None:
    """
    Full thesis generation pipeline.

    Steps:
    1. Fetch ThesisRequest; set status=PROCESSING
    2. PDFService.process(input_file.path) → chunks
    3. Bulk-create ThesisChunk records
    4. LLMService.generate_thesis(chunks, title) → thesis_text
    5. ThesisPDFGenerator.render(thesis_text, title) → pdf_bytes
    6. Write pdf_bytes to /media/outputs/<uuid>.pdf
    7. Update ThesisRequest: output_file=path, status=COMPLETED
    8. On any exception: set status=FAILED, log error
    """
    from thesis.models import StatusChoices, ThesisChunk, ThesisRequest
    from thesis.services.llm_service import LLMService, LLMServiceError
    from thesis.services.pdf_service import PDFService
    from thesis.services.thesis_pdf import ThesisPDFGenerator, ThesisPDFGeneratorError

    try:
        thesis = ThesisRequest.objects.get(pk=thesis_id)
    except ThesisRequest.DoesNotExist:
        logger.error('ThesisRequest %d not found', thesis_id)
        return

    try:
        # Step 1: Mark as PROCESSING
        thesis.status = StatusChoices.PROCESSING
        thesis.save(update_fields=['status', 'updated_at'])
        set_stage(thesis_id, STAGE_PROCESSING)
        logger.info('Thesis %d: started processing', thesis_id)

        # Step 2: Extract and chunk PDF text
        pdf_path = thesis.input_file.path
        chunks = PDFService.process(pdf_path)
        set_stage(thesis_id, STAGE_EXTRACTED)
        logger.info('Thesis %d: extracted %d chunks', thesis_id, len(chunks))

        # Step 3: Persist ThesisChunk records
        ThesisChunk.objects.filter(thesis_request=thesis).delete()
        chunk_objects = [
            ThesisChunk(
                thesis_request=thesis,
                order=i,
                content=chunk,
                token_count=len(chunk.split()),  # approximate; tiktoken used in PDFService
            )
            for i, chunk in enumerate(chunks)
        ]
        ThesisChunk.objects.bulk_create(chunk_objects)
        set_stage(thesis_id, STAGE_CHUNKED)
        logger.info('Thesis %d: saved %d chunk records', thesis_id, len(chunk_objects))

        # Step 4: Generate thesis via Claude
        llm = LLMService()
        thesis_text = llm.generate_thesis(chunks, thesis.title)
        thesis.generated_thesis = thesis_text
        thesis.save(update_fields=['generated_thesis', 'updated_at'])
        set_stage(thesis_id, STAGE_LLM_DONE)
        logger.info('Thesis %d: LLM generation complete (%d chars)', thesis_id, len(thesis_text))

        # Step 5: Render PDF
        pdf_bytes = ThesisPDFGenerator.render(thesis_text, thesis.title)
        set_stage(thesis_id, STAGE_PDF_RENDERED)
        logger.info('Thesis %d: PDF rendered (%d bytes)', thesis_id, len(pdf_bytes))

        # Step 6: Save output PDF to /media/outputs/
        outputs_dir = os.path.join(settings.MEDIA_ROOT, 'outputs')
        os.makedirs(outputs_dir, exist_ok=True)
        output_filename = f'{uuid.uuid4()}.pdf'
        output_path = os.path.join(outputs_dir, output_filename)
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

        # Step 7: Update ThesisRequest to COMPLETED
        thesis.output_file = f'outputs/{output_filename}'
        thesis.status = StatusChoices.COMPLETED
        thesis.save(update_fields=['output_file', 'status', 'updated_at'])
        set_stage(thesis_id, STAGE_COMPLETED)
        logger.info('Thesis %d: completed successfully', thesis_id)

    except Exception as e:
        logger.error('Thesis %d: pipeline failed: %s', thesis_id, e, exc_info=True)
        try:
            thesis.status = StatusChoices.FAILED
            thesis.error_message = str(e)
            thesis.save(update_fields=['status', 'error_message', 'updated_at'])
            set_stage(thesis_id, STAGE_FAILED)
        except Exception as save_err:
            logger.error('Thesis %d: failed to save FAILED status: %s', thesis_id, save_err)


@shared_task
def cleanup_old_uploads():
    """
    Delete input_file from disk for ThesisRequests where:
    - created_at < now() - 24h
    - input_file is not null/empty
    Sets input_file = '' after deletion.
    """
    from thesis.models import ThesisRequest

    cutoff = timezone.now() - timedelta(hours=24)
    old_requests = ThesisRequest.objects.filter(
        created_at__lt=cutoff,
    ).exclude(input_file='')

    deleted_count = 0
    for thesis in old_requests:
        if thesis.input_file:
            try:
                file_path = thesis.input_file.path
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info('Deleted old upload: %s', file_path)
                thesis.input_file = None
                thesis.save(update_fields=['input_file', 'updated_at'])
                deleted_count += 1
            except Exception as e:
                logger.error('Failed to delete upload for thesis %d: %s', thesis.pk, e)

    logger.info('cleanup_old_uploads: deleted %d old upload files', deleted_count)
    return deleted_count
