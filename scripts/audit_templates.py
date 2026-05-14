import os
import sys
sys.path.append(os.getcwd())
from config.tool_categories import TOOL_CATEGORIES

TEMPLATES_DIR = 'templates'

def run():
    missing_templates = []
    for category in TOOL_CATEGORIES:
        for tool in category.get('tools', []):
            if not tool.get('is_active', True):
                continue

            template_name = tool.get('template_name')
            if not template_name:
                print(f"Tool {tool.get('slug')} in category {category.get('slug')} is missing 'template_name'")
                continue

            template_path = os.path.join(TEMPLATES_DIR, template_name)
            if not os.path.exists(template_path):
                missing_templates.append(template_path)
                print(f"Missing template for tool '{tool.get('slug')}' in category '{category.get('slug')}': {template_path}")

    if not missing_templates:
        print("All active tool templates found.")
    else:
        print(f"\nFound {len(missing_templates)} missing templates for active tools.")

if __name__ == "__main__":
    run()
