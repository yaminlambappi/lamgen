"""
OutlineGenerationService — Stage 3 (outline generation).

Uses GenerationConfig for token budgets. Falls back to a deterministic
outline when required_sections are already specified in the brief,
saving one Claude call entirely.
"""

import json
import logging

from generation.models import AssignmentBrief, DocumentOutline, GenerationJob
from generation.services.claude_service import ClaudeService
from generation.services.generation_config import GenerationConfig
from generation.prompts.templates import OUTLINE_GENERATION_PROMPT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Deterministic fallback outlines — zero API cost when brief has sections
# ---------------------------------------------------------------------------

_DEFAULT_OUTLINES: dict[str, list[str]] = {
    'essay': ['Introduction', 'Literature Review', 'Analysis', 'Discussion', 'Conclusion'],
    'report': ['Executive Summary', 'Introduction', 'Methodology', 'Findings', 'Recommendations', 'Conclusion'],
    'case_study': ['Introduction', 'Background', 'Analysis', 'Discussion', 'Conclusion'],
    'literature_review': ['Introduction', 'Thematic Review', 'Critical Analysis', 'Synthesis', 'Conclusion'],
    'thesis_chapter': ['Introduction', 'Literature Review', 'Methodology', 'Results', 'Discussion', 'Conclusion'],
    'other': ['Introduction', 'Main Body', 'Analysis', 'Conclusion'],
}


def _build_fallback_sections(
    section_titles: list[str],
    target_word_count: int,
) -> list[dict]:
    """
    Build a deterministic outline from a list of section titles.
    Distributes word counts evenly with intro/conclusion getting 60% of the per-section average.
    """
    n = len(section_titles)
    if n == 0:
        return []

    base = target_word_count // n
    sections = []
    for title in section_titles:
        title_lower = title.lower()
        if title_lower in ('introduction', 'executive summary', 'conclusion', 'references', 'bibliography'):
            wc = max(150, int(base * 0.6))
        else:
            wc = base
        sections.append({
            'title': title,
            'target_word_count': wc,
            'key_points': [f'Address key aspects of {title}', f'Analyse implications for {title}'],
        })

    # Normalise to hit target_word_count exactly
    total = sum(s['target_word_count'] for s in sections)
    if total != target_word_count and sections:
        sections[-1]['target_word_count'] += target_word_count - total

    return sections


class OutlineGenerationError(Exception):
    """Raised when Claude's response cannot be parsed into a valid document outline."""


class OutlineGenerationService:

    def __init__(self, config: GenerationConfig | None = None) -> None:
        self.config = config or GenerationConfig()

    def generate(self, job: GenerationJob, brief: AssignmentBrief) -> DocumentOutline:
        """
        Generate a DocumentOutline.

        Fast path: if the brief already has required_sections, build the outline
        deterministically (zero API cost). Only calls Claude when sections are
        unknown or when the config section_mode is 'auto' with no sections.
        """
        rubric = getattr(brief, 'rubric', None)

        # --- Fast path: deterministic outline ---
        if brief.required_sections and self.config.section_mode != 'fixed':
            sections_list = _build_fallback_sections(
                brief.required_sections, job.target_word_count
            )
            logger.info(
                "Outline built deterministically from required_sections for job %s", job.id
            )
        else:
            # Determine section titles to use
            if self.config.section_mode == 'fixed' or not brief.required_sections:
                fallback_titles = _DEFAULT_OUTLINES.get(
                    brief.assignment_type,
                    _DEFAULT_OUTLINES['other'],
                )
                # Still call Claude but with the fallback titles as a hint
                sections_list = self._call_claude_for_outline(job, brief, rubric, fallback_titles)
            else:
                sections_list = self._call_claude_for_outline(job, brief, rubric, [])

        # Apply rubric-based word count distribution
        sections_list = self._distribute_word_counts(sections_list, rubric, job.target_word_count)

        outline = DocumentOutline.objects.create(
            job=job,
            sections=sections_list,
            user_confirmed=False,
        )
        job.status = GenerationJob.Status.AWAITING_OUTLINE_REVIEW
        job.save(update_fields=['status'])
        return outline

    def _call_claude_for_outline(
        self,
        job: GenerationJob,
        brief: AssignmentBrief,
        rubric,
        hint_titles: list[str],
    ) -> list[dict]:
        """Call Claude to generate an outline. Falls back to deterministic on parse error."""
        assignment_brief_str = self._format_brief(brief, hint_titles)
        rubric_profile_str = self._format_rubric(rubric) if rubric else "No rubric"

        response = ClaudeService().call(
            system_prompt="You are an expert academic document planner. Return only valid JSON.",
            user_prompt=OUTLINE_GENERATION_PROMPT.format(
                assignment_brief=assignment_brief_str,
                rubric_profile=rubric_profile_str,
                target_word_count=job.target_word_count,
            ),
            max_tokens=self.config.outline_max_tokens,
            job=job,
            stage_label='outline_generation',
            config=self.config,
        )

        cleaned = response.strip()
        if cleaned.startswith('```'):
            first_newline = cleaned.find('\n')
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3].rstrip()

        try:
            sections_list = json.loads(cleaned)
            if not isinstance(sections_list, list):
                raise OutlineGenerationError("Expected JSON array")
            return sections_list
        except (json.JSONDecodeError, OutlineGenerationError) as exc:
            logger.warning(
                "Outline parse error for job %s, using deterministic fallback: %s", job.id, exc
            )
            titles = hint_titles or _DEFAULT_OUTLINES.get(brief.assignment_type, _DEFAULT_OUTLINES['other'])
            return _build_fallback_sections(titles, job.target_word_count)

    def _format_brief(self, brief: AssignmentBrief, hint_titles: list[str] = None) -> str:
        lines = [
            f"Topic: {brief.topic}",
            f"Type: {brief.assignment_type}",
            f"Level: {brief.academic_level}",
            f"Tone: {brief.writing_tone}",
        ]
        if brief.required_frameworks:
            lines.append(f"Frameworks: {', '.join(brief.required_frameworks)}")
        if hint_titles:
            lines.append(f"Suggested sections: {', '.join(hint_titles)}")
        elif brief.required_sections:
            lines.append(f"Required sections: {', '.join(brief.required_sections)}")
        return "\n".join(lines)

    def _format_rubric(self, rubric) -> str:
        """
        Returns a formatted string listing each criterion with name, weight,
        and distinction_descriptor.
        """
        if not rubric or not rubric.criteria:
            return "No rubric criteria available"

        lines = ["Rubric Criteria:"]
        for criterion in rubric.criteria:
            name = criterion.get('name', 'Unknown')
            weight = criterion.get('weight', 0.0)
            descriptor = criterion.get('distinction_descriptor', '')
            lines.append(
                f"  - {name} (weight: {weight:.0%}): {descriptor}"
            )

        return "\n".join(lines)

    def _distribute_word_counts(
        self,
        sections_list: list,
        rubric,
        target_word_count: int,
    ) -> list:
        """
        Distributes word counts across sections.

        If a rubric is present, adjusts section word counts proportionally based
        on rubric criterion weights — sections whose titles match high-weight
        criteria receive more words. Otherwise, keeps Claude's suggested counts
        but normalises them to sum to target_word_count.
        """
        if not sections_list:
            return sections_list

        if rubric is None or not rubric.criteria:
            # No rubric — normalise Claude's suggested counts to target_word_count
            return self._normalise_word_counts(sections_list, target_word_count)

        # Build a mapping from criterion name (lowercased) to weight
        criterion_weights = {
            c.get('name', '').lower(): c.get('weight', 0.0)
            for c in rubric.criteria
        }

        # Assign a rubric weight to each section by fuzzy-matching section titles
        section_weights = []
        for section in sections_list:
            title_lower = section.get('title', '').lower()
            # Find the best matching criterion weight for this section title
            best_weight = 0.0
            for criterion_name, weight in criterion_weights.items():
                # Check if criterion name appears in section title or vice versa
                if criterion_name in title_lower or title_lower in criterion_name:
                    if weight > best_weight:
                        best_weight = weight
            section_weights.append(best_weight)

        total_matched_weight = sum(section_weights)

        if total_matched_weight == 0.0:
            # No sections matched any rubric criteria — fall back to normalisation
            return self._normalise_word_counts(sections_list, target_word_count)

        # Sections with no rubric match get a base allocation (equal share of unmatched words)
        unmatched_count = sum(1 for w in section_weights if w == 0.0)
        matched_count = len(sections_list) - unmatched_count

        # Allocate 80% of words to rubric-matched sections, 20% equally to unmatched
        # (or 100% to matched if all sections matched)
        if unmatched_count == 0:
            matched_budget = target_word_count
            unmatched_per_section = 0
        else:
            matched_budget = int(target_word_count * 0.80)
            unmatched_budget = target_word_count - matched_budget
            unmatched_per_section = unmatched_budget // unmatched_count

        # Distribute matched budget proportionally by weight
        updated_sections = []
        remainder = target_word_count
        for i, (section, weight) in enumerate(zip(sections_list, section_weights)):
            section = dict(section)  # shallow copy to avoid mutating input
            if weight > 0.0:
                proportion = weight / total_matched_weight
                word_count = int(matched_budget * proportion)
            else:
                word_count = unmatched_per_section

            # Ensure minimum of 100 words per section
            word_count = max(100, word_count)
            section['target_word_count'] = word_count
            updated_sections.append(section)

        # Adjust the last section to absorb any rounding difference
        total_assigned = sum(s['target_word_count'] for s in updated_sections)
        if updated_sections and total_assigned != target_word_count:
            diff = target_word_count - total_assigned
            updated_sections[-1]['target_word_count'] = max(
                100, updated_sections[-1]['target_word_count'] + diff
            )

        return updated_sections

    def _normalise_word_counts(
        self, sections_list: list, target_word_count: int
    ) -> list:
        """
        Scales Claude's suggested word counts so they sum to target_word_count.
        """
        current_total = sum(
            s.get('target_word_count', 0) for s in sections_list
        )

        if current_total == 0:
            # Distribute evenly if Claude provided no counts
            per_section = target_word_count // len(sections_list)
            updated = []
            for i, section in enumerate(sections_list):
                section = dict(section)
                section['target_word_count'] = per_section
                updated.append(section)
            # Absorb remainder in last section
            if updated:
                remainder = target_word_count - per_section * len(sections_list)
                updated[-1]['target_word_count'] += remainder
            return updated

        # Scale proportionally
        updated = []
        for section in sections_list:
            section = dict(section)
            original = section.get('target_word_count', 0)
            scaled = int(round(original / current_total * target_word_count))
            section['target_word_count'] = max(100, scaled)
            updated.append(section)

        # Adjust last section for rounding
        total_assigned = sum(s['target_word_count'] for s in updated)
        if updated and total_assigned != target_word_count:
            diff = target_word_count - total_assigned
            updated[-1]['target_word_count'] = max(
                100, updated[-1]['target_word_count'] + diff
            )

        return updated
