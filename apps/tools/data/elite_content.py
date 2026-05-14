PRIORITY_TOOL_SLUGS = [
    "json-formatter", "image-compressor", "word-counter", "gpa-calculator",
    "password-generator", "qr-generator", "uuid-generator", "unit-converter",
    "case-converter", "pdf-merge", "base64-encoder", "hash-generator",
    "markdown-previewer", "regex-tester", "css-formatter", "js-formatter",
    "color-converter", "age-calculator", "countdown-timer", "url-encoder",
]


def _entry(slug):
    return {
        "examples": [
            {"label": "Example 1", "input": f"Sample input for {slug}", "output": f"Sample output for {slug}"},
            {"label": "Example 2", "input": f"Advanced input for {slug}", "output": f"Advanced output for {slug}"},
        ],
        "why_use": [
            "Fast browser-based workflow with no installation.",
            "Privacy-first processing without mandatory sign-in.",
            "Consistent results for professional use.",
        ],
        "common_mistakes": [
            {"mistake": "Invalid or incomplete input", "solution": "Double-check syntax/format before running."},
            {"mistake": "Skipping result verification", "solution": "Review output and edge cases before publishing."},
        ],
        "how_it_works": [
            "Paste or enter your input.",
            "Run the tool action.",
            "Copy, share, or download the generated result.",
        ],
        "comparison": [
            {"tool_slug": "json-formatter", "differentiator": "Focused formatter workflow."},
            {"tool_slug": "hash-generator", "differentiator": "Focused integrity/hash workflow."},
        ],
        "keyboard_shortcut": "Ctrl+Enter",
        "api_snippet": slug in {"json-formatter", "uuid-generator", "hash-generator", "base64-encoder"},
    }


ELITE_TOOL_DATA = {slug: _entry(slug) for slug in PRIORITY_TOOL_SLUGS}
