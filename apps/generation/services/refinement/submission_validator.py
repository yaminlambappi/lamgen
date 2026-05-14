"""
SubmissionValidator: final audit, scoring, and RefinementResult persistence.

Uses StaticAnalyser for final audit scores (zero LLM calls for scoring).
Triggers auto-refinement (Opus) when submission readiness score < 70 or
AI suspicion score > 65.
"""
from __future__ import annotations

from apps.generation.models import (
    AssignmentBrief,
    GeneratedSection,
    GenerationJob,
    RefinementResult,
)


class SubmissionValidator:
    """
    Runs the final audit, computes the Submission_Readiness_Score, and
    persists the RefinementResult.

    Score weights::

        SCORE_WEIGHTS = {
            'ai_suspicion_inverted': 0.25,
            'rubric_coverage':       0.25,
            'citation_completeness': 0.20,
            'human_realism':         0.15,
            'word_count_compliance': 0.15,
        }

    Timeout: if 300 seconds elapse before the audit completes, logs a
    WARNING and proceeds with scores defaulting incomplete fields to 50.0.
    """

    SCORE_WEIGHTS: dict[str, float] = {
        "ai_suspicion_inverted": 0.25,
        "rubric_coverage": 0.25,
        "citation_completeness": 0.20,
        "human_realism": 0.15,
        "word_count_compliance": 0.15,
    }

    TIMEOUT_SECONDS: int = 300

    def process(
        self,
        sections: list[GeneratedSection],
        brief: AssignmentBrief,
        job: GenerationJob,
        scores: dict,
    ) -> RefinementResult:
        """
        Run the final submission validation pass.

        - Uses StaticAnalyser.compute_ai_suspicion_score() and
          compute_human_realism_score() for final audit scores.
        - Computes Submission_Readiness_Score via _compute_submission_readiness_score().
        - Triggers auto-refinement (Opus) if score < 70 or ai_suspicion > 65;
          performs at most one auto-refinement pass.
        - Updates job.current_stage = 'auto_refinement' and calls
          orchestrator.update_progress(job, 'auto_refinement') when triggered.
        - Tracks elapsed time; if ≥ TIMEOUT_SECONDS, logs WARNING and
          defaults incomplete scores to 50.0.
        - Creates and returns a persisted RefinementResult with all audit
          scores, cost fields, and skipped_stages.
        - Sets job.status = REFINEMENT_COMPLETE on success.

        Returns the persisted RefinementResult instance.
        """
        raise NotImplementedError

    def _compute_submission_readiness_score(self, scores: dict) -> float:
        """
        Compute the weighted submission readiness score::

            (100 - ai_suspicion) * 0.25
            + rubric_coverage    * 0.25
            + citation_completeness * 0.20
            + human_realism      * 0.15
            + word_count_compliance_score * 0.15

        Returns a float in [0.0, 100.0].
        """
        raise NotImplementedError
