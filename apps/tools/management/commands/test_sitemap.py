from django.core.management.base import BaseCommand
from django.test import Client
from apps.seo.engine.sitemap import get_sitemap_sections
from django.urls import reverse

class Command(BaseCommand):
    help = "Test sitemap URLs"

    def handle(self, *args, **options):
        client = Client()
        sections = get_sitemap_sections()
        failed = []
        
        self.stdout.write("Checking sitemap urls...")
        for name, sitemap_cls in sections.items():
            self.stdout.write(f"Section: {name}")
            sitemap = sitemap_cls()
            for item in sitemap.items():
                url = None
                try:
                    url = sitemap.location(item)
                    resp = client.get(url)
                    if resp.status_code != 200:
                        self.stdout.write(self.style.ERROR(f"Error {resp.status_code}: {url}"))
                        failed.append((url, resp.status_code))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Exception for {item}: {url} -> {e}"))
                    failed.append((url, str(e)))
                    
        self.stdout.write(f"Done. Found {len(failed)} issues.")
