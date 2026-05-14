import math
import os
import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import httpx
from django.core.cache import cache
from django.utils import timezone

from apps.tools.data.islamic_content import DUA_QURAN_KEYS, FEATURED_QURAN_KEYS, HADITH_CARDS, REMINDER_QURAN_KEYS

from .quran import QuranDatasetService


class PrayerTimesService:
    """Resolve and cache prayer timings for the global Islamic utility strip."""

    DEFAULT_LOCATION = {
        "city": "Dhaka",
        "country": "Bangladesh",
        "label": "Dhaka, Bangladesh",
        "latitude": 23.8103,
        "longitude": 90.4125,
        "timezone": "Asia/Dhaka",
    }
    PRAYER_NAMES = ("Fajr", "Dhuhr", "Asr", "Maghrib", "Isha")
    PRAYER_RAKAT = {
        "Fajr": "2 Farz + 2 Sunnah",
        "Dhuhr": "4 Farz + 2 Sunnah", 
        "Asr": "4 Farz",
        "Maghrib": "3 Farz + 2 Sunnah",
        "Isha": "4 Farz + 2 Sunnah + 3 Witr"
    }
    PRAYER_API = "https://api.aladhan.com/v1/timings"
    REVERSE_GEOCODE_API = "https://nominatim.openstreetmap.org/reverse"
    PRAYER_CACHE_TTL = 60 * 60 * 6
    LOCATION_CACHE_TTL = 60 * 60 * 24
    QIBLA_COORDS = (21.4225, 39.8262)
    FALLBACK_TIMINGS = {
        "Fajr": "04:45",
        "Dhuhr": "12:10",
        "Asr": "15:35",
        "Maghrib": "18:20",
        "Isha": "19:40",
    }

    @classmethod
    def get_default_snapshot(cls):
        today = timezone.localdate()
        cache_key = f"islamic:prayer:default:{today.isoformat()}"
        cached = cls._cache_get(cache_key)
        if cached is not None:
            return cached

        snapshot = cls._get_snapshot_for_coords(
            cls.DEFAULT_LOCATION["latitude"],
            cls.DEFAULT_LOCATION["longitude"],
            fallback_label=cls.DEFAULT_LOCATION["label"],
        )
        cls._cache_set(cache_key, snapshot, cls.PRAYER_CACHE_TTL)
        return snapshot

    @classmethod
    def get_snapshot(cls, *, latitude=None, longitude=None):
        if latitude is None or longitude is None:
            return cls.get_default_snapshot()

        normalized = cls._normalize_coords(latitude, longitude)
        if normalized is None:
            return cls.get_default_snapshot()

        lat, lon = normalized
        return cls._get_snapshot_for_coords(lat, lon)

    @classmethod
    def _get_snapshot_for_coords(cls, latitude, longitude, fallback_label=None):
        date_key = timezone.localdate().isoformat()
        coords_key = cls._coords_key(latitude, longitude)
        cache_key = f"islamic:prayer:{date_key}:{coords_key}"
        cached = cls._cache_get(cache_key)
        if cached is not None:
            return cached

        payload = None
        if cls._network_allowed():
            payload = cls._fetch_prayer_payload(latitude, longitude)

        if payload is not None:
            location_label = cls._resolve_location_label(latitude, longitude) or fallback_label
            snapshot = cls._build_snapshot_from_payload(payload, location_label=location_label)
        else:
            snapshot = cls._build_placeholder_snapshot(latitude, longitude, fallback_label=fallback_label)

        cls._cache_set(cache_key, snapshot, cls.PRAYER_CACHE_TTL)
        return snapshot

    @classmethod
    def _fetch_prayer_payload(cls, latitude, longitude):
        try:
            response = httpx.get(
                cls.PRAYER_API,
                params={"latitude": latitude, "longitude": longitude, "method": 2},
                timeout=3.0,
                headers={"User-Agent": "LamGen Islamic Utility/1.0"},
            )
            response.raise_for_status()
            data = response.json()
            if data.get("code") != 200:
                return None
            return data
        except Exception:
            return None

    @classmethod
    def _resolve_location_label(cls, latitude, longitude):
        coords_key = cls._coords_key(latitude, longitude)
        cache_key = f"islamic:location:{coords_key}"
        cached = cls._cache_get(cache_key)
        if cached is not None:
            return cached

        if not cls._network_allowed():
            return None

        try:
            response = httpx.get(
                cls.REVERSE_GEOCODE_API,
                params={"format": "jsonv2", "lat": latitude, "lon": longitude},
                timeout=3.0,
                headers={"User-Agent": "LamGen Islamic Utility/1.0"},
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return None

        address = payload.get("address", {})
        city = (
            address.get("city")
            or address.get("town")
            or address.get("municipality")
            or address.get("county")
            or address.get("state_district")
        )
        country = address.get("country")
        if not city and not country:
            return None

        label = ", ".join(part for part in (city, country) if part)
        cls._cache_set(cache_key, label, cls.LOCATION_CACHE_TTL)
        return label

    @classmethod
    def _build_snapshot_from_payload(cls, payload, *, location_label=None):
        data = payload["data"]
        meta = data["meta"]
        tz_name = meta.get("timezone") or cls.DEFAULT_LOCATION["timezone"]
        zone = ZoneInfo(tz_name)
        now_local = timezone.now().astimezone(zone)

        timings = data["timings"]
        prayer_entries = []
        for prayer_name in cls.PRAYER_NAMES:
            raw_time = str(timings.get(prayer_name, "--:--")).split(" ")[0]
            display_time = cls._format_time_display(raw_time, zone)
            prayer_entries.append(
                {
                    "name": prayer_name,
                    "time_24": raw_time,
                    "display_time": display_time,
                    "status": "upcoming",
                }
            )

        next_prayer_name, current_prayer_name, next_prayer_at = cls._resolve_prayer_status(
            prayer_entries,
            now_local,
            zone,
        )

        for entry in prayer_entries:
            if entry["name"] == next_prayer_name:
                entry["status"] = "next"
            elif entry["name"] == current_prayer_name:
                entry["status"] = "current"
            else:
                entry["status"] = "upcoming"

        gregorian = data["date"]["gregorian"]
        hijri = data["date"]["hijri"]

        resolved_label = location_label or cls.DEFAULT_LOCATION["label"]
        qibla_bearing = cls._calculate_qibla_bearing(float(meta["latitude"]), float(meta["longitude"]))

        return {
            "location": {
                "label": resolved_label,
                "city": resolved_label.split(",")[0],
                "country": resolved_label.split(",")[-1].strip() if "," in resolved_label else "",
                "latitude": float(meta["latitude"]),
                "longitude": float(meta["longitude"]),
                "timezone": tz_name,
            },
            "dates": {
                "gregorian_label": f'{gregorian["weekday"]["en"]}, {gregorian["day"]} {gregorian["month"]["en"]} {gregorian["year"]}',
                "gregorian_iso": cls._to_iso_date(gregorian["date"]),
                "hijri_label": f'{hijri["day"]} {hijri["month"]["en"]} {hijri["year"]} AH',
                "hijri_iso": hijri["date"],
            },
            "prayers": prayer_entries,
            "next_prayer": {
                "name": next_prayer_name,
                "display_time": cls._format_time_display(cls._datetime_to_hhmm(next_prayer_at), zone),
                "timestamp": next_prayer_at.isoformat(),
                "rakat": cls.PRAYER_RAKAT.get(next_prayer_name, "4 Rakat"),
            },
            "current_prayer_name": current_prayer_name,
            "qibla_bearing": qibla_bearing,
            "method_name": meta["method"]["name"],
            "source": "AlAdhan API",
            "daily_ayat": cls._get_daily_ayat(),
            "is_fallback": False,
        }

    @classmethod
    def _build_placeholder_snapshot(cls, latitude, longitude, *, fallback_label=None):
        zone = ZoneInfo(cls.DEFAULT_LOCATION["timezone"])
        now = timezone.now().astimezone(zone)
        lat = latitude if latitude is not None else cls.DEFAULT_LOCATION["latitude"]
        lon = longitude if longitude is not None else cls.DEFAULT_LOCATION["longitude"]
        qibla_bearing = cls._calculate_qibla_bearing(lat, lon)
        prayer_entries = []
        for prayer_name in cls.PRAYER_NAMES:
            raw_time = cls.FALLBACK_TIMINGS[prayer_name]
            prayer_entries.append(
                {
                    "name": prayer_name,
                    "time_24": raw_time,
                    "display_time": cls._format_time_display(raw_time, zone),
                    "status": "upcoming",
                }
            )

        next_prayer_name, current_prayer_name, next_prayer_at = cls._resolve_prayer_status(
            prayer_entries,
            now,
            zone,
        )
        for entry in prayer_entries:
            if entry["name"] == next_prayer_name:
                entry["status"] = "next"
            elif entry["name"] == current_prayer_name:
                entry["status"] = "current"
            else:
                entry["status"] = "upcoming"

        return {
            "location": {
                "label": fallback_label or cls.DEFAULT_LOCATION["label"],
                "city": (fallback_label or cls.DEFAULT_LOCATION["label"]).split(",")[0],
                "country": cls.DEFAULT_LOCATION["country"],
                "latitude": lat,
                "longitude": lon,
                "timezone": cls.DEFAULT_LOCATION["timezone"],
            },
            "dates": {
                "gregorian_label": now.strftime("%A, %d %B %Y"),
                "gregorian_iso": now.date().isoformat(),
                "hijri_label": "Hijri date syncing",
                "hijri_iso": "",
            },
            "prayers": prayer_entries,
            "next_prayer": {
                "name": next_prayer_name,
                "display_time": cls._format_time_display(cls._datetime_to_hhmm(next_prayer_at), zone),
                "timestamp": next_prayer_at.isoformat(),
                "rakat": cls.PRAYER_RAKAT.get(next_prayer_name, "4 Rakat"),
            },
            "current_prayer_name": current_prayer_name,
            "qibla_bearing": qibla_bearing,
            "method_name": "Location-aware prayer timing",
            "source": "LamGen fallback",
            "daily_ayat": cls._get_daily_ayat(),
            "is_fallback": True,
        }

    @classmethod
    def _resolve_prayer_status(cls, prayer_entries, now_local, zone):
        schedule = []
        for entry in prayer_entries:
            hour, minute = cls._split_hhmm(entry["time_24"])
            prayer_dt = now_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
            schedule.append((entry["name"], prayer_dt))

        next_name = cls.PRAYER_NAMES[0]
        next_at = schedule[0][1].replace(day=now_local.day)
        current_name = cls.PRAYER_NAMES[-1]
        previous_name = cls.PRAYER_NAMES[-1]

        for prayer_name, prayer_dt in schedule:
            if prayer_dt <= now_local:
                previous_name = prayer_name
            if prayer_dt > now_local:
                next_name = prayer_name
                next_at = prayer_dt
                current_name = previous_name
                break
        else:
            next_name = cls.PRAYER_NAMES[0]
            current_name = cls.PRAYER_NAMES[-1]
            first_today = schedule[0][1]
            next_at = first_today + timedelta(days=1)

        return next_name, current_name, next_at.astimezone(zone)

    @classmethod
    def _calculate_qibla_bearing(cls, latitude, longitude):
        kaaba_lat, kaaba_lon = cls.QIBLA_COORDS
        lat1 = math.radians(latitude)
        lon1 = math.radians(longitude)
        lat2 = math.radians(kaaba_lat)
        lon2 = math.radians(kaaba_lon)
        delta_lon = lon2 - lon1

        x = math.sin(delta_lon)
        y = math.cos(lat1) * math.tan(lat2) - math.sin(lat1) * math.cos(delta_lon)
        bearing = math.degrees(math.atan2(x, y))
        return int(round((bearing + 360) % 360))

    @staticmethod
    def _format_time_display(hhmm, zone):
        hour, minute = PrayerTimesService._split_hhmm(hhmm)
        if hour is None:
            return "--:--"
        dt = datetime(2000, 1, 1, hour, minute, tzinfo=zone)
        return dt.strftime("%I:%M %p").lstrip("0")

    @staticmethod
    def _datetime_to_hhmm(value):
        return value.strftime("%H:%M")

    @staticmethod
    def _split_hhmm(value):
        try:
            hours, minutes = value.split(":")
            return int(hours), int(minutes)
        except Exception:
            return None, None

    @staticmethod
    def _to_iso_date(value):
        day, month, year = value.split("-")
        return f"{year}-{month}-{day}"

    @staticmethod
    def _coords_key(latitude, longitude):
        return f"{latitude:.3f}:{longitude:.3f}"

    @staticmethod
    def _normalize_coords(latitude, longitude):
        try:
            lat = round(float(latitude), 3)
            lon = round(float(longitude), 3)
        except (TypeError, ValueError):
            return None
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return lat, lon

    @staticmethod
    def _network_allowed():
        return not (os.environ.get("PYTEST_CURRENT_TEST") or any("pytest" in arg for arg in sys.argv))

    @staticmethod
    def _cache_get(key):
        try:
            return cache.get(key)
        except Exception:
            return None

    @staticmethod
    def _cache_set(key, value, ttl):
        try:
            cache.set(key, value, ttl)
        except Exception:
            pass

    @classmethod
    def _get_daily_ayat(cls):
        """Get a dynamic rotating Quranic Ayat from the verified dataset with intelligent caching.
        
        Uses a rotating selection based on date to prevent repeating the same ayat frequently
        while maintaining cache efficiency. The same ayat is shown all day but changes daily.
        """
        today = timezone.localdate()
        cache_key = f"islamic:daily_ayat:{today.isoformat()}"
        cached_ayat = cls._cache_get(cache_key)
        
        if cached_ayat is not None:
            return cached_ayat
        
        # Load the verified Quran dataset
        try:
            ayah_map = QuranDatasetService.get_ayah_map()
            if not ayah_map:
                return cls._get_fallback_ayat()
            
            ayat_list = list(ayah_map.values())
            
            # Use date-based rotation to select an ayat
            # This ensures the same ayat is shown all day, but changes daily
            index = today.toordinal() % len(ayat_list)
            selected = ayat_list[index]
            
            ayat_data = {
                "arabic": selected.get("arabic_text", ""),
                "translation": selected.get("translation_text", ""),
                "surah": f"Surah {selected.get('surah_name', '')}",
                "ayah": selected.get("verse_key", ""),
            }
            
            cls._cache_set(cache_key, ayat_data, 60 * 60 * 24)  # Cache for 24 hours
            return ayat_data
            
        except Exception:
            return cls._get_fallback_ayat()
    
    @staticmethod
    def _get_fallback_ayat():
        """Fallback ayat data if Quran dataset is unavailable."""
        return {
            "arabic": "قُلْ هُوَ اللَّهُ أَحَدٌ",
            "translation": "Say, 'He is Allah, [who is] One.'",
            "surah": "Surah Al-Ikhlas",
            "ayah": "112:1"
        }



class IslamicContentService:
    """Build the static non-prayer cards for the global Islamic strip."""

    CARD_CONFIG = (
        ("quran", "Quran Verse", "bi-book-half", FEATURED_QURAN_KEYS),
        ("dua", "Daily Dua", "bi-stars", DUA_QURAN_KEYS),
        ("reminder", "Reminder", "bi-moon-stars", REMINDER_QURAN_KEYS),
    )

    @classmethod
    def get_panel_context(cls):
        today = timezone.localdate()
        cache_key = f"islamic:panel:{today.isoformat()}"
        cached = PrayerTimesService._cache_get(cache_key)
        if cached is not None:
            return cached

        panel_context = {
            "cards": cls.get_daily_cards(reference_date=today),
            "prayer": PrayerTimesService.get_default_snapshot(),
        }
        # Cache for 12 hours to balance freshness and performance
        PrayerTimesService._cache_set(cache_key, panel_context, 60 * 60 * 12)
        return panel_context

    @classmethod
    def get_daily_cards(cls, *, reference_date=None):
        today = reference_date or timezone.localdate()
        cards = []
        ayah_map = QuranDatasetService.get_ayah_map()

        for offset, (slug, title, icon, verse_keys) in enumerate(cls.CARD_CONFIG):
            selected = cls._select_by_day([ayah_map[key] for key in verse_keys if key in ayah_map], today, offset=offset)
            cards.append(
                {
                    "slug": slug,
                    "title": title,
                    "icon": icon,
                    "arabic_text": selected["arabic_text"],
                    "translation_text": selected["translation_text"],
                    "reference": f'{selected["surah_name"]} {selected["surah_number"]}:{selected["ayah_number"]}',
                    "source": selected["translation_source"],
                    "source_url": "",
                    "narrator": "",
                }
            )

        hadith = cls._select_by_day(HADITH_CARDS, today, offset=5)
        cards.append(
            {
                "slug": "hadith",
                "title": "Hadith",
                "icon": "bi-chat-quote",
                "arabic_text": hadith["arabic_text"],
                "translation_text": hadith["translation_text"],
                "reference": hadith["reference"],
                "source": hadith["source"],
                "source_url": hadith["source_url"],
                "narrator": hadith["narrator"],
            }
        )

        return cards

    @staticmethod
    def _select_by_day(items, today, *, offset=0):
        if not items:
            raise ValueError("Islamic content card dataset cannot be empty.")
        return items[(today.toordinal() + offset) % len(items)]
