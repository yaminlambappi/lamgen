"""
AssignmentIntelligenceEngine — Stages 1 + 2 combined.

Single Claude call extracts both the AssignmentBrief and the RubricProfile.
Rubric extraction is skipped entirely (no API call) when the document shows
no rubric keywords — saving ~2,500 input tokens per job.
"""

import json
import re
import logging

from apps.generation.models import AssignmentBrief, GenerationJob, RubricProfile
from apps.generation.services.claude_service import ClaudeService
from apps.generation.services.generation_config import GenerationConfig
from apps.generation.prompts.templates import build_combined_analysis_prompt

logger = logging.getLogger(__name__)

# Keywords that indicate a rubric is present in the document
_RUBRIC_KEYWORDS = re.compile(
    r'\b(rubric|marking criteria|assessment criteria|marks allocated|'
    r'grading criteria|mark scheme|marking scheme|criterion|criteria)\b',
    re.IGNORECASE,
)


class BriefExtractionError(Exception):
    """Raised when Claude's response cannot be parsed into a valid AssignmentBrief."""


class AssignmentIntelligenceEngine:
    VALID_ACADEMIC_LEVELS = {'undergraduate', 'postgraduate', 'doctoral'}
    VALID_ASSIGNMENT_TYPES = {
        'essay', 'report', 'case_study', 'literature_review', 'thesis_chapter', 'other'
    }
    VALID_WRITING_TONES = {
        'critical_analytical', 'descriptive_explanatory', 'reflective', 'professional_report'
    }

    def __init__(self, config: GenerationConfig | None = None) -> None:
        self.config = config or GenerationConfig()

    def analyse(self, text_chunks: list[str], job: GenerationJob) -> AssignmentBrief:
        """
        Combined Stage 1 + Stage 2: one Claude call extracts both the brief
        and the rubric (if present).

        Sets job.status = ANALYSING, calls Claude with COMBINED_ANALYSIS_PROMPT,
        persists AssignmentBrief and optionally RubricProfile, returns the brief.
        """
        job.status = GenerationJob.Status.ANALYSING
        job.save(update_fields=['status'])

        combined_text = '\n\n---\n\n'.join(text_chunks)
        has_rubric = bool(_RUBRIC_KEYWORDS.search(combined_text))

        user_prompt = build_combined_analysis_prompt(combined_text, has_rubric)
        system_prompt = (
            "You are an expert academic analyst. "
            "Extract structured metadata from assignment documents. Return only valid JSON."
        )

        response = ClaudeService().call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=self.config.analysis_max_tokens,
            job=job,
            stage_label='combined_analysis',
            model_override='haiku',  # Haiku: fast, cheap metadata extraction
        )

        data = self._parse_response(response)
        brief = self._persist_brief(job, data.get('brief', data))

        # Persist rubric only if the document had rubric keywords and Claude returned criteria
        if has_rubric:
            criteria = data.get('rubric_criteria', [])
            if isinstance(criteria, list) and criteria:
                RubricProfile.objects.create(brief=brief, criteria=criteria)

        return brief

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _parse_response(self, response: str) -> dict:
        """Strip markdown fences and parse JSON. Raises BriefExtractionError on failure."""
        cleaned = response.strip()
        if cleaned.startswith('```'):
            first_newline = cleaned.find('\n')
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3].rstrip()
        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise BriefExtractionError(f"Failed to parse analysis response as JSON: {exc}") from exc
        if 'topic' not in parsed and 'brief' not in parsed:
            raise BriefExtractionError("Response missing 'topic' or 'brief' key.")
        return parsed

    def _persist_brief(self, job: GenerationJob, fields: dict) -> AssignmentBrief:
        """Validate, normalise, and persist an AssignmentBrief from parsed fields.

        User-supplied hints (job.assignment_type_hint, citation_style_hint,
        writing_tone_hint) are used as fallbacks when the document analysis
        doesn't produce a valid value — giving the user's explicit choice
        priority over the config default.
        """
        academic_level = fields.get('academic_level', '')
        if academic_level not in self.VALID_ACADEMIC_LEVELS:
            academic_level = AssignmentBrief.AcademicLevel.POSTGRADUATE
            academic_level_inferred = True
        else:
            academic_level_inferred = False

        assignment_type = fields.get('assignment_type', '')
        if assignment_type not in self.VALID_ASSIGNMENT_TYPES:
            # Prefer user's explicit choice over config default
            assignment_type = (
                job.assignment_type_hint
                if job.assignment_type_hint in self.VALID_ASSIGNMENT_TYPES
                else self.config.assignment_type_default
            )

        writing_tone = fields.get('writing_tone', '')
        if writing_tone not in self.VALID_WRITING_TONES:
            writing_tone = (
                job.writing_tone_hint
                if job.writing_tone_hint in self.VALID_WRITING_TONES
                else self.config.writing_tone_default
            )

        # Citation style: document value wins; fall back to user hint, then config default
        citation_style = fields.get('citation_style', '').strip()
        if not citation_style:
            citation_style = job.citation_style_hint or self.config.citation_style_default

        return AssignmentBrief.objects.create(
            job=job,
            topic=fields.get('topic', ''),
            subject_area=fields.get('subject_area', ''),
            assignment_type=assignment_type,
            academic_level=academic_level,
            academic_level_inferred=academic_level_inferred,
            required_sections=fields.get('required_sections', []),
            citation_style=citation_style,
            formatting_instructions=fields.get('formatting_instructions', ''),
            required_frameworks=fields.get('required_frameworks', []),
            writing_tone=writing_tone,
            organisational_context=fields.get('organisational_context', ''),
        )
