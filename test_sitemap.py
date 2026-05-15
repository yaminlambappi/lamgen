import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import Client
from apps.seo.engine.sitemap import get_sitemap_sections
from django.urls import reverse
from django.conf import settings

def check_urls():
    client = Client()
    sections = get_sitemap_sections()
    failed = []
    
    print("Checking sitemap urls...")
    for name, sitemap_cls in sections.items():
        print(f"Section: {name}")
        sitemap = sitemap_cls()
        for item in sitemap.items():
            url = None
            try:
                url = sitemap.location(item)
                resp = client.get(url)
                if resp.status_code != 200:
                    print(f"Error {resp.status_code}: {url}")
                    failed.append((url, resp.status_code))
            except Exception as e:
                print(f"Exception for {item}: {url} -> {e}")
                failed.append((url, str(e)))
                
    print(f"Done. Found {len(failed)} issues.")
    
if __name__ == '__main__':
    check_urls()
