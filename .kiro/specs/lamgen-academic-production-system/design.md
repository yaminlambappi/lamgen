# Design Document: LamGen Academic Production System

## Overview

LamGen Academic Production System is a deep upgrade to the existing Universal Thesis Generator. It transforms the current single-pass LLM pipeline into a ten-stage, rubric-aware academic production system capable of delivering professional-grade assignment outputs for freelance academic writing workflows.

The system is built on the existing Django 4.2 / Celery 5.3 / Redis 7 / PostgreSQL 15 stack. The upgrade introduces a new `generation` Django app that owns all new models, tasks, services, and views. The existing `thesis` app is retained for backward compatibility but new submissions flow through the `generation` app exclusively.

The primary LLM is Anthropic Claude (Sonnet by default, Opus configurable). All generation, review, and coherence work is performed via the Anthropic Messages API with structured role-based prompting. The system is designed for quality of output over generation speed.

### Key Design Goals

- Every generated section is grounded in the actual assignment document — no hallucinated facts.
- Cross-section coherence is maintained via a Redis-backed Section Memory object passed through all pipeline stages.
- Output reads as naturally written academic prose via a dedicated Humanization Engine and Anti-Repetition Engine.
- A final Academic Reviewer Agent evaluates and rewrites weak sections before export.
- The freelancing workflow gives the operator review checkpoints at brief extraction and outline approval before committing to full generation.

---

## Architecture

The system follows the existing service-oriented monolith pattern. The new `generation` app slots into the existing architecture without replacing it.

```
Browser
  │
  ▼
Nginx (reverse proxy)
  │
  ▼
Gunicorn ── Django
              │
    ┌─────────┴──────────────────────────────────┐
    │  Apps                                       │
    │  ├── accounts  (auth, unchanged)            │
    │  ├── thesis    (legacy, unchanged)          │
    │  ├── dashboard (updated to show new jobs)   │
    │  └── generation (new — core of this spec)   │
    └─────────────────────────────────────────────┘
              │
              ▼
         Redis ◄──── Celery Worker
                          │
              ┌───────────┴──────────────────────────────┐
              │  generation.services                      │
              │  ├── DocumentParserService                │
              │  ├── AssignmentIntelligenceEngine         │
              │  ├── SectionMemoryService                 │
              │  ├── GenerationPipelineOrchestrator       │
              │  ├── HumanizationEngine                   │
              │  ├── AcademicReviewerAgent                │
              │  ├── CoherencePassService                 │
              │  ├── ClaudeService                        │
              │  └── ExportService                        │
              └──────────────────────────────────────────┘
              │
              ▼
         PostgreSQL (persistent data)
              │
              ▼
         media/outputs/ (DOCX + PDF files)
```

### Celery Task Architecture

The ten pipeline stages map to a single Celery task chain. Each stage is a discrete Python function called sequentially within `run_generation_pipeline`. This keeps the pipeline as one Celery task (for simple retry and failure handling) while maintaining clean stage separation internally.

```
run_generation_pipeline(job_id)
  │
  ├── Stage 1:  instruction_analysis(job)
  ├── Stage 2:  rubric_extraction(job, brief)
  ├── Stage 3:  outline_generation(job, brief)
  │             ── PAUSE: user reviews outline ──
  ├── Stage 4:  section_planning(job, outline)
  ├── Stage 5:  research_context_preparation(job, brief, outline)
  ├── Stage 6:  section_by_section_generation(job, brief, outline, memory)
  ├── Stage 7:  humanization_pass(job, sections, memory)
  ├── Stage 8:  academic_reviewer_pass(job, sections, brief, memory)
  ├── Stage 9:  coherence_pass(job, sections, memory)
  └── Stage 10: export_formatting(job, sections, brief)
```

The pipeline pauses after Stage 3 (Outline Generation) to allow the user to review and optionally edit the outline. A second Celery task `continue_generation_pipeline` resumes from Stage 4 when the user confirms the outline.

### Workflow State Machine

```
PENDING
  │  (user submits brief / uploads document)
  ▼
ANALYSING
  │  (Assignment Intelligence Engine runs)
  ▼
AWAITING_OUTLINE_REVIEW
  │  (user reviews and confirms outline)
  ▼
PROCESSING
  │  (stages 4–10 run)
  ▼
COMPLETED  ──or──  FAILED
```

---

## Components and Interfaces

### 1. DocumentParserService

Responsible for extracting raw text from uploaded PDF and DOCX files.

```python
class DocumentParserService:
    def parse(self, file_path: str, mime_type: str) -> str:
        """Returns cleaned, normalised plain text from the document."""

    def _parse_pdf(self, file_path: str) -> str:
        """Uses PyMuPDF (fitz) to extract text preserving paragraph boundaries."""

    def _parse_docx(self, file_path: str) -> str:
        """Uses python-docx to extract paragraphs and headings in order."""

    def _clean_text(self, raw: str) -> str:
        """Removes non-printable chars, normalises whitespace, collapses blank lines."""

    def chunk_text(self, text: str, max_tokens: int = 3000) -> list[str]:
        """Splits text into token-bounded chunks using tiktoken cl100k_base."""
```

### 2. AssignmentIntelligenceEngine

Analyses extracted document text and produces a structured `AssignmentBrief`.

```python
class AssignmentIntelligenceEngine:
    def analyse(self, text_chunks: list[str], job: GenerationJob) -> AssignmentBrief:
        """Runs the full analysis pipeline and persists the AssignmentBrief."""

    def _build_analysis_prompt(self, chunks: list[str]) -> str:
        """Constructs the structured extraction prompt for Claude."""

    def _parse_brief_response(self, response: str) -> dict:
        """Parses Claude's JSON response into AssignmentBrief field values."""
```

The engine calls Claude once with all document chunks (up to the context limit) and instructs it to return a structured JSON object containing all `AssignmentBrief` fields. The response is validated and persisted.

### 3. SectionMemoryService

Manages the Redis-backed cross-section context object.

```python
class SectionMemoryService:
    TTL_SECONDS = 14400  # 4 hours

    def initialise(self, job_id: str) -> SectionMemory:
        """Creates a new empty SectionMemory and stores it in Redis."""

    def get(self, job_id: str) -> SectionMemory:
        """Retrieves and deserialises the SectionMemory for a job."""

    def update(self, job_id: str, section_update: SectionUpdate) -> None:
        """Merges a section's output into the existing SectionMemory and re-saves."""

    def delete(self, job_id: str) -> None:
        """Removes the SectionMemory key from Redis."""
```

The `SectionMemory` object is serialised as JSON and stored under the key `section_memory:{job_id}`.

### 4. ClaudeService

Wraps the Anthropic SDK with retry logic, token logging, and prompt construction helpers.

```python
class ClaudeService:
    MAX_RETRIES = 3
    BACKOFF_BASE = 2  # seconds

    def call(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        job: GenerationJob,
        stage_label: str,
    ) -> str:
        """Calls the Anthropic Messages API with retry/backoff. Logs token usage."""

    def _build_system_prompt(
        self,
        brief: AssignmentBrief,
        memory: SectionMemory | None,
    ) -> str:
        """Injects AssignmentBrief and SectionMemory into the system prompt."""
```

Model variant is read from `settings.CLAUDE_MODEL` (default: `claude-sonnet-4-5`). Max output tokens per call is configurable per stage, capped at 16,000.

### 5. GenerationPipelineOrchestrator

Coordinates the ten pipeline stages, updates job progress, and handles failures.

```python
class GenerationPipelineOrchestrator:
    STAGE_WEIGHTS = {
        'instruction_analysis': 5,
        'rubric_extraction': 10,
        'outline_generation': 15,
        'section_planning': 20,
        'research_context_preparation': 25,
        'section_generation': 60,  # spread across sections
        'humanization_pass': 75,
        'academic_reviewer_pass': 85,
        'coherence_pass': 92,
        'export_formatting': 100,
    }

    def update_progress(self, job: GenerationJob, stage: str) -> None:
        """Writes stage name and percentage to Redis and updates the DB record."""

    def fail_job(self, job: GenerationJob, stage: str, error: str) -> None:
        """Sets job status to FAILED, records error, stops pipeline."""
```

### 6. HumanizationEngine

Rewrites generated sections to vary sentence structure, paragraph length, and vocabulary.

```python
class HumanizationEngine:
    def humanize(
        self,
        sections: list[GeneratedSection],
        brief: AssignmentBrief,
        memory: SectionMemory,
    ) -> list[GeneratedSection]:
        """Applies humanization and anti-repetition passes to all sections."""

    def _build_humanization_prompt(
        self,
        section: GeneratedSection,
        tone: str,
    ) -> str:
        """Constructs the humanization instruction prompt for Claude."""
```

The humanization prompt instructs Claude to vary sentence syntax, adjust paragraph lengths so adjacent paragraphs differ by at least 20% in word count, replace repeated transition phrases (>2 occurrences per section), and replace repeated non-technical vocabulary (>3 occurrences per 200-word window). The prompt explicitly forbids introducing new facts or citations.

### 7. AcademicReviewerAgent

Evaluates each section against the Rubric Profile and rewrites sections that fall below threshold.

```python
class AcademicReviewerAgent:
    PASSING_THRESHOLD = 0.65  # 65% of available marks per criterion

    def review(
        self,
        sections: list[GeneratedSection],
        brief: AssignmentBrief,
        memory: SectionMemory,
        job: GenerationJob,
    ) -> list[GeneratedSection]:
        """Reviews all sections, rewrites failing ones, logs scores to job."""

    def _score_section(
        self,
        section: GeneratedSection,
        rubric: RubricProfile,
    ) -> dict[str, float]:
        """Returns per-criterion quality scores from Claude's evaluation response."""
```

The reviewer prompt instructs Claude to act as a strict postgraduate marker, score each rubric criterion, identify weaknesses (robotic phrasing, shallow analysis, unsupported assertions, missing organisational context), and rewrite the section if any criterion falls below threshold.

### 8. CoherencePassService

Reads the complete assembled draft and corrects cross-section inconsistencies.

```python
class CoherencePassService:
    def run(
        self,
        sections: list[GeneratedSection],
        brief: AssignmentBrief,
        outline: DocumentOutline,
        memory: SectionMemory,
        job: GenerationJob,
    ) -> list[GeneratedSection]:
        """Runs terminology unification, scope/conclusion alignment, missing section check."""
```

If a section listed in the outline is missing from the assembled draft, the coherence pass generates it using the `AssignmentBrief` and `SectionMemory` before proceeding to export.

### 9. ExportService

Produces the DOCX and PDF Export Package.

```python
class ExportService:
    def export(
        self,
        sections: list[GeneratedSection],
        brief: AssignmentBrief,
        job: GenerationJob,
    ) -> ExportPackage:
        """Generates DOCX with python-docx and PDF with WeasyPrint. Returns file paths."""

    def _build_docx(
        self,
        sections: list[GeneratedSection],
        brief: AssignmentBrief,
    ) -> str:
        """Builds the DOCX file. Returns file path."""

    def _render_pdf(self, docx_path: str, brief: AssignmentBrief) -> str:
        """Renders PDF from HTML intermediate using WeasyPrint. Returns file path."""
```

The DOCX is built with `python-docx`: title page, auto-TOC, Heading 1/2 styles, Times New Roman 12pt, 1.5 line spacing, and a references section formatted per the citation style in the `AssignmentBrief`. The PDF is rendered by converting the DOCX content to styled HTML and passing it to WeasyPrint.

---

## Data Models

All new models live in the `generation` app.

### GenerationJob

Replaces `ThesisRequest` for new submissions. Tracks the full lifecycle of one generation run.

```python
class GenerationJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING'
        ANALYSING = 'ANALYSING'
        AWAITING_OUTLINE_REVIEW = 'AWAITING_OUTLINE_REVIEW'
        PROCESSING = 'PROCESSING'
        COMPLETED = 'COMPLETED'
        FAILED = 'FAILED'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generation_jobs',
    )
    title = models.CharField(max_length=500)
    input_file = models.FileField(upload_to='uploads/', blank=True)
    prompt_text = models.TextField(blank=True)  # alternative to file upload
    target_word_count = models.PositiveIntegerField(default=3000)
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    current_stage = models.CharField(max_length=100, blank=True)
    progress_percentage = models.PositiveSmallIntegerField(default=0)
    output_docx = models.FileField(upload_to='outputs/', blank=True)
    output_pdf = models.FileField(upload_to='outputs/', blank=True)
    generated_word_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    total_input_tokens = models.PositiveIntegerField(default=0)
    total_output_tokens = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
```

### AssignmentBrief

Persisted output of the Assignment Intelligence Engine.

```python
class AssignmentBrief(models.Model):
    class AssignmentType(models.TextChoices):
        ESSAY = 'essay'
        REPORT = 'report'
        CASE_STUDY = 'case_study'
        LITERATURE_REVIEW = 'literature_review'
        THESIS_CHAPTER = 'thesis_chapter'
        OTHER = 'other'

    class AcademicLevel(models.TextChoices):
        UNDERGRADUATE = 'undergraduate'
        POSTGRADUATE = 'postgraduate'
        DOCTORAL = 'doctoral'

    class WritingTone(models.TextChoices):
        CRITICAL_ANALYTICAL = 'critical_analytical'
        DESCRIPTIVE_EXPLANATORY = 'descriptive_explanatory'
        REFLECTIVE = 'reflective'
        PROFESSIONAL_REPORT = 'professional_report'

    job = models.OneToOneField(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='brief',
    )
    topic = models.TextField()
    subject_area = models.CharField(max_length=255)
    assignment_type = models.CharField(max_length=30, choices=AssignmentType.choices)
    academic_level = models.CharField(max_length=20, choices=AcademicLevel.choices)
    academic_level_inferred = models.BooleanField(default=False)
    required_sections = models.JSONField(default=list)  # list of section title strings
    citation_style = models.CharField(max_length=50)
    formatting_instructions = models.TextField(blank=True)
    required_frameworks = models.JSONField(default=list)
    writing_tone = models.CharField(max_length=30, choices=WritingTone.choices)
    organisational_context = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### RubricProfile

Extracted marking rubric, linked to an `AssignmentBrief`.

```python
class RubricProfile(models.Model):
    brief = models.OneToOneField(
        AssignmentBrief,
        on_delete=models.CASCADE,
        related_name='rubric',
    )
    criteria = models.JSONField(default=list)
    # criteria schema: [{"name": str, "weight": float, "distinction_descriptor": str}]
    created_at = models.DateTimeField(auto_now_add=True)
```

### DocumentOutline

The structured outline produced by Stage 3, editable by the user before generation proceeds.

```python
class DocumentOutline(models.Model):
    job = models.OneToOneField(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='outline',
    )
    sections = models.JSONField(default=list)
    # sections schema: [{"title": str, "target_word_count": int, "key_points": [str]}]
    user_confirmed = models.BooleanField(default=False)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### GeneratedSection

One section of the generated document, updated through the pipeline stages.

```python
class GeneratedSection(models.Model):
    job = models.ForeignKey(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='sections',
    )
    order = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    content = models.TextField()
    word_count = models.PositiveIntegerField(default=0)
    humanized = models.BooleanField(default=False)
    reviewer_score = models.JSONField(null=True, blank=True)
    # reviewer_score schema: {"criterion_name": float, ...}
    rewritten_by_reviewer = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']
        unique_together = [('job', 'order')]
```

### ReviewLog

Records the Academic Reviewer Agent's per-section evaluation for cost monitoring and audit.

```python
class ReviewLog(models.Model):
    job = models.ForeignKey(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='review_logs',
    )
    section = models.ForeignKey(
        GeneratedSection,
        on_delete=models.CASCADE,
        related_name='review_logs',
    )
    scores = models.JSONField()
    weaknesses_detected = models.JSONField(default=list)
    rewritten = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
```

### TokenUsageLog

Records per-API-call token consumption for cost monitoring.

```python
class TokenUsageLog(models.Model):
    job = models.ForeignKey(
        GenerationJob,
        on_delete=models.CASCADE,
        related_name='token_logs',
    )
    stage = models.CharField(max_length=100)
    input_tokens = models.PositiveIntegerField()
    output_tokens = models.PositiveIntegerField()
    model = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
```

### SectionMemory (Redis, not a DB model)

Stored in Redis as JSON under `section_memory:{job_id}`. Not a Django model.

```python
@dataclass
class SectionMemory:
    job_id: str
    thesis_argument: str
    terminology: dict[str, str]       # term -> definition/usage
    citations_used: list[str]         # list of citation keys/strings
    analytical_positions: list[str]   # key claims made so far
    concepts_discussed: list[str]     # concepts introduced per section
    section_summaries: list[dict]     # [{"title": str, "summary": str}]
```

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property 1: Upload validation rejects invalid files

*For any* file upload, the validator SHALL accept the file if and only if the actual MIME type (determined by byte-level inspection) is `application/pdf` or `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, AND the file size is at most 20 MB. Files that fail either check SHALL be rejected with a descriptive error message.

**Validates: Requirements 1.1, 1.2, 1.4, 1.5**

---

### Property 2: Prompt length validation

*For any* plain-text prompt string, the validator SHALL accept it if and only if its length is between 50 and 10,000 characters (inclusive). Strings outside this range SHALL be rejected.

**Validates: Requirements 1.3**

---

### Property 3: Document text extraction preserves content

*For any* valid PDF or DOCX file with known text content, extracting the text using `DocumentParserService.parse()` SHALL return a string that contains all readable text from the document, with paragraph boundaries preserved and non-printable characters removed.

**Validates: Requirements 1.6, 13.1, 13.2**

---

### Property 4: Text cleaning removes noise

*For any* string containing non-printable characters, irregular whitespace, or repeated blank lines, `DocumentParserService._clean_text()` SHALL return a string with no non-printable characters, normalised whitespace, and no consecutive blank lines.

**Validates: Requirements 13.3**

---

### Property 5: AssignmentBrief round-trip

*For any* valid `AssignmentBrief` object, serialising it to JSON and then deserialising it SHALL produce an object that is field-for-field equivalent to the original.

**Validates: Requirements 13.4**

---

### Property 6: Minimum content threshold

*For any* document that produces fewer than 100 characters of readable content after extraction and cleaning, the system SHALL reject the document. For any document that produces 100 or more characters, the system SHALL accept it for pipeline processing.

**Validates: Requirements 13.5**

---

### Property 7: Chunk size invariant

*For any* text string of any length, every chunk produced by `DocumentParserService.chunk_text()` SHALL contain at most 3,000 tokens when measured using the `cl100k_base` tiktoken encoding.

**Validates: Requirements 13.6**

---

### Property 8: Assignment Brief extraction completeness

*For any* document text that contains clearly stated assignment metadata, the `AssignmentIntelligenceEngine.analyse()` SHALL produce an `AssignmentBrief` with all required fields populated (topic, subject_area, assignment_type, academic_level, required_sections, citation_style, writing_tone), and the brief SHALL be persisted to the database before the pipeline proceeds.

**Validates: Requirements 2.1, 2.2, 2.3, 2.8**

---

### Property 9: Section Memory initialisation and TTL

*For any* `GenerationJob`, after `SectionMemoryService.initialise()` is called, the Redis key `section_memory:{job_id}` SHALL exist and SHALL have a TTL between 14,000 and 14,400 seconds (approximately 4 hours).

**Validates: Requirements 4.1, 4.4**

---

### Property 10: Section Memory update accumulates without duplicates

*For any* sequence of sections processed during a generation job, after each section update the `SectionMemory.citations_used` list SHALL contain all citations from all processed sections with no duplicate entries.

**Validates: Requirements 4.2, 4.6, 8.5**

---

### Property 11: Section Memory injected into every generation prompt

*For any* `SectionMemory` state and any section generation call, the constructed system prompt SHALL contain the Section_Memory's thesis argument, terminology, and analytical positions.

**Validates: Requirements 4.3, 10.4**

---

### Property 12: Section Memory deleted on job completion or failure

*For any* `GenerationJob` that transitions to COMPLETED or FAILED status, the Redis key `section_memory:{job_id}` SHALL no longer exist after the transition.

**Validates: Requirements 4.5**

---

### Property 13: Pipeline progress is monotonically increasing

*For any* pipeline run, the progress percentage recorded after each stage transition SHALL be strictly greater than the percentage recorded after the previous stage transition, and the final stage SHALL record exactly 100%.

**Validates: Requirements 5.2, 11.5**

---

### Property 14: Pipeline failure stops execution and records error

*For any* pipeline stage that raises an exception, the `GenerationJob` status SHALL be set to FAILED, the error message SHALL be recorded, and no subsequent pipeline stages SHALL execute.

**Validates: Requirements 5.3**

---

### Property 15: Humanization preserves citations

*For any* generated section containing citation references, after the humanization pass all citation references present in the input SHALL still be present in the humanized output.

**Validates: Requirements 6.6**

---

### Property 16: Anti-repetition transition phrase limit

*For any* humanized section, no transition phrase SHALL appear more than twice within that section.

**Validates: Requirements 6.3**

---

### Property 17: Anti-repetition vocabulary cluster limit

*For any* humanized section, no non-technical word SHALL appear more than three times within any 200-word window.

**Validates: Requirements 6.4**

---

### Property 18: Reviewer scores all rubric criteria and logs results

*For any* section reviewed by the `AcademicReviewerAgent` against a `RubricProfile` with N criteria, the reviewer SHALL assign a score for every one of the N criteria, and a `ReviewLog` record SHALL be created for that section against the `GenerationJob`.

**Validates: Requirements 7.1, 7.6**

---

### Property 19: Reviewer rewrites sections below threshold

*For any* section where any rubric criterion score is below the passing threshold (0.65), the `AcademicReviewerAgent` SHALL produce a rewritten version of that section.

**Validates: Requirements 7.2**

---

### Property 20: Coherence pass ensures all outline sections are present

*For any* `DocumentOutline` with N sections, after the coherence pass the assembled draft SHALL contain all N sections. If any section was missing before the coherence pass, it SHALL be generated during the pass.

**Validates: Requirements 8.3, 8.4**

---

### Property 21: Export package completeness

*For any* `GenerationJob` that reaches the export stage, the `ExportService` SHALL produce both a DOCX file and a PDF file, both stored in `media/outputs/`, and the `GenerationJob` record SHALL be updated with both file paths.

**Validates: Requirements 9.1, 9.5**

---

### Property 22: DOCX structural completeness

*For any* generated DOCX file, parsing it with `python-docx` SHALL reveal: at least one paragraph styled as a title page, a table of contents, at least one paragraph styled as Heading 1, body text in Times New Roman 12pt, and a references section.

**Validates: Requirements 9.2**

---

### Property 23: Claude API calls use role-based prompting with context injection

*For any* call to `ClaudeService.call()`, the Anthropic API request SHALL contain a non-empty `system` prompt that includes the academic expert persona, the `AssignmentBrief` fields, and (when provided) the `SectionMemory` context.

**Validates: Requirements 10.3, 10.4**

---

### Property 24: Claude API retry with exponential backoff

*For any* sequence of Anthropic API call failures, the `ClaudeService` SHALL retry up to 3 times with delays of 2s, 4s, and 8s respectively before marking the stage as failed.

**Validates: Requirements 10.5**

---

### Property 25: Token usage logged for every API call

*For any* successful `ClaudeService.call()`, a `TokenUsageLog` record SHALL be created for the associated `GenerationJob` containing the input token count, output token count, model name, and stage label.

**Validates: Requirements 10.7**

---

### Property 26: Generation Job creation invariant

*For any* new `GenerationJob`, the job SHALL have a UUID primary key that is unique across all jobs, and its initial status SHALL be PENDING.

**Validates: Requirements 11.1**

---

### Property 27: Progress polling endpoint contract

*For any* `GenerationJob` in PROCESSING status, a GET request to the polling endpoint SHALL return a JSON response containing `stage` (string), `progress_percentage` (integer 0–100), and `status` (string) fields.

**Validates: Requirements 11.4**

---

### Property 28: Job deletion removes all associated data

*For any* `GenerationJob` deletion request from the owning user, the system SHALL remove the database record, both output files from disk (if they exist), and the `section_memory:{job_id}` key from Redis.

**Validates: Requirements 11.6**

---

### Property 29: Authorization — users can only access their own jobs

*For any* authenticated user attempting to view, download, or delete a `GenerationJob` that belongs to a different user, the system SHALL return HTTP 403.

**Validates: Requirements 11.7**

---

### Property 30: Target word count validation

*For any* job submission, the system SHALL accept a target word count if and only if it is between 500 and 15,000 (inclusive). Values outside this range SHALL be rejected with a validation error.

**Validates: Requirements 12.4**

---

## Error Handling

### LLM API Failures

`ClaudeService` wraps every API call in a retry loop (max 3 attempts, exponential backoff: 2s, 4s, 8s). On the third failure, it raises a `ClaudeAPIError` which the pipeline orchestrator catches, calls `fail_job()`, and stops execution. The error message includes the stage name, attempt count, and the original exception message.

### Pipeline Stage Failures

Every pipeline stage function is wrapped in a try/except block inside `run_generation_pipeline`. Any unhandled exception triggers `GenerationPipelineOrchestrator.fail_job()`, which:
1. Sets `GenerationJob.status = FAILED`
2. Writes the error message to `GenerationJob.error_message`
3. Deletes the `SectionMemory` key from Redis
4. Returns without calling subsequent stages

### Document Parsing Failures

`DocumentParserService.parse()` raises `DocumentParseError` if:
- The file cannot be opened (corrupt file)
- Extraction produces fewer than 100 characters of readable content
- An unsupported MIME type is passed

The view layer catches `DocumentParseError` and returns a user-facing error message without creating a `GenerationJob`.

### Assignment Intelligence Engine Failures

If Claude returns a malformed JSON response for the brief extraction, `AssignmentIntelligenceEngine._parse_brief_response()` raises `BriefExtractionError`. The pipeline catches this and fails the job at the ANALYSING stage.

### Export Failures

`ExportService.export()` raises `ExportError` if DOCX generation or PDF rendering fails. The pipeline catches this, fails the job at the export stage, and records the error. Partially written output files are deleted.

### Outline Review Timeout

If the user does not confirm the outline within 24 hours, a Celery Beat task marks the job as FAILED with the message "Outline review timed out". The `SectionMemory` key is deleted.

### Redis Unavailability

If Redis is unavailable when reading or writing `SectionMemory`, the service raises `SectionMemoryError`. The pipeline treats this as a stage failure and fails the job. Progress updates that fail to write to Redis are logged as warnings but do not fail the pipeline (the DB record is the authoritative progress source).

---

## Testing Strategy

### Overview

The test suite uses `pytest-django` with `factory-boy` for fixtures and `hypothesis` for property-based tests. The existing `conftest.py` and `pytest.ini` are extended for the new `generation` app.

### Unit Tests

Unit tests cover specific examples, edge cases, and error conditions for each service class. They use mocks for external dependencies (Anthropic API, Redis, file system).

Key unit test areas:
- `DocumentParserService`: PDF extraction, DOCX extraction, text cleaning, chunking
- `AssignmentIntelligenceEngine`: prompt construction, JSON response parsing, brief persistence
- `SectionMemoryService`: initialise, get, update, delete, TTL verification
- `ClaudeService`: retry logic, backoff timing, token logging, prompt construction
- `HumanizationEngine`: citation preservation, prompt construction
- `AcademicReviewerAgent`: score parsing, rewrite triggering, log creation
- `ExportService`: DOCX structure verification, file path recording
- Views: authorization (403 for cross-user access), polling endpoint response shape

### Property-Based Tests

Property-based tests use `hypothesis` (already in `requirements.txt`) with a minimum of 100 examples per property. Each test is tagged with a comment referencing the design property.

```python
# Feature: lamgen-academic-production-system, Property 7: Chunk size invariant
@given(st.text(min_size=0, max_size=50000))
@settings(max_examples=100)
def test_chunk_size_invariant(text):
    chunks = DocumentParserService().chunk_text(text)
    enc = tiktoken.get_encoding("cl100k_base")
    for chunk in chunks:
        assert len(enc.encode(chunk)) <= 3000
```

Properties covered by hypothesis tests:
- Property 1: Upload validation (file size + MIME type)
- Property 2: Prompt length validation
- Property 4: Text cleaning removes noise
- Property 5: AssignmentBrief round-trip (JSON serialisation)
- Property 6: Minimum content threshold
- Property 7: Chunk size invariant
- Property 10: Section Memory citation deduplication
- Property 13: Pipeline progress monotonically increasing (mocked stages)
- Property 16: Anti-repetition transition phrase limit
- Property 17: Anti-repetition vocabulary cluster limit
- Property 26: Job creation UUID uniqueness
- Property 29: Authorization — cross-user access returns 403
- Property 30: Target word count validation

### Integration Tests

Integration tests run against a real PostgreSQL and Redis instance (available in the Docker Compose test environment). They cover:
- Full pipeline execution with a small test document (mocked Claude responses)
- Outline review pause/resume flow
- Export package file creation and retrieval
- Celery task registration and execution
- Cleanup task (file purge after 24 hours)
- Dashboard pagination with varying job counts

### Smoke Tests

Smoke tests verify one-time configuration:
- Claude API key is configured and the client initialises without error
- Celery worker discovers the `generation` tasks
- Redis connection is available
- PostgreSQL migrations are applied

### Test Configuration

```ini
# pytest.ini additions
[pytest]
DJANGO_SETTINGS_MODULE = config.settings
addopts = --cov=generation --cov-fail-under=80
```

Property tests are tagged with `@pytest.mark.property` and can be run in isolation:

```bash
pytest -m property --hypothesis-seed=0
```
