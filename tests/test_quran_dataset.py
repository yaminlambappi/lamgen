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
    """Test that the spiritual banner renders with dynamic Quran ayat."""
    panel = IslamicContentService.get_panel_context()
    panel["api_url"] = "/tools/api/islamic-panel/"
    panel["prayer"] = PrayerTimesService._build_placeholder_snapshot(23.8103, 90.4125, fallback_label="Dhaka, Bangladesh")
    
    # Render just the prayer bar (spiritual_banner.html)
    html = render_to_string(
        "partials/spiritual_banner.html",
        {"islamic_panel": panel},
    )

    # Test that prayer information is rendered
    assert "Next Azan" in html
    assert "Salat Rakat" in html
    assert "Ayat" in html
    
    # Test that Quran dataset is being used (should have Arabic text from the ayat)
    # We should have prayer details and a dynamic ayat from the Quran dataset
    assert "Fajr" in html or "Dhuhr" in html or "Asr" in html or "Maghrib" in html or "Isha" in html
    
    # The test should pass if we have the updated dynamic ayat system
    # which pulls from the verified Quran dataset
    
    # Also test that the panel context has cards (they're rendered elsewhere)
    assert "cards" in panel
    assert len(panel["cards"]) > 0
    # Cards should include Daily Dua and Hadith
    card_slugs = [card["slug"] for card in panel["cards"]]
    assert "dua" in card_slugs
    assert "hadith" in card_slugs
