"""
GenerationConfig — runtime configuration resolver for the LamGen pipeline.

Reads Django settings once per pipeline execution and exposes:
- Per-stage token budgets keyed by generation mode (economy / standard / quality)
- Model routing: Haiku for analysis, Sonnet for outline/validation, Opus for section writing
- Feature flags controlling prompt verbosity and memory injection
- Budget protection helpers
- Cost estimation utilities

All generation services import from here rather than reading settings directly.
"""

from django.conf import settings


# ---------------------------------------------------------------------------
# Model routing — specialised per pipeline role
# ---------------------------------------------------------------------------

# Haiku: fast, cheap — document parsing, analysis, metadata extraction
HAIKU_MODEL = 'claude-haiku-4-5'
# Sonnet: balanced — outline generation, validation, citation alignment
SONNET_MODEL = 'claude-sonnet-4-5'
# Opus: highest quality — section writing, analytical reasoning, natural generation
OPUS_MODEL = 'claude-opus-4-5'

# Opus generation settings — tuned for natural, varied academic writing
OPUS_GENERATION_SETTINGS = {
    'temperature': 0.82,
    'top_p': 0.92,
}

# ---------------------------------------------------------------------------
# Token budgets per generation mode
# ---------------------------------------------------------------------------

_MODE_BUDGETS = {
    # economy: Haiku analysis, Sonnet outline, Sonnet sections — lowest cost
    'economy': {
        'analysis_max_tokens': 600,
        'outline_max_tokens': 800,
        'section_token_multiplier': 1.2,
        'section_token_cap': 3000,
        'inject_full_brief': False,
        'inject_memory': False,
        'inject_research_context': False,
        'section_model': SONNET_MODEL,  # economy uses Sonnet for sections
    },
    # standard: Haiku analysis, Sonnet outline, Opus sections — recommended
    'standard': {
        'analysis_max_tokens': 800,
        'outline_max_tokens': 1000,
        'section_token_multiplier': 1.5,
        'section_token_cap': 5000,
        'inject_full_brief': False,
        'inject_memory': True,
        'inject_research_context': False,
        'section_model': OPUS_MODEL,
    },
    # quality: Haiku analysis, Sonnet outline, Opus sections — full context injection
    'quality': {
        'analysis_max_tokens': 1000,
        'outline_max_tokens': 1200,
        'section_token_multiplier': 1.6,
        'section_token_cap': 6000,
        'inject_full_brief': True,
        'inject_memory': True,
        'inject_research_context': True,
        'section_model': OPUS_MODEL,
    },
}

# Pricing (USD per million tokens) — Opus rates
_OPUS_INPUT_PRICE_PER_M = 15.0
_OPUS_OUTPUT_PRICE_PER_M = 75.0
# Sonnet rates
_SONNET_INPUT_PRICE_PER_M = 3.0
_SONNET_OUTPUT_PRICE_PER_M = 15.0
# Haiku rates
_HAIKU_INPUT_PRICE_PER_M = 0.8
_HAIKU_OUTPUT_PRICE_PER_M = 4.0

# Default to Sonnet blended rate for cost estimation
_INPUT_PRICE_PER_M = _SONNET_INPUT_PRICE_PER_M
_OUTPUT_PRICE_PER_M = _SONNET_OUTPUT_PRICE_PER_M


class GenerationConfig:
    """
    Resolved configuration for a single generation run.

    Instantiate once per pipeline execution and pass to all services that
    need token budgets, feature flags, model routing, or cost estimates.

    Model routing:
    - analysis_model  → Haiku  (fast, cheap metadata extraction)
    - outline_model   → Sonnet (structured planning)
    - section_model   → Opus   (natural long-form writing, standard/quality modes)
    - validation_model → Sonnet (light citation/rubric checks)
    """

    def __init__(self, mode: str | None = None) -> None:
        raw_mode = mode or getattr(settings, 'GENERATION_MODE', 'standard')
        if raw_mode not in _MODE_BUDGETS:
            raw_mode = 'standard'
        self.mode = raw_mode
        self._budget = _MODE_BUDGETS[self.mode]

        self.mock_mode = getattr(settings, 'CLAUDE_MOCK_MODE', False)
        self.max_tokens_per_job = getattr(settings, 'CLAUDE_MAX_TOKENS_PER_JOB', 80000)
        self.assignment_type_default = getattr(settings, 'ASSIGNMENT_TYPE_DEFAULT', 'essay')
        self.citation_style_default = getattr(settings, 'CITATION_STYLE_DEFAULT', 'APA')
        self.writing_tone_default = getattr(settings, 'WRITING_TONE_DEFAULT', 'critical_analytical')
        self.section_mode = getattr(settings, 'SECTION_MODE', 'auto')
        self.section_count_default = getattr(settings, 'SECTION_COUNT_DEFAULT', 5)
        self.max_budget_cents = getattr(settings, 'MAX_GENERATION_BUDGET_CENTS', 150)

        # Model routing — can be overridden per-role via env vars
        self.analysis_model = getattr(settings, 'HAIKU_MODEL', HAIKU_MODEL)
        self.outline_model = getattr(settings, 'SONNET_MODEL', SONNET_MODEL)
        self.section_model = self._budget['section_model']
        self.validation_model = getattr(settings, 'SONNET_MODEL', SONNET_MODEL)

        # Opus generation settings for natural writing
        self.opus_settings = OPUS_GENERATION_SETTINGS.copy()

    # ------------------------------------------------------------------
    # Token budget accessors
    # ------------------------------------------------------------------

    @property
    def analysis_max_tokens(self) -> int:
        return self._budget['analysis_max_tokens']

    @property
    def outline_max_tokens(self) -> int:
        return self._budget['outline_max_tokens']

    def section_max_tokens(self, target_word_count: int) -> int:
        """Return the output token cap for a section of the given word count."""
        raw = int(target_word_count * self._budget['section_token_multiplier'])
        return min(raw, self._budget['section_token_cap'])

    # ------------------------------------------------------------------
    # Feature flags
    # ------------------------------------------------------------------

    @property
    def inject_full_brief(self) -> bool:
        return self._budget['inject_full_brief']

    @property
    def inject_memory(self) -> bool:
        return self._budget['inject_memory']

    @property
    def inject_research_context(self) -> bool:
        return self._budget['inject_research_context']

    # ------------------------------------------------------------------
    # Budget protection
    # ------------------------------------------------------------------

    def tokens_remaining(self, job) -> int:
        """Return how many tokens the job can still consume before hitting the hard cap."""
        used = job.total_input_tokens + job.total_output_tokens
        return max(0, self.max_tokens_per_job - used)

    def budget_exhausted(self, job) -> bool:
        """Return True if the job has consumed its token budget."""
        return self.tokens_remaining(job) <= 0

    # ------------------------------------------------------------------
    # Cost estimation
    # ------------------------------------------------------------------

    def estimate_cost_cents(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD cents using blended Sonnet rates."""
        input_cost = (input_tokens / 1_000_000) * _INPUT_PRICE_PER_M * 100
        output_cost = (output_tokens / 1_000_000) * _OUTPUT_PRICE_PER_M * 100
        return round(input_cost + output_cost, 4)

    def estimate_job_cost_cents(self, job) -> float:
        """Return the estimated cost in cents for a completed or in-progress job."""
        return self.estimate_cost_cents(job.total_input_tokens, job.total_output_tokens)

    def estimate_assignment_cost_cents(self, target_word_count: int, n_sections: int) -> float:
        """
        Pre-generation cost estimate for a job.

        Assumptions:
        - 1 Haiku analysis call: ~1,500 input + analysis_max_tokens output
        - 1 Sonnet outline call: ~600 input + outline_max_tokens output
        - n_sections Opus generation calls: ~1,200 input each + section_max_tokens output
        """
        analysis_in = 1500
        analysis_out = self.analysis_max_tokens
        outline_in = 600
        outline_out = self.outline_max_tokens
        words_per_section = target_word_count // max(n_sections, 1)
        section_in = 1200  # larger due to persona + memory injection
        section_out = self.section_max_tokens(words_per_section)

        total_in = analysis_in + outline_in + (section_in * n_sections)
        total_out = analysis_out + outline_out + (section_out * n_sections)
        return self.estimate_cost_cents(total_in, total_out)
