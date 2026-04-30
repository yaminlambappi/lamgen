"""
ClaudeService — Anthropic API wrapper for the LamGen generation pipeline.

Responsibilities:
- Mock mode (CLAUDE_MOCK_MODE=True) for zero-cost local development
- Retry only on transient errors: network failures, 429, 5xx
- Hard per-job token budget guard
- Structured per-call logging: stage, tokens, cost, duration, retry count
- Token-efficient system prompt construction with selective memory injection
"""

import time
import logging

import anthropic
from django.conf import settings

from generation.models import AssignmentBrief, GenerationJob, TokenUsageLog
from generation.services.section_memory import SectionMemory

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
        "framework-based governance. "
        "The evidence suggests that organisations frequently adopt compliance-oriented "
        "interpretations of governance frameworks, prioritising audit readiness over "
        "substantive risk reduction [Jones & Patel, 2022]. This tendency, while "
        "understandable given regulatory pressures, may paradoxically increase systemic "
        "vulnerability by directing resources toward documentation rather than capability "
        "development. A more effective approach, as argued by Chen et al. [2023], involves "
        "integrating framework requirements with organisation-specific threat modelling. "
        "The implications for the organisation under examination are considerable. "
        "Operating across three jurisdictions introduces regulatory fragmentation that "
        "standard frameworks do not adequately address, requiring a governance architecture "
        "that can accommodate divergent compliance requirements without sacrificing coherence. "
        "The analysis presented here suggests that hybrid governance models, combining "
        "elements of NIST and ISO 27001, offer the most viable path forward, though "
        "their implementation demands sustained executive commitment and cross-functional "
        "coordination that many organisations struggle to maintain [Williams, 2023]. "
    ) * 2,
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

# Only retry on transient conditions — never on client errors (4xx except 429)
_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Approximate Sonnet pricing for cost logging (USD per million tokens)
_INPUT_PRICE_PER_M = 3.0
_OUTPUT_PRICE_PER_M = 15.0


def _estimate_cost_cents(input_tokens: int, output_tokens: int) -> float:
    input_cost = (input_tokens / 1_000_000) * _INPUT_PRICE_PER_M * 100
    output_cost = (output_tokens / 1_000_000) * _OUTPUT_PRICE_PER_M * 100
    return round(input_cost + output_cost, 4)


class ClaudeAPIError(Exception):
    """Raised when the Anthropic API call fails after exhausting all retries."""


class BudgetExhaustedError(Exception):
    """Raised when a job has consumed its per-job token budget."""


class ClaudeService:
    MAX_RETRIES = 3
    BACKOFF_BASE = 2  # seconds; delays are 2s, 4s, 8s

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        job: GenerationJob,
        stage_label: str,
        config=None,
    ) -> str:
        """
        Call the Anthropic Messages API and return the response text.

        Behaviour:
        - Returns a canned response immediately when CLAUDE_MOCK_MODE is enabled.
        - Raises BudgetExhaustedError before calling the API if the job has
          consumed its CLAUDE_MAX_TOKENS_PER_JOB limit.
        - Retries on network errors, 429, and 5xx responses with exponential
          backoff. Raises ClaudeAPIError immediately on 4xx client errors.
        - Logs structured metrics (stage, tokens, cost, duration, retries) on
          every call — successful or failed.
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
        max_per_job = getattr(settings, 'CLAUDE_MAX_TOKENS_PER_JOB', 40000)
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

        client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        last_exception = None
        retry_count = 0
        call_start = time.monotonic()

        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                response = client.messages.create(
                    model=settings.CLAUDE_MODEL,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
            except anthropic.APIConnectionError as exc:
                last_exception = exc
                retry_count += 1
                if attempt < self.MAX_RETRIES:
                    wait = self.BACKOFF_BASE ** attempt
                    logger.warning(
                        "generation.claude | stage=%s job=%s attempt=%d/%d "
                        "status=connection_error retry_in=%ds error=%s",
                        stage_label, job.id, attempt, self.MAX_RETRIES, wait, exc,
                    )
                    time.sleep(wait)
                continue

            except anthropic.APIStatusError as exc:
                if exc.status_code not in _RETRYABLE_STATUS_CODES:
                    duration = time.monotonic() - call_start
                    logger.error(
                        "generation.claude | stage=%s job=%s attempt=%d "
                        "status=client_error http=%d duration=%.2fs error=%s",
                        stage_label, job.id, attempt, exc.status_code, duration, exc,
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
                        "generation.claude | stage=%s job=%s attempt=%d/%d "
                        "status=rate_limit_or_server_error http=%d retry_in=%ds",
                        stage_label, job.id, attempt, self.MAX_RETRIES,
                        exc.status_code, wait,
                    )
                    time.sleep(wait)
                continue

            # --- Success ---
            duration = time.monotonic() - call_start
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            cost_cents = _estimate_cost_cents(input_tokens, output_tokens)

            TokenUsageLog.objects.create(
                job=job,
                stage=stage_label,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                model=settings.CLAUDE_MODEL,
            )
            job.total_input_tokens += input_tokens
            job.total_output_tokens += output_tokens
            job.save(update_fields=["total_input_tokens", "total_output_tokens"])

            logger.info(
                "generation.claude | stage=%s job=%s status=success "
                "input_tokens=%d output_tokens=%d cost_cents=%.4f "
                "duration=%.2fs retries=%d",
                stage_label, job.id,
                input_tokens, output_tokens, cost_cents,
                duration, retry_count,
            )

            return response.content[0].text

        duration = time.monotonic() - call_start
        logger.error(
            "generation.claude | stage=%s job=%s status=failed "
            "attempts=%d duration=%.2fs error=%s",
            stage_label, job.id, self.MAX_RETRIES, duration, last_exception,
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
        Build a token-efficient system prompt.

        Base (inject_full_brief=False): persona + 3 core fields (~30 tokens).
        Full brief (inject_full_brief=True): adds topic, type, org context, frameworks.
        Memory injection is gated by inject_memory and only fires when memory has content.
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

    # Backward-compatible alias — existing tests reference this name
    def _build_system_prompt(
        self,
        brief: AssignmentBrief,
        memory: SectionMemory | None = None,
    ) -> str:
        return self.build_system_prompt(brief, memory, inject_full_brief=False, inject_memory=True)
