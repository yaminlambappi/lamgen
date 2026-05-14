from xml.etree import ElementTree
from urllib.request import urlopen, Request
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Validate sitemap index and child sitemaps."

    def handle(self, *args, **options):
        root = settings.SITE_URL.rstrip("/")
        index_url = f"{root}/sitemap.xml"
        self.stdout.write(f"Checking {index_url}")
        req = Request(index_url, headers={"User-Agent": "LamGen Sitemap Validator"})
        with urlopen(req, timeout=10) as res:
            if res.status != 200:
                raise CommandError(f"sitemap index returned {res.status}")
            xml_bytes = res.read()

        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        tree = ElementTree.fromstring(xml_bytes)
        urls = [n.text for n in tree.findall(".//sm:loc", ns) if n.text]
        failures = []
        for url in urls:
            try:
                with urlopen(Request(url, headers={"User-Agent": "LamGen Sitemap Validator"}), timeout=10) as res:
                    if res.status != 200:
                        failures.append((url, res.status))
            except Exception as exc:
                failures.append((url, str(exc)))

        if failures:
            for url, err in failures:
                self.stdout.write(self.style.ERROR(f"FAIL {url} ({err})"))
            raise CommandError("Sitemap validation failed.")
        self.stdout.write(self.style.SUCCESS("All sitemap URLs returned HTTP 200."))
