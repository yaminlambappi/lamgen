"""
Unit tests for StaticAnalyser.

Tests cover all 15 methods using only Python standard library operations.
Zero LLM calls from any method.
"""
import pytest
from generation.services.refinement.static_analyser import StaticAnalyser


@pytest.fixture
def analyser():
    return StaticAnalyser()


# ------------------------------------------------------------------
# Basic text metrics
# ------------------------------------------------------------------

class TestCountWords:
    def test_empty_string(self, analyser):
        assert analyser.count_words("") == 0

    def test_single_word(self, analyser):
        assert analyser.count_words("hello") == 1

    def test_multiple_words(self, analyser):
        assert analyser.count_words("the quick brown fox") == 4

    def test_extra_whitespace(self, analyser):
        assert analyser.count_words("  hello   world  ") == 2

    def test_newlines_count_as_whitespace(self, analyser):
        assert analyser.count_words("hello\nworld\nfoo") == 3


class TestParagraphWordCounts:
    def test_single_paragraph(self, analyser):
        text = "This is a single paragraph with seven words."
        counts = analyser.paragraph_word_counts(text)
        assert len(counts) == 1
        assert counts[0] == 8

    def test_two_paragraphs(self, analyser):
        text = "First paragraph here.\n\nSecond paragraph here."
        counts = analyser.paragraph_word_counts(text)
        assert len(counts) == 2

    def test_empty_string(self, analyser):
        counts = analyser.paragraph_word_counts("")
        # Should return [0] for empty text
        assert counts == [0]

    def test_multiple_blank_lines_between_paragraphs(self, analyser):
        text = "Para one.\n\n\nPara two."
        counts = analyser.paragraph_word_counts(text)
        assert len(counts) == 2


class TestParagraphOpeningWords:
    def test_single_paragraph(self, analyser):
        text = "Hello world this is a test."
        words = analyser.paragraph_opening_words(text)
        assert words == ["Hello"]

    def test_two_paragraphs(self, analyser):
        text = "First paragraph.\n\nSecond paragraph."
        words = analyser.paragraph_opening_words(text)
        assert words == ["First", "Second"]

    def test_empty_string(self, analyser):
        words = analyser.paragraph_opening_words("")
        assert words == []


class TestSentenceLengths:
    def test_single_sentence(self, analyser):
        lengths = analyser.sentence_lengths("This is a sentence.")
        assert len(lengths) >= 1
        assert lengths[0] == 4

    def test_multiple_sentences(self, analyser):
        text = "First sentence. Second sentence. Third sentence."
        lengths = analyser.sentence_lengths(text)
        assert len(lengths) >= 3

    def test_empty_string(self, analyser):
        lengths = analyser.sentence_lengths("")
        assert lengths == [0]

    def test_question_mark_splits(self, analyser):
        text = "Is this a question? Yes it is."
        lengths = analyser.sentence_lengths(text)
        assert len(lengths) >= 2


# ------------------------------------------------------------------
# AI-pattern detection
# ------------------------------------------------------------------

class TestDetectAiSignaturePhrases:
    def test_no_phrases(self, analyser):
        text = "This is a normal sentence without any AI phrases."
        result = analyser.detect_ai_signature_phrases(text)
        assert result == []

    def test_single_phrase(self, analyser):
        text = "It is worth noting that this is important."
        result = analyser.detect_ai_signature_phrases(text)
        assert "it is worth noting" in result

    def test_multiple_phrases(self, analyser):
        text = "Fundamentally, this is multifaceted. In conclusion, it is clear that we need a robust framework."
        result = analyser.detect_ai_signature_phrases(text)
        assert "fundamentally" in result
        assert "multifaceted" in result
        assert "in conclusion" in result
        assert "it is clear that" in result
        assert "robust framework" in result

    def test_case_insensitive(self, analyser):
        text = "FUNDAMENTALLY this is important. IT IS WORTH NOTING the details."
        result = analyser.detect_ai_signature_phrases(text)
        assert "fundamentally" in result
        assert "it is worth noting" in result

    def test_all_phrases_detected(self, analyser):
        text = " ".join(StaticAnalyser.AI_SIGNATURE_PHRASES)
        result = analyser.detect_ai_signature_phrases(text)
        assert len(result) == len(StaticAnalyser.AI_SIGNATURE_PHRASES)

    def test_returns_list(self, analyser):
        result = analyser.detect_ai_signature_phrases("some text")
        assert isinstance(result, list)


class TestDetectMachineConfidencePhrases:
    def test_no_phrases(self, analyser):
        text = "This is a normal sentence."
        result = analyser.detect_machine_confidence_phrases(text)
        assert result == []

    def test_single_phrase(self, analyser):
        text = "It is undeniable that this is true."
        result = analyser.detect_machine_confidence_phrases(text)
        assert "it is undeniable that" in result

    def test_multiple_phrases(self, analyser):
        text = "Clearly, this is obvious. Without doubt, it is undeniable that we are right."
        result = analyser.detect_machine_confidence_phrases(text)
        assert "clearly" in result
        assert "obviously" not in result  # not in this text
        assert "without doubt" in result
        assert "it is undeniable that" in result

    def test_case_insensitive(self, analyser):
        text = "CLEARLY this is OBVIOUSLY true."
        result = analyser.detect_machine_confidence_phrases(text)
        assert "clearly" in result
        assert "obviously" in result

    def test_all_phrases_detected(self, analyser):
        text = " ".join(StaticAnalyser.MACHINE_CONFIDENCE_PHRASES)
        result = analyser.detect_machine_confidence_phrases(text)
        assert len(result) == len(StaticAnalyser.MACHINE_CONFIDENCE_PHRASES)


class TestDetectTransitionDensity:
    def test_empty_text(self, analyser):
        assert analyser.detect_transition_density("") == 0.0

    def test_no_transitions(self, analyser):
        text = "The cat sat on the mat. The dog ran away. The bird flew high."
        density = analyser.detect_transition_density(text)
        assert 0.0 <= density <= 1.0

    def test_high_transition_density(self, analyser):
        text = (
            "However, this is important. Furthermore, we must consider this. "
            "Moreover, the evidence shows. Therefore, we conclude. "
            "Additionally, there is more evidence."
        )
        density = analyser.detect_transition_density(text)
        assert density > 0.5

    def test_returns_float_in_range(self, analyser):
        text = "Some text here. More text there. Final text."
        density = analyser.detect_transition_density(text)
        assert isinstance(density, float)
        assert 0.0 <= density <= 1.0


class TestDetectAnalyticalVerbFrequency:
    def test_empty_text(self, analyser):
        result = analyser.detect_analytical_verb_frequency("")
        assert isinstance(result, dict)
        assert all(v == 0 for v in result.values())

    def test_single_verb(self, analyser):
        text = "This demonstrates the point. It also demonstrates the concept."
        result = analyser.detect_analytical_verb_frequency(text)
        assert result["demonstrates"] >= 1

    def test_returns_all_verbs(self, analyser):
        result = analyser.detect_analytical_verb_frequency("some text")
        expected_verbs = {
            "demonstrates", "highlights", "illustrates", "shows", "reveals",
            "suggests", "indicates", "argues", "contends", "asserts",
        }
        assert set(result.keys()) == expected_verbs

    def test_max_in_window(self, analyser):
        # Create text where a verb appears many times in a small window
        text = "This shows the point. " * 10
        result = analyser.detect_analytical_verb_frequency(text, window=500)
        assert result["shows"] >= 5

    def test_returns_dict_of_ints(self, analyser):
        result = analyser.detect_analytical_verb_frequency("text here")
        assert isinstance(result, dict)
        assert all(isinstance(v, int) for v in result.values())


class TestDetectRepetitiveSentenceOpenings:
    def test_empty_text(self, analyser):
        assert analyser.detect_repetitive_sentence_openings("") == 0.0

    def test_no_repetition(self, analyser):
        text = "The cat sat. A dog ran. Some birds flew. Many fish swam."
        rate = analyser.detect_repetitive_sentence_openings(text)
        assert 0.0 <= rate <= 1.0

    def test_all_same_opening(self, analyser):
        text = "The cat sat. The dog ran. The bird flew. The fish swam."
        rate = analyser.detect_repetitive_sentence_openings(text)
        assert rate == 1.0

    def test_half_repetitive(self, analyser):
        text = "The cat sat. The dog ran. A bird flew. Some fish swam."
        rate = analyser.detect_repetitive_sentence_openings(text)
        # "The" appears twice out of 4 sentences = 0.5
        assert rate == 0.5

    def test_returns_float_in_range(self, analyser):
        text = "Some text here. More text there."
        rate = analyser.detect_repetitive_sentence_openings(text)
        assert isinstance(rate, float)
        assert 0.0 <= rate <= 1.0


class TestDetectParagraphLengthUniformity:
    def test_single_paragraph(self, analyser):
        text = "This is a single paragraph."
        cv = analyser.detect_paragraph_length_uniformity(text)
        assert cv == 0.0

    def test_uniform_paragraphs(self, analyser):
        # Two paragraphs with same word count
        text = "one two three four five.\n\none two three four five."
        cv = analyser.detect_paragraph_length_uniformity(text)
        assert cv == 0.0

    def test_varied_paragraphs(self, analyser):
        # Very different paragraph lengths
        text = "one.\n\none two three four five six seven eight nine ten."
        cv = analyser.detect_paragraph_length_uniformity(text)
        assert cv > 0.0

    def test_returns_float(self, analyser):
        text = "Para one.\n\nPara two with more words here."
        cv = analyser.detect_paragraph_length_uniformity(text)
        assert isinstance(cv, float)
        assert cv >= 0.0


# ------------------------------------------------------------------
# Citation / reference validation
# ------------------------------------------------------------------

class TestValidateDoiFormat:
    def test_valid_doi(self, analyser):
        assert analyser.validate_doi_format("10.1234/some-article") is True

    def test_valid_doi_long_registrant(self, analyser):
        assert analyser.validate_doi_format("10.12345/journal.article.2021") is True

    def test_invalid_doi_wrong_prefix(self, analyser):
        assert analyser.validate_doi_format("11.1234/article") is False

    def test_invalid_doi_too_short_registrant(self, analyser):
        assert analyser.validate_doi_format("10.123/article") is False

    def test_invalid_doi_no_suffix(self, analyser):
        assert analyser.validate_doi_format("10.1234/") is False

    def test_doi_embedded_in_text(self, analyser):
        # The regex uses search, so it should find DOI in text
        assert analyser.validate_doi_format("See doi: 10.1234/article for details") is True

    def test_empty_string(self, analyser):
        assert analyser.validate_doi_format("") is False


class TestValidateCitationFormat:
    def test_harvard_valid(self, analyser):
        assert analyser.validate_citation_format("(Smith, 2021)", "Harvard") is True

    def test_apa_valid(self, analyser):
        assert analyser.validate_citation_format("(Jones, 2019)", "APA") is True

    def test_chicago_valid(self, analyser):
        assert analyser.validate_citation_format("[1]", "Chicago") is True

    def test_chicago_multi_digit(self, analyser):
        assert analyser.validate_citation_format("[42]", "Chicago") is True

    def test_mla_valid(self, analyser):
        assert analyser.validate_citation_format("(Brown 45)", "MLA") is True

    def test_harvard_invalid_format(self, analyser):
        assert analyser.validate_citation_format("Smith 2021", "Harvard") is False

    def test_chicago_invalid_format(self, analyser):
        assert analyser.validate_citation_format("(Smith, 2021)", "Chicago") is False

    def test_mla_invalid_format(self, analyser):
        assert analyser.validate_citation_format("(Smith, 2021)", "MLA") is False

    def test_unknown_style(self, analyser):
        assert analyser.validate_citation_format("(Smith, 2021)", "Vancouver") is False

    def test_case_insensitive_style(self, analyser):
        assert analyser.validate_citation_format("(Smith, 2021)", "harvard") is True
        assert analyser.validate_citation_format("[5]", "chicago") is True


class TestValidateReferenceListOrder:
    def test_empty_list(self, analyser):
        assert analyser.validate_reference_list_order([], "Harvard") is True

    def test_harvard_alphabetical_correct(self, analyser):
        refs = ["Adams, J. (2020).", "Brown, K. (2019).", "Carter, L. (2021)."]
        assert analyser.validate_reference_list_order(refs, "Harvard") is True

    def test_harvard_alphabetical_incorrect(self, analyser):
        refs = ["Brown, K. (2019).", "Adams, J. (2020).", "Carter, L. (2021)."]
        assert analyser.validate_reference_list_order(refs, "Harvard") is False

    def test_apa_alphabetical_correct(self, analyser):
        refs = ["Anderson, T. (2018).", "Brown, S. (2020)."]
        assert analyser.validate_reference_list_order(refs, "APA") is True

    def test_chicago_sequential_correct(self, analyser):
        refs = ["[1] First reference.", "[2] Second reference.", "[3] Third reference."]
        assert analyser.validate_reference_list_order(refs, "Chicago") is True

    def test_chicago_sequential_incorrect(self, analyser):
        refs = ["[1] First reference.", "[3] Third reference.", "[2] Second reference."]
        assert analyser.validate_reference_list_order(refs, "Chicago") is False

    def test_chicago_missing_number(self, analyser):
        refs = ["First reference.", "Second reference."]
        assert analyser.validate_reference_list_order(refs, "Chicago") is False

    def test_mla_alphabetical_correct(self, analyser):
        refs = ["Adams, J. Work Title.", "Brown, K. Another Work."]
        assert analyser.validate_reference_list_order(refs, "MLA") is True

    def test_single_reference(self, analyser):
        refs = ["Smith, J. (2020)."]
        assert analyser.validate_reference_list_order(refs, "Harvard") is True


# ------------------------------------------------------------------
# Composite scores
# ------------------------------------------------------------------

class TestComputeAiSuspicionScore:
    def test_empty_text(self, analyser):
        score = analyser.compute_ai_suspicion_score("")
        assert score == 0.0

    def test_returns_float_in_range(self, analyser):
        text = "This is some normal text about academic topics."
        score = analyser.compute_ai_suspicion_score(text)
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_high_ai_text_scores_higher(self, analyser):
        ai_text = (
            "Fundamentally, it is worth noting that this multifaceted issue requires "
            "a robust framework for seamless integration. It is important to note that "
            "in conclusion, it is clear that it is evident that we need to summarise. "
            "However, furthermore, moreover, therefore, consequently, additionally."
        )
        human_text = "I went to the store. The weather was nice. My friend called me."
        ai_score = analyser.compute_ai_suspicion_score(ai_text)
        human_score = analyser.compute_ai_suspicion_score(human_text)
        assert ai_score > human_score

    def test_score_clamped_to_100(self, analyser):
        # Even with extreme AI text, score should not exceed 100
        ai_text = " ".join(StaticAnalyser.AI_SIGNATURE_PHRASES * 5)
        score = analyser.compute_ai_suspicion_score(ai_text)
        assert score <= 100.0

    def test_score_not_negative(self, analyser):
        text = "Some text here."
        score = analyser.compute_ai_suspicion_score(text)
        assert score >= 0.0


class TestComputeHumanRealismScore:
    def test_empty_text(self, analyser):
        score = analyser.compute_human_realism_score("")
        assert score == 0.0

    def test_returns_float_in_range(self, analyser):
        text = "This is some normal text about academic topics."
        score = analyser.compute_human_realism_score(text)
        assert isinstance(score, float)
        assert 0.0 <= score <= 100.0

    def test_hedged_text_scores_higher(self, analyser):
        hedged_text = (
            "This may suggest that the approach could be effective. "
            "It seems that perhaps the results might indicate a trend. "
            "Arguably, this possibly demonstrates a pattern. "
            "The evidence tends to suggest that outcomes are likely positive."
        )
        unhedged_text = (
            "This is the correct approach. The results are definitive. "
            "The evidence proves the point. The conclusion is absolute."
        )
        hedged_score = analyser.compute_human_realism_score(hedged_text)
        unhedged_score = analyser.compute_human_realism_score(unhedged_text)
        assert hedged_score > unhedged_score

    def test_score_clamped_to_100(self, analyser):
        text = "This may suggest that perhaps it could be possible. " * 10
        score = analyser.compute_human_realism_score(text)
        assert score <= 100.0

    def test_score_not_negative(self, analyser):
        text = "Some text here."
        score = analyser.compute_human_realism_score(text)
        assert score >= 0.0

    def test_varied_sentence_lengths_help_realism(self, analyser):
        # Text with varied sentence lengths should score higher than uniform
        varied_text = (
            "Short sentence. "
            "This is a much longer sentence that contains many more words and provides more detail about the topic at hand. "
            "Medium length here. "
            "Another very long sentence that goes on and on with lots of detail and explanation about various aspects of the subject matter being discussed. "
            "Brief. "
        )
        uniform_text = (
            "This has five words. "
            "This has five words. "
            "This has five words. "
            "This has five words. "
            "This has five words. "
        )
        varied_score = analyser.compute_human_realism_score(varied_text)
        uniform_score = analyser.compute_human_realism_score(uniform_text)
        assert varied_score > uniform_score


# ------------------------------------------------------------------
# Integration / edge cases
# ------------------------------------------------------------------

class TestEdgeCases:
    def test_whitespace_only_text(self, analyser):
        text = "   \n\n   "
        assert analyser.count_words(text) == 0
        assert analyser.detect_ai_signature_phrases(text) == []
        assert analyser.detect_machine_confidence_phrases(text) == []

    def test_single_word_text(self, analyser):
        text = "Hello"
        assert analyser.count_words(text) == 1
        assert analyser.detect_transition_density(text) == 0.0

    def test_phrase_at_start_of_text(self, analyser):
        text = "Fundamentally, this is the core argument."
        result = analyser.detect_ai_signature_phrases(text)
        assert "fundamentally" in result

    def test_phrase_at_end_of_text(self, analyser):
        text = "This argument is multifaceted"
        result = analyser.detect_ai_signature_phrases(text)
        assert "multifaceted" in result

    def test_doi_with_various_suffixes(self, analyser):
        valid_dois = [
            "10.1000/xyz123",
            "10.1038/nature12345",
            "10.1016/j.cell.2021.01.001",
        ]
        for doi in valid_dois:
            assert analyser.validate_doi_format(doi) is True

    def test_class_level_constants_exist(self, analyser):
        assert hasattr(StaticAnalyser, 'AI_SIGNATURE_PHRASES')
        assert hasattr(StaticAnalyser, 'MACHINE_CONFIDENCE_PHRASES')
        assert isinstance(StaticAnalyser.AI_SIGNATURE_PHRASES, list)
        assert isinstance(StaticAnalyser.MACHINE_CONFIDENCE_PHRASES, list)
        assert len(StaticAnalyser.AI_SIGNATURE_PHRASES) == 11
        assert len(StaticAnalyser.MACHINE_CONFIDENCE_PHRASES) == 4
