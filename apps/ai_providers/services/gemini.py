"""
Gemini provider — supports two auth backends transparently:

  1. Gemini API Studio  (key starts with "AIza")
     Uses: google-generativeai SDK
     Env:  GEMINI_API_KEY=AIza...

  2. Google Cloud Vertex AI  (VERTEX_AI=true OR key starts with "AQ.")
     Uses: google-cloud-aiplatform / vertexai SDK
     Env:  VERTEX_AI=true
           GOOGLE_CLOUD_PROJECT_ID=my-project
           GOOGLE_CLOUD_LOCATION=us-central1
           GOOGLE_APPLICATION_CREDENTIALS=/path/to/sa.json  (optional if ADC)
           GEMINI_MODEL=gemini-2.5-flash

The correct backend is chosen automatically at instantiation time.
No code changes needed when switching between the two.
"""
from __future__ import annotations

import logging
import os

from django.conf import settings

from .base import BaseProvider

logger = logging.getLogger("ai_service")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _gemini_model_name() -> str:
    return getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")


def _use_vertex() -> bool:
    """
    Return True when Vertex AI should be used instead of Gemini API Studio.

    Triggers:
      - VERTEX_AI=true in settings/env
      - GEMINI_API_KEY is absent or starts with "AQ." (Vertex token, not API key)
      - GOOGLE_CLOUD_PROJECT_ID is set (explicit Vertex config)
    """
    if getattr(settings, "VERTEX_AI", False):
        return True
    project = getattr(settings, "GOOGLE_CLOUD_PROJECT_ID", "")
    if project:
        return True
    key = getattr(settings, "GEMINI_API_KEY", "")
    if key and not key.startswith("AIza"):
        return True
    return False


# ---------------------------------------------------------------------------
# Vertex AI backend
# ---------------------------------------------------------------------------

class _VertexBackend:
    """Wraps vertexai.generative_models.GenerativeModel."""

    def __init__(self, model_name: str):
        import vertexai
        from vertexai.generative_models import GenerativeModel

        project = getattr(settings, "GOOGLE_CLOUD_PROJECT_ID", "") or os.environ.get(
            "GOOGLE_CLOUD_PROJECT", ""
        )
        location = getattr(settings, "GOOGLE_CLOUD_LOCATION", "us-central1")
        creds_file = getattr(settings, "GOOGLE_APPLICATION_CREDENTIALS", "") or os.environ.get(
            "GOOGLE_APPLICATION_CREDENTIALS", ""
        )

        if not project:
            raise ValueError(
                "GOOGLE_CLOUD_PROJECT_ID is required for Vertex AI. "
                "Set it in .env or as an environment variable."
            )

        # If a service-account JSON path is given, set the env var so ADC picks it up
        if creds_file and os.path.isfile(creds_file):
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = creds_file

        vertexai.init(project=project, location=location)
        self.model = GenerativeModel(model_name)
        logger.info(
            "vertex_ai_init project=%s location=%s model=%s",
            project, location, model_name,
        )

    def generate(self, prompt: str) -> str:
        from vertexai.generative_models import GenerationConfig
        response = self.model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,
            ),
        )
        return response.text

    async def generate_async(self, prompt: str) -> str:
        from vertexai.generative_models import GenerationConfig
        response = await self.model.generate_content_async(
            prompt,
            generation_config=GenerationConfig(
                temperature=0.7,
                max_output_tokens=8192,
            ),
        )
        return response.text


# ---------------------------------------------------------------------------
# Gemini API Studio backend
# ---------------------------------------------------------------------------

class _StudioBackend:
    """Wraps google.generativeai (API Studio / AIza keys)."""

    def __init__(self, api_key: str, model_name: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        logger.info("gemini_studio_init model=%s", model_name)

    def generate(self, prompt: str) -> str:
        response = self.model.generate_content(prompt)
        return response.text

    async def generate_async(self, prompt: str) -> str:
        response = await self.model.generate_content_async(prompt)
        return response.text


# ---------------------------------------------------------------------------
# Public provider
# ---------------------------------------------------------------------------

class GeminiProvider(BaseProvider):
    """
    Unified Gemini provider.  Picks Vertex AI or API Studio automatically.
    """

    def __init__(self):
        super().__init__("gemini")
        model_name = _gemini_model_name()

        if _use_vertex():
            logger.info("gemini_backend=vertex_ai model=%s", model_name)
            self._backend = _VertexBackend(model_name)
            self._backend_name = "vertex_ai"
        else:
            api_key = getattr(settings, "GEMINI_API_KEY", "")
            if not api_key:
                raise ValueError(
                    "No Gemini credentials found. Set GEMINI_API_KEY (AIza...) "
                    "or configure Vertex AI via GOOGLE_CLOUD_PROJECT_ID + VERTEX_AI=true."
                )
            logger.info("gemini_backend=api_studio model=%s", model_name)
            self._backend = _StudioBackend(api_key, model_name)
            self._backend_name = "api_studio"

    # ── Sync ─────────────────────────────────────────────────────────────────

    def generate(self, prompt: str, **kwargs) -> str:
        try:
            completion = self._backend.generate(prompt)
        except Exception as exc:
            self._handle_exc(exc, "generate")
        prompt_tokens = self.get_token_count(prompt)
        completion_tokens = self.get_token_count(completion)
        self.log_usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
        return completion

    def generate_stream(self, prompt: str, **kwargs):
        # Vertex AI streaming — fall back to single call if not supported
        try:
            if self._backend_name == "vertex_ai":
                responses = self._backend.model.generate_content(prompt, stream=True)
                for chunk in responses:
                    yield chunk.text
            else:
                import google.generativeai as genai  # noqa: F401
                responses = self._backend.model.generate_content(prompt, stream=True)
                for chunk in responses:
                    yield chunk.text
        except Exception as exc:
            self._handle_exc(exc, "generate_stream")

    # ── Async ─────────────────────────────────────────────────────────────────

    async def generate_async(self, prompt: str, **kwargs) -> str:
        try:
            completion = await self._backend.generate_async(prompt)
        except Exception as exc:
            self._handle_exc(exc, "generate_async")
        prompt_tokens = self.get_token_count(prompt)
        completion_tokens = self.get_token_count(completion)
        self.log_usage(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
        return completion

    async def generate_stream_async(self, prompt: str, **kwargs):
        try:
            if self._backend_name == "vertex_ai":
                responses = await self._backend.model.generate_content_async(
                    prompt, stream=True
                )
                async for chunk in responses:
                    yield chunk.text
            else:
                responses = await self._backend.model.generate_content_async(
                    prompt, stream=True
                )
                async for chunk in responses:
                    yield chunk.text
        except Exception as exc:
            self._handle_exc(exc, "generate_stream_async")

    # ── Error handling ────────────────────────────────────────────────────────

    def _handle_exc(self, exc: Exception, method: str) -> None:
        err = str(exc)
        exc_type = type(exc).__name__

        if "API_KEY_SERVICE_BLOCKED" in err or (
            "PermissionDenied" in exc_type and "API_KEY" in err
        ):
            logger.error(
                "gemini_%s_blocked backend=%s — "
                "API key is blocked. For Vertex AI set VERTEX_AI=true + "
                "GOOGLE_CLOUD_PROJECT_ID. For API Studio use an AIza... key.",
                method, self._backend_name,
            )
            raise ConnectionError(
                "Gemini API key is blocked. "
                "Use VERTEX_AI=true with GOOGLE_CLOUD_PROJECT_ID, "
                "or replace GEMINI_API_KEY with a valid AIza... key."
            ) from exc

        if "PERMISSION_DENIED" in err or "403" in err:
            logger.error(
                "gemini_%s_permission_denied backend=%s error=%s",
                method, self._backend_name, exc,
            )
            raise ConnectionError(f"Gemini permission denied ({self._backend_name}): {exc}") from exc

        if "RESOURCE_EXHAUSTED" in err or "429" in err or "quota" in err.lower():
            logger.warning("gemini_%s_quota_exceeded backend=%s", method, self._backend_name)
            raise RuntimeError(f"Gemini quota exceeded: {exc}") from exc

        logger.error(
            "gemini_%s_failed backend=%s error=%s",
            method, self._backend_name, exc,
        )
        raise ConnectionError(f"Gemini {method} error ({self._backend_name}): {exc}") from exc
