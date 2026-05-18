
import ast
import os

def get_tools_from_file(file_path, list_variable_name):
    with open(file_path, "r") as f:
        content = f.read()

    tree = ast.parse(content)
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if target.id == list_variable_name:
                    # Handle the case where the value is a BinOp (e.g., _TOOL_CATEGORIES_BASE + ECOSYSTEM_TOOL_CATEGORIES)
                    if isinstance(node.value, ast.BinOp):
                        return [] # Return empty for now, will be handled in get_ai_tools_only
                    return ast.literal_eval(node.value)
    return []

def get_ai_tools_only():
    ai_tools = []

    # The tool_categories.py file is in the config directory
    base_registry_path = os.path.join("config", "tool_categories.py")
    ecosystem_registry_path = os.path.join("config", "tool_categories_ecosystem.py")

    # Create ecosystem file if it does not exist
    if not os.path.exists(ecosystem_registry_path):
        with open(ecosystem_registry_path, "w") as f:
            f.write("ECOSYSTEM_TOOL_CATEGORIES = []")

    base_tools = get_tools_from_file(base_registry_path, "_TOOL_CATEGORIES_BASE")
    ecosystem_tools = get_tools_from_file(ecosystem_registry_path, "ECOSYSTEM_TOOL_CATEGORIES")

    all_categories = base_tools + ecosystem_tools

    for category in all_categories:
        for tool in category.get("tools", []):
            is_ai = tool.get("is_ai_powered", False)
            slug = tool.get("slug", "")

            if is_ai:
                ai_tools.append(slug)

    return sorted(list(set(ai_tools)))

if __name__ == "__main__":
    ai_tools = get_ai_tools_only()
    for tool in ai_tools:
        print(tool)
