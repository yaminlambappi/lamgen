# Requirements Document

## Introduction

LamGen Academic Production System is an upgrade to the existing Universal Thesis Generator that transforms it into a high-quality AI academic writing platform designed for professional freelance assignment delivery. The system must produce assignment and thesis outputs that are analytically deep, contextually aware, naturally written, and academically mature — outputs that satisfy university grading expectations and read as the work of a skilled human expert.

The system extends the existing Django/Celery/Redis/PostgreSQL architecture with a dedicated Assignment Intelligence Engine, rubric-aware generation pipeline, humanization layer, cross-section memory, multi-stage generation pipeline, academic reviewer agent, and professional DOCX/PDF export. The primary LLM is Anthropic Claude (Sonnet and Opus). The target is quality of deliverable, not generation speed.

---

## Glossary

- **Assignment_Intelligence_Engine**: The analysis pipeline that extracts structured metadata from uploaded assignment documents before any content is generated.
- **Generation_Pipeline**: The ordered sequence of Celery task stages that produces the final academic document from extracted metadata.
- **Humanization_Engine**: The refinement layer that rewrites generated content to vary sentence structure, cadence, vocabulary, and paragraph size so the output reads as naturally written academic prose.
- **Section_Memory**: The persistent in-memory context object (stored in Redis and passed between pipeline stages) that carries thesis argument, tone, terminology, citation context, and previously discussed concepts across all sections.
- **Academic_Reviewer_Agent**: The final-pass LLM agent that evaluates generated content as a strict postgraduate marker and rewrites weak areas before export.
- **Rubric_Profile**: The structured data object extracted from a marking rubric that maps grading criteria to weightings and quality descriptors.
- **Assignment_Brief**: The structured metadata object produced by the Assignment_Intelligence_Engine, containing topic, subject area, assignment type, academic level, required sections, citation style, and inferred lecturer expectations.
- **Generation_Job**: A single end-to-end execution of the Generation_Pipeline for one user submission, tracked as a database record with status and progress.
- **Section**: A discrete, titled unit of academic content (e.g., Introduction, Literature Review, Methodology) within a generated document.
- **Coherence_Pass**: The final pipeline stage that reads the complete assembled draft and corrects cross-section inconsistencies, terminology drift, and structural gaps.
- **Export_Package**: The final deliverable produced by the system, consisting of a formatted DOCX file and a formatted PDF file.
- **Anti_Repetition_Engine**: The sub-component of the Humanization_Engine that detects and eliminates repeated sentence patterns, transition phrases, and vocabulary clusters.
- **System**: The LamGen Academic Production System as a whole.
- **User**: An authenticated operator of the System (freelance academic writer or administrator).

---

## Requirements

### Requirement 1: Assignment Document Ingestion

**User Story:** As a User, I want to upload assignment PDFs, thesis guidelines, marking rubrics, sample reports, or paste a direct assignment prompt, so that the System can extract all necessary context before generating any content.

#### Acceptance Criteria

1. THE System SHALL accept file uploads in PDF and DOCX formats with a maximum size of 20 MB per file.
2. WHEN a file is uploaded, THE System SHALL validate the actual MIME type of the file using byte-level inspection before accepting it.
3. THE System SHALL accept a plain-text assignment prompt as an alternative to a file upload, with a minimum length of 50 characters and a maximum length of 10,000 characters.
4. IF a submitted file fails MIME type validation, THEN THE System SHALL reject the upload and return a descriptive error message identifying the validation failure.
5. IF a submitted file exceeds the 20 MB size limit, THEN THE System SHALL reject the upload and return an error message stating the size limit.
6. WHEN a file is accepted, THE System SHALL extract all readable text content from the document and store it for pipeline processing.
7. THE System SHALL purge uploaded source files from disk within 24 hours of the associated Generation_Job completing or failing.

---

### Requirement 2: Assignment Intelligence Engine

**User Story:** As a User, I want the System to deeply analyse my uploaded assignment before writing anything, so that every generated section is grounded in the actual requirements and grading expectations.

#### Acceptance Criteria

1. WHEN document text is extracted, THE Assignment_Intelligence_Engine SHALL identify and store: assignment topic, subject area, assignment type (essay, report, case study, literature review, thesis chapter, or other), and academic level (undergraduate, postgraduate, doctoral).
2. WHEN document text is extracted, THE Assignment_Intelligence_Engine SHALL identify all required sections and their expected sequence.
3. WHEN a marking rubric is present in the document, THE Assignment_Intelligence_Engine SHALL extract a Rubric_Profile containing each criterion name, its weighting or mark allocation, and the quality descriptors for distinction-level performance.
4. WHEN document text is extracted, THE Assignment_Intelligence_Engine SHALL identify the required citation style (APA, Harvard, Chicago, Vancouver, or other) and any explicit formatting instructions.
5. WHEN document text is extracted, THE Assignment_Intelligence_Engine SHALL identify required theoretical frameworks, models, or named authors that must be engaged with.
6. WHEN document text is extracted, THE Assignment_Intelligence_Engine SHALL infer the expected writing tone (critical-analytical, descriptive-explanatory, reflective, or professional-report) based on assignment type and academic level.
7. WHEN document text is extracted, THE Assignment_Intelligence_Engine SHALL extract the business or organisational context described in the assignment, if present.
8. WHEN document text is extracted, THE Assignment_Intelligence_Engine SHALL produce a structured Assignment_Brief object and persist it to the database before the Generation_Pipeline begins.
9. IF the Assignment_Intelligence_Engine cannot determine the academic level from the document, THEN THE System SHALL default to postgraduate level and record the inference as uncertain in the Assignment_Brief.
10. THE Assignment_Intelligence_Engine SHALL complete its analysis within 120 seconds for documents up to 20 MB.

---

### Requirement 3: Rubric-Aware Generation

**User Story:** As a User, I want the generated content to be optimised against the marking rubric criteria, so that the output targets the highest available marks for each graded dimension.

#### Acceptance Criteria

1. WHEN a Rubric_Profile is present in the Assignment_Brief, THE Generation_Pipeline SHALL weight its generation prompts to emphasise the criteria with the highest mark allocations.
2. WHEN the Rubric_Profile identifies critical analysis as a graded criterion, THE Generation_Pipeline SHALL produce analytical content that evaluates competing perspectives, identifies limitations, and draws evidence-based conclusions rather than descriptive summaries.
3. WHEN the Rubric_Profile identifies organisational context application as a graded criterion, THE Generation_Pipeline SHALL integrate the business or organisational context from the Assignment_Brief into the analysis of each relevant section.
4. WHEN the Rubric_Profile identifies research depth as a graded criterion, THE Generation_Pipeline SHALL reference multiple theoretical positions and acknowledge areas of scholarly debate.
5. WHEN no Rubric_Profile is present, THE Generation_Pipeline SHALL apply postgraduate-level critical analysis standards as the default quality target.
6. THE Generation_Pipeline SHALL include the Rubric_Profile criteria in the prompt context for every section generation call.

---

### Requirement 4: Section Memory

**User Story:** As a User, I want the generated document to read as a coherent whole, so that arguments, terminology, and analytical positions are consistent from the first section to the last.

#### Acceptance Criteria

1. THE System SHALL initialise a Section_Memory object at the start of each Generation_Job and pass it to every subsequent pipeline stage.
2. WHEN a section is generated, THE System SHALL update the Section_Memory with: the core thesis argument established in that section, key terminology introduced, citation references used, analytical positions taken, and concepts discussed.
3. WHILE a Generation_Job is active, THE System SHALL inject the current Section_Memory context into the prompt for each new section generation call.
4. THE System SHALL store the Section_Memory object in Redis with a TTL of 4 hours, keyed by Generation_Job identifier.
5. WHEN the Generation_Job completes or fails, THE System SHALL delete the Section_Memory key from Redis.
6. THE Section_Memory SHALL maintain a running list of all citations used across sections to prevent duplicate reference entries in the final bibliography.

---

### Requirement 5: Multi-Stage Generation Pipeline

**User Story:** As a User, I want the system to follow a structured, multi-stage writing process, so that the final output is planned, drafted, refined, reviewed, and formatted before delivery.

#### Acceptance Criteria

1. THE Generation_Pipeline SHALL execute the following stages in order: (1) Instruction Analysis, (2) Rubric Extraction, (3) Outline Generation, (4) Section Planning, (5) Research Context Preparation, (6) Section-by-Section Generation, (7) Humanization Pass, (8) Academic Reviewer Pass, (9) Coherence Pass, (10) Export Formatting.
2. WHEN a pipeline stage completes, THE System SHALL update the Generation_Job progress record in Redis with the completed stage name and a percentage value.
3. IF any pipeline stage fails, THEN THE System SHALL record the failure reason against the Generation_Job, set the job status to FAILED, and stop pipeline execution without proceeding to subsequent stages.
4. THE System SHALL execute the Generation_Pipeline as an asynchronous Celery task so that the web process is not blocked during generation.
5. WHEN the Section-by-Section Generation stage runs, THE System SHALL generate each section as a separate LLM call, injecting the Assignment_Brief, Rubric_Profile, Section_Memory, and section-specific instructions into each call.
6. THE Outline Generation stage SHALL produce a structured document outline with section titles, target word counts per section, and key points to address, before any section content is written.
7. THE Research Context Preparation stage SHALL identify and list the key theoretical frameworks, authors, and concepts that must be engaged with in each section, based on the Assignment_Brief.

---

### Requirement 6: Humanization Engine

**User Story:** As a User, I want the generated text to read as naturally written academic prose, so that the output does not exhibit the mechanical patterns associated with AI-generated content.

#### Acceptance Criteria

1. WHEN the Humanization Pass stage runs, THE Humanization_Engine SHALL process every generated section and apply sentence structure variation so that no more than two consecutive sentences share the same syntactic pattern.
2. WHEN the Humanization Pass stage runs, THE Humanization_Engine SHALL vary paragraph length across each section so that paragraph word counts differ by at least 20% between adjacent paragraphs.
3. WHEN the Humanization Pass stage runs, THE Anti_Repetition_Engine SHALL detect and replace transition phrases that appear more than twice within any single section.
4. WHEN the Humanization Pass stage runs, THE Anti_Repetition_Engine SHALL detect and replace vocabulary clusters where the same non-technical word appears more than three times within any 200-word window.
5. WHEN the Humanization Pass stage runs, THE Humanization_Engine SHALL apply discipline-specific academic tone modulation based on the writing tone identified in the Assignment_Brief.
6. THE Humanization_Engine SHALL preserve all factual claims, citations, and analytical positions from the input text during humanization.
7. THE Humanization_Engine SHALL NOT introduce new factual claims, invented citations, or fabricated statistics during the humanization pass.

---

### Requirement 7: Academic Reviewer Agent

**User Story:** As a User, I want a final AI review pass that behaves like a strict postgraduate marker, so that weak sections are identified and rewritten before the document is exported.

#### Acceptance Criteria

1. WHEN the Academic Reviewer Pass stage runs, THE Academic_Reviewer_Agent SHALL evaluate each section against the Rubric_Profile criteria and assign an internal quality score per criterion.
2. WHEN the Academic_Reviewer_Agent assigns a quality score below the passing threshold for any criterion, THE Academic_Reviewer_Agent SHALL rewrite the affected section to address the identified weakness.
3. WHEN the Academic_Reviewer_Agent evaluates a section, THE Academic_Reviewer_Agent SHALL detect and flag: robotic phrasing, shallow descriptive analysis, repetitive sentence structures, unsupported assertions, and generic explanations that lack organisational context.
4. WHEN the Academic_Reviewer_Agent rewrites a section, THE Academic_Reviewer_Agent SHALL preserve the Section_Memory context and maintain consistency with previously generated sections.
5. THE Academic_Reviewer_Agent SHALL complete its review and rewrite pass for a standard 3,000-word document within 180 seconds.
6. WHEN the Academic Reviewer Pass completes, THE System SHALL log the quality scores per criterion and any sections that were rewritten, against the Generation_Job record.

---

### Requirement 8: Coherence Pass

**User Story:** As a User, I want the final document to read as a unified piece of writing, so that there are no cross-section inconsistencies, terminology drift, or structural gaps.

#### Acceptance Criteria

1. WHEN the Coherence Pass stage runs, THE System SHALL read the complete assembled draft and identify terminology inconsistencies where the same concept is referred to by different names across sections.
2. WHEN the Coherence Pass stage runs, THE System SHALL verify that the introduction's stated scope and the conclusion's summary are consistent with the content of the body sections.
3. WHEN the Coherence Pass stage runs, THE System SHALL verify that all sections listed in the document outline were generated and are present in the assembled draft.
4. IF the Coherence Pass identifies a missing section, THEN THE System SHALL generate the missing section using the Assignment_Brief and Section_Memory before proceeding to export.
5. WHEN the Coherence Pass stage runs, THE System SHALL ensure the reference list contains all citations used across all sections with no duplicates.

---

### Requirement 9: Export Quality

**User Story:** As a User, I want to download the completed assignment as a professionally formatted DOCX and PDF, so that the document is ready for client delivery with minimal manual editing.

#### Acceptance Criteria

1. THE System SHALL produce an Export_Package containing both a DOCX file and a PDF file for every completed Generation_Job.
2. THE Export_Package DOCX file SHALL include: a title page with assignment title, submission date, and word count; an auto-generated table of contents with page numbers; section headings formatted as Heading 1 and Heading 2 styles; body text in Times New Roman 12pt with 1.5 line spacing; and a references section formatted according to the citation style in the Assignment_Brief.
3. THE Export_Package PDF file SHALL be rendered from the DOCX content and SHALL match the DOCX formatting including title page, table of contents, headers, and page numbers.
4. THE System SHALL generate the DOCX file using python-docx and the PDF file using WeasyPrint.
5. WHEN the Export_Package is ready, THE System SHALL store both files in the media/outputs/ directory and update the Generation_Job record with the file paths.
6. THE System SHALL serve Export_Package files as secure downloads with Content-Disposition: attachment headers, not as directly accessible media URLs.
7. IF the Export_Package generation fails, THEN THE System SHALL set the Generation_Job status to FAILED and record the export error message.

---

### Requirement 10: Claude-Optimised LLM Architecture

**User Story:** As a User, I want the system to use Anthropic Claude as its primary LLM with structured prompt chaining, so that generation quality is maximised without unnecessary multi-provider complexity.

#### Acceptance Criteria

1. THE System SHALL use Anthropic Claude as the primary LLM provider for all Generation_Pipeline stages.
2. THE System SHALL support configuration of the Claude model variant (Sonnet or Opus) via an environment variable, defaulting to Claude Sonnet.
3. WHEN calling the Anthropic API, THE System SHALL use role-based prompting with a system prompt that establishes the academic expert persona and a user prompt that contains the generation task and context.
4. WHEN calling the Anthropic API, THE System SHALL inject the Section_Memory context and Assignment_Brief into the system prompt for all generation and review calls.
5. IF an Anthropic API call fails, THEN THE System SHALL retry the call up to 3 times with exponential backoff starting at 2 seconds before marking the pipeline stage as failed.
6. THE System SHALL set a per-call token output limit appropriate to the section being generated, with a maximum of 16,000 output tokens per call.
7. THE System SHALL log the token usage (input tokens, output tokens) for each Anthropic API call against the Generation_Job record for cost monitoring.

---

### Requirement 11: Generation Job Management

**User Story:** As a User, I want to track the progress of my generation job in real time and manage my completed jobs, so that I know when my assignment is ready and can access or delete previous work.

#### Acceptance Criteria

1. WHEN a Generation_Job is created, THE System SHALL assign it a unique identifier and set its initial status to PENDING.
2. WHEN the Generation_Pipeline begins processing a job, THE System SHALL set the job status to PROCESSING.
3. WHEN the Generation_Pipeline completes successfully, THE System SHALL set the job status to COMPLETED and record the completion timestamp.
4. WHEN a Generation_Job is in PROCESSING status, THE System SHALL expose a JSON polling endpoint that returns the current pipeline stage name, progress percentage (0–100), and job status.
5. THE System SHALL update the progress percentage at each of the 10 pipeline stage transitions.
6. WHEN a User requests deletion of a Generation_Job, THE System SHALL delete the database record, the Export_Package files from disk, and the associated Section_Memory key from Redis.
7. THE System SHALL enforce that a User can only view, download, or delete Generation_Jobs that belong to that User.
8. THE System SHALL display all Generation_Jobs for the authenticated User on the dashboard, paginated at 10 records per page, ordered by creation date descending.

---

### Requirement 12: Freelancing Workflow

**User Story:** As a User, I want a clear, linear workflow from client brief to deliverable, so that I can process assignments efficiently and deliver professional outputs with minimal manual intervention.

#### Acceptance Criteria

1. THE System SHALL present the workflow in the following sequence: (1) Submit client brief or upload document, (2) Review extracted Assignment_Brief before generation begins, (3) Confirm or edit the generated outline before section generation begins, (4) Monitor generation progress, (5) Download Export_Package.
2. WHEN the Assignment_Brief is extracted, THE System SHALL display it to the User for review before the Generation_Pipeline proceeds past the Outline Generation stage.
3. WHEN the document outline is generated, THE System SHALL display it to the User and allow the User to edit section titles and target word counts before section generation begins.
4. THE System SHALL allow the User to specify a total target word count between 500 and 15,000 words at job submission time.
5. WHEN the Generation_Job completes, THE System SHALL notify the User via an on-screen notification that the Export_Package is ready for download.
6. THE System SHALL display the total word count of the generated document on the job completion page.

---

### Requirement 13: Document Parser and Round-Trip Integrity

**User Story:** As a User, I want the system to reliably parse uploaded documents regardless of their internal structure, so that no assignment context is lost due to extraction failures.

#### Acceptance Criteria

1. WHEN a PDF file is uploaded, THE System SHALL extract all text content using PyMuPDF, preserving paragraph boundaries and heading structure where detectable.
2. WHEN a DOCX file is uploaded, THE System SHALL extract all text content using python-docx, preserving paragraph and heading structure.
3. THE System SHALL clean extracted text by removing non-printable characters, normalising whitespace, and collapsing repeated blank lines before passing it to the Assignment_Intelligence_Engine.
4. FOR ALL valid extracted text objects, parsing then serialising to the Assignment_Brief then re-parsing the Assignment_Brief SHALL produce an equivalent Assignment_Brief object (round-trip property).
5. IF text extraction produces fewer than 100 characters of readable content, THEN THE System SHALL reject the document and return an error message indicating the document appears to contain no readable text.
6. THE System SHALL split extracted text into token-bounded chunks of at most 3,000 tokens using the cl100k_base encoding before passing chunks to LLM calls that have context length constraints.
