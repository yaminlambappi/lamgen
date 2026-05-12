"""Staff-only admin views for operational dashboards."""

from __future__ import annotations

import json
from pathlib import Path

from django.conf import settings
from django.shortcuts import render


def tool_system_health_view(request):
    """Admin → System Health: latest Playwright tool audit summary."""
    root = Path(settings.BASE_DIR) / "reports" / "tool_health"
    latest = root / "latest.json"
    report = None
    error_message = None
    paths = {
        "latest_json": str(latest),
        "latest_html": str(root / "latest_dashboard.html"),
    }
    try:
        if latest.is_file():
            report = json.loads(latest.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        error_message = f"Could not read report: {exc}"

    return render(
        request,
        "admin/tool_health.html",
        {
            "title": "System Health",
            "report": report,
            "error_message": error_message,
            "paths": paths,
        },
    )
