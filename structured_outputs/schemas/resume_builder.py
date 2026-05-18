SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {"type": "string"},
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "company": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "description": {"type": "string"},
                },
                "required": ["title", "company", "start_date", "end_date", "description"],
            },
        },
        "skills": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["summary", "experience", "skills"],
}
