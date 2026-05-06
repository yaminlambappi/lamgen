import sys
import os
import django

sys.path.append('/home/yamin/Documents/my-project/lamgen')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from tools.models import ToolCategory

cats = ToolCategory.objects.filter(name__icontains='Workspace')
count = 0
for c in cats:
    old_name = c.name
    c.name = c.name.replace('Workspace', 'Tools')
    c.save()
    print(f"Renamed: {old_name} -> {c.name}")
    count += 1

print(f"Updated {count} categories")
