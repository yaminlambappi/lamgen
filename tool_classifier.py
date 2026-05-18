
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
                    return ast.literal_eval(node.value)
    return []

def classify_tools():
    ai_tools = []
    non_ai_tools = []
    uncertain_tools = []

    base_tools = get_tools_from_file("config/tool_categories.py", "_TOOL_CATEGORIES_BASE")
    ecosystem_tools = get_tools_from_file("config/tool_categories_ecosystem.py", "ECOSYSTEM_TOOL_CATEGORIES")

    all_categories = base_tools + ecosystem_tools

    for category in all_categories:
        for tool in category.get("tools", []):
            is_ai = tool.get("is_ai_powered", False)
            slug = tool.get("slug", "")

            if is_ai:
                ai_tools.append(slug)
            elif "ai-" in slug:
                uncertain_tools.append(slug)
            else:
                non_ai_tools.append(slug)

    return ai_tools, non_ai_tools, uncertain_tools

if __name__ == "__main__":
    # First, let's check if the ecosystem file exists.
    if not os.path.exists("config/tool_categories_ecosystem.py"):
        # Let's create an empty file to avoid errors.
        with open("config/tool_categories_ecosystem.py", "w") as f:
            f.write("ECOSYSTEM_TOOL_CATEGORIES = []")

    ai, non_ai, uncertain = classify_tools()

    print("--- AI TOOLS ---")
    for tool in sorted(list(set(ai))):
        print(tool)

    print("\n--- NON-AI TOOLS ---")
    for tool in sorted(list(set(non_ai))):
        print(tool)

    print("\n--- UNCERTAIN TOOLS ---")
    for tool in sorted(list(set(uncertain))):
        print(tool)
