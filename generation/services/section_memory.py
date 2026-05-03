"""
SectionMemory — Redis-backed cross-section writing continuity context.

Stores persistent writing state across section generation calls so each
Opus section call receives full continuity context:
  - previous_section_summary: what the last section covered
  - argument_continuity: the thread of argument to continue
  - writing_rhythm_memory: pacing/style notes from prior sections
  - terminology_memory: established terms and their usage
  - organisation_context_memory: org-specific details already introduced
  - student_persona: persistent writing identity injected into every Opus call
  - analytical_positions: rolling window of positions taken (last 3)
  - section_summaries: rolling window of section summaries (last 2)
  - citations_used: deduplicated list of citations already used

Size caps prevent unbounded prompt growth across long documents.
"""

import json
import logging
from dataclasses import asdict, dataclass, field

import redis
from django.conf import settings

from generation.services.author_identity import build_student_persona, DEFAULT_STUDENT_PERSONA as _AUTHOR_PERSONA

logger = logging.getLogger(__name__)

# Hard caps — keep memory blob under ~300 tokens regardless of document length
_MAX_THESIS_CHARS = 150
_MAX_TERMINOLOGY_ENTRIES = 12
_MAX_ANALYTICAL_POSITIONS = 3
_MAX_SECTION_SUMMARIES = 2
_MAX_SUMMARY_CHARS = 250
_MAX_CONTINUITY_CHARS = 200
_MAX_RHYTHM_CHARS = 120
_MAX_ORG_CONTEXT_CHARS = 200

# Default student persona — sourced from the canonical AUTHOR_PROFILE
# Import alias kept for backward-compatibility with any code that references this name.
DEFAULT_STUDENT_PERSONA = _AUTHOR_PERSONA


class SectionMemoryError(Exception):
    """Raised when a SectionMemory operation fails (e.g. key not found in Redis)."""


@dataclass
class SectionMemory:
    """
    Persistent writing continuity context stored in Redis.

    All fields are capped on every update to prevent unbounded prompt growth.
    Injected into every Opus section generation call to maintain natural
    long-form voice and prevent the stitched-together feeling.
    """
    job_id: str
    # Writing continuity fields — injected into Opus system prompt
    previous_section_summary: str = ""       # max 250 chars
    argument_continuity: str = ""            # max 200 chars — thread to continue
    writing_rhythm_memory: str = ""          # max 120 chars — pacing notes
    organisation_context_memory: str = ""   # max 200 chars — org details introduced
    student_persona: dict = field(default_factory=lambda: dict(DEFAULT_STUDENT_PERSONA))
    # Legacy / shared fields
    thesis_argument: str = ""               # max 150 chars
    terminology: dict = field(default_factory=dict)          # max 12 entries
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
    def initialise(cls, job_id: str, student_persona: dict | None = None) -> SectionMemory:
        """
        Create a fresh SectionMemory and store it in Redis with a 4-hour TTL.

        When no persona is supplied, builds one from the canonical AUTHOR_PROFILE
        via build_student_persona() so every job starts with the authored identity.
        """
        persona = student_persona or build_student_persona()
        memory = SectionMemory(job_id=job_id, student_persona=persona)
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
        # Drop legacy fields from old data
        data.pop('concepts_discussed', None)
        # Backfill new fields for existing memory objects
        data.setdefault('previous_section_summary', '')
        data.setdefault('argument_continuity', '')
        data.setdefault('writing_rhythm_memory', '')
        data.setdefault('organisation_context_memory', '')
        data.setdefault('student_persona', dict(DEFAULT_STUDENT_PERSONA))
        return SectionMemory(**data)

    @classmethod
    def update(cls, job_id: str, section_update: dict) -> SectionMemory:
        """
        Merge section output into SectionMemory and enforce size caps.

        Accepted keys in section_update:
          previous_section_summary (str) — summary of the section just written
          argument_continuity (str)      — argument thread to carry forward
          writing_rhythm_memory (str)    — pacing/style notes
          organisation_context_memory (str) — org details introduced
          student_persona (dict)         — update persona fields
          thesis_argument (str)          — replaces current; truncated to 150 chars
          terminology (dict)             — merged; capped at 12 entries
          citations_used (list)          — deduplicated append
          analytical_positions (list)    — appended; capped at last 3
          section_summary (dict)         — appended; capped at last 2
        """
        memory = cls.get(job_id)

        if "previous_section_summary" in section_update:
            memory.previous_section_summary = (
                section_update["previous_section_summary"][:_MAX_SUMMARY_CHARS]
            )

        if "argument_continuity" in section_update:
            memory.argument_continuity = (
                section_update["argument_continuity"][:_MAX_CONTINUITY_CHARS]
            )

        if "writing_rhythm_memory" in section_update:
            memory.writing_rhythm_memory = (
                section_update["writing_rhythm_memory"][:_MAX_RHYTHM_CHARS]
            )

        if "organisation_context_memory" in section_update:
            memory.organisation_context_memory = (
                section_update["organisation_context_memory"][:_MAX_ORG_CONTEXT_CHARS]
            )

        if "student_persona" in section_update:
            memory.student_persona.update(section_update["student_persona"])

        if "thesis_argument" in section_update:
            memory.thesis_argument = section_update["thesis_argument"][:_MAX_THESIS_CHARS]

        if "terminology" in section_update:
            memory.terminology.update(section_update["terminology"])
            if len(memory.terminology) > _MAX_TERMINOLOGY_ENTRIES:
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
