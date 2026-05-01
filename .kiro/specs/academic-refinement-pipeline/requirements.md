# Requirements Document

## Introduction

This document specifies the Academic Refinement Pipeline — a post-generation processing system that transforms LamGen's raw AI-generated assignment content into submission-ready academic documents. The pipeline operates as a series of automated passes executed after the existing section generation stage (Stage 6) and before document export. It targets every assignment type supported by the platform: essays, reports, reflections, critiques, research papers, policy analyses, case studies, technical documentation, literature reviews, business reports, dissertations, presentations, and mixed-format assessments.

The goal is to shift LamGen's value proposition from "AI assignment generator" to "university-safe academic writing system" — producing output that requires zero manual editing before submission in the majority of cases.

The pipeline integrates with the existing Django/Celery architecture, extending `GenerationJob` status tracking, `GeneratedSection` storage, and the `ClaudeService` model-routing layer. New Celery task stages are inserted between `section_generation` and `export_formatting` in the existing orchestrator.

---

## Glossary

- **Pipeline**: The complete sequence of automated processing stages applied to a `GenerationJob` after section generation.
- **Refinement_Pipeline**: The new post-generation system specified in this document, comprising the UnifiedRefinementEngine, CitationEngine, RequirementValidator, StructureQualitySystem, SubmissionValidator, DocumentAuthenticitySystem, and ReflectionGenerator.
- **GenerationJob**: The existing Django model representing a single user assignment generation request.
- **GeneratedSection**: The existing Django model storing one section of a generated assignment.
- **AssignmentBrief**: The existing Django model storing extracted assignment metadata (type, level, citation style, rubric, etc.).
- **RubricProfile**: The existing Django model storing extracted marking criteria and weights.
- **RefinementResult**: A new model storing the output and quality scores produced by the Refinement_Pipeline for a given `GenerationJob`.
- **HumanizationEngine**: The pipeline component responsible for varying sentence rhythm, introducing controlled imperfection, and adjusting tone realism. Merged into `UnifiedRefinementEngine`.
- **AI_Detection_Defense**: The pipeline component that scans for AI-detectable patterns and rewrites risky sections. Merged into `UnifiedRefinementEngine`.
- **Citation_Engine**: The pipeline component responsible for citation formatting, consistency validation, and hallucination detection.
- **Requirement_Validator**: The pipeline component that validates generated content against the assignment brief and rubric before export.
- **Realism_Engine**: The pipeline component that enforces natural student-like phrasing and avoids machine-confidence patterns. Merged into `UnifiedRefinementEngine`.
- **Structure_Quality_System**: The pipeline component that enforces dynamic structural variation across sections and paragraphs.
- **Submission_Validator**: The pipeline component that runs a final pre-export audit and produces quality scores.
- **Document_Authenticity**: The pipeline component responsible for realistic document formatting (title pages, tables, appendices, spacing).
- **ClaudeService**: The existing Anthropic API wrapper used by all LLM-calling services.
- **Academic_Level**: One of `undergraduate`, `postgraduate`, or `doctoral`, as stored in `AssignmentBrief`.
- **Citation_Style**: One of `Harvard`, `APA`, `Chicago`, or `MLA`.
- **AI_Suspicion_Score**: A numeric score (0–100) estimating the likelihood that a document will be flagged by AI detection tools, where lower is better.
- **Human_Realism_Score**: A numeric score (0–100) estimating how naturally human the writing reads, where higher is better.
- **Submission_Readiness_Score**: A composite numeric score (0–100) summarising overall document quality for submission, where higher is better.
- **Rubric_Coverage_Score**: A numeric score (0–100) representing the percentage of rubric criteria adequately addressed in the generated content.
- **High_Risk_Section**: An introduction, executive summary, conclusion, or reflection section, which carries elevated AI-detection risk.
- **Haiku**: Anthropic's `claude-haiku` model family, used for low-cost preprocessing tasks.
- **Sonnet**: Anthropic's `claude-sonnet` model family, used for balanced generation tasks.
- **Opus**: Anthropic's `claude-opus` model family, used only as a last resort for high-risk rewriting when Sonnet passes still score above 75, final auto-refinement, and difficult reflective rewriting.
- **StaticAnalyser**: A pure-Python utility class that performs deterministic text analysis with zero LLM calls, used by all pipeline stages before deciding whether to invoke an LLM.
- **AnalysisCache**: A Django-cache-backed utility class that caches expensive analysis results by content hash to avoid redundant computation on retries and regeneration.
- **UnifiedRefinementEngine**: A single pipeline component that merges humanization, realism enhancement, and AI detection defense into one combined pass per section or fragment, replacing the three separate engines.
- **ReflectionGenerator**: A dedicated service for reflection sections that performs one-pass generation with realism-first prompting and natural imperfection injection, using Sonnet and skipping the UnifiedRefinementEngine.
- **Fragment-Level Rewriting**: The practice of rewriting only the specific risky paragraphs or sentences within a section rather than the entire section, to minimise output token consumption.
- **Threshold-Based Skipping**: The practice of automatically skipping a pipeline stage when quality metrics already meet the required threshold, eliminating unnecessary LLM calls.

---

## Requirements

### Requirement 1: Humanization Engine

**User Story:** As a student, I want the generated assignment to read like naturally written human prose, so that it does not trigger AI detection tools and reflects realistic student writing.

#### Acceptance Criteria

1. WHEN the Refinement_Pipeline processes a `GeneratedSection`, THE HumanizationEngine SHALL vary sentence length distribution so that no more than 30% of consecutive sentences share the same approximate length (within ±5 words).

2. WHEN the Refinement_Pipeline processes a `GeneratedSection`, THE HumanizationEngine SHALL ensure that no single transition word or phrase (e.g. "furthermore", "moreover", "additionally") appears more than twice per 500 words of content.

3. WHEN the Refinement_Pipeline processes a `GeneratedSection`, THE HumanizationEngine SHALL remove or replace all instances of the following AI-signature phrases: "fundamentally", "it is worth noting", "it is important to note", "critical landscape", "multifaceted", "robust framework", "seamless integration", "in conclusion", "to summarise", "it is clear that", "it is evident that".

4. WHEN the `AssignmentBrief.academic_level` is `undergraduate`, THE HumanizationEngine SHALL apply a tone profile that permits occasional informal phrasing, shorter paragraphs, and direct declarative sentences.

5. WHEN the `AssignmentBrief.academic_level` is `postgraduate` or `doctoral`, THE HumanizationEngine SHALL apply a tone profile that maintains formal register while still introducing natural variation in sentence complexity and paragraph density.

6. WHEN the `AssignmentBrief.writing_tone` is `reflective`, THE HumanizationEngine SHALL inject first-person perspective markers, natural uncertainty language (e.g. "I found that", "this challenged my assumption that"), and personal reasoning moments at a rate of at least one per 200 words.

7. WHEN the `AssignmentBrief.writing_tone` is `critical_analytical` or `professional_report`, THE HumanizationEngine SHALL preserve formal register while reducing syntactic uniformity by varying clause order and sentence opening patterns.

8. THE HumanizationEngine SHALL ensure that no more than 20% of paragraph openings within a `GeneratedSection` begin with the same word or phrase.

9. THE HumanizationEngine SHALL mix paragraph lengths so that the standard deviation of paragraph word counts within a section is at least 40 words.

10. IF the `AssignmentBrief` indicates an ESL (English as a Second Language) student context, THEN THE HumanizationEngine SHALL apply an ESL tone profile that introduces minor grammatical naturalness variations consistent with non-native academic writing, without introducing errors that would affect meaning.

---

### Requirement 2: AI Detection Defense Layer

**User Story:** As a student, I want the generated assignment to pass AI detection tools used by universities, so that my submission is not flagged for academic integrity review.

#### Acceptance Criteria

1. WHEN the Refinement_Pipeline completes section generation, THE AI_Detection_Defense SHALL scan every `GeneratedSection` for the following risk patterns: repetitive sentence openings, paragraph length uniformity, over-structured transition sequences, excessive use of formal academic connectors, and syntactic consistency above a measurable threshold.

2. WHEN a `GeneratedSection` is identified as high-risk by the AI_Detection_Defense scan, THE AI_Detection_Defense SHALL rewrite that section using the Opus model to diversify syntax, reduce pattern repetition, vary paragraph density, and soften overconfident phrasing.

3. WHEN the AI_Detection_Defense processes a High_Risk_Section (introduction, executive summary, conclusion, or reflection), THE AI_Detection_Defense SHALL apply enhanced rewriting that specifically targets uniform paragraph structure, predictable rhetorical openings, and machine-confidence tone.

4. AFTER AI_Detection_Defense rewriting, THE AI_Detection_Defense SHALL produce an AI_Suspicion_Score for each processed section, stored in the `RefinementResult` model.

5. IF the AI_Suspicion_Score for any section exceeds 70 after the first rewrite pass, THEN THE AI_Detection_Defense SHALL perform a second rewrite pass on that section before proceeding.

6. THE AI_Detection_Defense SHALL not alter factual claims, citation references, or rubric-aligned analytical content during rewriting.

7. WHILE the AI_Detection_Defense is rewriting a section, THE AI_Detection_Defense SHALL preserve the section's target word count within a ±10% tolerance.

---

### Requirement 3: Citation and Evidence Engine

**User Story:** As a student, I want every factual and analytical claim in my assignment to have a properly formatted citation, so that my submission meets academic integrity standards and avoids plagiarism flags.

#### Acceptance Criteria

1. THE Citation_Engine SHALL support formatting citations in Harvard, APA, Chicago, and MLA styles, determined by `AssignmentBrief.citation_style`.

2. WHEN the Citation_Engine processes a `GeneratedSection`, THE Citation_Engine SHALL identify all factual and analytical claims that lack an in-text citation and flag them for citation insertion.

3. WHEN the Citation_Engine inserts citations, THE Citation_Engine SHALL format each in-text citation according to the active `Citation_Style` with correct author, year, and page number fields where applicable.

4. THE Citation_Engine SHALL validate that every in-text citation has a corresponding entry in the reference list, and every reference list entry has at least one corresponding in-text citation.

5. WHEN the Citation_Engine validates references, THE Citation_Engine SHALL detect and flag references with the following hallucination indicators: DOI patterns that do not match standard DOI format (`10.XXXX/XXXXX`), journal names that do not match known academic publisher patterns, author-year mismatches within the same reference, and URLs that do not resolve to a plausible academic domain.

6. IF the Citation_Engine detects a hallucinated reference, THEN THE Citation_Engine SHALL remove that reference from the reference list and replace the corresponding in-text citation with a flagged placeholder indicating that a real source is required.

7. THE Citation_Engine SHALL produce a citation completeness score (0–100) representing the percentage of claims that have valid, non-hallucinated citations, stored in the `RefinementResult` model.

8. WHEN the `Citation_Style` is Harvard or APA, THE Citation_Engine SHALL validate that the reference list is sorted alphabetically by author surname.

9. WHEN the `Citation_Style` is Chicago, THE Citation_Engine SHALL validate that footnote numbering is sequential and that the bibliography is sorted alphabetically.

10. THE Citation_Engine SHALL ensure that the same source is cited consistently using the same author-year format throughout the document, with no variation in author name spelling or year across citations of the same work.

---

### Requirement 4: Assignment Requirement Validator

**User Story:** As a student, I want the generated assignment to fully satisfy the marking rubric and all submission requirements from the assignment brief, so that I do not lose marks for missing sections or unmet criteria.

#### Acceptance Criteria

1. WHEN the Refinement_Pipeline begins the validation phase, THE Requirement_Validator SHALL extract the following from the `AssignmentBrief` and `RubricProfile`: required sections, marking criteria and weights, word count expectations, required frameworks, formatting instructions, and assignment type.

2. THE Requirement_Validator SHALL compute a Rubric_Coverage_Score by evaluating the degree to which each `RubricProfile` criterion is addressed in the generated content, weighted by criterion weight.

3. WHEN the Rubric_Coverage_Score for any individual rubric criterion falls below 60%, THE Requirement_Validator SHALL trigger auto-regeneration of the section most responsible for that criterion using the Sonnet model.

4. THE Requirement_Validator SHALL verify that all sections listed in `AssignmentBrief.required_sections` are present in the generated output, with a word count of at least 80% of the target allocation for that section.

5. IF a required section is missing or below the 80% word count threshold, THEN THE Requirement_Validator SHALL generate the missing or undersized section using the Sonnet model before proceeding to export.

6. WHEN the `AssignmentBrief.assignment_type` is `reflection`, THE Requirement_Validator SHALL verify that at least one section contains first-person reflective language and personal reasoning, and trigger regeneration if absent.

7. WHEN the `AssignmentBrief.assignment_type` is `case_study`, THE Requirement_Validator SHALL verify that the generated content references the specific organisational context from `AssignmentBrief.organisational_context`, and trigger regeneration of the relevant section if absent.

8. THE Requirement_Validator SHALL verify that the total generated word count is within ±10% of `GenerationJob.target_word_count`, and trigger supplementary generation or trimming if outside this range.

9. WHEN the `AssignmentBrief` specifies required frameworks (e.g. NIST, ISO 27001, COBIT), THE Requirement_Validator SHALL verify that each framework is referenced at least once in the generated content, and flag any missing framework references.

10. THE Requirement_Validator SHALL produce a structured validation report stored in the `RefinementResult` model, listing: rubric coverage per criterion, missing sections, word count compliance status, framework reference status, and overall Rubric_Coverage_Score.

---

### Requirement 5: Realism Engine

**User Story:** As a student, I want the generated assignment to contain natural student-like reasoning and phrasing, so that it reads as genuinely written rather than machine-generated.

#### Acceptance Criteria

1. THE Realism_Engine SHALL ensure that analytical sections contain at least one instance of hedged or qualified reasoning per 300 words (e.g. "this suggests", "the evidence indicates", "one interpretation is").

2. THE Realism_Engine SHALL ensure that no section contains more than three consecutive sentences with identical syntactic structure (subject-verb-object with no subordinate clauses).

3. WHEN the `AssignmentBrief.writing_tone` is `reflective`, THE Realism_Engine SHALL ensure that reflection sections contain natural uncertainty language at a rate of at least one instance per 200 words.

4. WHEN the `AssignmentBrief.writing_tone` is `critical_analytical` or `professional_report`, THE Realism_Engine SHALL ensure that technical sections maintain structured argumentation while avoiding machine-confidence phrasing such as "it is undeniable that", "clearly", "obviously", and "without doubt".

5. THE Realism_Engine SHALL introduce mild lexical variation by replacing repeated use of the same analytical verb (e.g. "demonstrates", "highlights", "illustrates") when the same verb appears more than three times within a 500-word window.

6. THE Realism_Engine SHALL ensure that paragraph transitions are not uniformly signposted — at least 30% of paragraph transitions within a section SHALL use implicit rather than explicit connective phrases.

7. IF the Realism_Engine detects that more than 40% of sentences in a section begin with a noun phrase followed immediately by a verb, THEN THE Realism_Engine SHALL rewrite a subset of those sentences to vary the opening structure.

---

### Requirement 6: Structure Quality System

**User Story:** As a student, I want the assignment structure to feel naturally written rather than mechanically uniform, so that the document does not exhibit the predictable symmetry of AI-generated text.

#### Acceptance Criteria

1. THE Structure_Quality_System SHALL ensure that paragraph word counts within any section vary by at least 25% between the shortest and longest paragraph.

2. THE Structure_Quality_System SHALL ensure that no two consecutive sections have the same number of paragraphs.

3. THE Structure_Quality_System SHALL ensure that heading levels and sub-heading usage vary across sections in a way consistent with the `AssignmentBrief.assignment_type` — not every section SHALL have the same sub-heading structure.

4. WHEN the `AssignmentBrief.assignment_type` is `report` or `business_report`, THE Structure_Quality_System SHALL ensure that the document contains at least one section with a different structural format (e.g. a bulleted list, a numbered recommendation, or a table) rather than uniform prose paragraphs throughout.

5. THE Structure_Quality_System SHALL ensure that the introduction and conclusion sections are structurally distinct from each other — they SHALL NOT share the same paragraph count, opening sentence pattern, or rhetorical structure.

6. THE Structure_Quality_System SHALL apply rhetorical variation by ensuring that at least 20% of analytical paragraphs use a claim-evidence-analysis structure, at least 20% use a problem-implication-response structure, and the remainder use varied structures.

---

### Requirement 7: Final Submission Validator

**User Story:** As a student, I want a final quality check before I download my assignment, so that I can be confident the document is ready to submit without manual editing.

#### Acceptance Criteria

1. BEFORE generating the export file (PDF or DOCX), THE Submission_Validator SHALL run a final audit of the complete document covering: AI_Suspicion_Score, citation completeness, Rubric_Coverage_Score, word count compliance, formatting compliance, reference validity, section completeness, Human_Realism_Score, and repetitive language score.

2. THE Submission_Validator SHALL compute a Submission_Readiness_Score (0–100) as a weighted composite of the individual audit scores, with the following minimum weights: AI_Suspicion_Score (inverted, 25%), Rubric_Coverage_Score (25%), citation completeness (20%), Human_Realism_Score (15%), word count compliance (15%).

3. IF the Submission_Readiness_Score is below 70, THEN THE Submission_Validator SHALL trigger an auto-refinement pass using the Opus model targeting the lowest-scoring dimensions before proceeding to export.

4. IF the AI_Suspicion_Score exceeds 65 at the final audit stage, THEN THE Submission_Validator SHALL trigger a targeted AI_Detection_Defense rewrite pass on the highest-risk sections before export.

5. THE Submission_Validator SHALL store all audit scores and the final Submission_Readiness_Score in the `RefinementResult` model, associated with the `GenerationJob`.

6. THE Submission_Validator SHALL expose the Submission_Readiness_Score, AI_Suspicion_Score, and Rubric_Coverage_Score to the user via the existing job status API endpoint before the download link is presented.

7. WHEN the Submission_Validator completes without triggering auto-refinement, THE Submission_Validator SHALL update the `GenerationJob.status` to `REFINEMENT_COMPLETE` and proceed to export.

8. WHEN the Submission_Validator triggers auto-refinement, THE Submission_Validator SHALL update the `GenerationJob.current_stage` to `auto_refinement` and update the progress percentage accordingly before re-running the final audit.

9. THE Submission_Validator SHALL complete the full audit and any triggered auto-refinement within a total elapsed time of 300 seconds per job, after which it SHALL proceed to export with the best available scores and log a timeout warning.

---

### Requirement 8: Document Authenticity System

**User Story:** As a student, I want the downloaded document to look like a naturally formatted student submission, so that it does not appear to have been generated by an AI tool based on its visual formatting alone.

#### Acceptance Criteria

1. THE Document_Authenticity system SHALL generate a title page that includes the assignment title, student identifier placeholder, module name, submission date, and word count — formatted consistently with the `AssignmentBrief.assignment_type` conventions.

2. THE Document_Authenticity system SHALL apply page numbering, line spacing, and font settings that match the formatting instructions in `AssignmentBrief.formatting_instructions`, defaulting to Times New Roman 12pt, 1.5 line spacing, and A4 page size when no instructions are provided.

3. THE Document_Authenticity system SHALL ensure that heading styles vary naturally — not every heading at the same level SHALL use identical capitalisation, bold, or underline formatting unless the assignment brief specifies a fixed style.

4. WHEN the generated document contains tables, THE Document_Authenticity system SHALL format tables with realistic column width variation and avoid perfectly uniform cell padding that is characteristic of AI-generated documents.

5. WHEN the generated document contains appendices, THE Document_Authenticity system SHALL format appendices with sequential labelling (Appendix A, Appendix B) and ensure each appendix is referenced at least once in the main body.

6. THE Document_Authenticity system SHALL ensure that the reference list formatting matches the active `Citation_Style` with realistic spacing between entries — not uniform single-line spacing throughout.

7. THE Document_Authenticity system SHALL avoid generating a table of contents with perfectly uniform dot-leader spacing or identical indentation at every level, introducing minor natural variation consistent with word-processor-generated tables of contents.

8. WHEN the `AssignmentBrief.assignment_type` is `presentation`, THE Document_Authenticity system SHALL generate slide-structured output with varied content density per slide rather than uniform bullet-point lists on every slide.

---

### Requirement 9: Model Routing Strategy

**User Story:** As the platform operator, I want the refinement pipeline to use the most cost-effective Claude model for each task, so that quality is maximised without unnecessary API cost.

#### Acceptance Criteria

1. THE Refinement_Pipeline SHALL use the Haiku model for all preprocessing tasks including: AI pattern scanning, citation format detection, word count analysis, and structural uniformity detection.

2. THE Refinement_Pipeline SHALL use the Sonnet model for: section generation during auto-regeneration triggered by the Requirement_Validator, citation insertion and formatting, and standard humanization passes on non-high-risk sections.

3. THE Refinement_Pipeline SHALL use the Opus model exclusively for: critical analysis rewriting, AI_Detection_Defense rewrites on High_Risk_Sections, realism polishing passes, and auto-refinement triggered by a Submission_Readiness_Score below 70.

4. THE ClaudeService SHALL be extended to accept a `model_override` parameter that allows individual pipeline stages to specify Haiku, Sonnet, or Opus independently of the global `CLAUDE_MODEL` setting.

5. THE Refinement_Pipeline SHALL log the model used, token counts, and estimated cost for every API call made during refinement, using the existing `TokenUsageLog` model.

6. THE Refinement_Pipeline SHALL enforce the existing per-job token budget (`CLAUDE_MAX_TOKENS_PER_JOB`) across all refinement stages combined, and SHALL raise a `BudgetExhaustedError` if the budget is exceeded during refinement, proceeding to export with the best available content.

7. WHEN the Refinement_Pipeline estimates that completing all refinement stages would exceed the remaining token budget, THE Refinement_Pipeline SHALL prioritise stages in the following order: Requirement_Validator, Citation_Engine, AI_Detection_Defense, HumanizationEngine, Realism_Engine, Structure_Quality_System.

---

### Requirement 10: Pipeline Orchestration and Status Tracking

**User Story:** As a student, I want to see real-time progress during the refinement phase, so that I know the system is working and how long to wait before downloading.

#### Acceptance Criteria

1. THE Refinement_Pipeline SHALL be implemented as a Celery task (`run_refinement_pipeline`) that is triggered automatically upon completion of the existing `continue_generation_pipeline` task.

2. THE Refinement_Pipeline SHALL update `GenerationJob.current_stage` and `GenerationJob.progress_percentage` at each sub-stage transition, using the existing `GenerationPipelineOrchestrator.update_progress` method.

3. THE GenerationPipelineOrchestrator SHALL be extended with the following new stage weights: `humanization_pass` (65%), `ai_detection_defense` (72%), `citation_validation` (78%), `requirement_validation` (83%), `realism_pass` (87%), `structure_quality` (91%), `submission_validation` (95%), `auto_refinement` (97%), `export_formatting` (100%).

4. THE `GenerationJob.Status` choices SHALL be extended with a `REFINING` status that is set when the `run_refinement_pipeline` task begins.

5. WHEN the Refinement_Pipeline fails at any stage, THE Refinement_Pipeline SHALL call `GenerationPipelineOrchestrator.fail_job` with the failing stage name and error message, consistent with the existing failure handling pattern.

6. THE Refinement_Pipeline SHALL store a `RefinementResult` record for every completed job, containing: all individual audit scores, the Submission_Readiness_Score, AI_Suspicion_Score, Human_Realism_Score, Rubric_Coverage_Score, citation completeness score, and a JSON log of which auto-refinement passes were triggered.

7. THE `RefinementResult` model SHALL be associated with `GenerationJob` via a one-to-one relationship.

---

### Requirement 11: RefinementResult Data Model

**User Story:** As the platform operator, I want all refinement quality scores to be persisted in the database, so that I can audit output quality and identify pipeline improvement opportunities.

#### Acceptance Criteria

1. THE system SHALL provide a `RefinementResult` Django model with the following fields: `job` (OneToOneField to `GenerationJob`), `submission_readiness_score` (FloatField, 0–100), `ai_suspicion_score` (FloatField, 0–100), `human_realism_score` (FloatField, 0–100), `rubric_coverage_score` (FloatField, 0–100), `citation_completeness_score` (FloatField, 0–100), `word_count_compliant` (BooleanField), `auto_refinement_triggered` (BooleanField), `refinement_passes_log` (JSONField), `created_at` (DateTimeField, auto), `updated_at` (DateTimeField, auto).

2. THE `RefinementResult` model SHALL be registered in the Django admin with filtering by `submission_readiness_score`, `ai_suspicion_score`, and `auto_refinement_triggered`.

3. THE system SHALL expose `submission_readiness_score`, `ai_suspicion_score`, and `rubric_coverage_score` from the `RefinementResult` in the existing job status JSON API response (`/generation/status/<id>/json/`), returning `null` for each field when no `RefinementResult` exists yet.

4. THE `GeneratedSection` model SHALL be extended with a `refinement_version` IntegerField (default 0) that is incremented each time the section content is rewritten by any refinement stage.

5. THE `GeneratedSection` model SHALL be extended with a `ai_suspicion_score` FloatField (nullable) storing the per-section AI suspicion score produced by the AI_Detection_Defense scan.

---

### Requirement 12: Assignment Type Coverage

**User Story:** As a student submitting any type of university assignment, I want the refinement pipeline to handle my specific assignment type correctly, so that the output meets the conventions of that format.

#### Acceptance Criteria

1. THE Refinement_Pipeline SHALL support the following assignment types without degradation in output quality: essay, report, reflection, critique, research_paper, policy_analysis, case_study, technical_documentation, literature_review, business_report, dissertation, presentation, mixed_format.

2. THE `AssignmentBrief.AssignmentType` choices SHALL be extended to include: `reflection`, `critique`, `research_paper`, `policy_analysis`, `technical_documentation`, `business_report`, `dissertation`, `presentation`, `mixed_format` in addition to the existing types.

3. WHEN the `AssignmentBrief.assignment_type` is `dissertation`, THE Refinement_Pipeline SHALL apply doctoral-level tone calibration in the HumanizationEngine regardless of the `academic_level` field value.

4. WHEN the `AssignmentBrief.assignment_type` is `technical_documentation`, THE Realism_Engine SHALL preserve structured formatting, numbered sections, and precise technical language without applying informal humanization patterns.

5. WHEN the `AssignmentBrief.assignment_type` is `mixed_format`, THE Refinement_Pipeline SHALL detect the sub-format of each section independently and apply the appropriate humanization and realism profile per section.

6. WHEN the `AssignmentBrief.assignment_type` is `policy_analysis`, THE Requirement_Validator SHALL verify that the document contains a policy recommendation section and a stakeholder analysis component, and trigger generation of missing components if absent.

7. WHEN the `AssignmentBrief.assignment_type` is `critique`, THE Realism_Engine SHALL ensure that evaluative language is present (e.g. "the argument is weakened by", "a significant limitation is", "the author fails to account for") at a rate of at least one evaluative statement per 300 words.

---

### Requirement 13: Deterministic Validation Layer

**User Story:** As the platform operator, I want expensive LLM calls replaced with pure Python analysis wherever possible, so that token costs are minimised without reducing quality.

#### Acceptance Criteria

1. THE system SHALL provide a `StaticAnalyser` utility class in `generation/services/refinement/static_analyser.py` that performs all text analysis using pure Python with zero LLM calls.

2. THE `StaticAnalyser` class SHALL implement the following methods:
   - `count_words(text: str) -> int`
   - `paragraph_word_counts(text: str) -> list[int]`
   - `paragraph_opening_words(text: str) -> list[str]`
   - `sentence_lengths(text: str) -> list[int]`
   - `detect_ai_signature_phrases(text: str) -> list[str]` — regex scan against `AI_SIGNATURE_PHRASES`
   - `detect_machine_confidence_phrases(text: str) -> list[str]` — regex scan against `MACHINE_CONFIDENCE_PHRASES`
   - `detect_transition_density(text: str) -> float` — ratio of explicit connective phrases to paragraph count
   - `detect_analytical_verb_frequency(text: str, window: int = 500) -> dict[str, int]` — per-verb counts in sliding windows
   - `detect_repetitive_sentence_openings(text: str) -> float` — ratio of repeated opening words
   - `detect_paragraph_length_uniformity(text: str) -> float` — coefficient of variation of paragraph word counts
   - `validate_doi_format(doi: str) -> bool` — regex `10\.\d{4,}/\S+`
   - `validate_citation_format(citation: str, style: str) -> bool` — regex per style
   - `validate_reference_list_order(references: list[str], style: str) -> bool` — alphabetical check for Harvard/APA
   - `compute_ai_suspicion_score(text: str) -> float` — weighted combination of the above signals, no LLM
   - `compute_human_realism_score(text: str) -> float` — weighted combination of realism signals, no LLM

3. THE `StaticAnalyser` class SHALL make zero LLM calls; all fifteen methods SHALL be implemented using only Python standard library operations (string manipulation, regex, statistics).

4. WHEN any pipeline stage needs to decide whether to invoke an LLM, THE pipeline stage SHALL first call the relevant `StaticAnalyser` methods to obtain deterministic scores before making that decision.

5. THE `StaticAnalyser.compute_ai_suspicion_score()` method SHALL return a float in the range [0, 100] for any non-empty text input.

6. THE `StaticAnalyser.compute_human_realism_score()` method SHALL return a float in the range [0, 100] for any non-empty text input.

---

### Requirement 14: Fragment-Level Rewriting

**User Story:** As the platform operator, I want the pipeline to rewrite only the specific fragments that are risky, not entire sections, so that output token consumption is minimised.

#### Acceptance Criteria

1. WHEN the `UnifiedRefinementEngine` processes a `GeneratedSection`, THE `UnifiedRefinementEngine` SHALL first use `StaticAnalyser` to detect risky fragments at paragraph level and sentence level before invoking any LLM.

2. WHEN the `StaticAnalyser` identifies risky fragments (repetitive openings, AI-signature phrases, machine-confidence tone, overly polished transitions, syntactic repetition), THE `UnifiedRefinementEngine` SHALL rewrite only those specific fragments rather than the entire section.

3. WHEN the AI_Suspicion_Score for a section is 75 or below, THE `UnifiedRefinementEngine` SHALL perform fragment-level rewriting only, not a full section rewrite.

4. WHEN the AI_Suspicion_Score for a section exceeds 75, THE `UnifiedRefinementEngine` SHALL perform a full section rewrite.

5. WHEN a rubric coverage failure is detected for a section, THE `UnifiedRefinementEngine` SHALL perform a full section rewrite for that section.

6. WHEN a hallucination is detected in a section, THE `UnifiedRefinementEngine` SHALL perform a full section rewrite for that section.

7. WHEN a section is structurally broken (missing required structural elements), THE `UnifiedRefinementEngine` SHALL perform a full section rewrite for that section.

8. WHEN fragment-level rewriting is performed, THE `UnifiedRefinementEngine` SHALL preserve the word count of the entire section within ±10% of the original.

9. WHEN fragment-level rewriting is performed, THE non-rewritten paragraphs in the section SHALL remain byte-identical to the original paragraphs.

---

### Requirement 15: Threshold-Based Stage Skipping

**User Story:** As the platform operator, I want pipeline stages to be skipped automatically when quality thresholds are already met, so that unnecessary LLM calls are eliminated.

#### Acceptance Criteria

1. WHEN the AI_Suspicion_Score for a section is below 45, THE `UnifiedRefinementEngine` SHALL skip all LLM rewriting for that section and proceed without modification.

2. WHEN the citation completeness score exceeds 92, THE `CitationEngine` SHALL skip the citation insertion pass for that document and proceed to reference list validation only.

3. WHEN the Human_Realism_Score for a section exceeds 80, THE `UnifiedRefinementEngine` SHALL skip the realism enhancement pass for that section.

4. WHEN the structure variation for a section is already acceptable (paragraph length coefficient of variation above threshold), THE `StructureQualitySystem` SHALL skip the structure rewrite for that section.

5. WHEN the Rubric_Coverage_Score exceeds 90, THE `RequirementValidator` SHALL skip requirement regeneration and proceed to the validation report only.

6. WHEN any stage is skipped due to a threshold condition, THE pipeline SHALL record the stage name in `RefinementResult.skipped_stages`.

7. THE `RefinementResult.skipped_stages` field SHALL contain the list of all stage names skipped during the pipeline run for that job.

---

### Requirement 16: UnifiedRefinementEngine

**User Story:** As the platform operator, I want humanization, realism, and AI detection defense merged into a single pass, so that repeated context loading and generation cost is eliminated.

#### Acceptance Criteria

1. THE system SHALL provide a `UnifiedRefinementEngine` class in `generation/services/refinement/unified_refinement_engine.py` that replaces the separate `HumanizationEngine`, `RealismEngine`, and `AIDetectionDefenseLayer` classes.

2. WHEN the `UnifiedRefinementEngine` processes a section or fragment, THE `UnifiedRefinementEngine` SHALL make a single LLM call that simultaneously applies humanization, realism enhancement, and AI pattern reduction.

3. BEFORE making any LLM call, THE `UnifiedRefinementEngine` SHALL use `StaticAnalyser` to detect all issues in the section or fragment.

4. THE `UnifiedRefinementEngine` SHALL use a diff-based prompt format that specifies exactly what to change, rather than requesting an open-ended rewrite.

5. THE diff-based prompt used by `UnifiedRefinementEngine` SHALL include: an explicit list of detected issues, preserve instructions (factual claims, citations, document structure, rubric-aligned content, word count within ±10%), and specific fragment references with line context.

6. THE `UnifiedRefinementEngine` SHALL use `model_override='sonnet'` for standard sections and fragments.

7. WHEN a section's AI_Suspicion_Score exceeds 75 after the Sonnet pass, THE `UnifiedRefinementEngine` SHALL perform a second pass using `model_override='opus'`.

8. THE `UnifiedRefinementEngine` SHALL NOT use Opus for scanning, validation, basic humanization, formatting, or simple rewrites.

9. THE `UnifiedRefinementEngine` SHALL receive only the section(s) it needs in its context window, not the full assignment.

10. THE `UnifiedRefinementEngine` SHALL receive only risky fragments in its context window when performing fragment-level rewriting, not full sections unless the AI_Suspicion_Score exceeds 75.

---

### Requirement 17: ReflectionGenerator

**User Story:** As a student submitting a reflection assignment, I want reflection sections generated with natural human imperfection in a single pass, so that they do not require expensive multi-pass refinement.

#### Acceptance Criteria

1. THE system SHALL provide a `ReflectionGenerator` class in `generation/services/refinement/reflection_generator.py` dedicated to generating and refining reflection sections.

2. THE `ReflectionGenerator` SHALL generate or refine reflection sections in a single LLM pass using `model_override='sonnet'`.

3. THE `ReflectionGenerator` SHALL use a realism-first prompt that builds natural imperfection, controlled inconsistency, human uncertainty markers, and personal reasoning simulation directly into the generation prompt.

4. THE `ReflectionGenerator` prompt SHALL include natural uncertainty markers (e.g. "I found that", "this challenged my assumption that", "I was not entirely sure"), personal reasoning moments, and reduced philosophical tone.

5. WHEN a section has type `reflection`, THE `RefinementPipelineRunner` SHALL route that section to `ReflectionGenerator` instead of `UnifiedRefinementEngine`.

6. WHEN a section has been processed by `ReflectionGenerator`, THE `RefinementPipelineRunner` SHALL NOT pass that section to `UnifiedRefinementEngine`.

7. THE `ReflectionGenerator` SHALL NOT use Opus under any circumstances; reflection quality SHALL be achieved through prompt design using Sonnet.

---

### Requirement 18: AnalysisCache

**User Story:** As the platform operator, I want expensive analysis results cached by content hash, so that retries and regeneration do not recompute the same analysis.

#### Acceptance Criteria

1. THE system SHALL provide an `AnalysisCache` utility class in `generation/services/refinement/analysis_cache.py` that uses Django's cache framework (`django.core.cache.cache`).

2. THE `AnalysisCache` SHALL use cache keys of the format `refinement:{job_id}:{content_hash}:{analysis_type}`, where `content_hash` is `hashlib.md5(content.encode()).hexdigest()[:16]`.

3. THE `AnalysisCache` SHALL store cached results with a TTL of 3600 seconds.

4. THE `AnalysisCache` SHALL implement a `get_or_compute(key: str, compute_fn: callable, ttl: int = 3600)` method that returns the cached result on a cache hit, or calls `compute_fn`, stores the result, and returns it on a cache miss.

5. WHEN a cache hit occurs, THE `AnalysisCache` SHALL log the cache hit at DEBUG level.

6. THE following expensive analyses SHALL be cached using `AnalysisCache`: rubric extraction results, assignment requirement parsing, framework extraction, section structure analysis, and static analysis scores per section.

7. WHEN a cache hit occurs for an analysis, THE pipeline SHALL increment `RefinementResult.cache_hit_count` by one.

8. WHEN a second call is made with identical content for the same analysis type, THE `AnalysisCache` SHALL return the same result as the first call without invoking any LLM or recomputing the analysis.

---

### Requirement 19: Diff-Based Rewriting Prompts

**User Story:** As the platform operator, I want all LLM rewrite prompts to specify exactly what to change rather than requesting open-ended rewrites, so that output token generation is minimised.

#### Acceptance Criteria

1. ALL LLM rewrite prompts generated by the `UnifiedRefinementEngine` SHALL use the constrained editing format:
   ```
   Modify ONLY the following detected issues in the text below:
   {issues_list}

   Preserve exactly:
   - All factual claims and citations
   - Document structure and section order
   - Rubric-aligned analytical content
   - Word count within ±10%

   Issues to fix:
   {specific_fragments_with_line_references}

   Text:
   {section_content}
   ```

2. NO rewrite prompt generated by any pipeline stage SHALL use open-ended instructions such as "Rewrite this section naturally", "Improve this text", or equivalent unspecified rewrite directives.

3. EVERY rewrite prompt SHALL include a non-empty issues list derived from `StaticAnalyser` detection results.

4. EVERY rewrite prompt SHALL include explicit preserve instructions covering factual claims, citations, document structure, and word count tolerance.

5. EVERY rewrite prompt SHALL include specific fragment references identifying the exact text to be changed.

6. THE output tokens per rewrite call using diff-based prompts SHALL be measurably lower than equivalent full-section open-ended rewrite calls for the same content.

---

### Requirement 20: Cost Intelligence System

**User Story:** As the platform operator, I want real-time token cost tracking per stage and per assignment, so that I can identify expensive stages and optimise them.

#### Acceptance Criteria

1. THE `RefinementResult` model SHALL include the following additional fields:
   - `export_generated = models.BooleanField(default=False)` — tracks whether the export file has been generated to prevent duplicate formatting
   - `total_refinement_cost_usd = models.DecimalField(max_digits=8, decimal_places=6, default=0)` — total cost of all LLM calls during refinement
   - `cost_breakdown = models.JSONField(default=dict)` — per-stage cost breakdown
   - `cache_hit_count = models.IntegerField(default=0)` — number of cache hits during the pipeline run
   - `llm_calls_count = models.IntegerField(default=0)` — total number of LLM calls made
   - `static_analysis_calls_count = models.IntegerField(default=0)` — total number of `StaticAnalyser` method calls made
   - `skipped_stages = models.JSONField(default=list)` — list of stage names skipped due to threshold conditions

2. THE system SHALL store the following cost-per-token settings in Django settings:
   - `HAIKU_COST_PER_1K_INPUT = 0.00025`
   - `HAIKU_COST_PER_1K_OUTPUT = 0.00125`
   - `SONNET_COST_PER_1K_INPUT = 0.003`
   - `SONNET_COST_PER_1K_OUTPUT = 0.015`
   - `OPUS_COST_PER_1K_INPUT = 0.015`
   - `OPUS_COST_PER_1K_OUTPUT = 0.075`

3. WHEN any LLM call is made during the refinement pipeline, THE pipeline SHALL compute the cost as `(input_tokens / 1000 * input_rate) + (output_tokens / 1000 * output_rate)` and add it to `RefinementResult.total_refinement_cost_usd`.

4. THE `RefinementResult.cost_breakdown` JSONField SHALL contain a per-stage breakdown of token costs, with each entry recording the stage name, model used, input tokens, output tokens, and cost in USD.

5. THE existing job status API endpoint (`/generation/status/<id>/json/`) SHALL include an `estimated_cost_usd` field in its response, returning the current value of `RefinementResult.total_refinement_cost_usd` or `null` when no `RefinementResult` exists.

6. THE pipeline SHALL target a total refinement cost of $0.80–$3.00 per assignment through the combined effect of fragment-level rewriting, threshold-based skipping, StaticAnalyser usage, AnalysisCache hits, and model routing optimisation.

7. WHEN the `DocumentAuthenticitySystem` is about to generate a PDF or DOCX export, THE system SHALL check `RefinementResult.export_generated`; IF `export_generated` is `True`, THE system SHALL skip export generation and return the existing export file path.

8. WHEN the `DocumentAuthenticitySystem` successfully generates an export file, THE system SHALL set `RefinementResult.export_generated = True`.
