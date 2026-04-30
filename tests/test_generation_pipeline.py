"""
Full Phase 2 pipeline smoke test (Stages 1–6) with mocked Claude responses.

Runs run_generation_pipeline() and continue_generation_pipeline() synchronously
(not via Celery delay) against a real Django DB and fakeredis.
"""

import json
from unittest.mock import patch

import fakeredis
import pytest
from django.utils import timezone

from generation.models import (
    AssignmentBrief,
    DocumentOutline,
    GeneratedSection,
    GenerationJob,
)
from generation.services.section_memory import SectionMemoryService
from generation.tasks import continue_generation_pipeline, run_generation_pipeline
from tests.factories import GenerationJobFactory, UserFactory


def mock_claude_call(system_prompt, user_prompt, max_tokens, job, stage_label, config=None):
    """
    Side-effect function for ClaudeService.call that returns appropriate
    mock responses for each pipeline stage.

    Stage labels after optimization:
      combined_analysis  — Stages 1+2 merged into one call
      outline_generation — Stage 3 (only called when brief has no required_sections)
      section_*          — Stage 6 per-section calls
    """
    if stage_label == "combined_analysis":
        return json.dumps(
            {
                "brief": {
                    "topic": "Cybersecurity Governance",
                    "subject_area": "Information Technology",
                    "assignment_type": "report",
                    "academic_level": "postgraduate",
                    "required_sections": ["Introduction", "Conclusion"],
                    "citation_style": "APA",
                    "writing_tone": "critical_analytical",
                    "organisational_context": "A financial services firm",
                    "required_frameworks": ["NIST", "ISO 27001"],
                },
                "rubric_criteria": [],
            }
        )
    elif stage_label == "outline_generation":
        return json.dumps(
            [
                {
                    "title": "Introduction",
                    "target_word_count": 500,
                    "key_points": ["Background", "Scope"],
                },
                {
                    "title": "Conclusion",
                    "target_word_count": 500,
                    "key_points": ["Summary", "Recommendations"],
                },
            ]
        )
    else:
        # Section generation stages (e.g. "section_Introduction", "section_Conclusion")
        return "This is the generated content for the section. " * 50


@pytest.mark.django_db
class TestFullPipelineSmokeTest:
    """
    Integration smoke test for the full Phase 2 pipeline (Stages 1–6).

    Uses mocked Claude responses and fakeredis to avoid external dependencies.
    """

    def test_full_pipeline_pending_to_completed(self):
        """
        Runs the full Phase 2 pipeline synchronously and verifies all expected
        DB records are created and the job reaches COMPLETED status.
        """
        # ------------------------------------------------------------------ #
        # Setup: create a GenerationJob with prompt_text only (no file upload)
        # ------------------------------------------------------------------ #
        user = UserFactory()
        job = GenerationJobFactory(
            user=user,
            prompt_text=(
                "Write a 3000-word report on Cybersecurity Governance for a "
                "financial services firm, covering NIST and ISO 27001 frameworks."
            ),
            target_word_count=3000,
        )

        fake_redis = fakeredis.FakeRedis()

        with (
            patch(
                "generation.services.claude_service.ClaudeService.call",
                side_effect=mock_claude_call,
            ),
            patch(
                "generation.services.section_memory.SectionMemoryService._get_redis",
                return_value=fake_redis,
            ),
            patch(
                "generation.services.orchestrator.redis.Redis.from_url",
                return_value=fake_redis,
            ),
        ):
            # ---------------------------------------------------------------- #
            # Phase A: run Stages 1–3 (instruction_analysis → outline_generation)
            # ---------------------------------------------------------------- #
            run_generation_pipeline(str(job.id))

            # Verify job paused at AWAITING_OUTLINE_REVIEW
            job.refresh_from_db()
            assert job.status == GenerationJob.Status.AWAITING_OUTLINE_REVIEW, (
                f"Expected AWAITING_OUTLINE_REVIEW after Stage 3, got {job.status}"
            )

            # Verify AssignmentBrief was created
            assert AssignmentBrief.objects.filter(job=job).exists(), (
                "AssignmentBrief should have been created by Stage 1"
            )
            brief = AssignmentBrief.objects.get(job=job)
            assert brief.topic == "Cybersecurity Governance"
            assert brief.academic_level == "postgraduate"

            # Verify DocumentOutline was created with user_confirmed=False
            assert DocumentOutline.objects.filter(job=job).exists(), (
                "DocumentOutline should have been created by Stage 3"
            )
            outline = DocumentOutline.objects.get(job=job)
            assert outline.user_confirmed is False, (
                "Outline should not be confirmed yet"
            )
            assert len(outline.sections) == 2, (
                f"Expected 2 outline sections, got {len(outline.sections)}"
            )

            # ---------------------------------------------------------------- #
            # Phase B: simulate user confirming the outline
            # ---------------------------------------------------------------- #
            outline.user_confirmed = True
            outline.confirmed_at = timezone.now()
            outline.save()

            # ---------------------------------------------------------------- #
            # Phase C: continue Stage 6 (section generation — Stages 4+5 eliminated)
            # ---------------------------------------------------------------- #
            continue_generation_pipeline(str(job.id))

            # Verify job reached COMPLETED
            job.refresh_from_db()
            assert job.status == GenerationJob.Status.COMPLETED, (
                f"Expected COMPLETED after Stage 6, got {job.status}"
            )

            # Verify GeneratedSection records were created (one per outline section)
            sections = GeneratedSection.objects.filter(job=job).order_by("order")
            assert sections.count() == 2, (
                f"Expected 2 GeneratedSection records, got {sections.count()}"
            )
            section_titles = [s.title for s in sections]
            assert "Introduction" in section_titles
            assert "Conclusion" in section_titles

            # Verify SectionMemory Redis key no longer exists after completion
            memory_key = SectionMemoryService._redis_key(str(job.id))
            assert fake_redis.get(memory_key) is None, (
                "SectionMemory Redis key should have been deleted on job completion"
            )
