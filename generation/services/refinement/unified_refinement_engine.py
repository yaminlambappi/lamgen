"""
UnifiedRefinementEngine: merged humanization, realism, and AI-defense pass.

Replaces the original HumanizationEngine, RealismEngine, and
AIDetectionDefenseLayer with a single combined pass per section or fragment.
"""
from __future__ import annotations

import logging

from generation.models import AssignmentBrief, GeneratedSection, GenerationJob
from generation.services.claude_service import ClaudeService
from generation.services.refinement.static_analyser import StaticAnalyser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt for the unified refinement pass
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are an expert academic editor. Your task is to make targeted edits to \
academic text to eliminate AI-detectable patterns while preserving all \
substantive content.

Core principles:
- Make ONLY the specific changes listed in the prompt — do not rewrite freely
- Preserve all factual claims, citations, and rubric-aligned analytical content
- Preserve document structure and section order
- Keep word count within ±10% of the original
- Vary sentence rhythm and paragraph length naturally
- Replace AI-signature phrases with natural academic alternatives
- Replace machine-confidence phrases with appropriately hedged language
- Vary analytical verb usage to avoid repetition
- Diversify paragraph opening words and sentence structures
- Do NOT use open-ended rewriting — only fix the specific issues listed
"""


def _is_reflection_section(section: GeneratedSection) -> bool:
    """Return True if the section title contains 'reflection' (case-insensitive)."""
    return 'reflection' in section.title.lower()


def _extract_risky_fragments(content: str, analyser: StaticAnalyser) -> list[str]:
    """
    Extract paragraphs that contain AI-signature phrases or machine-confidence
    phrases. These are the 'risky fragments' for fragment-level rewriting.

    Returns a list of paragraph strings that contain at least one risky phrase.
    """
    import re
    paragraphs = re.split(r'\n\s*\n', content)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]

    risky = []
    for para in paragraphs:
        para_lower = para.lower()
        has_ai_phrase = any(
            phrase.lower() in para_lower
            for phrase in StaticAnalyser.AI_SIGNATURE_PHRASES
        )
        has_mc_phrase = any(
            phrase.lower() in para_lower
            for phrase in StaticAnalyser.MACHINE_CONFIDENCE_PHRASES
        )
        if has_ai_phrase or has_mc_phrase:
            risky.append(para)

    return risky


def _build_issues_description(
    ai_phrases: list[str],
    mc_phrases: list[str],
    transition_density: float,
    analytical_verb_freq: dict[str, int],
    repetitive_openings: float,
    uniformity: float,
) -> list[str]:
    """
    Build a human-readable list of detected issues for inclusion in the prompt.
    """
    issues = []

    if ai_phrases:
        issues.append(
            f"AI-signature phrases present (remove or rephrase): "
            f"{', '.join(repr(p) for p in ai_phrases)}"
        )

    if mc_phrases:
        issues.append(
            f"Machine-confidence phrases present (replace with hedged language): "
            f"{', '.join(repr(p) for p in mc_phrases)}"
        )

    if transition_density > 0.5:
        issues.append(
            f"Transition density too high ({transition_density:.0%} of sentences "
            f"use explicit connectors — reduce to below 50%)"
        )

    overused_verbs = [
        verb for verb, count in analytical_verb_freq.items() if count > 3
    ]
    if overused_verbs:
        issues.append(
            f"Analytical verbs overused in 500-word windows (max 3 per window): "
            f"{', '.join(repr(v) for v in overused_verbs)}"
        )

    if repetitive_openings > 0.2:
        issues.append(
            f"Repetitive sentence openings ({repetitive_openings:.0%} of sentences "
            f"share an opening word — reduce to below 20%)"
        )

    if uniformity < 0.25:
        issues.append(
            f"Paragraph lengths too uniform (coefficient of variation = "
            f"{uniformity:.2f} — increase variation so paragraphs differ in length)"
        )

    return issues


class UnifiedRefinementEngine:
    """
    Performs one combined refinement pass per non-reflection section.

    Processing logic per section:
    1. Use StaticAnalyser to detect all issues (zero LLM calls).
    2. Apply threshold checks: skip if ai_suspicion < 45 or realism_score > 80.
    3. If rewriting needed: fragment-level if score ≤ 75, full section if > 75.
    4. Single LLM call with diff-based prompt: humanize + realism + AI-defense
       simultaneously.
    5. If Sonnet pass still scores > 75: second pass with Opus.
    6. Log skipped stages to skipped_stages instance attribute.

    Context window optimisation:
    - Receives only the section(s) it needs, not the full assignment.
    - For fragment-level rewriting: receives only the risky fragments.
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
        Process all non-reflection sections through the unified refinement pass.

        For each section:
        - Runs StaticAnalyser to detect AI-signature phrases, machine-confidence
          phrases, transition density, analytical verb frequency, repetitive
          openings, and paragraph length uniformity.
        - Computes ai_suspicion_score and human_realism_score.
        - Applies threshold-based skipping (ai_suspicion < 45 → skip).
        - Performs fragment-level or full-section rewriting as appropriate.
        - Invokes Opus as a second pass only when Sonnet still scores > 75.
        - Increments section.refinement_version and saves after each rewrite.

        Returns the updated list of sections.
        """
        analyser = StaticAnalyser()
        claude = ClaudeService()

        for section in sections:
            if _is_reflection_section(section):
                logger.debug(
                    "unified_refinement | job=%s section=%d title=%r "
                    "status=skipped reason=reflection_section",
                    job.id, section.order, section.title,
                )
                continue

            logger.info(
                "unified_refinement | job=%s section=%d title=%r "
                "status=analysing",
                job.id, section.order, section.title,
            )

            content = section.content

            # ------------------------------------------------------------------
            # Step 1: Detect all issues with StaticAnalyser (zero LLM calls)
            # ------------------------------------------------------------------
            ai_phrases = analyser.detect_ai_signature_phrases(content)
            mc_phrases = analyser.detect_machine_confidence_phrases(content)
            transition_density = analyser.detect_transition_density(content)
            analytical_verb_freq = analyser.detect_analytical_verb_frequency(content)
            repetitive_openings = analyser.detect_repetitive_sentence_openings(content)
            uniformity = analyser.detect_paragraph_length_uniformity(content)

            # ------------------------------------------------------------------
            # Step 2: Compute composite scores
            # ------------------------------------------------------------------
            ai_suspicion = analyser.compute_ai_suspicion_score(content)
            realism_score = analyser.compute_human_realism_score(content)

            # Store the per-section AI suspicion score
            section.ai_suspicion_score = ai_suspicion

            logger.info(
                "unified_refinement | job=%s section=%d title=%r "
                "ai_suspicion=%.1f realism_score=%.1f",
                job.id, section.order, section.title,
                ai_suspicion, realism_score,
            )

            # ------------------------------------------------------------------
            # Step 3: Threshold checks
            # ------------------------------------------------------------------
            if ai_suspicion < 45:
                # Section is clean enough — skip all LLM calls
                stage_key = f"unified_refinement:section_{section.order}:skipped_low_suspicion"
                self.skipped_stages.append(stage_key)
                logger.info(
                    "unified_refinement | job=%s section=%d title=%r "
                    "status=skipped reason=ai_suspicion_below_threshold "
                    "ai_suspicion=%.1f",
                    job.id, section.order, section.title, ai_suspicion,
                )
                # Save the ai_suspicion_score even when skipping
                section.save(update_fields=["ai_suspicion_score"])
                continue

            skip_realism = realism_score > 80
            if skip_realism:
                stage_key = f"unified_refinement:section_{section.order}:skipped_realism_enhancement"
                self.skipped_stages.append(stage_key)
                logger.info(
                    "unified_refinement | job=%s section=%d title=%r "
                    "status=realism_enhancement_skipped realism_score=%.1f",
                    job.id, section.order, section.title, realism_score,
                )

            # ------------------------------------------------------------------
            # Step 4 / 5: Determine rewriting strategy
            # ------------------------------------------------------------------
            issues_list = _build_issues_description(
                ai_phrases=ai_phrases,
                mc_phrases=mc_phrases,
                transition_density=transition_density,
                analytical_verb_freq=analytical_verb_freq,
                repetitive_openings=repetitive_openings,
                uniformity=uniformity,
            )

            if ai_suspicion <= 75:
                # Fragment-level rewriting: extract only risky paragraphs
                risky_fragments = _extract_risky_fragments(content, analyser)

                if not risky_fragments:
                    # No risky fragments found despite suspicion score — use full content
                    risky_fragments = [content]

                prompt = self._build_diff_prompt(
                    section_content="\n\n".join(risky_fragments),
                    issues_list=issues_list,
                    fragments=risky_fragments,
                )

                logger.info(
                    "unified_refinement | job=%s section=%d title=%r "
                    "strategy=fragment_level fragments=%d",
                    job.id, section.order, section.title, len(risky_fragments),
                )

                rewritten = claude.call(
                    system_prompt=_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    max_tokens=4096,
                    job=job,
                    stage_label="unified_refinement_fragment",
                    model_override="sonnet",
                )

                # Splice rewritten fragments back into the original content
                new_content = _splice_fragments(content, risky_fragments, rewritten)

            else:
                # Full section rewrite with Sonnet
                prompt = self._build_diff_prompt(
                    section_content=content,
                    issues_list=issues_list,
                    fragments=[],
                )

                logger.info(
                    "unified_refinement | job=%s section=%d title=%r "
                    "strategy=full_section",
                    job.id, section.order, section.title,
                )

                rewritten = claude.call(
                    system_prompt=_SYSTEM_PROMPT,
                    user_prompt=prompt,
                    max_tokens=4096,
                    job=job,
                    stage_label="unified_refinement_full",
                    model_override="sonnet",
                )

                new_content = rewritten

            # ------------------------------------------------------------------
            # Step 6: Check if Sonnet pass still scores > 75 → second pass Opus
            # ------------------------------------------------------------------
            post_sonnet_suspicion = analyser.compute_ai_suspicion_score(new_content)

            logger.info(
                "unified_refinement | job=%s section=%d title=%r "
                "post_sonnet_suspicion=%.1f",
                job.id, section.order, section.title, post_sonnet_suspicion,
            )

            if post_sonnet_suspicion > 75:
                logger.info(
                    "unified_refinement | job=%s section=%d title=%r "
                    "status=opus_pass_triggered post_sonnet_suspicion=%.1f",
                    job.id, section.order, section.title, post_sonnet_suspicion,
                )

                # Re-detect issues on the Sonnet output
                opus_ai_phrases = analyser.detect_ai_signature_phrases(new_content)
                opus_mc_phrases = analyser.detect_machine_confidence_phrases(new_content)
                opus_transition = analyser.detect_transition_density(new_content)
                opus_verb_freq = analyser.detect_analytical_verb_frequency(new_content)
                opus_repetitive = analyser.detect_repetitive_sentence_openings(new_content)
                opus_uniformity = analyser.detect_paragraph_length_uniformity(new_content)

                opus_issues = _build_issues_description(
                    ai_phrases=opus_ai_phrases,
                    mc_phrases=opus_mc_phrases,
                    transition_density=opus_transition,
                    analytical_verb_freq=opus_verb_freq,
                    repetitive_openings=opus_repetitive,
                    uniformity=opus_uniformity,
                )

                opus_prompt = self._build_diff_prompt(
                    section_content=new_content,
                    issues_list=opus_issues,
                    fragments=[],
                )

                new_content = claude.call(
                    system_prompt=_SYSTEM_PROMPT,
                    user_prompt=opus_prompt,
                    max_tokens=4096,
                    job=job,
                    stage_label="unified_refinement_opus",
                    model_override="opus",
                )

            # ------------------------------------------------------------------
            # Save the rewritten section
            # ------------------------------------------------------------------
            section.content = new_content
            section.ai_suspicion_score = analyser.compute_ai_suspicion_score(new_content)
            section.refinement_version += 1
            section.save(update_fields=["content", "ai_suspicion_score", "refinement_version"])

            logger.info(
                "unified_refinement | job=%s section=%d title=%r "
                "status=complete refinement_version=%d final_suspicion=%.1f",
                job.id, section.order, section.title,
                section.refinement_version, section.ai_suspicion_score,
            )

        return sections

    def _build_diff_prompt(
        self,
        section_content: str,
        issues_list: list[str],
        fragments: list[str],
    ) -> str:
        """
        Build a constrained editing prompt for the LLM.

        Format::

            Modify ONLY the following detected issues in the text below:
            {issues_list}

            Preserve exactly:
            - All factual claims and citations
            - Document structure and section order
            - Rubric-aligned analytical content
            - Word count within ±10%

            Issues to fix:
            {specific_fragments_with_line_references}

            Text:
            {section_content}

        Never uses open-ended "rewrite naturally" instructions.

        Returns the formatted prompt string.
        """
        # Format the issues list as a numbered list
        if issues_list:
            formatted_issues = "\n".join(
                f"{i + 1}. {issue}" for i, issue in enumerate(issues_list)
            )
        else:
            formatted_issues = "(No specific issues detected — make minimal improvements only)"

        # Format the specific fragments with references
        if fragments:
            fragment_lines = []
            for i, fragment in enumerate(fragments, start=1):
                # Truncate long fragments for readability in the prompt header
                preview = fragment[:120].replace('\n', ' ')
                if len(fragment) > 120:
                    preview += "..."
                fragment_lines.append(f"Fragment {i}: \"{preview}\"")
            formatted_fragments = "\n".join(fragment_lines)
        else:
            formatted_fragments = "(Apply fixes to the full text below)"

        prompt = (
            f"Modify ONLY the following detected issues in the text below:\n"
            f"{formatted_issues}\n"
            f"\n"
            f"Preserve exactly:\n"
            f"- All factual claims and citations\n"
            f"- Document structure and section order\n"
            f"- Rubric-aligned analytical content\n"
            f"- Word count within \u00b110%\n"
            f"\n"
            f"Issues to fix:\n"
            f"{formatted_fragments}\n"
            f"\n"
            f"Text:\n"
            f"{section_content}"
        )

        return prompt


# ---------------------------------------------------------------------------
# Helper: splice rewritten fragments back into original content
# ---------------------------------------------------------------------------

def _splice_fragments(
    original_content: str,
    risky_fragments: list[str],
    rewritten_text: str,
) -> str:
    """
    Replace the risky fragments in *original_content* with the rewritten text.

    The LLM is given only the risky fragments concatenated together and returns
    a rewritten version of that concatenated text. We splice the rewritten
    version back into the original, replacing each risky fragment in order.

    If the splice cannot be performed cleanly (e.g. the LLM changed the
    structure significantly), we fall back to returning the rewritten text
    directly.
    """
    if not risky_fragments:
        return rewritten_text

    # Split the rewritten text into the same number of paragraphs as the
    # risky fragments, using double-newline as separator.
    import re
    rewritten_paragraphs = [
        p.strip() for p in re.split(r'\n\s*\n', rewritten_text) if p.strip()
    ]

    # If the LLM returned a different number of paragraphs, fall back to
    # returning the rewritten text as-is (it covers the full section).
    if len(rewritten_paragraphs) != len(risky_fragments):
        logger.debug(
            "unified_refinement | splice_fragments: paragraph count mismatch "
            "(expected %d, got %d) — using rewritten text directly",
            len(risky_fragments), len(rewritten_paragraphs),
        )
        return rewritten_text

    # Replace each risky fragment in the original content with its rewritten
    # counterpart, in order.
    result = original_content
    for original_frag, rewritten_frag in zip(risky_fragments, rewritten_paragraphs):
        result = result.replace(original_frag, rewritten_frag, 1)

    return result
