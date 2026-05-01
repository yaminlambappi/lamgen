# Implementation Plan: Academic Refinement Pipeline

## Overview

Implement the post-generation refinement pipeline as service classes under `generation/services/refinement/`, a new `run_refinement_pipeline` Celery task, the `RefinementResult` Django model, and all required model/field extensions. The architecture uses a `StaticAnalyser` for deterministic pure-Python analysis, an `AnalysisCache` for result caching, a `ReflectionGenerator` for reflection sections, and a `UnifiedRefinementEngine` that merges humanization, realism, and AI-defense into a single pass. Each task builds incrementally on the previous, ending with full pipeline wiring.

## Tasks

- [x] 1. Data model extensions and migrations
  - Add `REFINING` and `REFINEMENT_COMPLETE` to `GenerationJob.Status` choices in `generation/models.py`
  - Add `refinement_version = models.IntegerField(default=0)` and `ai_suspicion_score = models.FloatField(null=True, blank=True)` to `GeneratedSection`
  - Add `esl_context = models.BooleanField(default=False)` to `AssignmentBrief`
  - Extend `AssignmentBrief.AssignmentType` with: `REFLECTION`, `CRITIQUE`, `RESEARCH_PAPER`, `POLICY_ANALYSIS`, `TECHNICAL_DOCUMENTATION`, `BUSINESS_REPORT`, `DISSERTATION`, `PRESENTATION`, `MIXED_FORMAT`
  - Create `RefinementResult` model with all fields from the design: `job` (OneToOneField), `submission_readiness_score`, `ai_suspicion_score`, `human_realism_score`, `rubric_coverage_score`, `citation_completeness_score`, `word_count_compliant`, `auto_refinement_triggered`, `refinement_passes_log` (JSONField), `created_at`, `updated_at`
  - Add cost optimisation fields to `RefinementResult`: `export_generated = models.BooleanField(default=False)`, `total_refinement_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)`, `cost_breakdown = models.JSONField(default=dict)`, `cache_hit_count = models.IntegerField(default=0)`, `llm_calls_count = models.IntegerField(default=0)`, `static_analysis_calls_count = models.IntegerField(default=0)`, `skipped_stages = models.JSONField(default=list)`
  - Register `RefinementResult` in `generation/admin.py` with `list_filter` on `submission_readiness_score`, `ai_suspicion_score`, `auto_refinement_triggered`
  - Add cost constants to `config/settings.py`: `HAIKU_COST_PER_1K_INPUT = 0.00025`, `HAIKU_COST_PER_1K_OUTPUT = 0.00125`, `SONNET_COST_PER_1K_INPUT = 0.003`, `SONNET_COST_PER_1K_OUTPUT = 0.015`, `OPUS_COST_PER_1K_INPUT = 0.015`, `OPUS_COST_PER_1K_OUTPUT = 0.075`
  - Generate and apply migration
  - _Requirements: 10.4, 11.1, 11.2, 12.2, 20.1, 20.2_

- [x] 2. Extend `ClaudeService` with `model_override`
  - [x] 2.1 Add `model_override: str | None = None` parameter to `ClaudeService.call()` in `generation/services/claude_service.py`
    - Add `_MODEL_ALIASES = {'haiku': 'claude-haiku-4-5', 'sonnet': 'claude-sonnet-4-5', 'opus': 'claude-opus-4-5'}` constant
    - When `model_override` is provided, resolve it via `_MODEL_ALIASES` (case-insensitive) and use it instead of `settings.CLAUDE_MODEL`
    - Log the resolved model name in the existing structured log line
    - _Requirements: 9.4_

- [x] 3. Extend `GenerationPipelineOrchestrator` with refinement stage weights
  - Update `STAGE_WEIGHTS` in `generation/services/orchestrator.py` to replace the placeholder entries with the design-specified values for the consolidated pipeline: `requirement_validation` → 65, `citation_validation` → 72, `unified_refinement` → 80, `structure_quality` → 87, `submission_validation` → 93, `auto_refinement` → 97, `export_formatting` → 100
  - Remove the old placeholder keys (`academic_reviewer_pass`, `coherence_pass`, `humanization_pass`, `ai_detection_defense`, `realism_pass`) that are superseded by the consolidated architecture
  - _Requirements: 10.2, 10.3_

- [x] 4. Create refinement service package scaffold
  - Create `generation/services/refinement/__init__.py`
  - Create stub files for all services and the pipeline runner: `static_analyser.py`, `analysis_cache.py`, `reflection_generator.py`, `unified_refinement_engine.py`, `citation_engine.py`, `requirement_validator.py`, `structure_quality_system.py`, `submission_validator.py`, `document_authenticity.py`, `pipeline_runner.py`
  - Each stub defines the class and method signatures matching the design interfaces, with `raise NotImplementedError` bodies
  - _Requirements: 10.1_

- [x] 5. Implement `StaticAnalyser`
  - [x] 5.1 Implement `StaticAnalyser` in `generation/services/refinement/static_analyser.py`
    - Define `AI_SIGNATURE_PHRASES` list: `["fundamentally", "it is worth noting", "it is important to note", "critical landscape", "multifaceted", "robust framework", "seamless integration", "in conclusion", "to summarise", "it is clear that", "it is evident that"]`
    - Define `MACHINE_CONFIDENCE_PHRASES` list: `["it is undeniable that", "clearly", "obviously", "without doubt"]`
    - Implement all 15 methods using only Python standard library (`re`, `statistics`, string operations): `count_words`, `paragraph_word_counts`, `paragraph_opening_words`, `sentence_lengths`, `detect_ai_signature_phrases`, `detect_machine_confidence_phrases`, `detect_transition_density`, `detect_analytical_verb_frequency`, `detect_repetitive_sentence_openings`, `detect_paragraph_length_uniformity`, `validate_doi_format`, `validate_citation_format`, `validate_reference_list_order`, `compute_ai_suspicion_score`, `compute_human_realism_score`
    - `validate_doi_format`: regex `10\.\d{4,}/\S+`
    - `compute_ai_suspicion_score`: weighted combination of `detect_ai_signature_phrases`, `detect_machine_confidence_phrases`, `detect_transition_density`, `detect_repetitive_sentence_openings`, `detect_paragraph_length_uniformity`; returns float in [0, 100]
    - `compute_human_realism_score`: weighted combination of realism signals (hedged reasoning rate, implicit transition ratio, sentence length variation); returns float in [0, 100]
    - Zero LLM calls from any method
    - _Requirements: 13.1–13.6_

  - [x] 5.2 Write property test for StaticAnalyser AI-signature detection
    - **Property 25: StaticAnalyser AI-signature detection matches LLM detection**
    - **Validates: Requirements 13.2, 13.3**
    - Use `@given(text_with_ai_phrases())` strategy generating text with random subsets of `AI_SIGNATURE_PHRASES`; assert `StaticAnalyser().detect_ai_signature_phrases(text)` returns every phrase that is present verbatim in the text

  - [x] 5.3 Write property test for threshold skipping correctness
    - **Property 27: Threshold skipping correctness**
    - **Validates: Requirements 15.1**
    - Use `@given(text_with_low_ai_suspicion())` strategy generating text that `StaticAnalyser().compute_ai_suspicion_score()` scores below 45; mock `ClaudeService.call` and assert it is never invoked when `UnifiedRefinementEngine` processes such a section

- [x] 6. Implement `AnalysisCache`
  - [x] 6.1 Implement `AnalysisCache` in `generation/services/refinement/analysis_cache.py`
    - Use `django.core.cache.cache` as the backing store
    - Implement `_make_key(job_id, content, analysis_type)`: returns `f"refinement:{job_id}:{hashlib.md5(content.encode()).hexdigest()[:16]}:{analysis_type}"`
    - Implement `get_or_compute(key, compute_fn, ttl=3600)`: on cache hit, log DEBUG and return cached value; on cache miss, call `compute_fn()`, store with TTL, return result
    - _Requirements: 18.1–18.8_

  - [x] 6.2 Write property test for cache hit returns identical result
    - **Property 28: Cache hit returns identical result**
    - **Validates: Requirements 18.4, 18.8**
    - Use `@given(st.text(min_size=1), st.text(min_size=1), st.text(min_size=1))` for `job_id`, `content`, `analysis_type`; call `get_or_compute` twice with the same key and a counter-incrementing `compute_fn`; assert the second call returns the same result and `compute_fn` was called exactly once

- [x] 7. Implement `ReflectionGenerator`
  - [x] 7.1 Implement `ReflectionGenerator.process()` in `generation/services/refinement/reflection_generator.py`
    - Filter input sections to only those with `section_type == 'reflection'` (or equivalent reflection indicator)
    - Build a realism-first prompt that includes: natural uncertainty markers ("I found that", "this challenged my assumption that", "I was not entirely sure"), personal reasoning moments at ≥1 per 200 words, controlled inconsistency, reduced philosophical tone
    - Use `model_override='sonnet'` exclusively — never Opus
    - Single LLM call per reflection section
    - Increment `section.refinement_version` and save after processing
    - _Requirements: 17.1–17.7_

  - [x] 7.2 Write property test for reflection sections skip UnifiedRefinementEngine
    - **Property 31: Reflection sections skip UnifiedRefinementEngine**
    - **Validates: Requirements 17.5, 17.6**
    - Use `@given(section_with_reflection_type())` strategy generating `GeneratedSection` objects with `section_type='reflection'`; mock `UnifiedRefinementEngine.process` and assert it is never called for reflection sections when `RefinementPipelineRunner.run()` executes

- [ ] 8. Implement `UnifiedRefinementEngine`
  - [x] 8.1 Implement `UnifiedRefinementEngine.process()` in `generation/services/refinement/unified_refinement_engine.py`
    - For each non-reflection section:
      1. Call `StaticAnalyser` to detect all issues: AI-signature phrases, machine-confidence phrases, transition density, analytical verb frequency, repetitive openings, paragraph length uniformity
      2. Call `StaticAnalyser.compute_ai_suspicion_score()` and `compute_human_realism_score()`
      3. Apply threshold checks: if `ai_suspicion < 45`, skip all LLM calls and log stage to `skipped_stages`; if `realism_score > 80`, skip realism enhancement
      4. If rewriting needed and `ai_suspicion <= 75`: perform fragment-level rewriting — extract only risky fragments, build diff-based prompt, single Sonnet call
      5. If `ai_suspicion > 75` or structural failure or rubric failure or hallucination detected: perform full section rewrite with Sonnet
      6. If Sonnet pass still scores > 75: second pass with Opus
      7. Simultaneously apply humanization + realism + AI pattern reduction in the single LLM call
    - Implement `_build_diff_prompt(section_content, issues_list, fragments)`: returns constrained editing prompt with explicit issues list, preserve instructions, and specific fragment references; never uses open-ended "rewrite naturally" instructions
    - Context window: pass only the section(s) needed, not the full assignment; for fragment-level, pass only risky fragments
    - Increment `section.refinement_version` and save after each rewrite
    - Log skipped stages to `RefinementResult.skipped_stages`
    - _Requirements: 1.1–1.10, 2.1–2.7, 5.1–5.7, 14.1–14.9, 15.1, 15.3, 16.1–16.10, 19.1–19.6_

  - [x] 8.2 Write property test for AI-signature phrase elimination
    - **Property 1: AI-signature phrase elimination**
    - **Validates: Requirements 1.3**
    - Use `@given(text_with_ai_phrases())` strategy; after `UnifiedRefinementEngine` processes the section, assert none of `AI_SIGNATURE_PHRASES` remain in the output

  - [x] 8.3 Write property test for paragraph opening diversity
    - **Property 2: Paragraph opening diversity**
    - **Validates: Requirements 1.8**
    - Use `@given(section_with_uniform_openings())` strategy; after processing, assert no single opening word/phrase exceeds 20% of paragraph count

  - [x] 8.4 Write property test for paragraph length standard deviation
    - **Property 3: Paragraph length standard deviation**
    - **Validates: Requirements 1.9**
    - Use `@given(section_with_uniform_paragraphs())` strategy (≥3 paragraphs, all same length); after processing, assert `stdev(word_counts) >= 40`

  - [x] 8.5 Write property test for reflective tone first-person rate
    - **Property 4: Reflective tone first-person rate**
  s    - Use `@given(st.text(min_size=200))` with `writing_tone='reflective'`; after processing, assert at least `len(content) // 200` first-person markers present

  - [x] 8.6 Write property test for AI suspicion score range
    - **Property 5: AI suspicion score is always produced and in range**
    - **Validates: Requirements 2.4**
    - Use `@given(st.text(min_size=50))` as section content; assert `StaticAnalyser().compute_ai_suspicion_score(text)` is `isinstance(score, float)` and `0.0 <= score <= 100.0`

  - [x] 8.7 Write property test for word count preservation through rewriting
    - **Property 6: Word count preservation through rewriting**
    - **Validates: Requirements 2.7, 14.8**
    - Use `@given(st.text(min_size=100))` as original content; after rewrite, assert `abs(new_word_count - original_word_count) / original_word_count <= 0.10`

  - [x] 8.8 Write property test for fragment rewriting preserves non-risky content
    - **Property 26: Fragment rewriting preserves non-risky content**
    - **Validates: Requirements 14.9**
    - Use `@given(section_with_mixed_risk_paragraphs())` strategy generating sections where some paragraphs contain AI-signature phrases and others do not; after `UnifiedRefinementEngine` fragment-level rewriting (score ≤ 75), assert non-risky paragraphs are byte-identical to originals

  - [x] 8.9 Write property test for diff-based prompt contains issues list
    - **Property 29: Diff-based prompt contains issues list**
    - **Validates: Requirements 19.1, 19.3, 19.4**
    - Use `@given(st.lists(st.text(min_size=1), min_size=1), st.lists(st.text(min_size=1), min_size=1))` for `issues_list` and `fragments`; assert `_build_diff_prompt()` output contains the issues list, the preserve instructions block, and the fragment references

  - [x] 8.10 Write property test for skipped stages logged
    - **Property 32: Skipped stages logged**
    - **Validates: Requirements 15.6, 15.7**
    - Use `@given(st.floats(min_value=0.0, max_value=44.9))` as AI suspicion score; after `UnifiedRefinementEngine` processes a section with that score, assert the relevant stage name appears in `RefinementResult.skipped_stages`

  - [x] 8.11 Write property test for hedged reasoning rate
    - **Property 16: Hedged reasoning rate in analytical sections**
    - **Validates: Requirements 5.1**
    - Use `@given(st.text(min_size=300))` as analytical section content; after processing, assert at least `len(content.split()) // 300` hedged reasoning instances present

  - [x] 8.12 Write property test for machine-confidence phrase elimination
    - **Property 17: Machine-confidence phrase elimination**
    - **Validates: Requirements 5.4**
    - Use `@given(text_with_machine_confidence_phrases())` strategy; after processing, assert none of `MACHINE_CONFIDENCE_PHRASES` remain in output

  - [x] 8.13 Write property test for analytical verb repetition limit
    - **Property 18: Analytical verb repetition limit** A12
    - **Validates: Requirements 5.5**
    - Use `@given(st.text(min_size=500))` with injected repeated analytical verbs; after processing, assert no single analytical verb appears > 3 times in any 500-word window

- [x] 9. Implement `CitationEngine`
  - [x] 9.1 Implement `CitationEngine.process()` in `generation/services/refinement/citation_engine.py`
    - Use `StaticAnalyser.validate_doi_format()` and `StaticAnalyser.validate_citation_format()` for format validation (zero LLM calls for format checking)
    - Apply threshold skip: if `citation_completeness > 92`, skip citation insertion pass and log to `skipped_stages`; proceed to reference list validation only
    - Define `SUPPORTED_STYLES = {'Harvard', 'APA', 'Chicago', 'MLA'}` and citation format regex patterns per style: Harvard/APA `\([A-Z][a-z]+,\s\d{4}\)`, Chicago footnote `\[\d+\]`, MLA `\([A-Z][a-z]+\s\d+\)`
    - Implement `_detect_uncited_claims(section, job)`: use `model_override='haiku'` to identify factual/analytical claims lacking in-text citations
    - Implement `_insert_citations(section, brief, job)`: use `model_override='sonnet'` to format and insert citations per active `citation_style`
    - Implement `_validate_reference_list(content, citation_style)`: check bidirectional consistency
    - Implement `_detect_hallucinations(references)`: use `StaticAnalyser.validate_doi_format()` for DOI checks; check journal name patterns, author-year mismatches, URL academic domain validation; replace hallucinated citations with flagged placeholders
    - Implement `_sort_reference_list(content, citation_style)`: use `StaticAnalyser.validate_reference_list_order()` for alphabetical check; sort for Harvard/APA; validate sequential footnote numbering for Chicago
    - Compute `citation_completeness_score = (valid_citations / total_claims) * 100`
    - Context window: receive only citation-relevant chunks (section content + reference list), not full assignment
    - _Requirements: 3.1–3.10, 15.2_

  - [x] 9.2 Write property test for citation format compliance
    - **Property 7: Citation format compliance**
    - **Validates: Requirements 3.1, 3.3**
    - Use `@given(st.sampled_from(['Harvard', 'APA', 'Chicago', 'MLA']), st.text())` to generate citation style and content; assert inserted citations match the expected regex pattern for that style

  - [x] 9.3 Write property test for bidirectional citation consistency
    - **Property 8: Bidirectional citation consistency**
    - **Validates: Requirements 3.4**
    - Use `@given(citation_document())` strategy; after processing, assert every in-text citation has a reference entry and every reference entry has at least one in-text citation

  - [x] 9.4 Write property test for hallucination detection completeness
    - **Property 9: Hallucination detection completeness**
    - **Validates: Requirements 3.5**
    - Use `@given(reference_with_hallucination_indicators())` strategy; assert `_detect_hallucinations()` flags every reference with malformed DOIs, bad URLs, or author-year mismatches

  - [x] 9.5 Write property test for citation completeness score accuracy
    - **Property 10: Citation completeness score reflects actual coverage**
    - **Validates: Requirements 3.7**
    - Use `@given(st.integers(1, 50), st.integers(0, 50))` for `total_claims` and `valid_citations` (clamped to ≤ total_claims); assert `score == (valid_citations / total_claims) * 100` within ±1 point

  - [x] 9.6 Write property test for Harvard/APA alphabetical reference list
    - **Property 11: Harvard/APA reference list alphabetical order**
    - **Validates: Requirements 3.8**
    - Use `@given(st.lists(st.text(min_size=1), min_size=2))` as author surnames; after `_sort_reference_list()`, assert entries are in alphabetical order by surname

- [ ] 10. Implement `RequirementValidator`
  - [ ] 10.1 Implement `RequirementValidator.process()` in `generation/services/refinement/requirement_validator.py`
    - Apply threshold skip: if `rubric_coverage > 90`, skip requirement regeneration and log to `skipped_stages`; proceed to validation report only
    - Implement `_compute_rubric_coverage(sections, rubric)`: use `model_override='haiku'` to score each criterion; compute weighted sum `rubric_coverage_score = sum(coverage_i * weight_i)`; use `AnalysisCache` to cache rubric extraction and requirement parsing results
    - Implement `_check_section_presence(sections, brief)`: for each required section in `brief.required_sections`, verify word count ≥ 80% of target allocation using `StaticAnalyser.count_words()`; collect missing/undersized sections
    - Implement `_regenerate_section(brief, job, section_spec)`: use `model_override='sonnet'` to generate missing or undersized sections
    - Implement `_check_word_count_compliance(sections, job)`: use `StaticAnalyser.count_words()` to verify total word count within ±10% of `job.target_word_count`
    - Implement `_check_framework_references(sections, brief)`: detect presence of each framework in `brief.required_frameworks`
    - Implement assignment-type-specific checks: `reflection` → first-person language present; `case_study` → organisational context referenced; `policy_analysis` → policy recommendation + stakeholder analysis present; `dissertation` → trigger doctoral tone in prompt
    - Trigger auto-regeneration via Sonnet when rubric criterion coverage < 60%
    - Build and return `validation_report` dict matching the design schema
    - _Requirements: 4.1–4.10, 12.6, 15.5_

  - [ ] 10.2 Write property test for rubric coverage score weighted calculation
    - **Property 12: Rubric coverage score is weighted correctly**
    - **Validates: Requirements 4.2**
    - Use `@given(rubric_with_weights())` strategy; assert `rubric_coverage_score == sum(coverage_i * weight_i)` within ±1 point

  - [ ] 10.3 Write property test for required section presence detection
    - **Property 13: Required section presence detection**
    - **Validates: Requirements 4.4**
    - Use `@given(st.lists(st.text(min_size=1), min_size=1, max_size=8))` as required section names with varying word counts; assert `_check_section_presence()` correctly classifies present (≥80% target) vs absent/undersized

  - [ ] 10.4 Write property test for word count compliance detection
    - **Property 14: Word count compliance detection**
    - **Validates: Requirements 4.8**
    - Use `@given(st.integers(500, 5000), st.floats(0.5, 1.5))` for `target_word_count` and a multiplier; assert `_check_word_count_compliance()` returns `True` iff actual count is within ±10% of target

  - [ ] 10.5 Write property test for framework reference detection
    - **Property 15: Framework reference detection**
    - **Validates: Requirements 4.9**
    - Use `@given(st.lists(st.sampled_from(['NIST', 'ISO 27001', 'COBIT', 'ITIL']), min_size=1))` as required frameworks; assert `_check_framework_references()` correctly identifies present and absent frameworks

- [ ] 11. Implement `StructureQualitySystem`
  - [ ] 11.1 Implement `StructureQualitySystem.process()` in `generation/services/refinement/structure_quality_system.py`
    - Use `StaticAnalyser.paragraph_word_counts()` and `StaticAnalyser.detect_paragraph_length_uniformity()` for detection (zero LLM calls in detection phase)
    - Apply threshold skip: if structure variation is already acceptable (coefficient of variation above threshold), skip structure rewrite and log to `skipped_stages`
    - Receive lightweight metadata summary (paragraph counts, word counts) for detection phase, not full content
    - Implement `_compute_paragraph_length_variation(section)`: compute `(max_wc - min_wc) / max_wc`; return deficit if < 25%
    - Implement `_check_consecutive_section_paragraph_counts(sections)`: detect any two consecutive sections with identical paragraph counts
    - Implement `_check_rhetorical_distribution(section)`: verify ≥ 20% claim-evidence-analysis, ≥ 20% problem-implication-response, remainder varied
    - Implement `_check_intro_conclusion_distinction(sections)`: verify introduction and conclusion differ in paragraph count, opening sentence pattern, and rhetorical structure
    - For `report` or `business_report` types: verify at least one section contains non-prose formatting
    - Build Claude prompt targeting identified structural deficits; use `model_override='sonnet'`
    - _Requirements: 6.1–6.6, 15.4_

  - [ ] 11.2 Write property test for paragraph length variation
    - **Property 19: Paragraph length variation**
    - **Validates: Requirements 6.1**
    - Use `@given(section_with_uniform_paragraphs())` strategy (≥2 paragraphs, all same word count); after processing, assert `(max_wc - min_wc) / max_wc >= 0.25`

- [ ] 12. Implement `SubmissionValidator`
  - [ ] 12.1 Implement `SubmissionValidator.process()` in `generation/services/refinement/submission_validator.py`
    - Use `StaticAnalyser.compute_ai_suspicion_score()` and `compute_human_realism_score()` for final audit scores (zero LLM calls for scoring)
    - Define `SCORE_WEIGHTS = {'ai_suspicion_inverted': 0.25, 'rubric_coverage': 0.25, 'citation_completeness': 0.20, 'human_realism': 0.15, 'word_count_compliance': 0.15}`
    - Implement `_compute_submission_readiness_score(scores)`: `(100 - ai_suspicion) * 0.25 + rubric_coverage * 0.25 + citation_completeness * 0.20 + human_realism * 0.15 + word_count_compliance_score * 0.15`
    - Implement timeout tracking: record `start_time = time.monotonic()` at entry; check elapsed time before each sub-step; if elapsed ≥ 300s, log WARNING and proceed with scores defaulting incomplete fields to 50.0
    - Trigger auto-refinement (Opus) if `submission_readiness_score < 70` or `ai_suspicion_score > 65`; perform at most one auto-refinement pass; update `job.current_stage = 'auto_refinement'` and call `orchestrator.update_progress(job, 'auto_refinement')`
    - Create and return `RefinementResult` with all audit scores, `auto_refinement_triggered`, `refinement_passes_log`, and all cost fields: `total_refinement_cost_usd`, `cost_breakdown`, `cache_hit_count`, `llm_calls_count`, `static_analysis_calls_count`, `skipped_stages`
    - Compute per-call cost as `(input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)` using settings constants; accumulate into `total_refinement_cost_usd` and `cost_breakdown`
    - Update `job.status = REFINEMENT_COMPLETE` on success
    - _Requirements: 7.1–7.9, 20.3, 20.4_

  - [ ] 12.2 Write property test for submission readiness score computation
    - **Property 20: Submission readiness score computation**
    - **Validates: Requirements 7.2**
    - Use `@given(audit_scores())` strategy generating dicts with all five score keys in [0, 100]; assert computed score equals weighted sum within ±0.1 points

  - [ ] 12.3 Write property test for all audit scores persisted
    - **Property 21: All audit scores persisted to RefinementResult**
    - **Validates: Requirements 7.5**
    - Use `@given(audit_scores())` strategy; after `SubmissionValidator` creates a `RefinementResult`, assert all five score fields are non-null floats

  - [ ] 12.4 Write property test for cost computation correctness
    - **Property 30: Cost computation correctness**
    - **Validates: Requirements 20.3**
    - Use `@given(st.integers(min_value=0, max_value=100000), st.integers(min_value=0, max_value=100000), st.sampled_from(['haiku', 'sonnet', 'opus']))` for input tokens, output tokens, and model; assert computed cost equals `(input_tokens/1000 * input_rate) + (output_tokens/1000 * output_rate)` within ±$0.0001

- [ ] 13. Implement `DocumentAuthenticitySystem`
  - Implement `DocumentAuthenticitySystem.process()` in `generation/services/refinement/document_authenticity.py`
  - Check `RefinementResult.export_generated` before generating export; if `True`, skip generation and return existing export file path
  - Implement `_build_title_page_fields(brief, job)`: return dict with `assignment_title`, `student_id_placeholder`, `module_name`, `submission_date`, `word_count` formatted per `assignment_type` conventions
  - Implement `_resolve_formatting_config(brief)`: parse `brief.formatting_instructions`; default to Times New Roman 12pt, 1.5 line spacing, A4 when empty
  - Implement `_vary_heading_styles(sections, brief)`: ensure not every heading at the same level uses identical capitalisation/bold/underline unless brief specifies fixed style
  - Implement `_format_reference_list_spacing(content)`: apply realistic spacing between reference entries (not uniform single-line)
  - For `presentation` type: generate slide-structured output with varied content density per slide
  - Set `RefinementResult.export_generated = True` after successful generation
  - Return `formatting_config` dict consumed by the export stage
  - _Requirements: 8.1–8.8, 20.7, 20.8_

- [ ] 14. Implement `RefinementPipelineRunner`
  - Implement `RefinementPipelineRunner.run(job)` in `generation/services/refinement/pipeline_runner.py`
  - Instantiate all service classes: `RequirementValidator`, `CitationEngine`, `ReflectionGenerator`, `UnifiedRefinementEngine`, `StructureQualitySystem`, `SubmissionValidator`, `DocumentAuthenticitySystem`
  - Execute stages in the updated order with budget checks between each stage:
    1. `RequirementValidator` (threshold skip if rubric_coverage > 90)
    2. `CitationEngine` (threshold skip if citation_completeness > 92)
    3. For each section: route to `ReflectionGenerator` if `section_type == 'reflection'`, else to `UnifiedRefinementEngine` (threshold skip if ai_suspicion < 45)
    4. `StructureQualitySystem` (threshold skip if variation acceptable)
    5. `SubmissionValidator`
    6. `DocumentAuthenticitySystem`
  - Wrap each stage in try/except: on failure, log error and continue with unmodified sections (stage-level isolation per design)
  - On `BudgetExhaustedError`: log warning, skip remaining lower-priority stages, proceed to `SubmissionValidator`
  - Call `orchestrator.update_progress(job, <stage_key>)` after each successful stage
  - Accumulate `skipped_stages` list and pass to `SubmissionValidator` for persistence in `RefinementResult`
  - _Requirements: 9.7, 10.2, 10.5, 15.6_

- [ ] 15. Checkpoint — core pipeline wiring
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 16. Implement `run_refinement_pipeline` Celery task and trigger wiring
  - [ ] 16.1 Add `run_refinement_pipeline` Celery task to `generation/tasks.py`
    - Follow the same error-handling pattern as `continue_generation_pipeline`
    - Set `job.status = GenerationJob.Status.REFINING` at task start
    - Instantiate `RefinementPipelineRunner` and call `.run(job)`
    - On unhandled exception: call `orchestrator.fail_job(job, stage, str(exc))` and return
    - _Requirements: 10.1, 10.4, 10.5_

  - [ ] 16.2 Wire `run_refinement_pipeline` as automatic successor to `continue_generation_pipeline`
    - In `continue_generation_pipeline`, replace `job.status = GenerationJob.Status.COMPLETED` with `run_refinement_pipeline.delay(str(job.id))` after `section_generation` completes
    - Remove the `completed_at` assignment from `continue_generation_pipeline` (it moves to after refinement)
    - _Requirements: 10.1_

- [ ] 17. Extend job status API endpoint with refinement scores and cost
  - In `generation/views.py`, locate the existing `/generation/status/<id>/json/` view
  - Add `submission_readiness_score`, `ai_suspicion_score`, `rubric_coverage_score`, and `estimated_cost_usd` to the JSON response
  - Use `getattr(job, 'refinement_result', None)` to safely access the related object; return `null` for each field when no `RefinementResult` exists
  - `estimated_cost_usd` maps to `RefinementResult.total_refinement_cost_usd`
  - _Requirements: 11.3, 7.6, 20.5_

- [ ] 18. Token usage and cost logging
  - [ ] 18.1 Verify `ClaudeService.call()` creates a `TokenUsageLog` record for every call including those using `model_override`
    - Ensure the `model` field in `TokenUsageLog` stores the resolved model name (e.g. `claude-haiku-4-5`), not the alias
    - _Requirements: 9.5_

  - [ ] 18.2 Add cost computation to `ClaudeService.call()` or the pipeline runner
    - After each LLM call, compute cost using settings constants and the resolved model name
    - Accumulate cost into `RefinementResult.total_refinement_cost_usd` and `cost_breakdown` per stage
    - Increment `RefinementResult.llm_calls_count` on each LLM call
    - Increment `RefinementResult.static_analysis_calls_count` on each `StaticAnalyser` method call
    - _Requirements: 20.3, 20.4_

  - [ ] 18.3 Write property test for token usage log completeness
    - **Property 23: Token usage log completeness**
    - **Validates: Requirements 9.5**
    - Use `@given(st.sampled_from(['haiku', 'sonnet', 'opus']))` as `model_override`; after a mocked `ClaudeService.call()`, assert a `TokenUsageLog` record exists with non-null `stage`, `model`, `input_tokens`, `output_tokens`

  - [ ] 18.4 Write property test for model routing correctness
    - **Property 22: Model routing correctness**
    - **Validates: Requirements 9.1, 9.2, 9.3**
    - Use `@given(st.sampled_from(['haiku', 'sonnet', 'opus', 'HAIKU', 'Sonnet']))` to verify `_MODEL_ALIASES` lookup is case-insensitive and returns the correct model identifier

  - [ ] 18.5 Write property test for budget enforcement
    - **Property 24: Budget enforcement**
    - **Validates: Requirements 9.6**
    - Use `@given(st.integers(min_value=0))` to generate token totals at or above `CLAUDE_MAX_TOKENS_PER_JOB` and assert `BudgetExhaustedError` is raised before any API call

- [ ] 19. Final checkpoint — full pipeline integration
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Property tests use Hypothesis (already present in `.hypothesis/`) with `@settings(max_examples=100)`
- Each property test is tagged with its property number and requirement reference per the design document
- Checkpoints ensure incremental validation before proceeding to the next phase
- The old `HumanizationEngine`, `RealismEngine`, and `AIDetectionDefenseLayer` stubs from task 4 are superseded by `UnifiedRefinementEngine`; they may be kept as thin wrappers or removed after task 8 is complete
