import os
import sys
from pathlib import Path

import django

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
django.setup()

from apps.tools.models import ToolCategory

cats = ToolCategory.objects.filter(name__icontains='Workspace')
count = 0
for c in cats:
    old_name = c.name
    c.name = c.name.replace('Workspace', 'Tools')
    c.save()
    print(f"Renamed: {old_name} -> {c.name}")
    count += 1

print(f"Updated {count} categories")
