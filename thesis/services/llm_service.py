import json
import logging
import os
import time

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an elite, highly intelligent academic system designed to act as a High-Achieving Master's Student and Senior Examiner.
Your ultimate goal is to produce assignments that perfectly align with instructor intentions, strictly follow all rubrics, and read indistinguishably from top-tier human student writing.

UNIVERSAL STRICT RULES:
1. ZERO HALLUCINATIONS: Never invent facts, data, frameworks, or references outside the provided document content.
2. NO AI PATTERNS: Avoid robotic phrasing, excessive transition words ("Moreover", "Furthermore", "In conclusion"), and generic fluff. Vary sentence lengths naturally.
3. CRITICAL DEPTH: Focus on analysis (why/how) rather than mere description (what).
4. STRICT ADHERENCE: Follow every instruction, word count, and formatting rule requested in the specific prompt.

You will be participating in a multi-pass pipeline. Execute your specific role in each pass flawlessly. Output exactly what is requested, without conversational filler.
"""

ANALYSIS_PROMPT = """You are a highly intelligent academic strategist and Master's student.
Your task is to deeply analyze the provided assignment brief/subject outline.
Read between the lines to understand the instructor's true intention.

Extract and output ONLY a valid JSON object with the following schema:
{
  "assignment_type": "string (e.g., Case Study, Research Essay)",
  "instructor_intent": "string (What is the instructor really testing here? What gets an HD?)",
  "dos_and_donts": ["list of strict rules to follow", "list of things to avoid"],
  "marking_rubric_criteria": "Detailed string summarizing the exact criteria for the highest grade band",
  "key_content_case_details": "String summarizing any specific facts, data, or context that MUST be included"
}

CRITICAL INSTRUCTIONS:
- Do NOT output any markdown blocks outside the JSON.
- Focus entirely on the overarching strategy, rules, and rubric.
"""

OUTLINE_PROMPT = """You are a master academic planner.
Based on the global analysis of the assignment, construct a detailed, rubric-aligned outline.

Extract and output ONLY a valid JSON object with the following schema:
{
  "required_sections": [
    {
      "name": "Exact heading name based on brief",
      "word_count_target": "integer (target words for this section, ensuring total is between 1700-2000)",
      "criteria": "Specific rubric instructions for this section alone",
      "key_points_to_cover": ["Bullet 1", "Bullet 2"]
    }
  ]
}

CRITICAL INSTRUCTIONS:
- Do NOT output any markdown blocks outside the JSON.
- Ensure the sum of `word_count_target` across all sections equals the total required word count.
- Map the rubric explicitly to the sections. If the assignment mentions specific tags (e.g., [Add], [Edit]), incorporate them into the criteria.
"""

HUMANIZATION_PROMPT = """You are an expert at removing AI-generated patterns and making academic writing sound authentically human.
A high-achieving Master's student wrote this draft. It needs to read perfectly naturally.

ANTI-PATTERN ADJUSTMENTS (Remove these completely):
- Delete predictable transition words (e.g., "Moreover", "Furthermore", "Additionally", "In conclusion", "Ultimately").
- Break up uniform sentence lengths. Mix very short, punchy sentences with longer, complex analytical ones.
- Remove generic, sweeping statements (e.g., "In today's rapidly changing world", "This highlights the importance of").
- Replace robotic, overly-dense vocabulary with natural, precise academic terminology.
- Avoid the "five-paragraph essay" cadence. Let the logic drive the paragraph breaks.

HUMANIZATION RULES:
- Introduce subtle nuances and natural academic phrasing (e.g., "This suggests...", "Given these constraints...", "A key implication is...").
- Keep all original facts, arguments, and section structures intact.
- DO NOT add external facts.
- Output ONLY the humanized text.
"""

EVALUATION_PROMPT = """You are a strict, detail-oriented academic examiner.
Review the following document against standard high-level academic expectations.

CHECK FOR AND FIX:
1. Hallucinations: Remove any facts, references, or data that seem invented or not grounded in the core assignment context.
2. Fluff: Delete redundant sentences that add no analytical value.
3. Answering the Prompt: Ensure the text actually answers the implied questions rather than just describing things.

TASK:
- Identify weak, fluffy, or hallucinated parts and fix them directly in the text.
- Do NOT add new information.
- Keep the exact section headings.
- Output ONLY the corrected text. No feedback, no explanations.
"""

RUBRIC_PROMPT = """You are the final gatekeeper: the Senior Grader.
Your sole focus is ensuring this assignment hits the High Distinction (HD) band for the specific rubric.

EVALUATION CRITERIA:
- Are the core deliverables explicitly met?
- Is the tone perfectly aligned with postgraduate expectations?
- Are the insights deeply tied to the specific case/brief rather than generalized?

TASK:
- Make final, targeted sentence-level adjustments to push the text into the highest grading band.
- Strengthen the analytical punchline of each section.
- Ensure absolute adherence to the rules.
- Output ONLY the final, polished document. No markdown fences unless formatting requires it, no conversational text.
"""

# Provider → default model mapping
# Provider → default model mapping (can be overridden via LLM_MODEL env var)
PROVIDER_MODELS = {
    'groq':       'llama-3.3-70b-versatile',
    'openrouter': 'meta-llama/llama-3.3-70b-instruct:free',
    'gemini':     'gemini-2.0-flash',
    'anthropic': 'claude-opus-4-7',
}


class LLMServiceError(Exception):
    """Raised when the LLM service fails after exhausting retries."""
    pass


class LLMService:
    MAX_RETRIES: int = 3
    BASE_BACKOFF_SECONDS: float = 1.0
    MAX_TOKENS: int = 8192

    def __init__(self, api_key: str = None, provider: str = None):
        self.temperature = 0.65
        """
        Initialise the appropriate LLM client based on LLM_PROVIDER env var.
        Supported providers: openrouter, groq, gemini, anthropic.
        API key is read from LLM_API_KEY env var.
        """
        self.provider = (provider or os.environ.get('LLM_PROVIDER', 'openrouter')).lower()
        self.api_key = api_key or os.environ.get('LLM_API_KEY', '')
        default_model = PROVIDER_MODELS.get(self.provider)
        self.model = os.environ.get('LLM_MODEL') or default_model

        if self.model is None:
            raise LLMServiceError(
                f"Unknown LLM_PROVIDER '{self.provider}'. "
                f"Supported: {', '.join(PROVIDER_MODELS)}"
            )

        self._init_client()

    def _init_client(self):
        """Initialise the provider-specific client."""
        if self.provider == 'openrouter':
            from openai import OpenAI
            self._client = OpenAI(
                api_key=self.api_key,
                base_url='https://openrouter.ai/api/v1',
            )

        elif self.provider == 'groq':
            import groq
            self._client = groq.Groq(api_key=self.api_key)

        elif self.provider == 'gemini':
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self._client = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=SYSTEM_PROMPT,
                generation_config=genai.GenerationConfig(max_output_tokens=self.MAX_TOKENS),
            )

        elif self.provider == 'anthropic':
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def generate_thesis(self, chunks: list, title: str, assignment_brief: str = "") -> str:
        """
        Fast high-quality assignment generator - 2 passes max.
        Much faster and more reliable than the old 6-pass pipeline.
        """
        document_content = "\n\n---\n\n".join(
            f"[Document Chunk {i+1}]\n{chunk}" for i, chunk in enumerate(chunks)
        )

        full_context = f"""ASSIGNMENT TITLE: {title}

        ASSIGNMENT BRIEF / QUESTION:
        {assignment_brief}

        SOURCE DOCUMENT CONTENT (You MUST use ONLY information from here. Never invent facts, data, theories, or references):
        {document_content}"""

        # === Pass 1: Generate high-quality draft (core content) ===
        generation_prompt = f"""You are a high-achieving Master's student who consistently scores High Distinction (HD).

        Write a complete, rubric-aligned assignment of **1800-2000 words** on the topic above.

        Requirements:
        - Use natural, intelligent academic tone (vary sentence length, avoid robotic transitions like "Furthermore", "Moreover", "In conclusion").
        - Show strong critical analysis (why and how, not just what).
        - Structure with clear, logical section headings appropriate for this assignment type.
        - Base every single point, example, and argument strictly on the provided source document. Zero hallucinations.
        - Demonstrate deep understanding of the case/context.
        - Target postgraduate level: precise language, analytical depth, coherent argument.

        {full_context}

        Write the full assignment now. Start directly with the first section heading."""

        logger.info("Starting fast generation (Pass 1/2)...")
        draft = self._call_with_retry(generation_prompt)
        draft = self._strip_fences(draft)

        # === Pass 2: Quick humanization + final polish ===
        polish_prompt = f"""{HUMANIZATION_PROMPT}

        Then apply these final checks:
        - Strengthen analytical depth where possible without adding new facts.
        - Remove any remaining fluff or repetitive phrasing.
        - Ensure the text flows naturally like a top student's work.
        - Keep word count around 1800-2000.

        Document to polish:
        {draft}"""

        logger.info("Starting final polish (Pass 2/2)...")
        final_text = self._call_with_retry(polish_prompt)
        return self._strip_fences(final_text)

    def _strip_fences(self, text: str) -> str:
        """Strip markdown code fences and leading/trailing whitespace from LLM output."""
        if not text:
            return text or ''
        text = text.strip()
        if text.startswith('```markdown'):
            text = text[11:].strip()
            if text.endswith('```'):
                text = text[:-3].strip()
        elif text.startswith('```'):
            text = text[3:].strip()
            if text.endswith('```'):
                text = text[:-3].strip()
        return text

    def humanize_document(self, text: str) -> str:
        """
        Pass 4 — Humanize the generated document to sound naturally written,
        breaking AI anti-patterns while keeping the content intact.
        """
        logger.info('Starting document humanization (Pass 4)...')
        prompt = f"{HUMANIZATION_PROMPT}\n\nDocument to humanize:\n\n{text}"
        return self._strip_fences(self._call_with_retry(prompt))

    def evaluate_and_fix(self, text: str) -> str:
        """
        Pass 5 — Auto-evaluate the humanized document and fix weak sections
        to ensure high academic quality and analytical depth.
        """
        logger.info('Starting document evaluation and auto-fix (Pass 5)...')
        prompt = f"{EVALUATION_PROMPT}\n\nDocument to evaluate and fix:\n\n{text}"
        return self._strip_fences(self._call_with_retry(prompt))

    def rubric_align(self, text: str) -> str:
        """
        Pass 6 — Final alignment layer to simulate rubric grading,
        strengthening weak answers to meet high academic expectations.
        """
        logger.info('Starting document rubric alignment (Pass 6)...')
        prompt = f"{RUBRIC_PROMPT}\n\nDocument to align:\n\n{text}"
        return self._strip_fences(self._call_with_retry(prompt))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _call_with_retry(self, user_content: str) -> str:
        """Call _call_api with exponential-backoff retry logic."""
        last_error = None
        for attempt in range(self.MAX_RETRIES):
            try:
                return self._call_api(user_content)
            except LLMServiceError:
                raise  # non-transient — propagate immediately
            except Exception as e:
                last_error = e
                wait = self.BASE_BACKOFF_SECONDS * (2 ** attempt)
                logger.warning(
                    'LLMService transient error (attempt %d/%d, provider=%s): %s. Retrying in %.1fs.',
                    attempt + 1, self.MAX_RETRIES, self.provider, e, wait
                )
                time.sleep(wait)

        raise LLMServiceError(
            f'{self.provider} API failed after {self.MAX_RETRIES} attempts. '
            f'Last error: {last_error}'
        )

    def _parse_analysis(self, raw: str) -> dict:
        """Extract JSON from the analysis response, tolerating markdown fences and truncation."""
        if not raw:
            logger.warning('_parse_analysis received empty/None response; returning empty dict.')
            return {}
        text = raw.strip()
        # Strip ```json ... ``` fences if present
        if text.startswith('```'):
            lines = text.splitlines()
            text = '\n'.join(
                line for line in lines
                if not line.strip().startswith('```')
            ).strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Attempt to recover truncated JSON by finding the last complete object/array
            # Try to close any open brackets to salvage partial responses
            try:
                # Find the last valid closing brace
                last_brace = text.rfind('}')
                if last_brace != -1:
                    candidate = text[:last_brace + 1]
                    # Count open/close braces to detect truncation
                    open_count = candidate.count('{') - candidate.count('}')
                    close_count = candidate.count('[') - candidate.count(']')
                    # Append missing closing brackets
                    candidate += ']' * close_count + '}' * open_count
                    result = json.loads(candidate)
                    logger.warning(
                        'Analysis response was truncated JSON; recovered partial result. Raw: %s', raw[:200]
                    )
                    return result
            except (json.JSONDecodeError, Exception):
                pass
            logger.warning('Analysis response was not valid JSON; returning empty dict. Raw: %s', raw[:200])
            return {}

    def _call_api(self, user_content: str) -> str:
        """Single API call dispatched to the active provider."""
        if self.provider == 'openrouter':
            return self._call_openrouter(user_content)
        elif self.provider == 'groq':
            return self._call_groq(user_content)
        elif self.provider == 'gemini':
            return self._call_gemini(user_content)
        elif self.provider == 'anthropic':
            return self._call_anthropic(user_content)
        else:
            raise LLMServiceError(
                f"Unknown LLM provider '{self.provider}'. "
                "Set LLM_PROVIDER to one of: anthropic, openrouter, groq, gemini."
            )

    def _call_openrouter(self, user_content: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user',   'content': user_content},
            ],
        )
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError('OpenRouter returned an empty response (content=None).')
        return content

    def _call_groq(self, user_content: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            messages=[
                {'role': 'system', 'content': SYSTEM_PROMPT},
                {'role': 'user',   'content': user_content},
            ],
        )
        content = response.choices[0].message.content
        if content is None:
            raise RuntimeError('Groq returned an empty response (content=None).')
        return content

    def _call_gemini(self, user_content: str) -> str:
        response = self._client.generate_content(user_content)
        text = response.text
        if text is None:
            raise RuntimeError('Gemini returned an empty response (text=None).')
        return text

    def _call_anthropic(self, user_content: str) -> str:
        import anthropic
        message = self._client.messages.create(
            model=self.model,
            max_tokens=self.MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{'role': 'user', 'content': user_content}],
        )
        text = message.content[0].text
        if text is None:
            raise RuntimeError('Anthropic returned an empty response (text=None).')
        return text
