"""
ReflectionGenerator: one-pass Sonnet generation for reflection sections.

Handles reflection sections with realism-first prompting. Never uses Opus.
Sections processed here are NOT passed to UnifiedRefinementEngine.
"""
from __future__ import annotations

import logging

from apps.generation.models import AssignmentBrief, GeneratedSection, GenerationJob
from apps.generation.services.claude_service import ClaudeService

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Realism-first prompt templates
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are a student writing a personal reflection for a university assignment.
Your writing must feel genuinely human — imperfect, uncertain, and personal.

Core principles:
- Write with natural uncertainty: use phrases like "I found that", \
"this challenged my assumption that", "I was not entirely sure", \
"looking back, I think", "I hadn't expected", "I realised that"
- Include personal reasoning moments at a rate of at least one per 200 words
- Introduce controlled inconsistency: not every paragraph needs to reach a \
tidy conclusion; some thoughts can trail off or be revisited
- Reduce philosophical tone: avoid grand abstract statements; stay grounded \
in specific experiences and concrete observations
- Vary sentence length naturally — mix short punchy sentences with longer \
reflective ones
- Do NOT use AI-signature phrases such as "fundamentally", "it is worth noting", \
"multifaceted", "robust framework", "seamless integration", "in conclusion", \
"to summarise", "it is clear that", "it is evident that"
- Do NOT use machine-confidence phrases such as "it is undeniable that", \
"clearly", "obviously", "without doubt"
- Write in first person throughout
"""

_USER_PROMPT_TEMPLATE = """\
Refine the following reflection section to read as naturally written student prose.

Requirements:
1. Preserve all factual claims, citations, and rubric-aligned content
2. Keep the word count within ±10% of the original
3. Add natural uncertainty markers ("I found that", "this challenged my \
assumption that", "I was not entirely sure") — at least one per 200 words
4. Include personal reasoning moments — at least one per 200 words
5. Introduce mild controlled inconsistency where appropriate
6. Reduce any philosophical or overly formal tone
7. Do NOT use AI-signature phrases or machine-confidence phrases
8. Maintain first-person perspective throughout

Section title: {title}

Original content:
{content}

Return only the refined section content, with no preamble or commentary.
"""


def _is_reflection_section(section: GeneratedSection) -> bool:
    """
    Identify reflection sections by checking if the section title contains
    'reflection' (case-insensitive).

    GeneratedSection does not have a section_type field, so we use the title
    as the indicator per the task specification.
    """
    return 'reflection' in section.title.lower()


class ReflectionGenerator:
    """
    Dedicated service for reflection sections.

    Performs one-pass generation with realism-first prompting using Sonnet.
    Prompt characteristics:
    - Natural uncertainty markers ("I found that", "this challenged my
      assumption that", "I was not entirely sure")
    - Personal reasoning moments at ≥1 per 200 words
    - Controlled inconsistency
    - Reduced philosophical tone
    """

    def process(
        self,
        sections: list[GeneratedSection],
        brief: AssignmentBrief,
        job: GenerationJob,
    ) -> list[GeneratedSection]:
        """
        Generate or refine reflection sections in a single Sonnet pass.

        Filters *sections* to only those whose title contains 'reflection'
        (case-insensitive). Non-reflection sections are returned unmodified.

        Uses ``model_override='sonnet'`` exclusively — never Opus.
        Increments ``section.refinement_version`` and saves after processing.

        Returns the full list of sections with reflection sections updated.
        """
        claude = ClaudeService()

        for section in sections:
            if not _is_reflection_section(section):
                logger.debug(
                    "reflection_generator | job=%s section=%d title=%r "
                    "status=skipped reason=not_reflection",
                    job.id, section.order, section.title,
                )
                continue

            logger.info(
                "reflection_generator | job=%s section=%d title=%r "
                "status=processing",
                job.id, section.order, section.title,
            )

            user_prompt = _USER_PROMPT_TEMPLATE.format(
                title=section.title,
                content=section.content,
            )

            refined_content = claude.call(
                system_prompt=_SYSTEM_PROMPT,
                user_prompt=user_prompt,
                max_tokens=4096,
                job=job,
                stage_label="reflection_generation",
                model_override="sonnet",
            )

            section.content = refined_content
            section.refinement_version += 1
            section.save(update_fields=["content", "refinement_version"])

            logger.info(
                "reflection_generator | job=%s section=%d title=%r "
                "status=complete refinement_version=%d",
                job.id, section.order, section.title, section.refinement_version,
            )

        return sections
