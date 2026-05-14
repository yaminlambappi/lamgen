"""
UnifiedRefinementEngine — light citation alignment pass only.

The previous aggressive rewrite pipeline (humanization → rewrite → evaluate →
fix → cleanup) has been replaced with a single light validation pass that:
- Checks citation format consistency (Sonnet)
- Skips sections that have no citation issues
- Does NOT rewrite paragraphs, normalise sentence structure, or enforce symmetry

The natural writing quality is now handled upstream by Opus with persona +
continuity memory injection. Refinement's job is only to ensure citation
consistency and factual plausibility — not to "clean up" the writing.
"""
from __future__ import annotations

import logging
import re

from apps.generation.models import AssignmentBrief, GeneratedSection, GenerationJob
from apps.generation.services.claude_service import ClaudeService
from apps.generation.prompts.templates import CITATION_VALIDATION_PROMPT

logger = logging.getLogger(__name__)

# Citation placeholder pattern — [Author, Year] or (Author, Year)
_CITATION_PATTERN = re.compile(r'\[[\w\s&,\.]+,\s*\d{4}\]|\([\w\s&,\.]+,\s*\d{4}\)')


def _has_citation_issues(content: str, citation_style: str) -> bool:
    """
    Quick heuristic check: returns True only if citations are present but
    appear inconsistently formatted (mixing bracket styles).
    """
    square = len(re.findall(r'\[[\w\s&,\.]+,\s*\d{4}\]', content))
    round_ = len(re.findall(r'\([\w\s&,\.]+,\s*\d{4}\)', content))
    # Mixed styles in the same section = inconsistency
    if square > 0 and round_ > 0:
        return True
    return False


class UnifiedRefinementEngine:
    """
    Light citation alignment pass.

    For each section:
    1. Check if citations are present and inconsistently formatted.
    2. If no issues: skip (zero LLM calls).
    3. If issues: single Sonnet call to fix citation format only.

    Does NOT rewrite content, restructure paragraphs, or normalise writing.
    """

    def __init__(self) -> None:
        self.skipped_stages: list[str] = []

    def process(
        self,
        sections: list[GeneratedSection],
        brief: AssignmentBrief,
        job: GenerationJob,
    ) -> list[GeneratedSection]:
        """
        Run light citation validation on all sections.
        Returns the (possibly updated) list of sections.
        """
        claude = ClaudeService()

        for section in sections:
            if not _has_citation_issues(section.content, brief.citation_style):
                self.skipped_stages.append(f"citation_check:section_{section.order}:skipped_clean")
                logger.debug(
                    "refinement | job=%s section=%d title=%r status=skipped reason=no_citation_issues",
                    job.id, section.order, section.title,
                )
                continue

            logger.info(
                "refinement | job=%s section=%d title=%r status=citation_fix_needed",
                job.id, section.order, section.title,
            )

            try:
                fixed = claude.call(
                    system_prompt=(
                        "You are an academic editor. Fix citation formatting only. "
                        "Do not change any other content."
                    ),
                    user_prompt=CITATION_VALIDATION_PROMPT.format(
                        citation_style=brief.citation_style,
                        section_content=section.content,
                    ),
                    max_tokens=len(section.content.split()) * 2,  # generous cap
                    job=job,
                    stage_label=f"citation_fix_{section.order}",
                    model_override='sonnet',
                )
                section.content = fixed
                section.save(update_fields=["content"])
                logger.info(
                    "refinement | job=%s section=%d title=%r status=citation_fixed",
                    job.id, section.order, section.title,
                )
            except Exception as exc:
                logger.warning(
                    "refinement | job=%s section=%d title=%r "
                    "status=citation_fix_failed error=%s — keeping original",
                    job.id, section.order, section.title, exc,
                )

        return sections
