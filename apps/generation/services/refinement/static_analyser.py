"""
StaticAnalyser: deterministic pure-Python text analysis utility.

Zero LLM calls. Used by all pipeline stages before deciding whether to
invoke an LLM. All methods use only Python standard library operations
(re, statistics, string manipulation).
"""
from __future__ import annotations

import re
import statistics


class StaticAnalyser:
    """
    Pure-Python utility class providing deterministic text analysis.
    Makes zero LLM calls from any method.
    """

    AI_SIGNATURE_PHRASES: list[str] = [
        "fundamentally",
        "it is worth noting",
        "it is important to note",
        "critical landscape",
        "multifaceted",
        "robust framework",
        "seamless integration",
        "in conclusion",
        "to summarise",
        "it is clear that",
        "it is evident that",
    ]

    MACHINE_CONFIDENCE_PHRASES: list[str] = [
        "it is undeniable that",
        "clearly",
        "obviously",
        "without doubt",
    ]

    # Transition words/phrases commonly used in academic writing
    _TRANSITION_WORDS: list[str] = [
        "however", "furthermore", "moreover", "therefore", "consequently",
        "additionally", "nevertheless", "nonetheless", "in contrast",
        "on the other hand", "as a result", "in addition", "for example",
        "for instance", "in particular", "specifically", "similarly",
        "likewise", "in summary", "in conclusion", "to summarise",
        "first", "second", "third", "finally", "subsequently",
        "meanwhile", "alternatively", "conversely", "thus", "hence",
        "accordingly", "subsequently", "previously", "initially",
    ]

    # Analytical verbs for frequency detection
    _ANALYTICAL_VERBS: list[str] = [
        "demonstrates", "highlights", "illustrates", "shows", "reveals",
        "suggests", "indicates", "argues", "contends", "asserts",
    ]

    # Hedging phrases for human realism scoring
    _HEDGE_PHRASES: list[str] = [
        "may", "might", "could", "perhaps", "possibly", "arguably",
        "it seems", "it appears", "it suggests", "tends to", "generally",
        "often", "sometimes", "in some cases", "to some extent",
        "relatively", "somewhat", "rather", "fairly", "appears to",
        "seems to", "likely", "unlikely", "probably", "presumably",
    ]

    # ------------------------------------------------------------------
    # Basic text metrics
    # ------------------------------------------------------------------

    def count_words(self, text: str) -> int:
        """Return the total word count of *text*."""
        if not text:
            return 0
        words = re.findall(r"\b\w+(?:[-\"]\w+)*\b", text.lower())
        return len(words)

    def paragraph_word_counts(self, text: str) -> list[int]:
        """
        Split *text* into paragraphs (double-newline separated) and return
        a list of word counts, one per paragraph.
        """
        paragraphs = re.split(r'\n\s*\n', text)
        counts = []
        for para in paragraphs:
            para = para.strip()
            if para:
                counts.append(len(para.split()))
        return counts if counts else [0]

    def paragraph_opening_words(self, text: str) -> list[str]:
        """
        Return the first word of each paragraph in *text*.
        Paragraphs are separated by one or more blank lines.
        """
        paragraphs = re.split(r'\n\s*\n', text)
        opening_words = []
        for para in paragraphs:
            para = para.strip()
            if para:
                words = para.split()
                if words:
                    opening_words.append(words[0])
        return opening_words

    def sentence_lengths(self, text: str) -> list[int]:
        """
        Tokenise *text* into sentences and return a list of word counts,
        one per sentence.
        """
        # Split on sentence-ending punctuation followed by whitespace or end of string
        sentences = re.split(r'[.!?]+(?:\s+|$)', text)
        lengths = []
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence:
                lengths.append(len(sentence.split()))
        return lengths if lengths else [0]

    # ------------------------------------------------------------------
    # AI-pattern detection
    # ------------------------------------------------------------------

    def detect_ai_signature_phrases(self, text: str) -> list[str]:
        """
        Return every phrase from *AI_SIGNATURE_PHRASES* that appears
        verbatim (case-insensitive) in *text*.
        """
        text_lower = text.lower()
        found = []
        for phrase in self.AI_SIGNATURE_PHRASES:
            if phrase.lower() in text_lower:
                found.append(phrase)
        return found

    def detect_machine_confidence_phrases(self, text: str) -> list[str]:
        """
        Return every phrase from *MACHINE_CONFIDENCE_PHRASES* that appears
        verbatim (case-insensitive) in *text*.
        """
        text_lower = text.lower()
        found = []
        for phrase in self.MACHINE_CONFIDENCE_PHRASES:
            if phrase.lower() in text_lower:
                found.append(phrase)
        return found

    def detect_transition_density(self, text: str) -> float:
        """
        Compute the ratio of transition words/phrases to total sentences.
        Returns a float in [0.0, 1.0].
        """
        sentences = re.split(r'[.!?]+(?:\s+|$)', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0.0

        transition_count = 0
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for transition in self._TRANSITION_WORDS:
                # Check if transition word appears at the start or within the sentence
                if re.search(r'\b' + re.escape(transition) + r'\b', sentence_lower):
                    transition_count += 1
                    break  # Count each sentence at most once

        return min(transition_count / len(sentences), 1.0)

    def detect_analytical_verb_frequency(
        self, text: str, window: int = 500
    ) -> dict[str, int]:
        """
        Count occurrences of common analytical verbs within each *window*-word
        sliding window of *text*.
        Returns a dict mapping verb → maximum count in any single window.
        """
        words = text.split()
        if not words:
            return {verb: 0 for verb in self._ANALYTICAL_VERBS}

        result: dict[str, int] = {verb: 0 for verb in self._ANALYTICAL_VERBS}

        # Slide a window of `window` words across the text
        step = max(1, window // 2)  # 50% overlap between windows
        for start in range(0, len(words), step):
            window_words = words[start:start + window]
            window_text_lower = ' '.join(window_words).lower()
            for verb in self._ANALYTICAL_VERBS:
                # Count whole-word occurrences of the verb in this window
                count = len(re.findall(r'\b' + re.escape(verb) + r'\b', window_text_lower))
                if count > result[verb]:
                    result[verb] = count

        return result

    def detect_repetitive_sentence_openings(self, text: str) -> float:
        """
        Compute the fraction of sentences that share their opening word with
        at least one other sentence in *text*.
        Returns a float in [0.0, 1.0].
        """
        sentences = re.split(r'[.!?]+(?:\s+|$)', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if not sentences:
            return 0.0

        opening_words = []
        for sentence in sentences:
            words = sentence.split()
            if words:
                opening_words.append(words[0].lower())

        if not opening_words:
            return 0.0

        # Count frequency of each opening word
        from collections import Counter
        freq = Counter(opening_words)

        # Count sentences whose opening word appears more than once
        repetitive_count = sum(1 for word in opening_words if freq[word] > 1)
        return repetitive_count / len(opening_words)

    def detect_paragraph_length_uniformity(self, text: str) -> float:
        """
        Measure how uniform paragraph lengths are.
        Returns the coefficient of variation (std / mean) of paragraph word
        counts; lower values indicate higher uniformity.
        Returns 0.0 when there is only one paragraph.
        """
        counts = self.paragraph_word_counts(text)
        if len(counts) <= 1:
            return 0.0

        mean = statistics.mean(counts)
        if mean == 0:
            return 0.0

        std = statistics.stdev(counts)
        return std / mean

    # ------------------------------------------------------------------
    # Citation / reference validation
    # ------------------------------------------------------------------

    def validate_doi_format(self, doi: str) -> bool:
        """
        Return True iff *doi* matches the pattern ``10\\.\\d{4,}/\\S+``.
        """
        pattern = r'10\.\d{4,}/\S+'
        return bool(re.search(pattern, doi))

    def validate_citation_format(self, citation: str, style: str) -> bool:
        """
        Return True iff *citation* conforms to the syntactic rules of *style*.

        Supported styles: 'Harvard', 'APA', 'Chicago', 'MLA'.
        - Harvard / APA : ``(Author, Year)``
        - Chicago       : footnote number ``[N]``
        - MLA           : ``(Author Page)``
        """
        style_upper = style.strip().upper()
        if style_upper in ('HARVARD', 'APA'):
            # Pattern: (Author, Year) e.g. (Smith, 2021)
            pattern = r'\([A-Z][a-z]+,\s\d{4}\)'
        elif style_upper == 'CHICAGO':
            # Pattern: [N] e.g. [1]
            pattern = r'\[\d+\]'
        elif style_upper == 'MLA':
            # Pattern: (Author Page) e.g. (Smith 42)
            pattern = r'\([A-Z][a-z]+\s\d+\)'
        else:
            return False

        return bool(re.search(pattern, citation))

    def validate_reference_list_order(
        self, references: list[str], style: str
    ) -> bool:
        """
        Return True iff *references* are in the correct order for *style*.

        - Harvard / APA : alphabetical by author surname
        - Chicago       : sequential footnote numbering
        - MLA           : alphabetical by author surname
        """
        if not references:
            return True

        style_upper = style.strip().upper()

        if style_upper in ('HARVARD', 'APA', 'MLA'):
            # Check alphabetical order by first word (author surname)
            first_words = [ref.split()[0].lower() if ref.split() else '' for ref in references]
            return first_words == sorted(first_words)

        elif style_upper == 'CHICAGO':
            # Check sequential numbering: [1], [2], [3], ...
            for i, ref in enumerate(references, start=1):
                match = re.match(r'^\[(\d+)\]', ref.strip())
                if not match or int(match.group(1)) != i:
                    return False
            return True

        return False

    # ------------------------------------------------------------------
    # Composite scores
    # ------------------------------------------------------------------

    def compute_ai_suspicion_score(self, text: str) -> float:
        """
        Return a float in [0.0, 100.0] representing how likely *text* was
        generated by an AI.

        Computed as a weighted combination of:
        - AI-signature phrase density
        - Machine-confidence phrase density
        - Transition density
        - Repetitive sentence opening rate
        - Paragraph length uniformity (inverted)
        """
        if not text.strip():
            return 0.0

        # 1. AI-signature phrase density: score based on number of phrases found
        ai_phrases = self.detect_ai_signature_phrases(text)
        # Normalise: 5+ phrases = max score
        ai_phrase_score = min(len(ai_phrases) / 5.0, 1.0) * 100.0

        # 2. Machine-confidence phrase density
        mc_phrases = self.detect_machine_confidence_phrases(text)
        # Normalise: 3+ phrases = max score
        mc_phrase_score = min(len(mc_phrases) / 3.0, 1.0) * 100.0

        # 3. Transition density (already in [0, 1])
        transition_score = self.detect_transition_density(text) * 100.0

        # 4. Repetitive sentence openings (already in [0, 1])
        repetitive_score = self.detect_repetitive_sentence_openings(text) * 100.0

        # 5. Paragraph length uniformity (inverted: low CV = high uniformity = more AI-like)
        # CV is typically in [0, ~2]; we invert so that low CV → high score
        cv = self.detect_paragraph_length_uniformity(text)
        # Map CV to [0, 1]: CV of 0 → uniformity score 1.0, CV of 1+ → uniformity score 0.0
        uniformity_score = max(0.0, 1.0 - cv) * 100.0

        # Weighted combination
        # Weights: ai_phrases=0.30, mc_phrases=0.20, transition=0.20, repetitive=0.15, uniformity=0.15
        score = (
            ai_phrase_score * 0.30
            + mc_phrase_score * 0.20
            + transition_score * 0.20
            + repetitive_score * 0.15
            + uniformity_score * 0.15
        )

        return float(max(0.0, min(100.0, score)))

    def compute_human_realism_score(self, text: str) -> float:
        """
        Return a float in [0.0, 100.0] representing how human-like *text*
        appears.

        Computed as a weighted combination of realism signals:
        - Hedged / qualified reasoning rate
        - Implicit (non-formulaic) transition ratio
        - Sentence length variation
        """
        if not text.strip():
            return 0.0

        # 1. Hedged reasoning rate
        sentences = re.split(r'[.!?]+(?:\s+|$)', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        total_sentences = len(sentences)

        if total_sentences == 0:
            return 0.0

        hedged_count = 0
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for hedge in self._HEDGE_PHRASES:
                if re.search(r'\b' + re.escape(hedge) + r'\b', sentence_lower):
                    hedged_count += 1
                    break  # Count each sentence at most once

        hedge_rate = hedged_count / total_sentences
        # Ideal hedge rate for human writing: ~30-50%; score peaks at 0.4
        # Map: 0 → 0, 0.4 → 100, 1.0 → 50 (too many hedges also looks odd)
        if hedge_rate <= 0.4:
            hedge_score = (hedge_rate / 0.4) * 100.0
        else:
            hedge_score = max(50.0, 100.0 - (hedge_rate - 0.4) * 100.0)

        # 2. Implicit transition ratio (non-formulaic transitions)
        # Formulaic transitions are the ones in _TRANSITION_WORDS
        # Implicit transitions = sentences that flow naturally without explicit markers
        transition_density = self.detect_transition_density(text)
        # Human writing has moderate transition density (~20-40%)
        # Very high transition density (>60%) is AI-like
        # Very low (<10%) can also be choppy
        if transition_density <= 0.3:
            implicit_score = (transition_density / 0.3) * 80.0 + 20.0
        elif transition_density <= 0.5:
            implicit_score = 100.0
        else:
            implicit_score = max(20.0, 100.0 - (transition_density - 0.5) * 160.0)

        # 3. Sentence length variation
        lengths = self.sentence_lengths(text)
        if len(lengths) <= 1:
            variation_score = 0.0
        else:
            mean_len = statistics.mean(lengths)
            if mean_len == 0:
                variation_score = 0.0
            else:
                std_len = statistics.stdev(lengths)
                cv = std_len / mean_len
                # Human writing typically has CV of 0.4-0.8 for sentence lengths
                # Map: CV=0 → 0, CV=0.6 → 100, CV=1.5+ → 60
                if cv <= 0.6:
                    variation_score = (cv / 0.6) * 100.0
                else:
                    variation_score = max(60.0, 100.0 - (cv - 0.6) * 40.0)

        # Weighted combination
        # Weights: hedge_rate=0.35, implicit_transition=0.30, sentence_variation=0.35
        score = (
            hedge_score * 0.35
            + implicit_score * 0.30
            + variation_score * 0.35
        )

        return float(max(0.0, min(100.0, score)))
