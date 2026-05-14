import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sys
import os

sys.path.append(os.getcwd())

from config.tool_registry import prepare_registry

BASE_URL = "http://localhost:8000"


def crawl():
    """Crawl the site and check for broken links."""
    all_links = set()
    broken_links = set()

    # Get all tool URLs
    registry = prepare_registry()
    for category in registry:
        for tool in category.get("tools", []):
            if tool.get("is_active"):
                all_links.add(urljoin(BASE_URL, f"/tools/{category['slug']}/{tool['slug']}/"))

    # Crawl each page and find more links
    crawled_links = set()
    while all_links:
        link = all_links.pop()
        if link in crawled_links:
            continue

        try:
            response = requests.get(link, timeout=10)
            crawled_links.add(link)

            if response.status_code != 200:
                broken_links.add((link, response.status_code))
                print(f"Broken link: {link} (status code: {response.status_code})")
                continue

            soup = BeautifulSoup(response.content, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                new_link = urljoin(BASE_URL, a_tag["href"])
                if new_link.startswith(BASE_URL) and new_link not in crawled_links:
                    all_links.add(new_link)

        except requests.exceptions.RequestException as e:
            broken_links.add((link, str(e)))
            print(f"Broken link: {link} (error: {e})")

    print("\n--- Crawl Report ---")
    print(f"Total links found: {len(crawled_links)}")
    print(f"Total broken links: {len(broken_links)}")
    for link, error in broken_links:
        print(f"- {link}: {error}")

if __name__ == "__main__":
    crawl()
