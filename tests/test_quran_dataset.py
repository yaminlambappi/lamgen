from django.template.loader import render_to_string

from tools.services.islamic_panel import PrayerTimesService, IslamicContentService
from tools.services.quran import QuranDatasetService


def test_quran_dataset_is_verified_and_consistent():
    dataset = QuranDatasetService.load_dataset(force_refresh=True)

    assert dataset["meta"]["translation_source"] == "Saheeh International"
    assert dataset["meta"]["entry_count"] == len(dataset["ayat"]) == 40
    assert (
        QuranDatasetService._compute_ayah_hash(dataset["ayat"])
        == dataset["meta"]["ayah_sha256"]
    )
    assert all(ayah["translation_source"] == "Saheeh International" for ayah in dataset["ayat"])
    assert all(isinstance(ayah["ayah_number"], int) for ayah in dataset["ayat"])
    assert all("<" not in ayah["translation_text"] and ">" not in ayah["translation_text"] for ayah in dataset["ayat"])


def test_spiritual_banner_renders_global_islamic_strip():
    panel = IslamicContentService.get_panel_context()
    panel["api_url"] = "/tools/api/islamic-panel/"
    panel["prayer"] = PrayerTimesService._build_placeholder_snapshot(23.8103, 90.4125, fallback_label="Dhaka, Bangladesh")
    html = render_to_string(
        "partials/spiritual_banner.html",
        {"islamic_panel": panel},
    )

    assert "Prayer Times" in html
    assert "Daily Dua" in html
    assert "Hadith" in html
    assert "Dhaka, Bangladesh" in html
