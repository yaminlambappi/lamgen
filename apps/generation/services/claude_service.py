"""
ClaudeService — Anthropic API wrapper for the LamGen generation pipeline.

Responsibilities:
- Mock mode (CLAUDE_MOCK_MODE=True) for zero-cost local development
- Per-call model routing: Haiku / Sonnet / Opus via model_override
- Opus generation settings (temperature=0.82, top_p=0.92) for natural writing
- Retry only on transient errors: network failures, 429, 5xx
- Hard per-job token budget guard
- Structured per-call logging: stage, model, tokens, cost, duration, retry count
"""

import time
import logging

import anthropic
from django.conf import settings

from apps.generation.models import AssignmentBrief, GenerationJob, TokenUsageLog
from apps.generation.services.section_memory import SectionMemory
from apps.generation.services.author_identity import (
    AUTHOR_PROFILE,
    CONFIDENCE_ENGINE,
    get_energy_depth_instruction,
    get_citation_density_instruction,
    check_transition_repetition,
    check_reflection_cliches,
    STRUCTURAL_ENTROPY,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Canned responses for local development (CLAUDE_MOCK_MODE=True)
# ---------------------------------------------------------------------------

_MOCK_RESPONSES: dict[str, str] = {
    'combined_analysis': '''{
  "brief": {
    "topic": "Cybersecurity Governance and Risk Management in Financial Services",
    "subject_area": "Information Security Management",
    "assignment_type": "report",
    "academic_level": "postgraduate",
    "required_sections": ["Introduction", "Literature Review", "Analysis", "Recommendations", "Conclusion"],
    "citation_style": "APA",
    "writing_tone": "critical_analytical",
    "organisational_context": "A mid-sized retail banking organisation operating across three jurisdictions",
    "required_frameworks": ["NIST Cybersecurity Framework", "ISO 27001", "COBIT"]
  },
  "rubric_criteria": [
    {"name": "Critical Analysis", "weight": 0.40, "distinction_descriptor": "Demonstrates sophisticated evaluation of competing theoretical positions, identifies limitations in existing frameworks, and draws evidence-based conclusions that go beyond description"},
    {"name": "Research Depth", "weight": 0.30, "distinction_descriptor": "Engages substantively with multiple scholarly positions, acknowledges areas of academic debate, and situates arguments within the broader literature"},
    {"name": "Professional Application", "weight": 0.20, "distinction_descriptor": "Integrates organisational context meaningfully into the analysis, with specific and actionable recommendations grounded in evidence"},
    {"name": "Academic Writing", "weight": 0.10, "distinction_descriptor": "Clear, well-structured prose with accurate citation, appropriate hedging, and consistent academic register throughout"}
  ]
}''',
    'outline_generation': '''[
  {"title": "Introduction", "target_word_count": 250, "key_points": ["Establish the governance challenge in financial services cybersecurity", "State the analytical scope and key frameworks under examination", "Articulate the central argument of the report"]},
  {"title": "Literature Review", "target_word_count": 600, "key_points": ["Theoretical foundations of cybersecurity governance", "Comparative analysis of NIST, ISO 27001, and COBIT", "Gaps and tensions in the existing literature"]},
  {"title": "Analysis", "target_word_count": 900, "key_points": ["Application of frameworks to the banking context", "Critical evaluation of governance limitations", "Organisational risk implications"]},
  {"title": "Recommendations", "target_word_count": 500, "key_points": ["Framework integration strategy", "Governance structure improvements", "Implementation priorities and constraints"]},
  {"title": "Conclusion", "target_word_count": 250, "key_points": ["Synthesis of key analytical findings", "Contribution to the governance debate", "Limitations and directions for further inquiry"]}
]''',
    'default_section': (
        "The governance of cybersecurity risk within financial institutions presents a "
        "complex challenge that existing frameworks address with varying degrees of "
        "effectiveness. While the NIST Cybersecurity Framework offers a structured "
        "approach to risk identification and response, its application in multi-jurisdictional "
        "banking environments reveals significant tensions between standardisation and "
        "contextual adaptation [Smith, 2021]. This section examines these tensions critically, "
        "drawing on recent empirical work to evaluate the practical limitations of "
        "framework-based governance.\n\n"
        "The evidence suggests that organisations frequently adopt compliance-oriented "
        "interpretations of governance frameworks, prioritising audit readiness over "
        "substantive risk reduction [Jones & Patel, 2022]. This tendency, while "
        "understandable given regulatory pressures, may paradoxically increase systemic "
        "vulnerability by directing resources toward documentation rather than capability "
        "development. A more effective approach, as argued by Chen et al. [2023], involves "
        "integrating framework requirements with organisation-specific threat modelling.\n\n"
        "The implications for the organisation under examination are considerable. "
        "Operating across three jurisdictions introduces regulatory fragmentation that "
        "standard frameworks do not adequately address, requiring a governance architecture "
        "that can accommodate divergent compliance requirements without sacrificing coherence. "
        "Hybrid governance models, combining elements of NIST and ISO 27001, offer the most "
        "viable path forward, though their implementation demands sustained executive "
        "commitment and cross-functional coordination [Williams, 2023]."
    ),
}


def _get_mock_response(stage_label: str) -> str:
    """Return a canned development response for the given stage label."""
    if stage_label == 'combined_analysis':
        return _MOCK_RESPONSES['combined_analysis']
    if stage_label == 'outline_generation':
        return _MOCK_RESPONSES['outline_generation']
    return _MOCK_RESPONSES['default_section']


# ---------------------------------------------------------------------------
# Retry policy
# ---------------------------------------------------------------------------

_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Pricing per million tokens (USD) — used for cost logging
_MODEL_PRICING = {
    'haiku':  {'input': 0.8,  'output': 4.0},
    'sonnet': {'input': 3.0,  'output': 15.0},
    'opus':   {'input': 15.0, 'output': 75.0},
}
# Default to Sonnet rates for unknown models
_DEFAULT_PRICING = _MODEL_PRICING['sonnet']


def _get_pricing(model_name: str) -> dict:
    model_lower = model_name.lower()
    for key in _MODEL_PRICING:
        if key in model_lower:
            return _MODEL_PRICING[key]
    return _DEFAULT_PRICING


def _estimate_cost_cents(input_tokens: int, output_tokens: int, model: str = '') -> float:
    pricing = _get_pricing(model)
    input_cost = (input_tokens / 1_000_000) * pricing['input'] * 100
    output_cost = (output_tokens / 1_000_000) * pricing['output'] * 100
    return round(input_cost + output_cost, 4)


class ClaudeAPIError(Exception):
    """Raised when the Anthropic API call fails after exhausting all retries."""


class BudgetExhaustedError(Exception):
    """Raised when a job has consumed its per-job token budget."""


class ClaudeService:
    MAX_RETRIES = 3
    BACKOFF_BASE = 2  # seconds; delays are 2s, 4s, 8s

    def _resolve_model(self, model_override: str | None, config=None) -> str:
        """
        Resolve the model to use for this call.

        Priority:
        1. model_override string (e.g. 'opus', 'sonnet', 'haiku', or full model name)
        2. config.section_model (if config provided)
        3. settings.CLAUDE_MODEL fallback
        """
        from apps.generation.services.generation_config import HAIKU_MODEL, SONNET_MODEL, OPUS_MODEL
        _ALIASES = {
            'haiku': HAIKU_MODEL,
            'sonnet': SONNET_MODEL,
            'opus': OPUS_MODEL,
        }
        if model_override:
            return _ALIASES.get(model_override.lower(), model_override)
        if config and hasattr(config, 'section_model'):
            return config.section_model
        return getattr(settings, 'CLAUDE_MODEL', SONNET_MODEL)

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        job: GenerationJob,
        stage_label: str,
        config=None,
        model_override: str | None = None,
    ) -> str:
        """
        Call the Anthropic Messages API and return the response text.

        model_override accepts a short alias ('haiku', 'sonnet', 'opus') or a
        full model name. When omitted, falls back to config.section_model or
        settings.CLAUDE_MODEL.

        Opus calls automatically apply temperature=0.82 and top_p=0.92 for
        natural, varied writing output.
        """
        # --- Development mock mode ---
        if getattr(settings, 'CLAUDE_MOCK_MODE', False):
            mock_text = _get_mock_response(stage_label)
            TokenUsageLog.objects.create(
                job=job, stage=stage_label,
                input_tokens=0, output_tokens=0, model='mock',
            )
            logger.debug(
                "generation.claude | stage=%s job=%s mode=mock",
                stage_label, job.id,
            )
            return mock_text

        # --- Budget guard ---
        max_per_job = getattr(settings, 'CLAUDE_MAX_TOKENS_PER_JOB', 80000)
        used = job.total_input_tokens + job.total_output_tokens
        if used >= max_per_job:
            logger.error(
                "generation.claude | stage=%s job=%s status=budget_exhausted "
                "used=%d limit=%d",
                stage_label, job.id, used, max_per_job,
            )
            raise BudgetExhaustedError(
                f"Job {job.id} has consumed {used} tokens "
                f"(limit: {max_per_job}). Stage: {stage_label}."
            )

        model = self._resolve_model(model_override, config)
        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        last_exception = None
        retry_count = 0
        call_start = time.monotonic()

        # Opus-specific generation settings for natural writing variation
        extra_kwargs = {}
        if 'opus' in model.lower():
            from apps.generation.services.generation_config import OPUS_GENERATION_SETTINGS
            extra_kwargs['temperature'] = OPUS_GENERATION_SETTINGS['temperature']
            extra_kwargs['top_p'] = OPUS_GENERATION_SETTINGS['top_p']

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    **extra_kwargs,
                )
            except anthropic.APIConnectionError as exc:
                last_exception = exc
                retry_count += 1
                if attempt < self.MAX_RETRIES:
                    wait = self.BACKOFF_BASE ** attempt
                    logger.warning(
                        "generation.claude | stage=%s job=%s model=%s attempt=%d/%d "
                        "status=connection_error retry_in=%ds error=%s",
                        stage_label, job.id, model, attempt, self.MAX_RETRIES, wait, exc,
                    )
                    time.sleep(wait)
                continue

            except anthropic.APIStatusError as exc:
                if exc.status_code not in _RETRYABLE_STATUS_CODES:
                    duration = time.monotonic() - call_start
                    logger.error(
                        "generation.claude | stage=%s job=%s model=%s attempt=%d "
                        "status=client_error http=%d duration=%.2fs error=%s",
                        stage_label, job.id, model, attempt, exc.status_code, duration, exc,
                    )
                    raise ClaudeAPIError(
                        f"Non-retryable API error (HTTP {exc.status_code}) "
                        f"at stage '{stage_label}': {exc}"
                    ) from exc

                last_exception = exc
                retry_count += 1
                if attempt < self.MAX_RETRIES:
                    wait = self.BACKOFF_BASE ** attempt
                    logger.warning(
                        "generation.claude | stage=%s job=%s model=%s attempt=%d/%d "
                        "status=rate_limit_or_server_error http=%d retry_in=%ds",
                        stage_label, job.id, model, attempt, self.MAX_RETRIES,
                        exc.status_code, wait,
                    )
                    time.sleep(wait)
                continue

            # --- Success ---
            duration = time.monotonic() - call_start
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost_cents = _estimate_cost_cents(input_tokens, output_tokens, model)

            TokenUsageLog.objects.create(
                job=job,
                stage=stage_label,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=model,
            )
            job.total_input_tokens += input_tokens
            job.total_output_tokens += output_tokens
            job.save(update_fields=["total_input_tokens", "total_output_tokens"])

            logger.info(
                "generation.claude | stage=%s job=%s model=%s status=success "
                "input_tokens=%d output_tokens=%d cost_cents=%.4f "
                "duration=%.2fs retries=%d",
                stage_label, job.id, model,
                input_tokens, output_tokens, cost_cents,
                duration, retry_count,
            )

            return response.content[0].text

        duration = time.monotonic() - call_start
        logger.error(
            "generation.claude | stage=%s job=%s model=%s status=failed "
            "attempts=%d duration=%.2fs error=%s",
            stage_label, job.id, model, self.MAX_RETRIES, duration, last_exception,
        )
        raise ClaudeAPIError(
            f"API call failed after {self.MAX_RETRIES} attempts "
            f"at stage '{stage_label}': {last_exception}"
        )

    def build_system_prompt(
        self,
        brief: AssignmentBrief,
        memory: SectionMemory | None = None,
        inject_full_brief: bool = False,
        inject_memory: bool = True,
    ) -> str:
        """
        Build a token-efficient system prompt for Sonnet/Haiku calls.

        For Opus section generation, use build_opus_system_prompt() instead.
        """
        lines = [
            f"You are an expert {brief.academic_level} academic writer specialising in "
            f"{brief.subject_area}. Write in {brief.writing_tone} tone. "
            f"Apply {brief.citation_style} citation style throughout.",
        ]

        if inject_full_brief:
            lines += ["", f"Assignment topic: {brief.topic}"]
            if brief.assignment_type:
                lines.append(f"Assignment type: {brief.assignment_type}")
            if brief.organisational_context:
                lines.append(f"Organisational context: {brief.organisational_context}")
            if brief.required_frameworks:
                lines.append(f"Required frameworks: {', '.join(brief.required_frameworks)}")

        if inject_memory and memory is not None:
            mem_parts = []
            if memory.thesis_argument:
                mem_parts.append(f"Central argument established: {memory.thesis_argument[:150]}")
            if memory.terminology:
                recent = list(memory.terminology.items())[-5:]
                terms = "; ".join(f"{k}: {v}" for k, v in recent)
                mem_parts.append(f"Established terminology: {terms}")
            if memory.analytical_positions:
                positions = memory.analytical_positions[-3:]
                mem_parts.append(f"Positions taken: {'; '.join(positions)}")
            if mem_parts:
                lines += ["", "Cross-section context: " + " | ".join(mem_parts)]

        return "\n".join(lines)

    def build_opus_system_prompt(
        self,
        brief: AssignmentBrief,
        student_persona: dict,
        memory: SectionMemory | None = None,
        inject_full_brief: bool = False,
        is_reflection: bool = False,
    ) -> str:
        """
        Build the authored-personality system prompt for Opus section generation calls.

        Injects the full AUTHOR_PROFILE identity with:
        - Stable writing personality (name, style, tone, argument behaviour)
        - Confidence drift instructions (hedging probability, softened conclusions)
        - Attention calibration (interest-driven depth, compact routine sections)
        - Session energy depth instruction
        - Citation density guidance appropriate for section type
        - Structural entropy nudges (paragraph variation, anti-symmetry)
        - Anti-AI controls (blacklisted transitions, anti-encyclopedic tone)
        - Writing continuity memory from prior sections

        DOES NOT use "write professionally and academically" framing.
        DOES NOT inject fake grammar errors or artificial weakness.
        DOES optimize for believable authorship.
        """
        persona = student_persona
        energy = persona.get("session_energy", "normal")
        energy_instruction = get_energy_depth_instruction(energy)
        session_title = brief.topic[:60] if brief.topic else "this topic"
        citation_instruction = get_citation_density_instruction(
            section_title=session_title, is_reflection=is_reflection
        )

        # Confidence drift thresholds — surfaced as natural writing instructions
        hedge_pct = int(CONFIDENCE_ENGINE["hedging_probability"] * 100)
        softened_pct = int(CONFIDENCE_ENGINE["softened_conclusion_probability"] * 100)

        lines = [
            f"You are a {brief.academic_level} student named {persona.get('name', AUTHOR_PROFILE['identity']['name'])} "
            f"writing a {brief.assignment_type} on {brief.subject_area}.",
            "",
            "Your authored writing identity:",
            f"- Academic range: {AUTHOR_PROFILE['identity']['academic_range']} — capable but not a perfectionist",
            f"- Style: {persona.get('writing_style', 'analytical but grounded')}",
            f"- Tone: {persona.get('tone', 'practical university student register — not robotic or encyclopedic')}",
            f"- Strength: {persona.get('strength', 'practical reasoning and real-world application')}",
            f"- Natural tendency: {persona.get('weakness', 'slight unevenness in paragraph rhythm — this is authentic')}",
            f"- Verbosity: {persona.get('verbosity', 'moderate; naturally more detailed on interesting points')}",
            f"- Transitions: {persona.get('transition_style', 'contextual — avoids Furthermore / Moreover / Additionally')}",
            f"- Argument style: {persona.get('argument_style', 'balanced, practical, aware of tradeoffs')}",
            f"- Confidence: {persona.get('confidence', 'moderate — occasionally hedges, avoids absolute claims')}",
            "",
            "Confidence behaviour (apply naturally throughout):",
            f"- Roughly {hedge_pct}% of claims should use hedging language: 'suggests', 'indicates', 'may', 'tends to', 'arguably'",
            f"- Roughly {softened_pct}% of conclusions or closing paragraphs should use a softened opener",
            "- Do not present every argument as fully resolved — allow some analytical uncertainty",
            "- Never fake insecurity. The uncertainty must feel like genuine careful reasoning, not self-doubt.",
            "",
            "Structural entropy (prevent AI-detectable symmetry):",
            f"- Paragraph variation: {STRUCTURAL_ENTROPY['paragraph_variation']} — vary lengths naturally",
            "- Do NOT normalise paragraph sizes or equalize section density",
            "- Do NOT maintain perfect pacing consistency across paragraphs",
            "- Some paragraphs will be shorter analytical observations; others will develop reasoning at length",
            "",
            "How to write:",
            "- Write analytically and contextually — like someone who has genuinely thought about this, not memorised it",
            "- Prioritise real-world reasoning over abstract theory",
            "- Allow reasoning to evolve naturally through the section — not every idea needs to be fully resolved immediately",
            "- Open with a substantive claim or observation, never a meta-statement about what the section will do",
            "- Where competing perspectives exist, acknowledge tensions and tradeoffs directly",
            "- Close analytical sections with a synthesising thought, not a grand conclusion",
            "- Write in flowing prose — no bullet points, no subheadings",
            f"- Apply {brief.citation_style} citation style",
            "",
            f"Citations: {citation_instruction}",
        ]

        if energy_instruction:
            lines += ["", f"Session note: {energy_instruction}"]

        if inject_full_brief and brief.topic:
            lines += ["", f"Assignment topic: {brief.topic}"]
            if brief.organisational_context:
                lines.append(f"Organisational context (weave analytically — do not describe separately): {brief.organisational_context}")
            if brief.required_frameworks:
                lines.append(f"Required frameworks: {', '.join(brief.required_frameworks)}")

        if memory is not None:
            mem_parts = []
            if memory.previous_section_summary:
                mem_parts.append(
                    f"Previous section ended with: {memory.previous_section_summary[:200]}"
                )
            if memory.argument_continuity:
                mem_parts.append(
                    f"Argument thread to continue: {memory.argument_continuity[:150]}"
                )
            if memory.writing_rhythm_memory:
                mem_parts.append(
                    f"Established rhythm: {memory.writing_rhythm_memory}"
                )
            if memory.terminology:
                recent = list(memory.terminology.keys())[-6:]
                mem_parts.append(f"Terminology already used: {', '.join(recent)}")
            if memory.organisation_context_memory:
                mem_parts.append(
                    f"Organisational details already introduced: {memory.organisation_context_memory[:150]}"
                )
            if mem_parts:
                lines += ["", "Writing continuity (maintain natural consistency with prior sections):"]
                lines.extend(f"- {p}" for p in mem_parts)

        return "\n".join(lines)

    # Backward-compatible alias — existing tests reference this name
    def _build_system_prompt(
        self,
        brief: AssignmentBrief,
        memory: SectionMemory | None = None,
    ) -> str:
        return self.build_system_prompt(brief, memory, inject_full_brief=False, inject_memory=True)
