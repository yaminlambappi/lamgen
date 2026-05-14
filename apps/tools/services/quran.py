import hashlib
import json
import re
from pathlib import Path

from django.conf import settings
from django.core.cache import cache


class QuranDatasetError(ValueError):
    """Raised when the verified Quran dataset fails validation."""


class QuranDatasetService:
    """Load and verify the static Quran banner dataset."""

    CACHE_KEY = "tools:quran_banner_dataset:v1"
    CACHE_TTL = 60 * 60 * 12
    DATASET_PATH = settings.BASE_DIR / "static" / "data" / "quran" / "verified_banner_ayat.json"
    ALLOWED_SOURCES = {
        "Saheeh International",
        "Dr. Mustafa Khattab (The Clear Quran)",
        "Pickthall",
        "Yusuf Ali",
    }
    VERSE_KEY_RE = re.compile(r"^\d+:\d+$")
    SHA256_RE = re.compile(r"^[a-f0-9]{64}$")

    @classmethod
    def load_dataset(cls, *, force_refresh=False):
        if not force_refresh:
            try:
                cached = cache.get(cls.CACHE_KEY)
            except Exception:
                cached = None
            if cached is not None:
                return cached

        dataset = cls._load_from_disk()
        try:
            cache.set(cls.CACHE_KEY, dataset, cls.CACHE_TTL)
        except Exception:
            pass
        return dataset

    @classmethod
    def get_default_ayah(cls):
        dataset = cls.load_dataset()
        return dataset["ayat"][0]

    @classmethod
    def get_ayah_map(cls):
        dataset = cls.load_dataset()
        return {ayah["verse_key"]: ayah for ayah in dataset["ayat"]}

    @classmethod
    def _load_from_disk(cls):
        if not cls.DATASET_PATH.exists():
            raise QuranDatasetError(f"Quran dataset file not found: {cls.DATASET_PATH}")

        try:
            dataset = json.loads(cls.DATASET_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise QuranDatasetError("Quran dataset JSON is malformed.") from exc

        cls._validate_dataset(dataset)
        return dataset

    @classmethod
    def _validate_dataset(cls, dataset):
        if not isinstance(dataset, dict):
            raise QuranDatasetError("Quran dataset root must be an object.")

        meta = dataset.get("meta")
        ayat = dataset.get("ayat")
        if not isinstance(meta, dict) or not isinstance(ayat, list) or not ayat:
            raise QuranDatasetError("Quran dataset must contain non-empty meta and ayat sections.")

        translation_source = meta.get("translation_source")
        expected_hash = meta.get("ayah_sha256")
        if translation_source not in cls.ALLOWED_SOURCES:
            raise QuranDatasetError("Quran dataset uses an unapproved translation source.")
        if not isinstance(expected_hash, str) or not cls.SHA256_RE.match(expected_hash):
            raise QuranDatasetError("Quran dataset is missing its checksum.")

        seen_keys = set()
        for ayah in ayat:
            cls._validate_ayah(ayah, translation_source, seen_keys)

        computed_hash = cls._compute_ayah_hash(ayat)
        if computed_hash != expected_hash:
            raise QuranDatasetError("Quran dataset checksum mismatch.")

        if meta.get("entry_count") != len(ayat):
            raise QuranDatasetError("Quran dataset entry count does not match its metadata.")

    @classmethod
    def _validate_ayah(cls, ayah, translation_source, seen_keys):
        required_fields = (
            "verse_key",
            "surah_number",
            "surah_name",
            "ayah_number",
            "arabic_text",
            "translation_text",
            "translation_source",
        )
        if not isinstance(ayah, dict) or any(field not in ayah for field in required_fields):
            raise QuranDatasetError("Quran dataset contains an incomplete ayah entry.")

        verse_key = ayah["verse_key"]
        if not isinstance(verse_key, str) or not cls.VERSE_KEY_RE.match(verse_key):
            raise QuranDatasetError("Quran dataset contains an invalid verse key.")
        if verse_key in seen_keys:
            raise QuranDatasetError("Quran dataset contains duplicate verses.")
        seen_keys.add(verse_key)

        if not isinstance(ayah["surah_number"], int) or ayah["surah_number"] < 1:
            raise QuranDatasetError("Quran dataset contains an invalid surah number.")
        if not isinstance(ayah["ayah_number"], int) or ayah["ayah_number"] < 1:
            raise QuranDatasetError("Quran dataset contains an invalid ayah number.")
        if ayah["translation_source"] != translation_source:
            raise QuranDatasetError("Quran dataset mixes translation sources.")

        for text_field in ("surah_name", "arabic_text", "translation_text", "translation_source"):
            value = ayah[text_field]
            if not isinstance(value, str) or not value.strip():
                raise QuranDatasetError(f"Quran dataset field {text_field} is empty.")
            if "<" in value or ">" in value:
                raise QuranDatasetError(f"Quran dataset field {text_field} contains markup.")

    @classmethod
    def _compute_ayah_hash(cls, ayat):
        canonical_json = json.dumps(
            ayat,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
