import importlib

def get_schema(tool_slug):
    try:
        module = importlib.import_module(f"structured_outputs.schemas.{tool_slug.replace('-', '_')}")
        return module.SCHEMA
    except (ImportError, AttributeError):
        return None
