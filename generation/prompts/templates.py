"""
Prompt templates for the LamGen academic generation pipeline.

Design principles:
- Analysis (Haiku): extract precise metadata in one call
- Outline (Sonnet): structured, rubric-weighted document plan
- Section generation (Opus): natural long-form writing with persona + continuity memory
- Prompts avoid "write professionally and academically" framing
- Prompts encourage natural reasoning, contextual analysis, realistic pacing
"""

# ---------------------------------------------------------------------------
# Stages 1 + 2 combined: assignment brief + rubric extraction (Haiku)
# ---------------------------------------------------------------------------

COMBINED_ANALYSIS_PROMPT = """You are analysing an academic assignment document. Extract all structured metadata precisely.

Return ONLY valid JSON — no markdown fences, no commentary, no extra text:

{{
  "brief": {{
    "topic": "<the specific assignment question or topic, verbatim where possible>",
    "subject_area": "<academic discipline, e.g. Cybersecurity, Strategic Management, Public Health>",
    "assignment_type": "<essay|report|case_study|literature_review|thesis_chapter|other>",
    "academic_level": "<undergraduate|postgraduate|doctoral>",
    "required_sections": ["<section title as stated in the brief>", ...],
    "citation_style": "<APA|Harvard|Chicago|Vancouver|other — infer from context if not stated>",
    "writing_tone": "<critical_analytical|descriptive_explanatory|reflective|professional_report>",
    "organisational_context": "<the specific organisation, industry, or scenario described — empty string if none>",
    "required_frameworks": ["<named theory, model, or framework the assignment requires>", ...]
  }},
  "rubric_criteria": {rubric_instruction}
}}

Extraction rules:
- topic: extract the actual question or task, not a paraphrase
- academic_level: default to "postgraduate" if not explicitly stated
- writing_tone: infer from assignment type and level
- required_sections: list only sections explicitly named in the brief
- required_frameworks: include only frameworks explicitly named
- Return ONLY the JSON object

Assignment document:
{document_text}"""

_RUBRIC_SCHEMA = (
    '[{{"name": "<criterion name>", "weight": <proportion of total marks as float 0.0–1.0>, '
    '"distinction_descriptor": "<quality descriptor for distinction-level performance>"}}]'
)
_RUBRIC_EMPTY = '[]'


def build_combined_analysis_prompt(document_text: str, has_rubric: bool) -> str:
    return COMBINED_ANALYSIS_PROMPT.format(
        document_text=document_text,
        rubric_instruction=_RUBRIC_SCHEMA if has_rubric else _RUBRIC_EMPTY,
    )


# ---------------------------------------------------------------------------
# Stage 3: Outline generation (Sonnet)
# ---------------------------------------------------------------------------

OUTLINE_GENERATION_PROMPT = """Generate a structured document outline for the following assignment.

Return ONLY a JSON array — no markdown, no commentary:

[
  {{
    "title": "<section title>",
    "target_word_count": <integer>,
    "key_points": ["<specific analytical point or argument to develop>", ...]
  }}
]

Outline rules:
- Word counts must sum to approximately {target_word_count}
- Where a rubric is provided, allocate more words to higher-weighted criteria
- Section titles must match or closely follow required_sections from the brief where specified
- Each section requires at least 3 substantive key_points — specific arguments, not generic headings
- Introduction and Conclusion should each receive 8–12% of the total word count
- Body sections should reflect the analytical weight of the assignment

Assignment brief:
{assignment_brief}

Rubric:
{rubric_profile}

Total word count: {target_word_count}"""


# ---------------------------------------------------------------------------
# Stage 6: Section generation (Opus)
#
# Designed for natural, human-like academic writing.
# Avoids "write professionally and academically" framing.
# Encourages contextual reasoning, realistic pacing, natural variation.
# ---------------------------------------------------------------------------

SECTION_GENERATION_PROMPT = """Write the "{section_title}" section of this {academic_level}-level {assignment_type}.

Target: approximately {target_word_count} words.

Points to develop:
{key_points}
{optional_context}
How to write this section:
- Write naturally and analytically — like a capable student who has genuinely thought about this
- Prioritise contextual, practical reasoning over textbook explanation or theory recitation
- Allow reasoning to develop as you write — not every point needs to be fully resolved at the outset
- Let paragraph length vary naturally: some short analytical observations, some longer developed arguments
- Open with a substantive claim or observation — not a definition, not a meta-statement about the section
- Develop each point with evidence, evaluation, and a clear line of reasoning
- Where competing perspectives exist, engage with them directly — acknowledge tensions and real tradeoffs
- Use hedging where appropriate: "suggests", "indicates", "may", "tends to", "arguably", "in some respects"
- Roughly a quarter of major claims should be softened with hedging — avoid projecting false certainty
- Do NOT present every conclusion as fully resolved — some analytical uncertainty is authentic and expected
- Use placeholder citations in the form [Author, Year] where a real source would appear
- Avoid predictable transitions like "Furthermore", "Moreover", "Additionally" — use contextual flow
- Do not begin with the section title or announce what the section will do
- Close with a synthesising thought that connects naturally to the broader argument — not a grand conclusion
- Write in flowing prose — no bullet points, no subheadings, no numbered lists
- Some sections may be tighter or more compact than others — uneven density is natural and desirable

Write the section now:"""


def build_section_prompt(
    section_title: str,
    target_word_count: int,
    key_points: str,
    writing_tone: str,
    academic_level: str,
    assignment_type: str,
    citation_style: str,
    organisational_context: str = '',
    rubric_criteria: str = '',
    generation_memory: str = '',
) -> str:
    """
    Assemble the Opus section generation user prompt.

    Optional context blocks are only injected when they contain meaningful content.
    Organisational context is framed as something to integrate analytically,
    not as background to describe.
    """
    optional_parts = []

    if organisational_context and organisational_context.strip() not in ('', 'None'):
        optional_parts.append(
            f"Organisational context (weave this into the analysis — do not describe it separately):\n"
            f"{organisational_context}"
        )

    if rubric_criteria and rubric_criteria.strip() not in ('', 'No rubric provided'):
        optional_parts.append(
            f"Rubric criteria (let these shape your analytical emphasis, not your structure):\n"
            f"{rubric_criteria}"
        )

    if generation_memory and generation_memory.strip() not in ('', 'No prior sections generated.'):
        optional_parts.append(
            f"Writing continuity (pick up naturally from where the previous section left off):\n"
            f"{generation_memory}"
        )

    optional_context = ('\n' + '\n\n'.join(optional_parts) + '\n') if optional_parts else '\n'

    return SECTION_GENERATION_PROMPT.format(
        section_title=section_title,
        target_word_count=target_word_count,
        key_points=key_points,
        writing_tone=writing_tone,
        academic_level=academic_level,
        assignment_type=assignment_type,
        citation_style=citation_style,
        optional_context=optional_context,
    )


# ---------------------------------------------------------------------------
# Reflection section prompt (Opus) — personal, experiential, non-generic
# ---------------------------------------------------------------------------

REFLECTION_SECTION_PROMPT = """Write the "{section_title}" section of this {academic_level}-level {assignment_type}.

Target: approximately {target_word_count} words.

Points to reflect on:
{key_points}
{optional_context}
How to write this reflection:
- Write from a genuine first-person perspective — this is personal and experiential
- Show evolving understanding, not a polished summary of what you learned
- Include realistic implementation challenges, uncertainties, and tradeoffs you encountered or considered
- Avoid motivational language and generic reflective clichés
- Do NOT use phrases like: "this assignment enhanced my understanding", "I gained valuable insight",
  "this experience taught me", "this task was extremely beneficial"
- Let the reflection feel like it was reasoned through while writing, not tidied up afterwards
- Acknowledge where things were genuinely unclear, difficult, or less interesting than expected
- Connect personal observations to the broader analytical context of the assignment
- Use natural, slightly informal academic register — not robotic self-analysis
- Write in flowing prose — no subheadings, no structured bullet-point self-assessment

Write the reflection now:"""


def build_reflection_prompt(
    section_title: str,
    target_word_count: int,
    key_points: str,
    academic_level: str,
    assignment_type: str,
    organisational_context: str = '',
    generation_memory: str = '',
) -> str:
    optional_parts = []
    if organisational_context and organisational_context.strip() not in ('', 'None'):
        optional_parts.append(f"Context: {organisational_context}")
    if generation_memory and generation_memory.strip():
        optional_parts.append(f"Prior sections covered: {generation_memory}")
    optional_context = ('\n' + '\n\n'.join(optional_parts) + '\n') if optional_parts else '\n'

    return REFLECTION_SECTION_PROMPT.format(
        section_title=section_title,
        target_word_count=target_word_count,
        key_points=key_points,
        academic_level=academic_level,
        assignment_type=assignment_type,
        optional_context=optional_context,
    )


# ---------------------------------------------------------------------------
# Light validation prompt (Sonnet) — citation alignment only
# ---------------------------------------------------------------------------

CITATION_VALIDATION_PROMPT = """Review the following academic text for citation consistency only.

Check:
1. All in-text citations follow {citation_style} format
2. Citation placeholders [Author, Year] are consistently formatted
3. No citation appears in a format inconsistent with the rest of the document

Do NOT rewrite content. Do NOT change analytical substance. Do NOT restructure paragraphs.
Make only the minimum citation formatting corrections needed.

If no citation issues are found, return the text unchanged.

Text:
{section_content}"""
