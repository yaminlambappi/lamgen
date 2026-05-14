import re

def run():
    with open("missing_templates.txt", "r") as f:
        missing_templates_output = f.read()

    missing_tools = []
    for line in missing_templates_output.strip().split("\n"):
        match = re.search(r"Missing template for tool \'(.+?)\' in category \'(.+?)\'", line)
        if match:
            tool_slug, category_slug = match.groups()
            missing_tools.append(tool_slug)

    process_file("config/tool_categories.py", missing_tools)
    process_file("config/tool_categories_ecosystem.py", missing_tools)

def process_file(filepath, missing_tools):
    with open(filepath, "r") as f:
        lines = f.readlines()

    new_lines = []
    in_tool = False
    for line in lines:
        if "'slug': '" in line or '"slug": "' in line:
            slug_match = re.search(r"slug'\s*:\s*'([^']*)'", line) or re.search(r'"slug"\s*:\s*"([^"]*)"', line)
            if slug_match:
                slug = slug_match.group(1)
                if slug in missing_tools:
                    in_tool = True
                else:
                    in_tool = False

        if in_tool and ("'is_active': True" in line or '"is_active": True' in line):
            line = line.replace("True", "False")
            in_tool = False # only replace once

        new_lines.append(line)

    with open(filepath, "w") as f:
        f.writelines(new_lines)
    print(f"Updated {filepath}")

if __name__ == "__main__":
    run()
