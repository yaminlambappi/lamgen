import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
os.chdir(REPO_ROOT)

APPS_TO_FIX = ["tools", "seo", "games", "blog"]

for app in APPS_TO_FIX:
    app_path = REPO_ROOT / "apps" / app
    for root, dirs, files in os.walk(str(app_path)):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                with open(file_path, "r") as f:
                    content = f.read()
                
                # Fix from app. ... to from apps.app. ...
                new_content = content.replace(f"from {app}", f"from apps.{app}")
                new_content = new_content.replace("from seo.models", "from apps.seo.models")
                new_content = new_content.replace("from tools.models", "from apps.tools.models")
                new_content = new_content.replace("from games.models", "from apps.games.models")
                new_content = new_content.replace("from blog.models", "from apps.blog.models")


                
                if content != new_content:
                    print(f"Updating {file_path}")
                    with open(file_path, "w") as f:
                        f.write(new_content)
