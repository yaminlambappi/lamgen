"""
Property-based tests for GenerationJob model invariants.

**Validates: Requirements 11.1**
"""
import pytest
from hypothesis import HealthCheck, given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from apps.generation.models import GenerationJob
from tests.factories import UserFactory


@pytest.mark.django_db
class TestGenerationJobCreationInvariant:
    """
    Property 26: Generation Job creation invariant.

    For any new GenerationJob, the UUID primary key is unique across all jobs
    and the initial status is PENDING.

    **Validates: Requirements 11.1**
    """

    @given(count=st.integers(min_value=1, max_value=50))
    @h_settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
        deadline=None,
    )
    def test_generation_job_uuid_unique_and_status_pending(self, count):
        """
        For any batch of `count` newly created GenerationJob instances:
        - Each job has a UUID primary key that is unique across all jobs in the batch.
        - Each job's initial status is PENDING.
        """
        user = UserFactory()

        jobs = [
            GenerationJob.objects.create(
                user=user,
                title=f"Test Job {i}",
            )
            for i in range(count)
        ]

        # Collect all primary keys
        pks = [job.pk for job in jobs]

        # 1. All UUIDs must be unique
        assert len(pks) == len(set(pks)), (
            f"Expected {count} unique UUIDs but found duplicates: {pks}"
        )

        # 2. Every job must start with PENDING status
        for job in jobs:
            assert job.status == GenerationJob.Status.PENDING, (
                f"Expected status PENDING but got {job.status!r} for job {job.pk}"
            )
