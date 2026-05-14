import os
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

URL_FILES = [
    REPO_ROOT / "config" / "urls.py",
    REPO_ROOT / "apps" / "users" / "urls.py",
    REPO_ROOT / "apps" / "thesis" / "urls.py",
    REPO_ROOT / "apps" / "generation" / "urls.py",
    REPO_ROOT / "apps" / "games" / "urls.py",
    REPO_ROOT / "apps" / "tools" / "urls.py",
    REPO_ROOT / "apps" / "seo" / "urls.py",
    REPO_ROOT / "apps" / "blog" / "urls.py",
]

all_routes = []


def discover_routes(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            # find all paths
            paths = re.findall(r"path\([\"\'](.*)[\"\']", content)
            for path in paths:
                all_routes.append(path)
            
            # find all included urls
            included_urls = re.findall(r"include\([\"\'](.*)[\"\']\)", content)
            for included_url in included_urls:
                if not included_url.endswith(".urls"):
                    continue
                base = included_url[: -len(".urls")]
                segments = base.split(".")
                if not segments:
                    continue
                url_file = REPO_ROOT.joinpath(*segments) / "urls.py"
                if url_file not in URL_FILES:
                    URL_FILES.append(url_file)

    except FileNotFoundError:
        print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")

for url_file in list(URL_FILES):
    discover_routes(url_file)

for route in all_routes:
    print(route)
