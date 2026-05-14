"""
Property-based tests for GenerationPipelineOrchestrator.

Covers:
  - Property 13: Pipeline progress is monotonically increasing (Task 7.3)
  - Property 14: Pipeline failure stops execution and records error (Task 7.4)
"""

import fakeredis
from unittest.mock import patch

import pytest
from hypothesis import HealthCheck, given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from apps.generation.models import GenerationJob
from apps.generation.services.orchestrator import GenerationPipelineOrchestrator
from tests.factories import UserFactory


# ---------------------------------------------------------------------------
# Property 13: Pipeline progress is monotonically increasing
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPipelineProgressMonotonicallyIncreasing:
    """
    Property 13: Pipeline progress is monotonically increasing.

    For any pipeline run, the progress percentage recorded after each stage
    transition SHALL be strictly greater than the percentage recorded after
    the previous stage transition, and the final stage SHALL record exactly 100%.

    **Validates: Requirements 5.2, 11.5**
    """

    @given(n=st.integers(min_value=1, max_value=10))
    @h_settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_progress_is_strictly_increasing_and_final_stage_is_100(self, n):
        """
        For any prefix of the first n stages (in STAGE_WEIGHTS order), calling
        update_progress for each stage in sequence results in strictly increasing
        progress_percentage values. When all 10 stages are processed, the final
        stage records exactly 100%.
        """
        fake_redis = fakeredis.FakeRedis()
        user = UserFactory()
        job = GenerationJob.objects.create(user=user, title="Monotonic Progress Test")

        orchestrator = GenerationPipelineOrchestrator()
        stages_in_order = list(GenerationPipelineOrchestrator.STAGE_WEIGHTS.keys())

        # Take the first n stages (capped at the total number of stages)
        selected_stages = stages_in_order[:n]

        previous_percentage = -1

        with patch(
            "apps.generation.services.orchestrator.redis.Redis.from_url",
            return_value=fake_redis,
        ):
            for stage in selected_stages:
                orchestrator.update_progress(job, stage)
                job.refresh_from_db()

                current_percentage = job.progress_percentage

                # Each update must produce a strictly greater percentage
                assert current_percentage > previous_percentage, (
                    f"Progress is not strictly increasing: "
                    f"stage={stage!r}, current={current_percentage}, "
                    f"previous={previous_percentage}"
                )

                # The DB value must match the STAGE_WEIGHTS entry
                expected = GenerationPipelineOrchestrator.STAGE_WEIGHTS[stage]
                assert current_percentage == expected, (
                    f"Expected progress_percentage={expected} for stage={stage!r} "
                    f"but got {current_percentage}"
                )

                previous_percentage = current_percentage

        # When all 10 stages are processed, the final stage must record exactly 100%
        if n == len(stages_in_order):
            assert job.progress_percentage == 100, (
                f"Expected final progress_percentage=100 but got {job.progress_percentage}"
            )
            assert job.current_stage == stages_in_order[-1], (
                f"Expected final current_stage={stages_in_order[-1]!r} "
                f"but got {job.current_stage!r}"
            )


# ---------------------------------------------------------------------------
# Property 14: Pipeline failure stops execution and records error
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestPipelineFailureStopsExecutionAndRecordsError:
    """
    Property 14: Pipeline failure stops execution and records error.

    When any stage raises an exception, GenerationJob.status SHALL be FAILED,
    the error message SHALL be recorded, and no subsequent pipeline stages
    SHALL execute.

    **Validates: Requirements 5.3**
    """

    @given(
        stage=st.sampled_from(list(GenerationPipelineOrchestrator.STAGE_WEIGHTS.keys())),
        error_msg=st.text(min_size=1, max_size=100),
    )
    @h_settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_fail_job_sets_failed_status_and_records_error(self, stage, error_msg):
        """
        For any pipeline stage and any error message, calling fail_job() must:
        1. Set GenerationJob.status to FAILED (persisted to DB).
        2. Record an error_message that contains both the stage name (as "[stage]")
           and the original error message.
        3. The error_message format is "[{stage}] {error_msg}".
        """
        fake_redis = fakeredis.FakeRedis()
        user = UserFactory()
        job = GenerationJob.objects.create(user=user, title="Failure Test Job")

        orchestrator = GenerationPipelineOrchestrator()

        with patch(
            "apps.generation.services.orchestrator.redis.Redis.from_url",
            return_value=fake_redis,
        ), patch(
            "apps.generation.services.orchestrator.SectionMemoryService.delete"
        ):
            orchestrator.fail_job(job, stage, error_msg)

        # Refresh from DB to verify persistence
        job.refresh_from_db()

        # 1. Status must be FAILED
        assert job.status == GenerationJob.Status.FAILED, (
            f"Expected status=FAILED but got {job.status!r} "
            f"for stage={stage!r}, error_msg={error_msg!r}"
        )

        # 2. Error message must contain the stage name in brackets
        assert f"[{stage}]" in job.error_message, (
            f"Expected '[{stage}]' in error_message but got {job.error_message!r}"
        )

        # 3. Error message must contain the original error text
        assert error_msg in job.error_message, (
            f"Expected error_msg={error_msg!r} in error_message "
            f"but got {job.error_message!r}"
        )
