"""
SectionPlanningService — Stage 4 (section planning).

For each section in the confirmed DocumentOutline, calls Claude with the
SECTION_PLANNING_PROMPT to expand key points into detailed sub-points and
research angles, then merges the enriched plan back into outline.sections.
"""

import json
import logging

from generation.models import AssignmentBrief, DocumentOutline, GenerationJob
from generation.services.claude_service import ClaudeService
from generation.prompts.templates import SECTION_PLANNING_PROMPT

logger = logging.getLogger(__name__)


class SectionPlanningService:
    """
    Orchestrates Stage 4 (section planning).

    Iterates over each section in the confirmed DocumentOutline and calls
    Claude to expand the key points into detailed sub-points, research angles,
    and suggested sources. The enriched data is merged back into the section
    dict and persisted to the database.
    """

    def plan(
        self,
        job: GenerationJob,
        outline: DocumentOutline,
        brief: AssignmentBrief,
    ) -> None:
        """
        Expands each section in the outline with detailed planning data.

        For each section in outline.sections:
        - Calls Claude with SECTION_PLANNING_PROMPT.
        - Parses the JSON response (stripping markdown fences if present).
        - Merges expanded_key_points, research_angles, and suggested_sources
          back into the section dict.
        - On parse error, logs a warning and keeps the original section unchanged.

        After all sections are processed, saves the updated sections list back
        to outline.sections and calls outline.save(update_fields=['sections']).
        """
        brief_str = self._format_brief(brief)
        updated_sections = []

        for i, section in enumerate(outline.sections):
            section = dict(section)  # shallow copy to avoid mutating the original

            user_prompt = SECTION_PLANNING_PROMPT.format(
                section_title=section['title'],
                key_points=json.dumps(section.get('key_points', [])),
                assignment_brief=brief_str,
            )

            response = ClaudeService().call(
                system_prompt=(
                    "You are an expert academic planner. Expand section outlines into "
                    "detailed plans with sub-points and research angles."
                ),
                user_prompt=user_prompt,
                max_tokens=1024,
                job=job,
                stage_label=f'section_planning_{i}',
                model_override='sonnet',  # Sonnet: structural planning
            )

            # Strip markdown fences if present
            cleaned = response.strip()
            if cleaned.startswith('```'):
                first_newline = cleaned.find('\n')
                if first_newline != -1:
                    cleaned = cleaned[first_newline + 1:]
                if cleaned.endswith('```'):
                    cleaned = cleaned[:-3].rstrip()

            # Parse the JSON response and merge into the section dict
            try:
                expanded = json.loads(cleaned)
                section['expanded_key_points'] = expanded.get('expanded_key_points', [])
                section['research_angles'] = expanded.get('research_angles', [])
                section['suggested_sources'] = expanded.get('suggested_sources', [])
            except (json.JSONDecodeError, AttributeError) as exc:
                logger.warning(
                    "Section planning parse error for section %d ('%s'): %s — "
                    "keeping original section unchanged.",
                    i,
                    section.get('title', ''),
                    exc,
                )

            updated_sections.append(section)

        outline.sections = updated_sections
        outline.save(update_fields=['sections'])

    def _format_brief(self, brief: AssignmentBrief) -> str:
        """
        Returns a brief formatted string with the core assignment metadata.
        """
        lines = [
            f"Topic: {brief.topic}",
            f"Subject Area: {brief.subject_area}",
            f"Assignment Type: {brief.assignment_type}",
            f"Academic Level: {brief.academic_level}",
        ]
        return "\n".join(lines)
