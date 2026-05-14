import os
import sys
from pathlib import Path

import django

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.tools.models import Tool, ToolCategory

print(f"Total Categories: {ToolCategory.objects.count()}")
print(f"Total Tools: {Tool.objects.count()}")

for cat in ToolCategory.objects.all():
    tools_count = Tool.objects.filter(category=cat).count()
    print(f"Category: {cat.name} (slug: {cat.slug}) - Tools: {tools_count}")

# Check first few tools to see if they have categories
for tool in Tool.objects.all()[:5]:
    print(f"Tool: {tool.name} (slug: {tool.slug}) - Category: {tool.category.name} (is_active: {tool.is_active})")
