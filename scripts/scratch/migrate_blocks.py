import glob
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
templates_dir = REPO_ROOT / "templates" / "tools"
files = glob.glob(str(templates_dir / "**" / "*.html"), recursive=True)

count = 0
for file_path in files:
    with open(file_path, 'r') as f:
        content = f.read()
    
    if "block tool_workspace" in content:
        new_content = content.replace("block tool_workspace", "block tool_content")
        with open(file_path, 'w') as f:
            f.write(new_content)
        count += 1

print(f"Updated {count} files")
