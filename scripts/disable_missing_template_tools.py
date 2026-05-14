import re
import ast

def run():
    with open('missing_templates.txt', 'r') as f:
        missing_templates_output = f.read()

    missing_tools = []
    for line in missing_templates_output.strip().split('\n'):
        match = re.search(r"Missing template for tool '(.+?)' in category '(.+?)'", line)
        if match:
            tool_slug, category_slug = match.groups()
            missing_tools.append((category_slug, tool_slug))

    # Process config/tool_categories.py
    process_tool_file('config/tool_categories.py', missing_tools)

    # Process config/tool_categories_ecosystem.py
    process_tool_file('config/tool_categories_ecosystem.py', missing_tools)

def process_tool_file(filepath, missing_tools):
    with open(filepath, 'r') as f:
        content = f.read()

    # It's a string representation of a list of dicts, not straight python, so we can't easily import it.
    # Instead, we'll do string manipulation.

    for category_slug, tool_slug in missing_tools:
        # This is getting complex, let's try to find the tool and category and then update the is_active flag
        # We can find the tool by its slug
        tool_marker = f"'slug': '{tool_slug}'"
        content_parts = content.split(tool_marker)

        if len(content_parts) > 1:
            # find the is_active flag
            is_active_marker = "'is_active': True"
            if is_active_marker in content_parts[1]:
                # replace it
                content_parts[1] = content_parts[1].replace(is_active_marker, "'is_active': False", 1)
                content = tool_marker.join(content_parts)

    with open(filepath, 'w') as f:
        f.write(content)

    print(f"Updated {filepath} to disable tools with missing templates.")


if __name__ == "__main__":
    run()
