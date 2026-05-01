"""
AnalysisCache: Django-cache-backed result caching for refinement analysis.

Caches expensive analysis results by content hash to avoid redundant
computation on retries.
"""
from __future__ import annotations

import hashlib
import logging
from typing import Any, Callable

from django.core.cache import cache

logger = logging.getLogger("refinement.cache")


class AnalysisCache:
    """
    Django-cache-backed utility for caching expensive analysis results.

    Cached analysis types include: rubric extraction, assignment requirement
    parsing, framework extraction, section structure analysis, and static
    analysis scores per section.
    """

    TTL_SECONDS: int = 3600

    def _make_key(self, job_id: str, content: str, analysis_type: str) -> str:
        """
        Build a cache key in the format::

            refinement:{job_id}:{md5_16}:{analysis_type}

        where ``md5_16`` is the first 16 hex characters of the MD5 digest
        of *content* encoded as UTF-8.
        """
        md5_16 = hashlib.md5(content.encode()).hexdigest()[:16]
        return f"refinement:{job_id}:{md5_16}:{analysis_type}"

    def get_or_compute(
        self,
        key: str,
        compute_fn: Callable[[], Any],
        ttl: int = 3600,
    ) -> Any:
        """
        Return the cached result for *key* if present (log DEBUG cache hit).

        On a cache miss: call ``compute_fn()``, store the result with *ttl*
        seconds TTL, and return the result.
        """
        cached = cache.get(key)
        if cached is not None:
            logger.debug("refinement.cache | hit key=%s", key)
            return cached

        result = compute_fn()
        cache.set(key, result, ttl)
        return result
