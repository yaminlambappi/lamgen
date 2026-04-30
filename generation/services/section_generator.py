"""
SectionGenerationService — Stage 6 of the LamGen generation pipeline.

Generates each document section in outline order, maintaining cross-section
memory and emitting structured logs per section (duration, tokens, cost).
Applies deterministic post-processing to reduce mechanical AI patterns.
"""

import time
import logging
import re

from generation.models import AssignmentBrief, DocumentOutline, GeneratedSection, GenerationJob
from generation.services.claude_service import ClaudeService, BudgetExhaustedError, _estimate_cost_cents
from generation.services.generation_config import GenerationConfig
from generation.services.section_memory import SectionMemory, SectionMemoryService
from generation.prompts.templates import build_section_prompt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Deterministic post-processing — zero additional API calls
#
# Targets the most common mechanical patterns in LLM-generated academic text.
# Replacements are chosen to preserve meaning while varying register.
# ---------------------------------------------------------------------------

_PHRASE_REPLACEMENTS = [
    # Filler openers
    (re.compile(r'\bIt is important to note that\b', re.I), 'Notably,'),
    (re.compile(r'\bIt is worth noting that\b', re.I), 'Of note,'),
    (re.compile(r'\bIt should be noted that\b', re.I), ''),
    (re.compile(r'\bIt can be seen that\b', re.I), ''),
    (re.compile(r'\bIt is clear that\b', re.I), ''),
    (re.compile(r'\bIt is evident that\b', re.I), 'The evidence suggests that'),
    # Mechanical transitions
    (re.compile(r'\bFurthermore,\b', re.I), 'Beyond this,'),
    (re.compile(r'\bMoreover,\b', re.I), 'Additionally,'),
    (re.compile(r'\bIn addition,\b', re.I), 'Further,'),
    (re.compile(r'\bIn conclusion,\b', re.I), 'Taken together,'),
    (re.compile(r'\bIn summary,\b', re.I), 'Overall,'),
    (re.compile(r'\bTo summarise,\b', re.I), 'In aggregate,'),
    (re.compile(r'\bTo summarize,\b', re.I), 'In aggregate,'),
    # Verbose constructions
    (re.compile(r'\bIn order to\b', re.I), 'To'),
    (re.compile(r'\bDue to the fact that\b', re.I), 'Because'),
    (re.compile(r'\bAt this point in time\b', re.I), 'Currently'),
    (re.compile(r'\bIn the event that\b', re.I), 'If'),
    (re.compile(r'\bWith regard to\b', re.I), 'Regarding'),
    (re.compile(r'\bWith respect to\b', re.I), 'Regarding'),
    # Self-referential meta-statements
    (re.compile(r'\bThis essay will\b', re.I), 'This section'),
    (re.compile(r'\bThis report will\b', re.I), 'This section'),
    (re.compile(r'\bThis paper will\b', re.I), 'This section'),
    (re.compile(r'\bThis assignment will\b', re.I), 'This section'),
    (re.compile(r'\bThis section will explore\b', re.I), 'This section examines'),
    (re.compile(r'\bThis section will discuss\b', re.I), 'This section analyses'),
    (re.compile(r'\bThis section will examine\b', re.I), 'This section considers'),
]


def _apply_post_processing(text: str) -> str:
    """
    Apply deterministic phrase substitutions to reduce mechanical AI patterns.
    Collapses any double spaces introduced by empty replacements.
    """
    for pattern, replacement in _PHRASE_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    text = re.sub(r'  +', ' ', text)
    # Remove any leading comma+space left by empty replacements at sentence start
    text = re.sub(r'(?<=[.!?]\s),\s*', '', text)
    return text.strip()


# ---------------------------------------------------------------------------
# Section type classification — controls token budget allocation
# ---------------------------------------------------------------------------

_STRUCTURAL_SECTION_PATTERN = re.compile(
    r'\b(introduction|conclusion|background|methodology|methods|references|'
    r'bibliography|executive summary|table of contents|appendix|abstract)\b',
    re.IGNORECASE,
)


def _is_structural_section(title: str) -> bool:
    """
    Return True for sections that are structurally predictable.
    These receive a tighter token cap since they require less analytical depth.
    """
    return bool(_STRUCTURAL_SECTION_PATTERN.search(title))


class SectionGenerationService:

    def __init__(self, config: GenerationConfig | None = None) -> None:
        self.config = config or GenerationConfig()

    def generate_all(
        self,
        job: GenerationJob,
        brief: AssignmentBrief,
        outline: DocumentOutline,
        memory: SectionMemory,
    ) -> list:
        """
        Generate all sections in outline order.

        Emits a structured log entry per section and a summary log on completion.
        Stops gracefully if the job token budget is exhausted.
        Returns a list of GeneratedSection objects.
        """
        sections = outline.sections
        generated_sections = []
        job_start = time.monotonic()
        failed_sections: list[str] = []

        for i, section in enumerate(sections):
            if self.config.budget_exhausted(job):
                logger.warning(
                    "generation.section_generator | job=%s status=budget_exhausted "
                    "completed=%d/%d remaining_tokens=%d",
                    job.id, i, len(sections), self.config.tokens_remaining(job),
                )
                break

            section_start = time.monotonic()
            section_title = section.get("title", f"Section {i + 1}")

            try:
                generated_section = self._generate_section(
                    job, brief, section, memory, order=i
                )
            except BudgetExhaustedError:
                logger.warning(
                    "generation.section_generator | job=%s section=%r "
                    "status=budget_exhausted_mid_section",
                    job.id, section_title,
                )
                break
            except Exception as exc:
                failed_sections.append(section_title)
                logger.error(
                    "generation.section_generator | job=%s section=%r "
                    "status=section_failed error=%s",
                    job.id, section_title, exc,
                )
                # Continue to next section rather than aborting the entire job
                continue

            section_duration = time.monotonic() - section_start
            generated_sections.append(generated_section)

            # Structured per-section log
            section_tokens_in = job.total_input_tokens
            section_tokens_out = job.total_output_tokens
            logger.info(
                "generation.section_generator | job=%s section=%r status=complete "
                "word_count=%d duration=%.2fs order=%d/%d",
                job.id, section_title,
                generated_section.word_count, section_duration,
                i + 1, len(sections),
            )

            # Update cross-section memory
            SectionMemoryService.update(str(job.id), {
                "thesis_argument": generated_section.content[:150],
                "citations_used": [],
                "analytical_positions": [f"{section_title} analysed"],
                "section_summary": {
                    "title": section_title,
                    "summary": f"{generated_section.word_count} words",
                },
            })
            memory = SectionMemoryService.get(str(job.id))

            # Progress: 25–60% range spread across sections
            progress = 25 + int((i + 1) / len(sections) * 35)
            job.progress_percentage = progress
            job.current_stage = "section_generation"
            job.save(update_fields=["progress_percentage", "current_stage"])

        # Job-level summary log
        total_duration = time.monotonic() - job_start
        total_words = sum(s.word_count for s in generated_sections)
        job.refresh_from_db()
        total_cost = _estimate_cost_cents(job.total_input_tokens, job.total_output_tokens)

        logger.info(
            "generation.section_generator | job=%s status=generation_complete "
            "sections_generated=%d sections_failed=%d total_words=%d "
            "total_input_tokens=%d total_output_tokens=%d "
            "estimated_cost_cents=%.4f total_duration=%.2fs",
            job.id,
            len(generated_sections), len(failed_sections), total_words,
            job.total_input_tokens, job.total_output_tokens,
            total_cost, total_duration,
        )

        if failed_sections:
            logger.warning(
                "generation.section_generator | job=%s failed_sections=%s",
                job.id, failed_sections,
            )

        return generated_sections

    def _generate_section(
        self,
        job: GenerationJob,
        brief: AssignmentBrief,
        outline_section: dict,
        memory: SectionMemory,
        order: int = 0,
    ) -> GeneratedSection:
        section_title = outline_section["title"]
        target_word_count = outline_section.get("target_word_count", 500)
        structural = _is_structural_section(section_title)

        # Key points — prefer expanded if section planning ran, fall back to key_points
        key_points_raw = outline_section.get(
            "expanded_key_points",
            outline_section.get("key_points", []),
        )
        key_points = "\n".join(f"- {p}" for p in key_points_raw) if key_points_raw else ""

        # Rubric criteria — only inject for analytical sections
        rubric_criteria = ""
        if not structural:
            try:
                rubric = brief.rubric
                if rubric and rubric.criteria:
                    lines = [
                        f"- {c.get('name', '')} ({c.get('weight', 0):.0%}): "
                        f"{c.get('distinction_descriptor', '')}"
                        for c in rubric.criteria
                    ]
                    rubric_criteria = "\n".join(lines)
            except Exception:
                pass

        # Memory context — only inject when config enables it and memory has content
        generation_memory = ""
        if self.config.inject_memory and (
            memory.thesis_argument or memory.analytical_positions
        ):
            parts = []
            if memory.thesis_argument:
                parts.append(f"Central argument: {memory.thesis_argument}")
            if memory.analytical_positions:
                parts.append(f"Sections covered: {'; '.join(memory.analytical_positions[-3:])}")
            generation_memory = " | ".join(parts)

        user_prompt = build_section_prompt(
            section_title=section_title,
            target_word_count=target_word_count,
            key_points=key_points,
            writing_tone=brief.writing_tone,
            academic_level=brief.academic_level,
            assignment_type=brief.assignment_type,
            citation_style=brief.citation_style,
            organisational_context=brief.organisational_context or '',
            rubric_criteria=rubric_criteria,
            generation_memory=generation_memory,
        )

        system_prompt = ClaudeService().build_system_prompt(
            brief,
            memory if self.config.inject_memory else None,
            inject_full_brief=self.config.inject_full_brief,
            inject_memory=False,  # memory already embedded in user_prompt above
        )

        # Structural sections get a tighter token cap
        if structural:
            max_tokens = min(int(target_word_count * 1.2), 2000)
        else:
            max_tokens = self.config.section_max_tokens(target_word_count)

        content = ClaudeService().call(
            system_prompt,
            user_prompt,
            max_tokens,
            job,
            stage_label=f"section_{section_title[:30]}",
            config=self.config,
        )

        # Deterministic post-processing — no additional API calls
        content = _apply_post_processing(content)
        word_count = len(content.split())

        return GeneratedSection.objects.create(
            job=job,
            order=order,
            title=section_title,
            content=content,
            word_count=word_count,
        )
