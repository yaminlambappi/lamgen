"""
Property-based tests for AssignmentIntelligenceEngine.

Covers:
  - Property 8: Assignment Brief extraction completeness (Task 6.2)
"""

import json
from unittest.mock import patch

import pytest
from hypothesis import HealthCheck, given
from hypothesis import settings as h_settings
from hypothesis import strategies as st

from apps.generation.models import AssignmentBrief, GenerationJob
from apps.generation.services.assignment_intelligence import AssignmentIntelligenceEngine
from tests.factories import UserFactory


# ---------------------------------------------------------------------------
# Property 8: Assignment Brief extraction completeness
# ---------------------------------------------------------------------------


@pytest.mark.django_db
class TestAssignmentBriefExtractionCompleteness:
    """
    Property 8: Assignment Brief extraction completeness.

    For any document text with clearly stated metadata, analyse() produces an
    AssignmentBrief with all required fields populated and persisted before the
    pipeline proceeds.

    **Validates: Requirements 2.1, 2.2, 2.3, 2.8**
    """

    @given(
        topic=st.text(min_size=5, max_size=100),
        subject_area=st.text(min_size=3, max_size=50),
        assignment_type=st.sampled_from(
            ['essay', 'report', 'case_study', 'literature_review', 'thesis_chapter', 'other']
        ),
        academic_level=st.sampled_from(['undergraduate', 'postgraduate', 'doctoral']),
        citation_style=st.sampled_from(['APA', 'Harvard', 'Chicago', 'Vancouver']),
        writing_tone=st.sampled_from(
            ['critical_analytical', 'descriptive_explanatory', 'reflective', 'professional_report']
        ),
    )
    @h_settings(
        max_examples=50,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture],
    )
    def test_analyse_produces_complete_assignment_brief(
        self,
        topic,
        subject_area,
        assignment_type,
        academic_level,
        citation_style,
        writing_tone,
    ):
        """
        For any combination of valid assignment metadata values, AssignmentIntelligenceEngine
        .analyse() must:
        1. Return an AssignmentBrief with all required fields populated.
        2. Persist the brief to the database before returning.
        3. Set job.status to ANALYSING.
        """
        user = UserFactory()
        job = GenerationJob.objects.create(user=user, title="Test Job")

        # Build the JSON payload that the mocked ClaudeService.call will return
        # for the combined_analysis stage (Stages 1+2 merged).
        combined_analysis_response = json.dumps({
            "brief": {
                "topic": topic,
                "subject_area": subject_area,
                "assignment_type": assignment_type,
                "academic_level": academic_level,
                "required_sections": ["Introduction", "Body", "Conclusion"],
                "citation_style": citation_style,
                "writing_tone": writing_tone,
                "formatting_instructions": "",
                "required_frameworks": [],
                "organisational_context": "",
            },
            "rubric_criteria": [],
        })

        def mock_claude_call(system_prompt, user_prompt, max_tokens, job, stage_label, config=None):
            if stage_label == 'combined_analysis':
                return combined_analysis_response
            return "[]"

        text_chunks = [
            f"Assignment topic: {topic}. Subject area: {subject_area}. "
            f"This is a {assignment_type} at {academic_level} level. "
            f"Use {citation_style} citation style. "
            f"Writing tone: {writing_tone}."
        ]

        with patch(
            "apps.generation.services.assignment_intelligence.ClaudeService.call",
            side_effect=mock_claude_call,
        ):
            brief = AssignmentIntelligenceEngine().analyse(text_chunks, job)

        # 1. The returned object must be an AssignmentBrief
        assert isinstance(brief, AssignmentBrief), (
            f"Expected AssignmentBrief instance but got {type(brief)}"
        )

        # 2. All required fields must be populated (non-empty)
        assert brief.topic, (
            f"Expected brief.topic to be populated but got {brief.topic!r}"
        )
        assert brief.subject_area, (
            f"Expected brief.subject_area to be populated but got {brief.subject_area!r}"
        )
        assert brief.assignment_type, (
            f"Expected brief.assignment_type to be populated but got {brief.assignment_type!r}"
        )
        assert brief.academic_level, (
            f"Expected brief.academic_level to be populated but got {brief.academic_level!r}"
        )
        assert brief.required_sections is not None, (
            "Expected brief.required_sections to be populated but got None"
        )
        assert brief.citation_style, (
            f"Expected brief.citation_style to be populated but got {brief.citation_style!r}"
        )
        assert brief.writing_tone, (
            f"Expected brief.writing_tone to be populated but got {brief.writing_tone!r}"
        )

        # 3. Field values must match the mocked Claude response
        assert brief.topic == topic, (
            f"Expected topic={topic!r} but got {brief.topic!r}"
        )
        assert brief.subject_area == subject_area, (
            f"Expected subject_area={subject_area!r} but got {brief.subject_area!r}"
        )
        assert brief.assignment_type == assignment_type, (
            f"Expected assignment_type={assignment_type!r} but got {brief.assignment_type!r}"
        )
        assert brief.academic_level == academic_level, (
            f"Expected academic_level={academic_level!r} but got {brief.academic_level!r}"
        )
        assert brief.citation_style == citation_style, (
            f"Expected citation_style={citation_style!r} but got {brief.citation_style!r}"
        )
        assert brief.writing_tone == writing_tone, (
            f"Expected writing_tone={writing_tone!r} but got {brief.writing_tone!r}"
        )

        # 4. The brief must be persisted to the database before the pipeline proceeds
        assert AssignmentBrief.objects.filter(job=job).exists(), (
            f"Expected AssignmentBrief to be persisted for job={job.pk} but none found"
        )

        # 5. The persisted brief must match the returned brief
        persisted_brief = AssignmentBrief.objects.get(job=job)
        assert persisted_brief.pk == brief.pk, (
            f"Persisted brief pk={persisted_brief.pk} does not match returned brief pk={brief.pk}"
        )

        # 6. job.status must be ANALYSING after the call
        job.refresh_from_db()
        assert job.status == GenerationJob.Status.ANALYSING, (
            f"Expected job.status=ANALYSING but got {job.status!r}"
        )
