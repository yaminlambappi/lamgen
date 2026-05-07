from datetime import datetime, timezone as dt_timezone
from unittest.mock import patch

from django.template.loader import render_to_string
from django.urls import reverse

from tools.services.islamic_panel import IslamicContentService, PrayerTimesService


SAMPLE_PRAYER_PAYLOAD = {
    "code": 200,
    "status": "OK",
    "data": {
        "timings": {
            "Fajr": "04:14",
            "Dhuhr": "11:55",
            "Asr": "15:19",
            "Maghrib": "18:30",
            "Isha": "19:37",
        },
        "date": {
            "gregorian": {
                "date": "07-05-2026",
                "day": "07",
                "month": {"en": "May"},
                "year": "2026",
                "weekday": {"en": "Thursday"},
            },
            "hijri": {
                "date": "20-11-1447",
                "day": "20",
                "month": {"en": "Dhū al-Qaʿdah"},
                "year": "1447",
            },
        },
        "meta": {
            "latitude": 23.8103,
            "longitude": 90.4125,
            "timezone": "Asia/Dhaka",
            "method": {"name": "Islamic Society of North America (ISNA)"},
        },
    },
}


def test_prayer_times_service_builds_snapshot():
    fake_now = datetime(2026, 5, 7, 5, 0, tzinfo=dt_timezone.utc)

    with patch.object(PrayerTimesService, "_cache_get", return_value=None), \
         patch.object(PrayerTimesService, "_cache_set"), \
         patch.object(PrayerTimesService, "_network_allowed", return_value=True), \
         patch.object(PrayerTimesService, "_fetch_prayer_payload", return_value=SAMPLE_PRAYER_PAYLOAD), \
         patch.object(PrayerTimesService, "_resolve_location_label", return_value="Dhaka, Bangladesh"), \
         patch("tools.services.islamic_panel.timezone.now", return_value=fake_now):
        snapshot = PrayerTimesService.get_snapshot(latitude="23.8103", longitude="90.4125")

    assert snapshot["location"]["label"] == "Dhaka, Bangladesh"
    assert snapshot["next_prayer"]["name"] == "Dhuhr"
    assert snapshot["current_prayer_name"] == "Fajr"
    assert len(snapshot["prayers"]) == 5
    assert any(prayer["status"] == "next" for prayer in snapshot["prayers"])
    assert snapshot["qibla_bearing"] > 0


def test_islamic_panel_api_returns_snapshot(client):
    sample_snapshot = PrayerTimesService._build_placeholder_snapshot(
        23.8103,
        90.4125,
        fallback_label="Dhaka, Bangladesh",
    )

    with patch("tools.views.PrayerTimesService.get_snapshot", return_value=sample_snapshot):
        response = client.get(reverse("tools:islamic_panel_api"), {"lat": "23.8103", "lon": "90.4125"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["location"]["label"] == "Dhaka, Bangladesh"
    assert payload["next_prayer"]["name"] in PrayerTimesService.PRAYER_NAMES
    assert payload["next_prayer"]["display_time"] != "--:--"


def test_spiritual_banner_partial_renders_content_cards():
    panel = IslamicContentService.get_panel_context()
    panel["api_url"] = reverse("tools:islamic_panel_api")
    panel["prayer"] = PrayerTimesService._build_placeholder_snapshot(
        23.8103,
        90.4125,
        fallback_label="Dhaka, Bangladesh",
    )

    html = render_to_string("partials/spiritual_banner.html", {"islamic_panel": panel})

    assert "Quran Verse" in html
    assert "Daily Dua" in html
    assert "Reminder" in html
    assert "Hadith" in html
