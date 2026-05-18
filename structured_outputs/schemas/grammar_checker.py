SCHEMA = {
    "type": "object",
    "properties": {
        "corrected_text": {"type": "string"},
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "correction": {"type": "string"},
                },
                "required": ["error", "correction"],
            },
        },
    },
    "required": ["corrected_text"],
}
