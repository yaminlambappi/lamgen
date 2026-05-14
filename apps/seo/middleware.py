from pathlib import Path
from django.conf import settings
from django.utils import timezone


class CrawlErrorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        try:
            if response.status_code == 404 and request.path.startswith(("/tools/", "/content/", "/blog/")):
                log_dir = Path(settings.BASE_DIR) / "logs"
                log_dir.mkdir(parents=True, exist_ok=True)
                ref = request.META.get("HTTP_REFERER", "-")
                line = f"{timezone.now().isoformat()} 404 {request.path} {ref}\n"
                with (log_dir / "crawl_errors.log").open("a", encoding="utf-8") as fp:
                    fp.write(line)
        except Exception:
            pass
        return response
