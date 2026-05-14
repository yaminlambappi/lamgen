"""
Property-based tests for SectionMemoryService.

**Validates: Requirements 4.1, 4.2, 4.4, 4.5, 4.6, 8.5**
"""
import fakeredis
import pytest
from unittest.mock import patch

from hypothesis import HealthCheck, given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from apps.generation.models import GenerationJob
from apps.generation.services.orchestrator import GenerationPipelineOrchestrator
from apps.generation.services.section_memory import SectionMemoryService
from tests.factories import UserFactory


# ---------------------------------------------------------------------------
# Property 9: Section Memory initialisation and TTL
# ---------------------------------------------------------------------------

class TestSectionMemoryInitialisationAndTTL:
    """
    Property 9: Section Memory initialisation and TTL.

    After SectionMemoryService.initialise(job_id), the Redis key
    ``section_memory:{job_id}`` must exist and have a TTL between
    14,000 and 14,400 seconds.

    **Validates: Requirements 4.1, 4.4**
    """

    @given(
        job_id=st.text(
            min_size=1,
            max_size=50,
            alphabet=st.characters(
                whitelist_categories=("Lu", "Ll", "Nd"),
                whitelist_characters="-_",
            ),
        )
    )
    @h_settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_redis_key_exists_with_correct_ttl(self, job_id):
        """
        For any valid job_id, after initialise() the Redis key must exist
        and its TTL must be in the range [14_000, 14_400] seconds.
        """
        fake_redis = fakeredis.FakeRedis()

        with patch.object(SectionMemoryService, "_get_redis", return_value=fake_redis):
            SectionMemoryService.initialise(job_id)

            key = SectionMemoryService._redis_key(job_id)

            # Key must exist
            assert fake_redis.exists(key), (
                f"Redis key {key!r} does not exist after initialise(job_id={job_id!r})"
            )

            # TTL must be within the expected window
            ttl = fake_redis.ttl(key)
            assert 14_000 <= ttl <= 14_400, (
                f"Expected TTL in [14000, 14400] but got {ttl} "
                f"for job_id={job_id!r}"
            )


# ---------------------------------------------------------------------------
# Property 10: Section Memory update accumulates without duplicates
# ---------------------------------------------------------------------------

class TestSectionMemoryUpdateNoDuplicates:
    """
    Property 10: Section Memory update accumulates without duplicates.

    After any sequence of section updates, ``citations_used`` contains all
    citations with no duplicate entries.

    **Validates: Requirements 4.2, 4.6, 8.5**
    """

    @given(
        citation_batches=st.lists(
            st.lists(
                st.text(min_size=1, max_size=30),
                min_size=0,
                max_size=10,
            ),
            min_size=1,
            max_size=10,
        )
    )
    @h_settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_citations_accumulate_without_duplicates(self, citation_batches):
        """
        For any sequence of citation batches, after applying all updates:
        1. citations_used contains no duplicate entries.
        2. Every unique citation from every batch is present in citations_used.
        """
        fake_redis = fakeredis.FakeRedis()
        job_id = "test-dedup-job"

        with patch.object(SectionMemoryService, "_get_redis", return_value=fake_redis):
            # Initialise a fresh SectionMemory for this job
            SectionMemoryService.initialise(job_id)

            # Apply each batch as a separate update
            for batch in citation_batches:
                SectionMemoryService.update(job_id, {"citations_used": batch})

            # Retrieve the final state
            memory = SectionMemoryService.get(job_id)

        # 1. No duplicates
        assert len(memory.citations_used) == len(set(memory.citations_used)), (
            f"citations_used contains duplicates: {memory.citations_used}"
        )

        # 2. All unique citations from all batches must be present
        all_unique_citations = set()
        for batch in citation_batches:
            all_unique_citations.update(batch)

        for citation in all_unique_citations:
            assert citation in memory.citations_used, (
                f"Citation {citation!r} is missing from citations_used: "
                f"{memory.citations_used}"
            )


# ---------------------------------------------------------------------------
# Property 12: Section Memory deleted on job completion or failure
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestSectionMemoryDeletedOnJobCompletionOrFailure:
    """
    Property 12: Section Memory deleted on job completion or failure.

    After GenerationJob transitions to COMPLETED or FAILED, the Redis key
    ``section_memory:{job_id}`` SHALL no longer exist.

    **Validates: Requirements 4.5**
    """

    @given(
        final_status=st.sampled_from(
            [GenerationJob.Status.COMPLETED, GenerationJob.Status.FAILED]
        )
    )
    @h_settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_section_memory_key_deleted_after_job_terminal_transition(
        self, final_status
    ):
        """
        For any GenerationJob that transitions to COMPLETED or FAILED:
        1. After SectionMemoryService.initialise(), the Redis key must exist.
        2. After the terminal transition, the Redis key must no longer exist.

        For COMPLETED: SectionMemoryService.delete() is called directly
        (as done in continue_generation_pipeline).
        For FAILED: orchestrator.fail_job() is called, which internally
        calls SectionMemoryService.delete().
        """
        fake_redis = fakeredis.FakeRedis()
        user = UserFactory()
        job = GenerationJob.objects.create(
            user=user, title="Section Memory Deletion Test"
        )
        job_id = str(job.id)

        if final_status == GenerationJob.Status.COMPLETED:
            # COMPLETED path: patch only SectionMemoryService._get_redis
            with patch.object(
                SectionMemoryService, "_get_redis", return_value=fake_redis
            ):
                # Initialise and verify key exists
                SectionMemoryService.initialise(job_id)
                key = SectionMemoryService._redis_key(job_id)
                assert fake_redis.exists(key), (
                    f"Redis key {key!r} should exist after initialise() "
                    f"for job_id={job_id!r}"
                )

                # Simulate COMPLETED transition: delete section memory
                SectionMemoryService.delete(job_id)

                # Key must no longer exist
                assert not fake_redis.exists(key), (
                    f"Redis key {key!r} should not exist after delete() "
                    f"(COMPLETED transition) for job_id={job_id!r}"
                )

        else:
            # FAILED path: patch both orchestrator Redis and SectionMemoryService._get_redis
            # so that fail_job()'s internal SectionMemoryService.delete() uses the same
            # fakeredis instance as the initialise() call.
            with patch(
                "apps.generation.services.orchestrator.redis.Redis.from_url",
                return_value=fake_redis,
            ), patch.object(
                SectionMemoryService, "_get_redis", return_value=fake_redis
            ):
                # Initialise and verify key exists
                SectionMemoryService.initialise(job_id)
                key = SectionMemoryService._redis_key(job_id)
                assert fake_redis.exists(key), (
                    f"Redis key {key!r} should exist after initialise() "
                    f"for job_id={job_id!r}"
                )

                # Simulate FAILED transition via orchestrator.fail_job()
                orchestrator = GenerationPipelineOrchestrator()
                orchestrator.fail_job(job, "test_stage", "test error")

                # Key must no longer exist
                assert not fake_redis.exists(key), (
                    f"Redis key {key!r} should not exist after fail_job() "
                    f"(FAILED transition) for job_id={job_id!r}"
                )
