"""
ResearchContextService — Stage 5 (research context preparation).

Calls Claude to identify theoretical frameworks, key authors, and core concepts
required for each section of the assignment, then persists the research context
map to the DocumentOutline.
"""

import json
import logging

from apps.generation.models import AssignmentBrief, DocumentOutline, GenerationJob
from apps.generation.services.claude_service import ClaudeService
from apps.generation.prompts.templates import RESEARCH_CONTEXT_PROMPT

logger = logging.getLogger(__name__)


class ResearchContextService:
    """
    Orchestrates Stage 5 (research context preparation).

    Calls Claude with the RESEARCH_CONTEXT_PROMPT to identify the theoretical
    frameworks, key authors, and core concepts that must be engaged with in each
    section. Ensures all required_frameworks from the AssignmentBrief appear in
    the research context for at least one section, then persists the result to
    outline.research_context.
    """

    def prepare(
        self,
        job: GenerationJob,
        brief: AssignmentBrief,
        outline: DocumentOutline,
    ) -> None:
        """
        Prepares the research context for all sections in the outline.

        - Builds a JSON string of section titles from outline.sections.
        - Builds a formatted assignment brief string.
        - Builds a comma-joined required_frameworks string (or "None specified").
        - Calls ClaudeService with RESEARCH_CONTEXT_PROMPT.
        - Parses the JSON response (stripping markdown fences if present).
        - Validates the response is a dict; falls back to empty dict on parse error.
        - Ensures all required_frameworks from brief appear in the research context
          for at least one section; adds missing frameworks to any section that
          lacks them.
        - Saves outline.research_context and calls outline.save().
        """
        # Build sections string (JSON array of section titles)
        section_titles = [
            section.get('title', '') for section in outline.sections
        ]
        sections_str = json.dumps(section_titles)

        # Build required frameworks string
        if brief.required_frameworks:
            required_frameworks_str = ", ".join(brief.required_frameworks)
        else:
            required_frameworks_str = "None specified"

        # Build assignment brief string
        assignment_brief_str = self._format_brief(brief)

        # Call Claude
        response = ClaudeService().call(
            system_prompt=(
                "You are an expert academic researcher. Identify the theoretical "
                "frameworks, key authors, and core concepts required for each section "
                "of an academic assignment."
            ),
            user_prompt=RESEARCH_CONTEXT_PROMPT.format(
                sections=sections_str,
                assignment_brief=assignment_brief_str,
                required_frameworks=required_frameworks_str,
            ),
            max_tokens=2048,
            job=job,
            stage_label='research_context_preparation',
        )

        # Strip markdown fences if present
        cleaned = response.strip()
        if cleaned.startswith('```'):
            first_newline = cleaned.find('\n')
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3].rstrip()

        # Parse the JSON response
        try:
            research_context_dict = json.loads(cleaned)
            if not isinstance(research_context_dict, dict):
                logger.warning(
                    "Research context response is not a dict (got %s) — "
                    "falling back to empty dict.",
                    type(research_context_dict).__name__,
                )
                research_context_dict = {}
        except json.JSONDecodeError as exc:
            logger.warning(
                "Failed to parse research context response as JSON: %s — "
                "falling back to empty dict.",
                exc,
            )
            research_context_dict = {}

        # Ensure all required_frameworks appear in the research context
        if brief.required_frameworks:
            research_context_dict = self._ensure_required_frameworks(
                research_context_dict, brief.required_frameworks, section_titles
            )

        # Persist to the outline
        outline.research_context = research_context_dict
        outline.save(update_fields=['research_context'])

    def _format_brief(self, brief: AssignmentBrief) -> str:
        """
        Returns a formatted string with the core assignment metadata for use
        in the research context prompt.
        """
        lines = [
            f"Topic: {brief.topic}",
            f"Subject Area: {brief.subject_area}",
            f"Assignment Type: {brief.assignment_type}",
            f"Academic Level: {brief.academic_level}",
        ]

        if brief.required_frameworks:
            frameworks_str = ", ".join(brief.required_frameworks)
            lines.append(f"Required Frameworks: {frameworks_str}")

        return "\n".join(lines)

    def _ensure_required_frameworks(
        self,
        research_context: dict,
        required_frameworks: list,
        section_titles: list,
    ) -> dict:
        """
        Ensures every required framework appears in the research context for at
        least one section.

        For each required framework not found in any section's frameworks list,
        adds it to the first available section's frameworks list. If the research
        context is empty or no sections are present, creates a minimal entry for
        the first section title.
        """
        for framework in required_frameworks:
            # Check if this framework already appears in any section
            framework_present = False
            for section_data in research_context.values():
                if isinstance(section_data, dict):
                    section_frameworks = section_data.get('frameworks', [])
                    if framework in section_frameworks:
                        framework_present = True
                        break

            if not framework_present:
                # Add the framework to the first section that exists in the context,
                # or to the first section title if no sections are in the context yet.
                added = False
                for title in section_titles:
                    if title in research_context:
                        section_data = research_context[title]
                        if isinstance(section_data, dict):
                            if 'frameworks' not in section_data:
                                section_data['frameworks'] = []
                            if framework not in section_data['frameworks']:
                                section_data['frameworks'].append(framework)
                            added = True
                            break

                if not added and section_titles:
                    # Create a minimal entry for the first section title
                    first_title = section_titles[0]
                    if first_title not in research_context:
                        research_context[first_title] = {
                            'frameworks': [],
                            'key_authors': [],
                            'core_concepts': [],
                        }
                    section_data = research_context[first_title]
                    if isinstance(section_data, dict):
                        if 'frameworks' not in section_data:
                            section_data['frameworks'] = []
                        if framework not in section_data['frameworks']:
                            section_data['frameworks'].append(framework)

        return research_context
