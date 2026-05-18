"""
Shared AI Service Layer — the single place all AI tool calls go through.

Responsibilities:
  - Input validation against the tool registry schema
  - Prompt assembly from the registry template
  - Provider selection via AIRouter (health-score ranked)
  - Per-tool response cache (configurable TTL from registry)
  - Retry logic (tenacity) with exponential back-off
  - Rate limiting (per-user, sliding window via Django cache)
  - Performance tracking (latency, tokens, success)
  - Structured logging for every request/response
  - Consistent error response envelope

No duplicate logic should exist inside individual tool handlers.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple

from django.conf import settings
from django.core.cache import cache
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from apps.ai_tools.registry import get_tool
from apps.ai_providers.services.factory import ProviderFactory
from orchestration.router import AIRouter

logger = logging.getLogger("ai_service")

# ── Constants (overridable via Django settings) ───────────────────────────────

RATE_LIMIT_CALLS: int = getattr(settings, "AI_RATE_LIMIT_CALLS", 20)
RATE_LIMIT_WINDOW: int = getattr(settings, "AI_RATE_LIMIT_WINDOW", 60)   # seconds
MAX_RETRIES: int = getattr(settings, "AI_MAX_RETRIES", 3)
RETRY_MIN_WAIT: float = getattr(settings, "AI_RETRY_MIN_WAIT", 1.0)
RETRY_MAX_WAIT: float = getattr(settings, "AI_RETRY_MAX_WAIT", 8.0)
DEFAULT_CACHE_TTL: int = getattr(settings, "AI_DEFAULT_CACHE_TTL", 3600)

# Exceptions that are safe to retry
_RETRYABLE = (RuntimeError, TimeoutError, ConnectionError)


# ── Public API ────────────────────────────────────────────────────────────────

class AIServiceError(Exception):
    """Raised for all AI service failures. Carries a user-safe message."""
    def __init__(self, message: str, code: str = "ai_error", status: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status


class AIService:
    """
    Stateless service — instantiate per request or use the module-level
    `run_tool()` helper which wraps this class.
    """

    def __init__(self, user=None):
        self.user = user

    # ── Entry point ───────────────────────────────────────────────────────────

    def execute(self, slug: str, raw_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run an AI tool end-to-end.

        Returns a consistent envelope:
          {
            "ok": true,
            "slug": "<slug>",
            "result": <str | dict>,
            "format": "text" | "json",
            "latency_ms": 123,
            "cached": false
          }

        Raises AIServiceError on validation / provider failures.
        """
        # 1. Resolve tool from registry
        tool = get_tool(slug)
        if not tool:
            raise AIServiceError(
                f"Tool '{slug}' not found.", code="tool_not_found", status=404
            )

        # 2. Validate input
        user_input = self._validate_input(tool, raw_input)

        # 3. Rate limit
        self._check_rate_limit(slug)

        # 4. Build prompt
        prompt = self._build_prompt(tool, user_input)

        # 5. Cache lookup
        cache_ttl = tool.get("cache_ttl", DEFAULT_CACHE_TTL)
        cache_key = self._cache_key(slug, prompt)
        if cache_ttl > 0:
            cached = cache.get(cache_key)
            if cached is not None:
                logger.info("cache_hit tool=%s user=%s", slug, self._user_id())
                return self._envelope(slug, cached, tool["response_format"], latency_ms=0, cached=True)

        # 6. Provider selection
        router = AIRouter()
        provider_name = router.get_provider(slug)
        provider = self._get_provider(provider_name)

        # 7. Generate (with retry)
        start = time.monotonic()
        try:
            raw_output = self._generate_with_retry(provider, prompt)
        except Exception as exc:
            latency_ms = int((time.monotonic() - start) * 1000)
            self._track(slug, provider_name, latency_ms, success=False)
            logger.error(
                "generation_failed tool=%s provider=%s error=%s",
                slug, provider_name, exc
            )
            raise AIServiceError(
                "The AI model failed to generate a response. Please try again.",
                code="provider_error",
                status=502,
            ) from exc
        latency_ms = int((time.monotonic() - start) * 1000)

        # 8. Parse response
        result = self._parse_output(tool, raw_output)

        # 9. Cache store
        if cache_ttl > 0:
            cache.set(cache_key, result, timeout=cache_ttl)

        # 10. Track analytics
        self._track(slug, provider_name, latency_ms, success=True)

        logger.info(
            "tool_executed tool=%s provider=%s latency_ms=%d user=%s",
            slug, provider_name, latency_ms, self._user_id()
        )

        return self._envelope(slug, result, tool["response_format"], latency_ms=latency_ms, cached=False)

    # ── Validation ────────────────────────────────────────────────────────────

    def _validate_input(self, tool: Dict, raw_input: Dict) -> str:
        """Validate and extract the primary input string. Returns cleaned input."""
        for field in tool.get("input_fields", []):
            name = field["name"]
            value = raw_input.get(name, "")
            if field.get("required") and not str(value).strip():
                raise AIServiceError(
                    f"Field '{field.get('label', name)}' is required.",
                    code="validation_error",
                    status=400,
                )
            max_len = field.get("max_length")
            if max_len and len(str(value)) > max_len:
                raise AIServiceError(
                    f"Field '{field.get('label', name)}' exceeds maximum length of {max_len} characters.",
                    code="validation_error",
                    status=400,
                )
        # Primary input is always from the "prompt" field (or first required field)
        primary = raw_input.get("prompt") or raw_input.get(tool["input_fields"][0]["name"], "")
        return str(primary).strip()

    # ── Prompt assembly ───────────────────────────────────────────────────────

    def _build_prompt(self, tool: Dict, user_input: str) -> str:
        system = tool["system_prompt"]
        user_tmpl = tool.get("user_prompt_template", "{input}")
        user_part = user_tmpl.format(input=user_input)
        return f"{system}\n\n{user_part}"

    # ── Rate limiting ─────────────────────────────────────────────────────────

    def _check_rate_limit(self, slug: str) -> None:
        key = f"rl:{self._user_id()}:{slug}"
        count = cache.get(key, 0)
        if count >= RATE_LIMIT_CALLS:
            raise AIServiceError(
                f"Rate limit exceeded. Max {RATE_LIMIT_CALLS} requests per {RATE_LIMIT_WINDOW}s.",
                code="rate_limited",
                status=429,
            )
        # Increment with sliding window
        pipe_count = count + 1
        cache.set(key, pipe_count, timeout=RATE_LIMIT_WINDOW)

    # ── Provider ──────────────────────────────────────────────────────────────

    def _get_provider(self, provider_name: str):
        try:
            return ProviderFactory.get_provider(provider_name)
        except Exception as exc:
            logger.error("provider_init_failed provider=%s error=%s", provider_name, exc)
            raise AIServiceError(
                "AI provider is currently unavailable. Please try again shortly.",
                code="provider_unavailable",
                status=503,
            ) from exc

    # ── Generation with retry ─────────────────────────────────────────────────

    def _generate_with_retry(self, provider, prompt: str) -> str:
        @retry(
            retry=retry_if_exception_type(_RETRYABLE),
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
            before_sleep=before_sleep_log(logger, logging.WARNING),
            reraise=True,
        )
        def _call():
            return provider.generate(prompt)

        return _call()

    # ── Output parsing ────────────────────────────────────────────────────────

    def _parse_output(self, tool: Dict, raw: str) -> Any:
        fmt = tool.get("response_format", "text")
        if fmt == "json":
            return self._parse_json(raw)
        return raw  # text — return as-is

    def _parse_json(self, raw: str) -> Any:
        """Try to extract JSON from the model output (handles markdown fences)."""
        text = raw.strip()
        # Strip markdown fences if present
        if text.startswith("```"):
            lines = text.splitlines()
            inner = []
            in_fence = False
            for line in lines:
                if line.startswith("```"):
                    in_fence = not in_fence
                    continue
                if in_fence or not line.startswith("```"):
                    inner.append(line)
            text = "\n".join(inner).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Return as text if JSON parsing fails — don't crash
            logger.warning("json_parse_failed raw_snippet=%s", raw[:200])
            return {"output": raw, "_parse_error": True}

    # ── Cache key ─────────────────────────────────────────────────────────────

    def _cache_key(self, slug: str, prompt: str) -> str:
        digest = hashlib.sha256(prompt.encode()).hexdigest()[:16]
        return f"ai_tool:{slug}:{digest}"

    # ── Analytics tracking ────────────────────────────────────────────────────

    def _track(self, slug: str, provider: str, latency_ms: int, success: bool) -> None:
        try:
            from apps.ai_tools_core.services.analytics_manager import AnalyticsManager
            AnalyticsManager.track_event(
                self.user,
                "tool_usage",
                {
                    "tool_slug": slug,
                    "provider": provider,
                    "latency": latency_ms,
                    "cost": 0,
                    "is_successful": success,
                },
            )
        except Exception as exc:
            # Analytics must never break the response
            logger.warning("analytics_track_failed error=%s", exc)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _user_id(self) -> str:
        if self.user and hasattr(self.user, "id") and self.user.id:
            return str(self.user.id)
        return "anon"

    def _envelope(
        self,
        slug: str,
        result: Any,
        fmt: str,
        latency_ms: int,
        cached: bool,
    ) -> Dict[str, Any]:
        return {
            "ok": True,
            "slug": slug,
            "result": result,
            "format": fmt,
            "latency_ms": latency_ms,
            "cached": cached,
        }


# ── Module-level convenience function ─────────────────────────────────────────

def run_tool(slug: str, raw_input: Dict[str, Any], user=None) -> Dict[str, Any]:
    """Convenience wrapper. Raises AIServiceError on failure."""
    return AIService(user=user).execute(slug, raw_input)
