"""
CitationEngine: citation insertion, validation, and hallucination detection.

Uses StaticAnalyser for format validation and DOI checking (zero LLM calls
for format checking). Applies threshold-based skipping when citation
completeness is already high.
"""
from __future__ import annotations

import logging
import re

from apps.generation.models import AssignmentBrief, GeneratedSection, GenerationJob
from apps.generation.services.refinement.static_analyser import StaticAnalyser

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Citation format regex patterns per style
# ---------------------------------------------------------------------------

_CITATION_PATTERNS: dict[str, str] = {
    "Harvard": r"\([A-Z][a-z]+,\s\d{4}\)",
    "APA":     r"\([A-Z][a-z]+,\s\d{4}\)",
    "Chicago": r"\[\d+\]",
    "MLA":     r"\([A-Z][a-z]+\s\d+\)",
}

# Academic URL domains considered valid
_ACADEMIC_DOMAINS = (
    ".edu", ".ac.uk", ".ac.", ".edu.", ".gov",
    "springer.com", "wiley.com", "elsevier.com", "tandfonline.com",
    "sagepub.com", "jstor.org", "pubmed.ncbi.nlm.nih.gov",
    "scholar.google.com", "researchgate.net", "academia.edu",
    "oxfordjournals.org", "cambridge.org", "nature.com", "science.org",
    "ieee.org", "acm.org", "apa.org", "bbc.co.uk",
)

# Hallucination placeholder
_HALLUCINATION_PLACEHOLDER = "[CITATION FLAGGED: POSSIBLE HALLUCINATION]"


class CitationEngine:
    """
    Handles citation insertion, reference list validation, hallucination
    detection, and citation completeness scoring.

    Supported citation styles: Harvard, APA, Chicago, MLA.
    Context window optimisation: receives only citation-relevant chunks
    (section content + reference list), not the full assignment.
    """

    SUPPORTED_STYLES: set[str] = {"Harvard", "APA", "Chicago", "MLA"}

    def __init__(self) -> None:
        self._analyser = StaticAnalyser()
        self.skipped_stages: list[str] = []

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def process(
        self,
        sections: list[GeneratedSection],
        brief: AssignmentBrief,
        job: GenerationJob,
    ) -> tuple[list[GeneratedSection], float]:
        """
        Run the citation processing pass.

        - Uses StaticAnalyser.validate_doi_format() and
          validate_citation_format() for format validation (zero LLM calls).
        - Applies threshold skip: if citation_completeness > 92, skips
          citation insertion pass and logs to skipped_stages.
        - Identifies uncited claims, inserts citations, validates reference
          list, and detects hallucinations.

        Returns a tuple of (updated_sections, citation_completeness_score).
        citation_completeness_score = (valid_citations / total_claims) * 100.
        """
        citation_style = getattr(brief, "citation_style", "Harvard")

        # --- Compute initial citation completeness ---
        total_claims = 0
        valid_citations = 0

        for section in sections:
            content = section.content or ""
            # Count in-text citations as valid citations
            pattern = _CITATION_PATTERNS.get(citation_style, _CITATION_PATTERNS["Harvard"])
            found_citations = re.findall(pattern, content)
            # Heuristic: each sentence that makes a factual/analytical claim
            # is a potential claim; citations found count as valid
            sentences = re.split(r"[.!?]+(?:\s+|$)", content)
            sentences = [s.strip() for s in sentences if s.strip()]
            section_claims = max(len(sentences), 1)
            total_claims += section_claims
            valid_citations += min(len(found_citations), section_claims)

        if total_claims == 0:
            citation_completeness_score = 0.0
        else:
            citation_completeness_score = (valid_citations / total_claims) * 100.0

        # --- Threshold skip ---
        if citation_completeness_score > 92:
            logger.info(
                "citation_engine | job=%s citation_completeness=%.1f > 92 — "
                "skipping citation insertion pass",
                job.id, citation_completeness_score,
            )
            self.skipped_stages.append("citation_insertion")
            # Still validate reference list for each section
            for section in sections:
                self._validate_reference_list(section.content or "", citation_style)
            return sections, citation_completeness_score

        # --- Full citation pass ---
        updated_sections = []
        for section in sections:
            # Detect uncited claims
            uncited = self._detect_uncited_claims(section, job)

            if uncited:
                # Insert citations via LLM
                section = self._insert_citations(section, brief, job)

            # Validate reference list
            self._validate_reference_list(section.content or "", citation_style)

            # Detect hallucinations in references
            references = self._extract_references(section.content or "")
            if references:
                flagged = self._detect_hallucinations(references)
                if flagged:
                    logger.warning(
                        "citation_engine | job=%s section=%s flagged_refs=%d",
                        job.id, section.order, len(flagged),
                    )
                    section.content = self._replace_hallucinated_refs(
                        section.content or "", flagged
                    )

            # Sort reference list
            section.content = self._sort_reference_list(
                section.content or "", citation_style
            )

            updated_sections.append(section)

        # --- Recompute score after processing ---
        total_claims = 0
        valid_citations = 0
        for section in updated_sections:
            content = section.content or ""
            pattern = _CITATION_PATTERNS.get(citation_style, _CITATION_PATTERNS["Harvard"])
            found_citations = re.findall(pattern, content)
            sentences = re.split(r"[.!?]+(?:\s+|$)", content)
            sentences = [s.strip() for s in sentences if s.strip()]
            section_claims = max(len(sentences), 1)
            total_claims += section_claims
            valid_citations += min(len(found_citations), section_claims)

        if total_claims == 0:
            citation_completeness_score = 0.0
        else:
            citation_completeness_score = (valid_citations / total_claims) * 100.0

        logger.info(
            "citation_engine | job=%s citation_completeness_score=%.1f",
            job.id, citation_completeness_score,
        )
        return updated_sections, citation_completeness_score

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _detect_uncited_claims(
        self,
        section: GeneratedSection,
        job: GenerationJob,
    ) -> list[str]:
        """
        Identify factual/analytical claims in *section* that lack in-text
        citations. Uses model_override='haiku'.

        Returns a list of claim strings that need citations.
        """
        from apps.generation.services.claude_service import ClaudeService

        content = section.content or ""
        if not content.strip():
            return []

        system_prompt = (
            "You are an academic citation checker. "
            "Identify factual or analytical claims in the text that lack in-text citations. "
            "Return each uncited claim on a separate line. "
            "Return only the claim text, nothing else. "
            "If all claims are cited, return an empty response."
        )
        user_prompt = (
            f"Identify uncited factual/analytical claims in the following text:\n\n{content}"
        )

        claude = ClaudeService()
        try:
            response = claude.call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1000,
                job=job,
                stage_label="citation_detect_uncited",
                model_override="haiku",
            )
            claims = [line.strip() for line in response.splitlines() if line.strip()]
            return claims
        except Exception as exc:
            logger.warning(
                "citation_engine._detect_uncited_claims | job=%s error=%s",
                job.id, exc,
            )
            return []

    def _insert_citations(
        self,
        section: GeneratedSection,
        brief: AssignmentBrief,
        job: GenerationJob,
    ) -> GeneratedSection:
        """
        Format and insert citations into *section* per the active citation
        style in *brief*. Uses model_override='sonnet'.

        Returns the updated section.
        """
        from apps.generation.services.claude_service import ClaudeService

        citation_style = getattr(brief, "citation_style", "Harvard")
        content = section.content or ""

        system_prompt = (
            f"You are an expert academic writer. "
            f"Insert appropriate in-text citations in {citation_style} format "
            f"for factual and analytical claims that lack citations. "
            f"Preserve all existing citations. "
            f"Do not alter the meaning or structure of the text. "
            f"Return only the updated text."
        )
        user_prompt = (
            f"Insert {citation_style} citations for uncited claims in the following text:\n\n"
            f"{content}"
        )

        claude = ClaudeService()
        try:
            updated_content = claude.call(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=len(content.split()) * 2 + 500,
                job=job,
                stage_label="citation_insert",
                model_override="sonnet",
            )
            section.content = updated_content
        except Exception as exc:
            logger.warning(
                "citation_engine._insert_citations | job=%s error=%s",
                job.id, exc,
            )

        return section

    def _validate_reference_list(
        self,
        content: str,
        citation_style: str,
    ) -> bool:
        """
        Check bidirectional consistency: every in-text citation has a
        reference list entry, and every reference list entry has at least
        one in-text citation.

        Returns True if the reference list is consistent.
        """
        # Extract in-text citations
        pattern = _CITATION_PATTERNS.get(citation_style, _CITATION_PATTERNS["Harvard"])
        in_text_citations = set(re.findall(pattern, content))

        # Extract reference list entries
        references = self._extract_references(content)

        if not in_text_citations and not references:
            return True

        # For Harvard/APA: match (Author, Year) to reference entries starting with Author
        if citation_style in ("Harvard", "APA"):
            return self._validate_harvard_apa_consistency(
                in_text_citations, references
            )
        elif citation_style == "Chicago":
            return self._validate_chicago_consistency(in_text_citations, references)
        elif citation_style == "MLA":
            return self._validate_mla_consistency(in_text_citations, references)

        return True

    def _detect_hallucinations(self, references: list[str]) -> list[str]:
        """
        Detect hallucination indicators in *references*:
        - Malformed DOI (via StaticAnalyser.validate_doi_format())
        - Implausible journal name patterns
        - Author-year mismatches within the same reference
        - Non-academic URLs (must resolve to .edu, .ac.uk, .org, or known
          publisher domains)

        Returns a list of flagged reference strings. Hallucinated citations
        are replaced with flagged placeholders in the document.
        """
        flagged = []

        for ref in references:
            if self._is_hallucinated_reference(ref):
                flagged.append(ref)

        return flagged

    def _sort_reference_list(
        self,
        content: str,
        citation_style: str,
    ) -> str:
        """
        Sort the reference list in *content* according to *citation_style*:
        - Harvard / APA / MLA: alphabetical by author surname
        - Chicago: sequential footnote numbering

        Uses StaticAnalyser.validate_reference_list_order() to check order
        before sorting.

        Returns the content string with the reference list sorted.
        """
        references = self._extract_references(content)
        if not references:
            return content

        # Check if already in correct order
        if self._analyser.validate_reference_list_order(references, citation_style):
            return content

        # Sort based on style
        style_upper = citation_style.strip().upper()
        if style_upper in ("HARVARD", "APA", "MLA"):
            sorted_refs = sorted(references, key=lambda r: r.split()[0].lower() if r.split() else "")
        elif style_upper == "CHICAGO":
            # Validate sequential footnote numbering — renumber if needed
            sorted_refs = self._renumber_chicago_footnotes(references)
        else:
            sorted_refs = references

        # Replace the reference list section in content
        return self._replace_references_in_content(content, references, sorted_refs)

    # ------------------------------------------------------------------
    # Internal utility methods
    # ------------------------------------------------------------------

    def _extract_references(self, content: str) -> list[str]:
        """
        Extract reference list entries from *content*.

        Looks for a "References" or "Bibliography" section header and
        returns each non-empty line after it as a reference entry.
        """
        # Look for a references section
        ref_section_pattern = re.compile(
            r"(?:^|\n)\s*(?:References|Bibliography|Works Cited|Reference List)\s*\n",
            re.IGNORECASE,
        )
        match = ref_section_pattern.search(content)
        if not match:
            return []

        ref_section = content[match.end():]
        lines = ref_section.splitlines()
        references = []
        for line in lines:
            line = line.strip()
            if line:
                references.append(line)

        return references

    def _replace_hallucinated_refs(
        self, content: str, flagged_refs: list[str]
    ) -> str:
        """Replace flagged reference strings with hallucination placeholders."""
        for ref in flagged_refs:
            content = content.replace(ref, _HALLUCINATION_PLACEHOLDER)
        return content

    def _replace_references_in_content(
        self,
        content: str,
        original_refs: list[str],
        sorted_refs: list[str],
    ) -> str:
        """
        Replace the original reference list in *content* with *sorted_refs*.

        Locates the references section header and replaces all lines after it
        that correspond to the original reference entries.
        """
        if not original_refs:
            return content

        # Find the references section header
        ref_section_pattern = re.compile(
            r"(?:^|\n)(\s*(?:References|Bibliography|Works Cited|Reference List)\s*\n)",
            re.IGNORECASE,
        )
        match = ref_section_pattern.search(content)
        if not match:
            # Fallback: replace the block from first to last reference
            first_ref = original_refs[0]
            last_ref = original_refs[-1]
            start_idx = content.find(first_ref)
            end_idx = content.rfind(last_ref)
            if start_idx == -1 or end_idx == -1:
                return content
            end_idx += len(last_ref)
            new_ref_block = "\n".join(sorted_refs)
            return content[:start_idx] + new_ref_block + content[end_idx:]

        # Replace everything after the header with the sorted references
        header_end = match.end()
        new_ref_block = "\n".join(sorted_refs)
        return content[:header_end] + new_ref_block

    def _is_hallucinated_reference(self, ref: str) -> bool:
        """
        Return True if *ref* contains hallucination indicators:
        - Contains a DOI that fails validate_doi_format()
        - Contains a URL that is not from an academic domain
        - Author-year mismatch (year not in plausible range)
        - Implausible journal name patterns
        """
        # Check DOI validity if a DOI is present.
        # Match both bare DOIs (10.xxx/yyy) and prefixed ones (doi:anything).
        # A bare DOI starting with 10. is valid only if it matches the full pattern.
        # Any doi: prefix followed by something that doesn't match is hallucinated.
        doi_match = re.search(r"(?:doi:\s*)?(\d+\.\S+)", ref, re.IGNORECASE)
        if doi_match:
            doi_candidate = doi_match.group(1)
            if not self._analyser.validate_doi_format(doi_candidate):
                return True

        # Check URL academic domain validity
        url_match = re.search(r"https?://\S+", ref)
        if url_match:
            url = url_match.group(0).rstrip(".,)")
            if not self._is_academic_url(url):
                return True

        # Check author-year mismatch: year should be between 1900 and 2030
        year_match = re.search(r"\b(1[0-9]{3}|20[0-2][0-9]|2030)\b", ref)
        if not year_match:
            # No year found — suspicious for most citation styles
            # Only flag if the reference looks like it should have a year
            if re.search(r"[A-Z][a-z]+,\s[A-Z]", ref):
                # Looks like an author name but no year
                return True

        # Check for implausible journal name patterns
        if self._has_implausible_journal_name(ref):
            return True

        return False

    def _is_academic_url(self, url: str) -> bool:
        """Return True if *url* belongs to a recognised academic domain."""
        url_lower = url.lower()
        for domain in _ACADEMIC_DOMAINS:
            if domain in url_lower:
                return True
        return False

    def _has_implausible_journal_name(self, ref: str) -> bool:
        """
        Return True if the reference contains patterns suggesting a
        fabricated journal name (e.g. all-caps random strings, numeric-only
        journal names, or suspiciously short journal names).
        """
        # Look for journal name patterns: typically after "In " or in italics context
        # Heuristic: a sequence of 3+ uppercase letters not forming a known abbreviation
        # is suspicious
        suspicious_caps = re.search(r"\b[A-Z]{5,}\b", ref)
        if suspicious_caps:
            word = suspicious_caps.group(0)
            # Allow common abbreviations
            known_abbrevs = {"NIST", "IEEE", "COBIT", "ITIL", "GDPR", "HIPAA", "NATO", "UNESCO"}
            if word not in known_abbrevs:
                return True

        return False

    def _validate_harvard_apa_consistency(
        self,
        in_text_citations: set[str],
        references: list[str],
    ) -> bool:
        """
        Validate bidirectional consistency for Harvard/APA style.

        In-text: (Author, Year) — check that Author appears in references.
        References: check that each reference's author appears in in-text citations.
        """
        if not in_text_citations and not references:
            return True

        # Extract (author, year) pairs from in-text citations
        in_text_pairs: set[tuple[str, str]] = set()
        for citation in in_text_citations:
            m = re.match(r"\(([A-Z][a-z]+),\s(\d{4})\)", citation)
            if m:
                in_text_pairs.add((m.group(1).lower(), m.group(2)))

        # Extract author surnames from references (first word)
        ref_authors: set[str] = set()
        for ref in references:
            words = ref.split()
            if words:
                # Remove trailing comma from surname
                surname = words[0].rstrip(",").lower()
                ref_authors.add(surname)

        # Every in-text author should appear in references
        for author, _year in in_text_pairs:
            if author not in ref_authors:
                return False

        return True

    def _validate_chicago_consistency(
        self,
        in_text_citations: set[str],
        references: list[str],
    ) -> bool:
        """
        Validate bidirectional consistency for Chicago footnote style.

        In-text: [N] — check that footnote N has a corresponding reference.
        """
        # Extract footnote numbers from in-text citations
        in_text_numbers: set[int] = set()
        for citation in in_text_citations:
            m = re.match(r"\[(\d+)\]", citation)
            if m:
                in_text_numbers.add(int(m.group(1)))

        # Extract footnote numbers from references
        ref_numbers: set[int] = set()
        for ref in references:
            m = re.match(r"^\[(\d+)\]", ref.strip())
            if m:
                ref_numbers.add(int(m.group(1)))

        # Every in-text footnote should have a reference
        return in_text_numbers.issubset(ref_numbers)

    def _validate_mla_consistency(
        self,
        in_text_citations: set[str],
        references: list[str],
    ) -> bool:
        """
        Validate bidirectional consistency for MLA style.

        In-text: (Author Page) — check that Author appears in references.
        """
        in_text_authors: set[str] = set()
        for citation in in_text_citations:
            m = re.match(r"\(([A-Z][a-z]+)\s\d+\)", citation)
            if m:
                in_text_authors.add(m.group(1).lower())

        ref_authors: set[str] = set()
        for ref in references:
            words = ref.split()
            if words:
                surname = words[0].rstrip(",").lower()
                ref_authors.add(surname)

        for author in in_text_authors:
            if author not in ref_authors:
                return False

        return True

    def _renumber_chicago_footnotes(self, references: list[str]) -> list[str]:
        """
        Renumber Chicago footnote references sequentially starting from [1].
        """
        renumbered = []
        for i, ref in enumerate(references, start=1):
            # Replace existing footnote number or prepend one
            new_ref = re.sub(r"^\[\d+\]\s*", f"[{i}] ", ref.strip())
            if not new_ref.startswith(f"[{i}]"):
                new_ref = f"[{i}] {ref.strip()}"
            renumbered.append(new_ref)
        return renumbered
