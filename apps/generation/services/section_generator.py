"""
SectionGenerationService — Stage 6 of the LamGen generation pipeline.

Uses Claude Opus for all section writing with:
- Student persona injection for consistent writing identity
- Full continuity memory (previous section summary, argument thread, rhythm notes)
- Natural writing prompts — no "write professionally" framing
- Reflection sections get a dedicated personal/experiential prompt
- Minimal post-processing: only removes the most egregious mechanical phrases
  without normalising paragraph structure or enforcing symmetry
"""

import time
import logging
import re

from apps.generation.models import AssignmentBrief, DocumentOutline, GeneratedSection, GenerationJob
from apps.generation.services.claude_service import ClaudeService, BudgetExhaustedError, _estimate_cost_cents
from apps.generation.services.generation_config import GenerationConfig
from apps.generation.services.section_memory import SectionMemory, SectionMemoryService
from apps.generation.services.author_identity import (
    build_student_persona,
    get_attention_modifier,
    get_session_energy,
    get_energy_depth_instruction,
    check_transition_repetition,
    check_reflection_cliches,
    BLACKLISTED_REFLECTION_PHRASES,
)
from apps.generation.prompts.templates import build_section_prompt, build_reflection_prompt

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Minimal post-processing — only the most egregious mechanical phrases
#
# Deliberately light: we do NOT normalise paragraph lengths, enforce sentence
# symmetry, or aggressively clean transitions. Natural variation is the goal.
# ---------------------------------------------------------------------------

_PHRASE_REPLACEMENTS = [
    # Self-referential meta-openers that Opus occasionally produces
    (re.compile(r'\bThis essay will\b', re.I), 'This section'),
    (re.compile(r'\bThis report will\b', re.I), 'This section'),
    (re.compile(r'\bThis paper will\b', re.I), 'This section'),
    (re.compile(r'\bThis assignment will\b', re.I), 'This section'),
    # Filler openers — remove entirely (collapse double space after)
    (re.compile(r'\bIt is important to note that\b', re.I), ''),
    (re.compile(r'\bIt should be noted that\b', re.I), ''),
    (re.compile(r'\bIt is worth noting that\b', re.I), ''),
    # Verbose constructions
    (re.compile(r'\bIn order to\b', re.I), 'To'),
    (re.compile(r'\bDue to the fact that\b', re.I), 'Because'),
]

# Blacklisted transitions — only replace when they appear at sentence start
# (preserves natural mid-sentence usage)
_TRANSITION_REPLACEMENTS = [
    (re.compile(r'(?<=[.!?]\s)Furthermore,\s', re.I), ''),
    (re.compile(r'(?<=[.!?]\s)Moreover,\s', re.I), ''),
    (re.compile(r'(?<=[.!?]\s)Additionally,\s', re.I), ''),
    (re.compile(r'(?<=[.!?]\s)In conclusion,\s', re.I), 'Taken together, '),
    (re.compile(r'(?<=[.!?]\s)In summary,\s', re.I), 'Overall, '),
]


def _apply_minimal_post_processing(text: str, is_reflection: bool = False) -> str:
    """
    Apply only the minimum phrase substitutions to remove the most obvious
    mechanical patterns. Does NOT normalise paragraph structure.

    For reflection sections, additionally strips blacklisted generic phrases.
    """
    for pattern, replacement in _PHRASE_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    for pattern, replacement in _TRANSITION_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    # Collapse any double spaces introduced by empty replacements
    text = re.sub(r'  +', ' ', text)

    if is_reflection:
        # Remove blacklisted generic reflection phrases (case-insensitive)
        for phrase in BLACKLISTED_REFLECTION_PHRASES:
            text = re.sub(re.escape(phrase), '', text, flags=re.IGNORECASE)
        text = re.sub(r'  +', ' ', text)

    return text.strip()


# ---------------------------------------------------------------------------
# Section type classification
# ---------------------------------------------------------------------------

_REFLECTION_PATTERN = re.compile(r'\breflect', re.IGNORECASE)
_STRUCTURAL_PATTERN = re.compile(
    r'\b(introduction|conclusion|background|methodology|methods|references|'
    r'bibliography|executive summary|table of contents|appendix|abstract)\b',
    re.IGNORECASE,
)


def _is_reflection_section(title: str) -> bool:
    return bool(_REFLECTION_PATTERN.search(title))


def _is_structural_section(title: str) -> bool:
    return bool(_STRUCTURAL_PATTERN.search(title))


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
        Generate all sections in outline order using Opus with full continuity memory.

        Each section call receives:
        - Student persona (persistent writing identity)
        - Previous section summary
        - Argument continuity thread
        - Writing rhythm notes
        - Established terminology
        - Organisational context already introduced

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
                continue

            section_duration = time.monotonic() - section_start
            generated_sections.append(generated_section)

            logger.info(
                "generation.section_generator | job=%s section=%r status=complete "
                "word_count=%d duration=%.2fs order=%d/%d model=opus",
                job.id, section_title,
                generated_section.word_count, section_duration,
                i + 1, len(sections),
            )

            # Update continuity memory with rich context from this section
            content = generated_section.content
            words = content.split()
            SectionMemoryService.update(str(job.id), {
                "previous_section_summary": " ".join(words[:60]),  # first ~60 words as summary
                "argument_continuity": " ".join(words[-40:]),       # last ~40 words as thread
                "writing_rhythm_memory": _extract_rhythm_note(content),
                "thesis_argument": content[:150],
                "analytical_positions": [f"{section_title} analysed"],
                "section_summary": {
                    "title": section_title,
                    "summary": f"{generated_section.word_count} words",
                },
            })
            memory = SectionMemoryService.get(str(job.id))

            # Progress: 25–90% range spread across sections
            progress = 25 + int((i + 1) / len(sections) * 65)
            job.progress_percentage = progress
            job.current_stage = "section_generation"
            job.save(update_fields=["progress_percentage", "current_stage"])

        # Job-level summary log
        total_duration = time.monotonic() - job_start
        total_words = sum(s.word_count for s in generated_sections)
        job.refresh_from_db()
        total_cost = _estimate_cost_cents(
            job.total_input_tokens, job.total_output_tokens, self.config.section_model
        )

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
        base_word_count = outline_section.get("target_word_count", 500)
        is_reflection = _is_reflection_section(section_title)
        is_structural = _is_structural_section(section_title)

        # Attention variability: adjust word count based on author interest profile
        attention_modifier = get_attention_modifier(section_title)
        target_word_count = int(base_word_count * attention_modifier)
        if attention_modifier != 1.0:
            logger.debug(
                "generation.section_generator | job=%s section=%r "
                "attention_modifier=%.3f base_wc=%d adjusted_wc=%d",
                job.id, section_title, attention_modifier, base_word_count, target_word_count,
            )

        key_points_raw = outline_section.get(
            "expanded_key_points",
            outline_section.get("key_points", []),
        )
        key_points = "\n".join(f"- {p}" for p in key_points_raw) if key_points_raw else ""

        # Rubric criteria — only for analytical sections
        rubric_criteria = ""
        if not is_structural and not is_reflection:
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

        # Build continuity memory string for the user prompt
        generation_memory = _build_continuity_string(memory, self.config)

        # Build the appropriate user prompt
        if is_reflection:
            user_prompt = build_reflection_prompt(
                section_title=section_title,
                target_word_count=target_word_count,
                key_points=key_points,
                academic_level=brief.academic_level,
                assignment_type=brief.assignment_type,
                organisational_context=brief.organisational_context or '',
                generation_memory=generation_memory,
            )
        else:
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

        # Build Opus system prompt with full authored-personality identity + continuity memory
        claude = ClaudeService()
        system_prompt = claude.build_opus_system_prompt(
            brief=brief,
            student_persona=memory.student_persona,
            memory=memory if self.config.inject_memory else None,
            inject_full_brief=self.config.inject_full_brief,
            is_reflection=is_reflection,
        )

        # Token cap: structural sections get tighter budget
        if is_structural:
            max_tokens = min(int(target_word_count * 1.3), 2500)
        else:
            max_tokens = self.config.section_max_tokens(target_word_count)

        content = claude.call(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=max_tokens,
            job=job,
            stage_label=f"section_{section_title[:30]}",
            config=self.config,
            model_override='opus',
        )

        # Minimal post-processing — no paragraph normalisation; reflection cliché strip
        content = _apply_minimal_post_processing(content, is_reflection=is_reflection)

        # Log flagged transitions for observability (does not mutate content further)
        flagged = check_transition_repetition(content)
        if flagged:
            logger.debug(
                "generation.section_generator | job=%s section=%r flagged_transitions=%s",
                job.id, section_title, flagged,
            )

        if is_reflection:
            cliches = check_reflection_cliches(content)
            if cliches:
                logger.debug(
                    "generation.section_generator | job=%s section=%r reflection_cliches_stripped=%s",
                    job.id, section_title, cliches,
                )

        word_count = len(content.split())

        return GeneratedSection.objects.create(
            job=job,
            order=order,
            title=section_title,
            content=content,
            word_count=word_count,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_continuity_string(memory: SectionMemory, config: GenerationConfig) -> str:
    """
    Build the generation_memory string injected into the user prompt.
    Only populated when config.inject_memory is True and memory has content.
    """
    if not config.inject_memory:
        return ''

    parts = []
    if memory.previous_section_summary:
        parts.append(f"Previous section ended with: {memory.previous_section_summary}")
    if memory.argument_continuity:
        parts.append(f"Argument thread: {memory.argument_continuity}")
    if memory.analytical_positions:
        parts.append(f"Sections already covered: {'; '.join(memory.analytical_positions[-3:])}")
    if memory.terminology:
        terms = list(memory.terminology.keys())[-6:]
        parts.append(f"Terms already established: {', '.join(terms)}")

    return "\n".join(parts) if parts else ''


def _extract_rhythm_note(content: str) -> str:
    """
    Extract a brief rhythm note from the generated content.
    Counts paragraphs and notes average length for continuity.
    """
    paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
    if not paragraphs:
        return ''
    avg_words = sum(len(p.split()) for p in paragraphs) // max(len(paragraphs), 1)
    return f"{len(paragraphs)} paragraphs, avg {avg_words} words each"
