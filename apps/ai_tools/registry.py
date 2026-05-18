"""
AI Tool Registry — single source of truth.

Every AI tool is registered here with:
  - slug: unique identifier (used in URL /api/tools/<slug>/)
  - name: human-readable label
  - category: logical grouping
  - input_fields: validated input schema
  - system_prompt: base instruction for the model
  - user_prompt_template: how to embed user input (uses {input})
  - response_format: "text" | "json"
  - provider_preference: optional override; falls back to env default
  - cache_ttl: seconds (0 = no cache)

To add a new tool: append one dict to TOOL_REGISTRY. No backend changes required.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional


TOOL_REGISTRY: List[Dict[str, Any]] = [
    # ── Career ──────────────────────────────────────────────────────────────
    {
        "slug": "resume-builder",
        "name": "AI Resume Builder",
        "category": "career",
        "input_fields": [
            {"name": "prompt", "label": "Job title / experience summary", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are an expert resume writer. Given the user's background, produce a professional, ATS-optimised "
            "resume in JSON with keys: summary (string), experience (array of {title, company, start_date, end_date, description}), "
            "skills (array of strings). Return only valid JSON."
        ),
        "user_prompt_template": "User background:\n{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "ats-checker",
        "name": "ATS Checker",
        "category": "career",
        "input_fields": [
            {"name": "prompt", "label": "Paste your resume text", "required": True, "max_length": 5000},
        ],
        "system_prompt": (
            "You are an ATS (Applicant Tracking System) expert. Analyse the provided resume and return JSON with keys: "
            "score (0-100 integer), issues (array of strings), suggestions (array of strings), "
            "keyword_density (object). Return only valid JSON."
        ),
        "user_prompt_template": "Resume:\n{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "cover-letter-generator",
        "name": "Cover Letter Generator",
        "category": "career",
        "input_fields": [
            {"name": "prompt", "label": "Job description + your background", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are a professional cover letter writer. Write a compelling, tailored cover letter based on the "
            "provided job description and candidate background. Return only the letter text."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "linkedin-headline-generator",
        "name": "LinkedIn Headline Generator",
        "category": "career",
        "input_fields": [
            {"name": "prompt", "label": "Your role, skills, and value proposition", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are a LinkedIn profile optimisation expert. Generate 5 compelling LinkedIn headline options "
            "(max 220 chars each). Return JSON: {\"headlines\": [\"...\", ...]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "linkedin-post-generator",
        "name": "LinkedIn Post Generator",
        "category": "career",
        "input_fields": [
            {"name": "prompt", "label": "Topic or key message", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are a LinkedIn content strategist. Write a professional, engaging LinkedIn post optimised for reach. "
            "Use hooks, storytelling, and a clear CTA. Return only the post text."
        ),
        "user_prompt_template": "Topic: {input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    # ── Writing ──────────────────────────────────────────────────────────────
    {
        "slug": "ai-humanizer",
        "name": "AI Humanizer",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "AI-generated text to humanize", "required": True, "max_length": 5000},
        ],
        "system_prompt": (
            "You are a skilled editor. Rewrite the provided AI-generated text so it sounds natural, "
            "human, and engaging — without losing the original meaning. Return only the rewritten text."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "essay-writer",
        "name": "Essay Writer",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Essay topic and requirements", "required": True, "max_length": 2000},
        ],
        "system_prompt": (
            "You are an expert academic essay writer. Write a well-structured, persuasive essay with "
            "introduction, body paragraphs, and conclusion. Use clear arguments and evidence."
        ),
        "user_prompt_template": "Essay topic: {input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "paraphrasing-tool",
        "name": "Paraphrasing Tool",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Text to paraphrase", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are a paraphrasing expert. Rewrite the provided text using different words and sentence structures "
            "while preserving the original meaning. Return only the paraphrased text."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "grammar-checker",
        "name": "Grammar Checker",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Text to check", "required": True, "max_length": 5000},
        ],
        "system_prompt": (
            "You are a grammar and style expert. Analyse the text and return JSON: "
            "{\"corrected_text\": \"...\", \"errors\": [{\"original\": \"\", \"corrected\": \"\", \"explanation\": \"\"}], "
            "\"score\": <0-100>}. Return only valid JSON."
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "email-writer",
        "name": "Email Writer",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Email purpose and context", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are a professional email writer. Write a clear, concise, and effective email based on the "
            "provided purpose. Include subject line and body. Return only the email text."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "cold-email-generator",
        "name": "Cold Email Generator",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Target audience and your offer", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are a cold outreach specialist. Write a personalised, high-converting cold email with "
            "a compelling subject line, strong hook, clear value proposition, and CTA. Return only the email."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    # ── SEO / Content ────────────────────────────────────────────────────────
    {
        "slug": "blog-writer",
        "name": "Blog Writer",
        "category": "seo",
        "input_fields": [
            {"name": "prompt", "label": "Blog topic or title", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an expert blog writer. Write a comprehensive, SEO-optimised blog post with "
            "an engaging introduction, well-structured sections with H2/H3 headings, and a conclusion. "
            "Return only the blog post content."
        ),
        "user_prompt_template": "Blog topic: {input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "seo-article-generator",
        "name": "SEO Article Generator",
        "category": "seo",
        "input_fields": [
            {"name": "prompt", "label": "Target keyword + topic", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an SEO content strategist. Write a long-form, keyword-rich article optimised for "
            "search engines. Include the target keyword naturally throughout. Return only the article."
        ),
        "user_prompt_template": "Keyword and topic: {input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "meta-description-generator",
        "name": "Meta Description Generator",
        "category": "seo",
        "input_fields": [
            {"name": "prompt", "label": "Page topic or URL description", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an SEO expert. Generate 5 compelling meta descriptions (each 150-160 chars) for the given page. "
            "Return JSON: {\"meta_descriptions\": [\"...\", ...]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "keyword-cluster-generator",
        "name": "Keyword Cluster Generator",
        "category": "seo",
        "input_fields": [
            {"name": "prompt", "label": "Seed keyword or topic", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an SEO keyword research expert. Generate a comprehensive keyword cluster for the given seed. "
            "Return JSON: {\"primary_keyword\": \"\", \"clusters\": [{\"theme\": \"\", \"keywords\": []}]}"
        ),
        "user_prompt_template": "Seed keyword: {input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    # ── Creator / Social ─────────────────────────────────────────────────────
    {
        "slug": "youtube-script-generator",
        "name": "YouTube Script Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Video topic and target audience", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are a YouTube content creator coach. Write an engaging, conversational YouTube video script "
            "with hook, main content sections, and a strong CTA. Include [PAUSE] and [B-ROLL] cues."
        ),
        "user_prompt_template": "Video topic: {input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "youtube-title-generator",
        "name": "YouTube Title Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Video topic", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a YouTube growth expert. Generate 10 click-worthy, SEO-optimised YouTube titles. "
            "Return JSON: {\"titles\": [\"...\", ...]}"
        ),
        "user_prompt_template": "Video topic: {input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "thumbnail-prompt-generator",
        "name": "Thumbnail Prompt Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Video title or topic", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a visual design expert. Generate 3 detailed image generation prompts for YouTube thumbnails "
            "that maximise CTR. Return JSON: {\"prompts\": [\"...\", ...]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "instagram-caption-generator",
        "name": "Instagram Caption Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Post topic or image description", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a social media content expert. Write 3 engaging Instagram captions with relevant hashtags. "
            "Return JSON: {\"captions\": [{\"text\": \"\", \"hashtags\": []}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "tweet-generator",
        "name": "Tweet Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Topic or key message", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a Twitter/X content strategist. Generate 5 engaging tweets (max 280 chars each). "
            "Return JSON: {\"tweets\": [\"...\", ...]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    # ── Business ─────────────────────────────────────────────────────────────
    {
        "slug": "startup-name-generator",
        "name": "Startup Name Generator",
        "category": "business",
        "input_fields": [
            {"name": "prompt", "label": "What your startup does", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a branding expert. Generate 10 creative, memorable startup name ideas. "
            "Return JSON: {\"names\": [{\"name\": \"\", \"rationale\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "business-plan-generator",
        "name": "Business Plan Generator",
        "category": "business",
        "input_fields": [
            {"name": "prompt", "label": "Business idea and target market", "required": True, "max_length": 2000},
        ],
        "system_prompt": (
            "You are a business consultant. Create a concise business plan with: executive summary, "
            "problem/solution, target market, revenue model, go-to-market strategy, and financials overview."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "logo-prompt-generator",
        "name": "Logo Prompt Generator",
        "category": "business",
        "input_fields": [
            {"name": "prompt", "label": "Brand name and industry", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a brand design expert. Generate 3 detailed logo design prompts suitable for AI image generators. "
            "Return JSON: {\"prompts\": [\"...\", ...]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "image-prompt-generator",
        "name": "Image Prompt Generator",
        "category": "business",
        "input_fields": [
            {"name": "prompt", "label": "Describe the image you want", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a professional prompt engineer. Generate 3 highly detailed, optimised prompts for AI image "
            "generators (Midjourney/DALL-E/Stable Diffusion). Return JSON: {\"prompts\": [\"...\", ...]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    # ── Education ────────────────────────────────────────────────────────────
    {
        "slug": "notes-generator",
        "name": "Notes Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Topic or paste lecture content", "required": True, "max_length": 5000},
        ],
        "system_prompt": (
            "You are a study expert. Create clear, concise, well-structured study notes from the provided content "
            "using bullet points, headings, and key takeaways."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "quiz-generator",
        "name": "Quiz Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Topic or content to quiz on", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are an educational quiz designer. Generate 10 multiple-choice questions. "
            "Return JSON: {\"questions\": [{\"question\": \"\", \"options\": [\"A\",\"B\",\"C\",\"D\"], "
            "\"answer\": \"A\", \"explanation\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "flashcard-generator",
        "name": "Flashcard Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Topic or content", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are a spaced-repetition learning expert. Generate 15 flashcards for the given topic. "
            "Return JSON: {\"flashcards\": [{\"front\": \"\", \"back\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    # ── Developer ────────────────────────────────────────────────────────────
    {
        "slug": "sql-query-generator",
        "name": "SQL Query Generator",
        "category": "developer",
        "input_fields": [
            {"name": "prompt", "label": "Describe what the query should do", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are a senior database engineer. Generate an optimised SQL query for the described requirement. "
            "Return JSON: {\"query\": \"...\", \"explanation\": \"...\", \"notes\": []}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "regex-generator",
        "name": "Regex Generator",
        "category": "developer",
        "input_fields": [
            {"name": "prompt", "label": "Describe what to match", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a regex expert. Generate a regex pattern for the described requirement. "
            "Return JSON: {\"pattern\": \"...\", \"flags\": \"\", \"explanation\": \"\", \"examples\": []}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "code-debugger",
        "name": "Code Debugger",
        "category": "developer",
        "input_fields": [
            {"name": "prompt", "label": "Paste your code and describe the bug", "required": True, "max_length": 5000},
        ],
        "system_prompt": (
            "You are a senior software engineer. Analyse the provided code, identify the bug, and return: "
            "JSON: {\"issue\": \"\", \"fixed_code\": \"\", \"explanation\": \"\", \"suggestions\": []}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },

    # ── Developer extras ─────────────────────────────────────────────────────
    {
        "slug": "sql-generator",
        "name": "SQL Generator",
        "category": "developer",
        "input_fields": [
            {"name": "prompt", "label": "Describe the query you need (include table/column names if known)", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are a senior database engineer. Generate a clean, optimised SQL query for the described requirement. "
            "Return JSON: {\"query\": \"...\", \"explanation\": \"...\", \"dialect\": \"standard SQL\", \"notes\": []}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "html-minifier",
        "name": "HTML Minifier",
        "category": "developer",
        "input_fields": [
            {"name": "prompt", "label": "Paste your HTML to minify", "required": True, "max_length": 10000},
        ],
        "system_prompt": (
            "You are a web performance expert. Minify the provided HTML by removing all unnecessary whitespace, "
            "comments, and redundant attributes while preserving full functionality. "
            "Return JSON: {\"minified\": \"...\", \"original_size\": 0, \"minified_size\": 0, \"savings_pct\": 0}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },

    # ── Extended AI Tools (DB-only slugs mapped to registry) ────────────────

    # Career / Resume
    {
        "slug": "ai-resume-builder",
        "name": "AI Resume Builder",
        "category": "career",
        "input_fields": [
            {"name": "prompt", "label": "Job title, skills, and experience summary", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are an expert resume writer. Given the user's background, produce a professional, ATS-optimised "
            "resume in JSON with keys: summary (string), experience (array of {title, company, start_date, end_date, "
            "description}), skills (array of strings), education (array of {degree, institution, year}). Return only valid JSON."
        ),
        "user_prompt_template": "User background:\n{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "salary-negotiation-script",
        "name": "Salary Negotiation Script",
        "category": "career",
        "input_fields": [
            {"name": "prompt", "label": "Your role, current salary, and target salary", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are a career coach specialising in compensation negotiation. Write a confident, professional "
            "salary negotiation script the user can use in a conversation or email. Include an opening, "
            "value justification, the ask, and a graceful close. Return only the script text."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },

    # Education / Student
    {
        "slug": "ai-essay-outline-generator",
        "name": "AI Essay Outline Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Essay topic and any specific requirements", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are an academic writing expert. Generate a detailed, well-structured essay outline with "
            "thesis statement, introduction points, body paragraph topics with supporting arguments, "
            "and conclusion. Return JSON: {\"thesis\": \"\", \"outline\": [{\"section\": \"\", \"points\": []}]}"
        ),
        "user_prompt_template": "Essay topic: {input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "ai-thesis-statement-generator",
        "name": "AI Thesis Statement Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Essay topic or research question", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an academic writing coach. Generate 5 strong, arguable thesis statements for the given topic. "
            "Return JSON: {\"statements\": [{\"thesis\": \"\", \"type\": \"argumentative|analytical|expository\"}]}"
        ),
        "user_prompt_template": "Topic: {input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "ai-notes-summarizer",
        "name": "AI Notes Summarizer",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Paste your notes or lecture content", "required": True, "max_length": 5000},
        ],
        "system_prompt": (
            "You are a study expert. Summarise the provided notes into clear, concise bullet points "
            "organised by topic. Highlight key terms and main takeaways. Return only the summarised notes."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "ai-flashcard-generator",
        "name": "AI Flashcard Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Topic or content to create flashcards from", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are a spaced-repetition learning expert. Generate 15 high-quality flashcards. "
            "Return JSON: {\"flashcards\": [{\"front\": \"\", \"back\": \"\", \"hint\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "ai-study-planner",
        "name": "AI Study Planner",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Subjects, exam date, and available study hours per day", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are a study coach. Create a personalised, realistic study plan based on the provided details. "
            "Return JSON: {\"plan\": [{\"day\": \"\", \"tasks\": [{\"subject\": \"\", \"duration_mins\": 0, \"focus\": \"\"}]}], "
            "\"tips\": []}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "ai-citation-generator",
        "name": "AI Citation Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Source details (title, author, year, URL, etc.)", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are an academic citation expert. Generate properly formatted citations for the provided source "
            "in APA, MLA, and Chicago styles. "
            "Return JSON: {\"apa\": \"\", \"mla\": \"\", \"chicago\": \"\"}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },

    # Student tools
    {
        "slug": "grade-predictor",
        "name": "Grade Predictor",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Your current grades, assignments, and remaining assessments", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are an academic advisor. Analyse the student's current grades and predict their final grade. "
            "Return JSON: {\"predicted_grade\": \"\", \"percentage\": 0, \"analysis\": \"\", \"recommendations\": []}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "research-topic-generator",
        "name": "Research Topic Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Subject area and academic level", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an academic research advisor. Generate 10 original, researchable topic ideas with brief rationale. "
            "Return JSON: {\"topics\": [{\"title\": \"\", \"rationale\": \"\", \"keywords\": []}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "essay-outline-builder",
        "name": "Essay Outline Builder",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Essay topic and type (argumentative, analytical, etc.)", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an academic writing tutor. Build a detailed essay outline with introduction, "
            "body paragraphs (with topic sentences and evidence points), and conclusion. Return only the outline text."
        ),
        "user_prompt_template": "Essay topic: {input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "thesis-statement-generator",
        "name": "Thesis Statement Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Your essay topic or argument", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an academic writing coach. Generate 5 strong thesis statements for the given topic. "
            "Return JSON: {\"statements\": [\"\"]}"
        ),
        "user_prompt_template": "Topic: {input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "bibliography-generator",
        "name": "Bibliography Generator",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "List your sources (title, author, year, publisher, URL)", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are a citation expert. Format the provided sources into a complete bibliography in APA, MLA, and Chicago styles. "
            "Return JSON: {\"apa\": [\"\"], \"mla\": [\"\"], \"chicago\": [\"\"]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "paragraph-organizer",
        "name": "Paragraph Organizer",
        "category": "education",
        "input_fields": [
            {"name": "prompt", "label": "Paste your unorganised paragraphs or ideas", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are an academic writing editor. Reorganise the provided content into a logical, "
            "coherent structure with clear paragraph flow and transitions. Return only the reorganised text."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },

    # Writing tools
    {
        "slug": "readability-improver",
        "name": "Readability Improver",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Text to improve", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are a professional editor. Rewrite the provided text to improve its readability: "
            "simplify complex sentences, vary sentence length, improve flow, and use active voice. "
            "Return JSON: {\"improved_text\": \"\", \"changes\": [], \"readability_score\": \"\"}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "text-simplifier",
        "name": "Text Simplifier",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Complex text to simplify", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are a plain-language expert. Rewrite the provided text at a simple, easy-to-understand level "
            "without losing the core meaning. Aim for a Grade 6-8 reading level. Return only the simplified text."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "story-hook-generator",
        "name": "Story Hook Generator",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Story genre, premise, or main character", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a creative writing coach. Generate 5 compelling story opening hooks that immediately "
            "grab the reader's attention. Return JSON: {\"hooks\": [{\"hook\": \"\", \"technique\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "passive-active-converter",
        "name": "Passive to Active Voice Converter",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Text with passive voice sentences", "required": True, "max_length": 3000},
        ],
        "system_prompt": (
            "You are a grammar expert. Convert all passive voice sentences in the provided text to active voice. "
            "Return JSON: {\"converted_text\": \"\", \"changes\": [{\"original\": \"\", \"converted\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "random-sentence-generator",
        "name": "Random Sentence Generator",
        "category": "writing",
        "input_fields": [
            {"name": "prompt", "label": "Topic, tone, or style (optional)", "required": False, "max_length": 200},
        ],
        "system_prompt": (
            "You are a creative writing assistant. Generate 10 unique, interesting sentences. "
            "Return JSON: {\"sentences\": [\"\"]}"
        ),
        "user_prompt_template": "Style/topic: {input}",
        "response_format": "json",
        "cache_ttl": 0,
    },

    # SEO tools
    {
        "slug": "ai-meta-description-generator",
        "name": "AI Meta Description Generator",
        "category": "seo",
        "input_fields": [
            {"name": "prompt", "label": "Page topic, target keyword, and URL", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an SEO expert. Generate 5 compelling meta descriptions (150-160 chars each) optimised "
            "for the target keyword and click-through rate. "
            "Return JSON: {\"meta_descriptions\": [\"\"]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "ai-blog-title-generator",
        "name": "AI Blog Title Generator",
        "category": "seo",
        "input_fields": [
            {"name": "prompt", "label": "Blog topic and target audience", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are an SEO content strategist. Generate 10 click-worthy, SEO-optimised blog titles. "
            "Return JSON: {\"titles\": [{\"title\": \"\", \"type\": \"how-to|listicle|question|guide\"}]}"
        ),
        "user_prompt_template": "Topic: {input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "ai-keyword-intent-analyzer",
        "name": "AI Keyword Intent Analyzer",
        "category": "seo",
        "input_fields": [
            {"name": "prompt", "label": "Keywords to analyse (one per line)", "required": True, "max_length": 1000},
        ],
        "system_prompt": (
            "You are an SEO keyword research expert. Analyse each keyword and classify its search intent. "
            "Return JSON: {\"keywords\": [{\"keyword\": \"\", \"intent\": \"informational|navigational|transactional|commercial\", "
            "\"difficulty\": \"low|medium|high\", \"content_type\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "ai-faq-generator",
        "name": "AI FAQ Generator",
        "category": "seo",
        "input_fields": [
            {"name": "prompt", "label": "Topic, product, or page content", "required": True, "max_length": 2000},
        ],
        "system_prompt": (
            "You are an SEO content expert. Generate 10 frequently asked questions with detailed answers "
            "optimised for featured snippets and People Also Ask. "
            "Return JSON: {\"faqs\": [{\"question\": \"\", \"answer\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
    {
        "slug": "ai-youtube-title-generator",
        "name": "AI YouTube Title Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Video topic, niche, and target audience", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a YouTube growth expert. Generate 10 high-CTR, SEO-optimised YouTube video titles. "
            "Mix formats: how-to, listicle, curiosity gap, and emotional hooks. "
            "Return JSON: {\"titles\": [{\"title\": \"\", \"format\": \"\", \"hook_type\": \"\"}]}"
        ),
        "user_prompt_template": "Video topic: {input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },

    # Social / Viral
    {
        "slug": "ai-caption-generator",
        "name": "AI Caption Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Post topic, platform, and tone", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a social media content expert. Write 5 engaging captions with relevant hashtags for the given post. "
            "Return JSON: {\"captions\": [{\"text\": \"\", \"hashtags\": [], \"platform\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "ai-viral-hook-generator",
        "name": "AI Viral Hook Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Content topic and platform (TikTok/Instagram/YouTube)", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a viral content strategist. Generate 10 scroll-stopping opening hooks for the given topic. "
            "Return JSON: {\"hooks\": [{\"hook\": \"\", \"technique\": \"curiosity|controversy|value|story|shock\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "ai-carousel-copy-generator",
        "name": "AI Carousel Copy Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Topic and number of slides (e.g. 7 slides about productivity)", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a social media content creator. Write compelling carousel slide copy with a hook slide, "
            "value slides, and a CTA slide. "
            "Return JSON: {\"slides\": [{\"slide_number\": 1, \"headline\": \"\", \"body\": \"\"}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "ai-reels-script-outline",
        "name": "AI Reels Script Outline",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Reel topic, niche, and target duration (e.g. 30s, 60s)", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a short-form video content strategist. Write a punchy Reels/TikTok script outline "
            "with hook (0-3s), value delivery, and CTA. Include visual cues and on-screen text suggestions. "
            "Return only the script outline."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "social-content-calendar-planner",
        "name": "Social Content Calendar Planner",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Niche, platforms, and posting frequency (e.g. 3x/week)", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a social media strategist. Create a 4-week content calendar with post ideas, formats, and captions. "
            "Return JSON: {\"weeks\": [{\"week\": 1, \"posts\": [{\"day\": \"\", \"platform\": \"\", \"format\": \"\", \"topic\": \"\", \"caption_idea\": \"\"}]}]}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "platform-tone-rewriter",
        "name": "Platform Tone Rewriter",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Your content and target platform (LinkedIn/Twitter/Instagram/TikTok)", "required": True, "max_length": 2000},
        ],
        "system_prompt": (
            "You are a social media content expert. Rewrite the provided content optimised for each major platform's "
            "tone and format. Return JSON: {\"linkedin\": \"\", \"twitter\": \"\", \"instagram\": \"\", \"tiktok\": \"\"}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 0,
    },
    {
        "slug": "influencer-collab-pitch-generator",
        "name": "Influencer Collab Pitch Generator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Your brand/product and target influencer niche", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a brand partnerships expert. Write a professional, personalised influencer collaboration pitch "
            "with subject line, introduction, value proposition, deliverables, and CTA. Return only the pitch text."
        ),
        "user_prompt_template": "{input}",
        "response_format": "text",
        "cache_ttl": 0,
    },
    {
        "slug": "engagement-benchmark-estimator",
        "name": "Engagement Benchmark Estimator",
        "category": "creator",
        "input_fields": [
            {"name": "prompt", "label": "Platform, follower count, niche, and recent post performance", "required": True, "max_length": 500},
        ],
        "system_prompt": (
            "You are a social media analytics expert. Estimate engagement benchmarks and provide actionable advice. "
            "Return JSON: {\"benchmark_rate\": \"\", \"your_estimate\": \"\", \"rating\": \"below/at/above average\", "
            "\"tips\": []}"
        ),
        "user_prompt_template": "{input}",
        "response_format": "json",
        "cache_ttl": 3600,
    },
]

# ── Registry lookup helpers ──────────────────────────────────────────────────

_REGISTRY_BY_SLUG: Dict[str, Dict[str, Any]] = {t["slug"]: t for t in TOOL_REGISTRY}


def get_tool(slug: str) -> Optional[Dict[str, Any]]:
    """Return the tool definition for a given slug, or None."""
    return _REGISTRY_BY_SLUG.get(slug)


def get_all_tools() -> List[Dict[str, Any]]:
    return list(TOOL_REGISTRY)


def get_tools_by_category(category: str) -> List[Dict[str, Any]]:
    return [t for t in TOOL_REGISTRY if t["category"] == category]


def list_slugs() -> List[str]:
    return list(_REGISTRY_BY_SLUG.keys())
