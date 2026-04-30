"""
Prompt templates for the LamGen academic generation pipeline.

Design principles:
- Analysis prompt extracts precise metadata in one call (Stages 1+2 combined)
- Outline prompt produces a structured, rubric-weighted document plan
- Section generation prompt drives postgraduate-quality analytical writing
- All templates use Python .format() substitution
- Optional context blocks are assembled by the calling service, not inside templates
"""

# ---------------------------------------------------------------------------
# Stages 1 + 2 combined: assignment brief + rubric extraction
#
# {rubric_instruction} is filled by build_combined_analysis_prompt() with
# either the rubric schema (when rubric keywords are detected in the document)
# or an empty array literal (when no rubric is present).
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
- writing_tone: infer from assignment type and level — reports and case studies are typically "professional_report" or "critical_analytical"; reflective journals are "reflective"
- required_sections: list only sections explicitly named in the brief; leave empty if none specified
- required_frameworks: include only frameworks, models, or theorists explicitly named
- Return ONLY the JSON object — no preamble, no explanation

Assignment document:
{document_text}"""

# Injected as {rubric_instruction} when rubric keywords are detected in the document
_RUBRIC_SCHEMA = (
    '[{{"name": "<criterion name>", "weight": <proportion of total marks as float 0.0–1.0>, '
    '"distinction_descriptor": "<quality descriptor for distinction-level performance>"}}]'
)
# Injected when no rubric is present
_RUBRIC_EMPTY = '[]'


def build_combined_analysis_prompt(document_text: str, has_rubric: bool) -> str:
    """Return the combined analysis prompt with the appropriate rubric instruction."""
    return COMBINED_ANALYSIS_PROMPT.format(
        document_text=document_text,
        rubric_instruction=_RUBRIC_SCHEMA if has_rubric else _RUBRIC_EMPTY,
    )


# ---------------------------------------------------------------------------
# Stage 3: Outline generation
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
- Each section requires at least 3 substantive key_points — not generic headings, but specific arguments or analytical moves
- Introduction and Conclusion should each receive 8–12% of the total word count
- Body sections should reflect the analytical weight of the assignment

Assignment brief:
{assignment_brief}

Rubric:
{rubric_profile}

Total word count: {target_word_count}"""


# ---------------------------------------------------------------------------
# Stage 6: Section generation
#
# This is the core generation call. The prompt is designed to produce
# postgraduate-quality analytical writing with natural sentence rhythm,
# appropriate hedging, and rubric-aligned depth.
# ---------------------------------------------------------------------------

SECTION_GENERATION_PROMPT = """Write the "{section_title}" section of a {academic_level}-level {assignment_type}.

Target length: {target_word_count} words (±5%). Writing tone: {writing_tone}. Citation style: {citation_style}.

Points to develop in this section:
{key_points}
{optional_context}
Writing standards:
1. Reach {target_word_count} words (±5%). Count carefully before finishing.
2. Open with a clear analytical claim — not a definition or background statement.
3. Develop each key point with evidence, critical evaluation, and a clear line of argument. Do not summarise; analyse.
4. Where competing perspectives exist, engage with them directly — acknowledge limitations, tensions, and scholarly disagreement.
5. Vary sentence length and structure naturally. Mix short declarative sentences with longer analytical ones. Avoid uniform rhythm.
6. Use hedging language where appropriate: "suggests", "indicates", "may", "tends to" — not overconfident assertions.
7. Use placeholder citations in the form [Author, Year] where a real source would appear. Do not fabricate statistics or invent authors.
8. Write in flowing academic prose. No bullet points, numbered lists, or subheadings in the output.
9. Close the section with a synthesising statement that connects the analysis to the broader argument of the assignment.
10. Do not begin the section with the section title or a meta-statement about what the section will do.

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
    Assemble the section generation user prompt.

    Optional context blocks (organisational context, rubric, prior section memory)
    are only injected when they contain meaningful content, keeping token usage lean.
    """
    optional_parts = []

    if organisational_context and organisational_context.strip() not in ('', 'None'):
        optional_parts.append(
            f"Organisational context (integrate this into the analysis, do not treat it as background):\n"
            f"{organisational_context}"
        )

    if rubric_criteria and rubric_criteria.strip() not in ('', 'No rubric provided'):
        optional_parts.append(
            f"Rubric criteria (weight your analytical depth and emphasis accordingly):\n"
            f"{rubric_criteria}"
        )

    if generation_memory and generation_memory.strip() not in ('', 'No prior sections generated.'):
        optional_parts.append(
            f"Consistency with prior sections (maintain these positions and do not repeat covered ground):\n"
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
