SCHEMA = {
    "type": "object",
    "properties": {
        "score": {"type": "integer"},
        "suggestions": {
            "type": "array",
            "items": {"type": "string"},
        },
    },
    "required": ["score", "suggestions"],
}
