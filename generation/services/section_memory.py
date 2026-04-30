"""
SectionMemory — Redis-backed cross-section context with hard size caps.

Caps prevent prompt growth across sections:
  - thesis_argument: truncated to 150 chars
  - terminology: max 10 entries (most recent)
  - analytical_positions: rolling window of last 3
  - section_summaries: rolling window of last 2
  - concepts_discussed: REMOVED (was never used in generation prompts)
"""

import json
import logging
from dataclasses import asdict, dataclass, field

import redis
from django.conf import settings

logger = logging.getLogger(__name__)

# Hard caps — keep memory blob under ~200 tokens regardless of document length
_MAX_THESIS_CHARS = 150
_MAX_TERMINOLOGY_ENTRIES = 10
_MAX_ANALYTICAL_POSITIONS = 3
_MAX_SECTION_SUMMARIES = 2


class SectionMemoryError(Exception):
    """Raised when a SectionMemory operation fails (e.g. key not found in Redis)."""


@dataclass
class SectionMemory:
    """
    Compact cross-section context stored in Redis.

    Fields are capped on every update to prevent unbounded prompt growth.
    """
    job_id: str
    thesis_argument: str = ""           # max 150 chars
    terminology: dict = field(default_factory=dict)          # max 10 entries
    citations_used: list = field(default_factory=list)       # deduplicated, no cap
    analytical_positions: list = field(default_factory=list) # last 3 only
    section_summaries: list = field(default_factory=list)    # last 2 only


class SectionMemoryService:
    TTL_SECONDS = 14400  # 4 hours

    @staticmethod
    def _redis_key(job_id: str) -> str:
        return f"section_memory:{job_id}"

    @staticmethod
    def _get_redis() -> redis.Redis:
        return redis.Redis.from_url(settings.REDIS_URL)

    @classmethod
    def initialise(cls, job_id: str) -> SectionMemory:
        """Create an empty SectionMemory and store it in Redis with a 4-hour TTL."""
        memory = SectionMemory(job_id=job_id)
        r = cls._get_redis()
        r.setex(cls._redis_key(job_id), cls.TTL_SECONDS, json.dumps(asdict(memory)))
        return memory

    @classmethod
    def get(cls, job_id: str) -> SectionMemory:
        """Retrieve and deserialise the SectionMemory. Raises SectionMemoryError if missing."""
        r = cls._get_redis()
        raw = r.get(cls._redis_key(job_id))
        if raw is None:
            raise SectionMemoryError(
                f"SectionMemory not found for job_id={job_id!r}. "
                "Key may have expired or was never initialised."
            )
        data = json.loads(raw)
        # Drop legacy 'concepts_discussed' field if present in old data
        data.pop('concepts_discussed', None)
        return SectionMemory(**data)

    @classmethod
    def update(cls, job_id: str, section_update: dict) -> SectionMemory:
        """
        Merge section output into SectionMemory and enforce size caps.

        Accepted keys in section_update:
          thesis_argument (str)   — replaces current; truncated to 150 chars
          terminology (dict)      — merged; capped at 10 entries
          citations_used (list)   — deduplicated append
          analytical_positions (list) — appended; capped at last 3
          section_summary (dict)  — appended; capped at last 2
        """
        memory = cls.get(job_id)

        if "thesis_argument" in section_update:
            memory.thesis_argument = section_update["thesis_argument"][:_MAX_THESIS_CHARS]

        if "terminology" in section_update:
            memory.terminology.update(section_update["terminology"])
            if len(memory.terminology) > _MAX_TERMINOLOGY_ENTRIES:
                # Keep the most recently added entries
                keys = list(memory.terminology.keys())[-_MAX_TERMINOLOGY_ENTRIES:]
                memory.terminology = {k: memory.terminology[k] for k in keys}

        if "citations_used" in section_update:
            existing = set(memory.citations_used)
            for citation in section_update["citations_used"]:
                if citation not in existing:
                    memory.citations_used.append(citation)
                    existing.add(citation)

        if "analytical_positions" in section_update:
            memory.analytical_positions.extend(section_update["analytical_positions"])
            memory.analytical_positions = memory.analytical_positions[-_MAX_ANALYTICAL_POSITIONS:]

        if "section_summary" in section_update:
            memory.section_summaries.append(section_update["section_summary"])
            memory.section_summaries = memory.section_summaries[-_MAX_SECTION_SUMMARIES:]

        r = cls._get_redis()
        r.setex(cls._redis_key(job_id), cls.TTL_SECONDS, json.dumps(asdict(memory)))
        return memory

    @classmethod
    def delete(cls, job_id: str) -> None:
        """Remove the SectionMemory key from Redis."""
        r = cls._get_redis()
        r.delete(cls._redis_key(job_id))
