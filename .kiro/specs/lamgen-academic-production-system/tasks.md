# Implementation Plan: LamGen Academic Production System — Phase 2: Rubric-Aware Generation Pipeline

## Overview

Build the `generation` Django app and implement the full rubric-aware generation pipeline (Stages 1–6) on top of the existing Django/Celery/Redis/PostgreSQL stack. Phase 2 covers: app scaffolding, data models, ClaudeService, prompt template system, rubric-aware prompt builder, outline generation, section planning, research context preparation, and section-by-section generation orchestration with GenerationMemory injection.

Phase 3 components (Humanization Engine, Academic Reviewer Agent, Coherence Pass, Export) are explicitly out of scope.

---

## Tasks

- [x] 1. Scaffold the `generation` Django app and register it
  - Create `generation/` app directory with `__init__.py`, `apps.py`, `admin.py`, `urls.py`
  - Register `generation` in `INSTALLED_APPS` in `config/settings.py`
  - Add `CLAUDE_MODEL` setting (default `claude-sonnet-4-5`) and `CLAUDE_MAX_TOKENS` (default `16000`) to `config/settings.py`
  - Wire `generation.urls` into `config/urls.py`
  - _Requirements: 5.4, 10.1, 10.2_

- [x] 2. Define Phase 2 data models
  - [x] 2.1 Create `generation/models.py` with `GenerationJob`, `AssignmentBrief`, `RubricProfile`, `DocumentOutline`, `GeneratedSection`, and `TokenUsageLog` models exactly as specified in the design
    - `GenerationJob`: UUID PK, status choices (PENDING / ANALYSING / AWAITING_OUTLINE_REVIEW / PROCESSING / COMPLETED / FAILED), `current_stage`, `progress_percentage`, `total_input_tokens`, `total_output_tokens`, `error_message`, `target_word_count`
    - `AssignmentBrief`: OneToOne to `GenerationJob`, all fields including `required_sections` (JSONField), `required_frameworks` (JSONField), `organisational_context`, `academic_level_inferred`
    - `RubricProfile`: OneToOne to `AssignmentBrief`, `criteria` JSONField with schema `[{"name": str, "weight": float, "distinction_descriptor": str}]`
    - `DocumentOutline`: OneToOne to `GenerationJob`, `sections` JSONField with schema `[{"title": str, "target_word_count": int, "key_points": [str]}]`, `user_confirmed`, `confirmed_at`
    - `GeneratedSection`: FK to `GenerationJob`, `order`, `title`, `content`, `word_count`, `humanized`, `reviewer_score` (JSONField, nullable), `rewritten_by_reviewer`; unique_together `(job, order)`; ordered by `order`
    - `TokenUsageLog`: FK to `GenerationJob`, `stage`, `input_tokens`, `output_tokens`, `model`, `created_at`
    - _Requirements: 2.8, 3.6, 4.1, 5.1, 10.7, 11.1_

  - [x] 2.2 Create `generation/migrations/0001_initial.py` via `python manage.py makemigrations generation`
    - Run after model definition to generate the migration file
    - _Requirements: 2.8, 11.1_

  - [x] 2.3 Register all models in `generation/admin.py` for visibility
    - _Requirements: 11.1_

  - [x] 2.4 Write property test for `GenerationJob` creation invariant
    - **Property 26: Generation Job creation invariant** — for any new `GenerationJob`, UUID PK is unique and initial status is PENDING
    - **Validates: Requirements 11.1**

- [x] 3. Implement `SectionMemory` dataclass and `SectionMemoryService`
  - [x] 3.1 Create `generation/services/section_memory.py` with the `SectionMemory` dataclass and `SectionMemoryService`
    - `SectionMemory` dataclass: `job_id`, `thesis_argument`, `terminology` (dict), `citations_used` (list), `analytical_positions` (list), `concepts_discussed` (list), `section_summaries` (list of dicts)
    - `SectionMemoryService.initialise(job_id)`: creates empty `SectionMemory`, serialises to JSON, stores in Redis under `section_memory:{job_id}` with TTL of 14,400 seconds
    - `SectionMemoryService.get(job_id)`: retrieves and deserialises from Redis; raises `SectionMemoryError` if key missing
    - `SectionMemoryService.update(job_id, section_update)`: merges new citations (deduplicating), appends summaries, updates thesis argument and terminology, re-saves to Redis
    - `SectionMemoryService.delete(job_id)`: removes the Redis key
    - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6_

  - [x] 3.2 Write property test for `SectionMemory` initialisation and TTL
    - **Property 9: Section Memory initialisation and TTL** — after `initialise()`, Redis key exists with TTL between 14,000 and 14,400 seconds
    - **Validates: Requirements 4.1, 4.4**

  - [x] 3.3 Write property test for citation deduplication
    - **Property 10: Section Memory update accumulates without duplicates** — after any sequence of section updates, `citations_used` contains all citations with no duplicates
    - **Validates: Requirements 4.2, 4.6, 8.5**

- [x] 4. Implement `ClaudeService` with retry, backoff, and token logging
  - [x] 4.1 Create `generation/services/claude_service.py`
    - `ClaudeService.call(system_prompt, user_prompt, max_tokens, job, stage_label)`: calls Anthropic Messages API using `settings.CLAUDE_MODEL`; retries up to 3 times with exponential backoff (2s, 4s, 8s) on `APIConnectionError` or `APIStatusError`; raises `ClaudeAPIError` after exhausting retries
    - On success: creates a `TokenUsageLog` record with `input_tokens`, `output_tokens`, `model`, `stage_label`, and increments `job.total_input_tokens` / `job.total_output_tokens`
    - Uses role-based prompting: `system` role for persona + context, `user` role for the generation task
    - `ClaudeService._build_system_prompt(brief, memory)`: injects academic expert persona, all `AssignmentBrief` fields, and (when provided) `SectionMemory` thesis argument, terminology, and analytical positions
    - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6, 10.7_

  - [x] 4.2 Write property test for Claude retry with exponential backoff
    - **Property 24: Claude API retry with exponential backoff** — on consecutive failures, delays are 2s, 4s, 8s before raising `ClaudeAPIError`
    - **Validates: Requirements 10.5**

  - [x] 4.3 Write property test for token usage logging
    - **Property 25: Token usage logged for every API call** — every successful `ClaudeService.call()` creates a `TokenUsageLog` record with correct fields
    - **Validates: Requirements 10.7**

  - [x] 4.4 Write property test for system prompt context injection
    - **Property 11: Section Memory injected into every generation prompt** — constructed system prompt contains thesis argument, terminology, and analytical positions from `SectionMemory`
    - **Validates: Requirements 4.3, 10.4**

- [x] 5. Implement the prompt template system
  - Create `generation/prompts/` package with `__init__.py`
  - Create `generation/prompts/templates.py` containing all prompt template strings as named constants:
    - `ASSIGNMENT_ANALYSIS_PROMPT`: extracts topic, subject area, assignment type, academic level, required sections, citation style, writing tone, organisational context, required frameworks; instructs Claude to return structured JSON
    - `RUBRIC_EXTRACTION_PROMPT`: extracts rubric criteria with name, weight, and distinction descriptor; returns JSON array
    - `OUTLINE_GENERATION_PROMPT`: produces section titles, target word counts, and key points as JSON; accepts `Assignment_Brief` and `Rubric_Profile` as template variables
    - `SECTION_PLANNING_PROMPT`: expands each outline section with detailed sub-points and research angles
    - `RESEARCH_CONTEXT_PROMPT`: identifies theoretical frameworks, key authors, and concepts per section
    - `SECTION_GENERATION_PROMPT`: the core per-section generation template — injects `Assignment_Brief`, `Rubric_Profile`, `GenerationMemory`, section objective, target word count, writing tone, academic level, and organisational context; instructs rubric-weighted analytical depth
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.6, 5.5, 5.6, 5.7, 10.3_

- [x] 6. Implement `AssignmentIntelligenceEngine` (Stage 1 + Stage 2)
  - [x] 6.1 Create `generation/services/assignment_intelligence.py`
    - `AssignmentIntelligenceEngine.analyse(text_chunks, job)`: orchestrates Stage 1 (instruction analysis) and Stage 2 (rubric extraction); persists `AssignmentBrief` and `RubricProfile` to DB; sets `job.status = ANALYSING` at start; defaults `academic_level` to postgraduate and sets `academic_level_inferred=True` when level cannot be determined
    - `_build_analysis_prompt(chunks)`: constructs the structured extraction prompt using `ASSIGNMENT_ANALYSIS_PROMPT` template; handles multi-chunk documents
    - `_parse_brief_response(response)`: parses Claude's JSON response into `AssignmentBrief` field values; raises `BriefExtractionError` on malformed JSON
    - `_extract_rubric(brief, text_chunks)`: calls Claude with `RUBRIC_EXTRACTION_PROMPT`; creates `RubricProfile` if rubric criteria are found; skips gracefully if no rubric is present
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 2.10_

  - [x] 6.2 Write property test for `AssignmentBrief` extraction completeness
    - **Property 8: Assignment Brief extraction completeness** — for any document text with clearly stated metadata, `analyse()` produces an `AssignmentBrief` with all required fields populated and persisted before pipeline proceeds
    - **Validates: Requirements 2.1, 2.2, 2.3, 2.8**

- [x] 7. Implement `GenerationPipelineOrchestrator` and Celery task scaffolding
  - [x] 7.1 Create `generation/services/orchestrator.py` with `GenerationPipelineOrchestrator`
    - `STAGE_WEIGHTS` dict mapping stage names to progress percentages (as per design)
    - `update_progress(job, stage)`: writes stage name and percentage to Redis progress key and updates `job.current_stage` and `job.progress_percentage` in DB; progress must be monotonically increasing
    - `fail_job(job, stage, error)`: sets `job.status = FAILED`, writes `error_message`, deletes `SectionMemory` from Redis, stops pipeline
    - _Requirements: 5.2, 5.3, 11.2, 11.3, 11.5_

  - [x] 7.2 Create `generation/tasks.py` with `run_generation_pipeline(job_id)` Celery task
    - Decorated with `@shared_task`
    - Wraps each stage call in try/except; calls `orchestrator.fail_job()` on any unhandled exception
    - Phase 2 stages only: `instruction_analysis` → `rubric_extraction` → `outline_generation` → PAUSE (set status to `AWAITING_OUTLINE_REVIEW`) → `section_planning` → `research_context_preparation` → `section_by_section_generation`
    - Create `continue_generation_pipeline(job_id)` Celery task that resumes from Stage 4 after outline confirmation
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 12.3_

  - [x] 7.3 Write property test for pipeline progress monotonically increasing
    - **Property 13: Pipeline progress is monotonically increasing** — progress percentage after each stage is strictly greater than the previous, and final stage records 100%
    - **Validates: Requirements 5.2, 11.5**

  - [x] 7.4 Write property test for pipeline failure stops execution
    - **Property 14: Pipeline failure stops execution and records error** — when any stage raises an exception, `GenerationJob.status` is FAILED, error is recorded, and no subsequent stages execute
    - **Validates: Requirements 5.3**

- [x] 8. Implement Outline Generation engine (Stage 3)
  - Create `generation/services/outline_generator.py` with `OutlineGenerationService`
  - `OutlineGenerationService.generate(job, brief)`: calls Claude with `OUTLINE_GENERATION_PROMPT` injecting `Assignment_Brief` and `Rubric_Profile`; parses JSON response into `DocumentOutline` sections schema; persists `DocumentOutline` to DB with `user_confirmed=False`; sets `job.status = AWAITING_OUTLINE_REVIEW`
  - Distributes `job.target_word_count` across sections proportionally based on rubric criterion weights where applicable
  - Raises `OutlineGenerationError` on malformed Claude response
  - _Requirements: 5.6, 12.2, 12.3_

- [x] 9. Implement Section Planning engine (Stage 4)
  - Create `generation/services/section_planner.py` with `SectionPlanningService`
  - `SectionPlanningService.plan(job, outline, brief)`: for each section in the confirmed `DocumentOutline`, calls Claude with `SECTION_PLANNING_PROMPT` to expand key points into detailed sub-points and research angles; stores enriched section plans back into `outline.sections` JSONField
  - _Requirements: 5.1, 5.5_

- [x] 10. Implement Research Context Preparation (Stage 5)
  - Create `generation/services/research_context.py` with `ResearchContextService`
  - `ResearchContextService.prepare(job, brief, outline)`: calls Claude with `RESEARCH_CONTEXT_PROMPT` to identify theoretical frameworks, key authors, and concepts that must be engaged with per section; stores the research context map as a JSON dict on the `DocumentOutline` (add `research_context` JSONField to `DocumentOutline` model)
  - Ensures all `required_frameworks` from `AssignmentBrief` are represented in the research context
  - _Requirements: 5.7, 2.5_

- [x] 11. Implement Section-by-Section Generation orchestration (Stage 6)
  - [x] 11.1 Create `generation/services/section_generator.py` with `SectionGenerationService`
    - `SectionGenerationService.generate_all(job, brief, outline, memory)`: iterates over confirmed outline sections in order; calls `_generate_section()` for each; updates `SectionMemory` after each section; updates job progress proportionally within the stage weight range (25–60%)
    - `_generate_section(job, brief, outline_section, memory, research_context)`: builds the full generation prompt using `SECTION_GENERATION_PROMPT` template, injecting all required context: `Assignment_Brief`, `Rubric_Profile`, `GenerationMemory` (current `SectionMemory` state), section objective, target word count, writing tone, academic level, organisational context, required frameworks/theories
    - Calls `ClaudeService.call()` with `max_tokens` proportional to section target word count (approx 1.5× word count, capped at 16,000)
    - Creates a `GeneratedSection` DB record for each section with `order`, `title`, `content`, and computed `word_count`
    - After each section: calls `SectionMemoryService.update()` with extracted thesis argument, new terminology, citations used, analytical positions, and a section summary
    - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 4.2, 4.3, 5.5, 10.3, 10.4_

  - [x] 11.2 Write property test for `SectionMemory` deletion on job completion/failure
    - **Property 12: Section Memory deleted on job completion or failure** — after `GenerationJob` transitions to COMPLETED or FAILED, Redis key `section_memory:{job_id}` no longer exists
    - **Validates: Requirements 4.5**

- [x] 12. Implement job submission view and outline review view
  - [x] 12.1 Create `generation/views.py` with:
    - `submit_job` view (POST): validates uploaded file (MIME type via `python-magic`, size ≤ 20 MB) or prompt text (50–10,000 chars); validates `target_word_count` (500–15,000); creates `GenerationJob` with status PENDING; enqueues `run_generation_pipeline.delay(job.id)`; redirects to job status page
    - `job_status` view (GET): renders job status page for authenticated owner; returns 403 for non-owners
    - `job_status_json` view (GET): JSON polling endpoint returning `{"stage": str, "progress_percentage": int, "status": str}`; enforces ownership (403 for non-owners)
    - `confirm_outline` view (POST): sets `outline.user_confirmed = True`, `outline.confirmed_at = now()`; enqueues `continue_generation_pipeline.delay(job.id)`; enforces ownership
    - `edit_outline` view (POST): accepts JSON body with updated section titles and target word counts; updates `outline.sections`; enforces ownership; only allowed when job is in `AWAITING_OUTLINE_REVIEW` status
    - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.4, 11.7, 12.1, 12.2, 12.3, 12.4_

  - [x] 12.2 Create minimal `generation/templates/generation/` templates:
    - `submit.html`: file upload form + prompt textarea + word count field
    - `status.html`: job status display with progress bar; shows outline for review when status is `AWAITING_OUTLINE_REVIEW`; shows download links when COMPLETED
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

  - [x] 12.3 Write property test for upload validation
    - **Property 1: Upload validation rejects invalid files** — validator accepts file if and only if MIME type is PDF or DOCX AND size ≤ 20 MB; rejects otherwise with descriptive error
    - **Validates: Requirements 1.1, 1.2, 1.4, 1.5**

  - [x] 12.4 Write property test for prompt length validation
    - **Property 2: Prompt length validation** — validator accepts prompt if and only if length is between 50 and 10,000 characters inclusive
    - **Validates: Requirements 1.3**

  - [x] 12.5 Write property test for target word count validation
    - **Property 30: Target word count validation** — system accepts word count if and only if it is between 500 and 15,000 inclusive
    - **Validates: Requirements 12.4**

  - [x] 12.6 Write property test for authorization
    - **Property 29: Authorization — users can only access their own jobs** — any authenticated user attempting to view, download, or delete a job belonging to another user receives HTTP 403
    - **Validates: Requirements 11.7**

  - [x] 12.7 Write property test for progress polling endpoint contract
    - **Property 27: Progress polling endpoint contract** — GET to polling endpoint for a PROCESSING job returns JSON with `stage` (str), `progress_percentage` (int 0–100), and `status` (str)
    - **Validates: Requirements 11.4**

- [x] 13. Add `generation` app factories and extend `conftest.py`
  - Add `GenerationJobFactory`, `AssignmentBriefFactory`, `RubricProfileFactory`, `DocumentOutlineFactory`, `GeneratedSectionFactory` to `tests/factories.py`
  - Extend `conftest.py` with a `redis_client` fixture (uses `fakeredis` or real Redis from settings) for `SectionMemoryService` tests
  - _Requirements: 4.1, 5.1, 11.1_

- [x] 14. Checkpoint — ensure all tests pass
  - Run `pytest` and confirm all Phase 2 tests pass with no regressions against existing thesis app tests
  - Ensure `python manage.py makemigrations --check` reports no pending migrations
  - Ask the user if any questions arise before proceeding

- [x] 15. Wire up Celery Beat cleanup task for `GenerationJob` uploads
  - Add a Celery Beat schedule entry in `config/celery.py` for `generation.tasks.cleanup_old_generation_uploads` running hourly
  - Implement `cleanup_old_generation_uploads` in `generation/tasks.py`: deletes `input_file` from disk for `GenerationJob` records where `created_at < now() - 24h` and job is COMPLETED or FAILED
  - _Requirements: 1.7_

- [x] 16. Final checkpoint — full pipeline smoke test
  - Write one integration test in `tests/test_generation_pipeline.py` that runs the full Phase 2 pipeline (Stages 1–6) with mocked Claude responses against a real PostgreSQL + Redis test instance
  - Verify: `GenerationJob` transitions through PENDING → ANALYSING → AWAITING_OUTLINE_REVIEW → PROCESSING → COMPLETED; `AssignmentBrief`, `RubricProfile`, `DocumentOutline`, and `GeneratedSection` records are all created; `SectionMemory` is deleted on completion
  - Ensure all tests pass, ask the user if questions arise.

---

## Notes

- Tasks marked with `*` are optional and can be deferred to a later iteration
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation at natural breaks
- Property tests use `hypothesis` (already in `requirements.txt`) with `@pytest.mark.property` and `@settings(max_examples=100)`
- Phase 3 components (Humanization Engine, Academic Reviewer Agent, Coherence Pass, Export) are intentionally absent — `STAGE_WEIGHTS` in the orchestrator reserves slots 75–100 for those stages
- After completing all tasks, run: `python manage.py makemigrations && python manage.py migrate && pytest && docker compose up -d --build`
