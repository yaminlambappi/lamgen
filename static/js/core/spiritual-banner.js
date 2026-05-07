/**
 * LamGen Global Islamic Utility Strip
 * -----------------------------------
 * Server-rendered static Qur'an / dua / reminder / hadith cards.
 * Client-enhanced prayer card with location-aware timings and countdown.
 */
(function () {
    "use strict";

    const root = document.getElementById("globalIslamicUtility");
    if (!root) return;

    const apiUrl = root.dataset.panelApiUrl;
    const prayerGrid = document.getElementById("islamicPrayerGrid");

    const el = {
        nextPrayerName: document.getElementById("islamicNextPrayerName"),
        nextPrayerTime: document.getElementById("islamicNextPrayerTime"),
        salatRakat: document.getElementById("islamicSalatRakat"),
        dailyAyat: document.getElementById("islamicDailyAyat"),
    };

    const STATIC_RAKAT = {
        Fajr: "2 Farz + 2 Sunnah",
        Dhuhr: "4 Farz + 2 Sunnah",
        Asr: "4 Farz",
        Maghrib: "3 Farz + 2 Sunnah",
        Isha: "4 Farz + 2 Sunnah + 3 Witr",
    };
    const CACHE_KEY = "lamgen:islamic-panel:snapshot:v1";
    const CACHE_TTL_MS = 1000 * 60 * 30;

    let nextPrayerAt = root.dataset.nextPrayerAt || "";
    let countdownTimer = null;
    let refreshTimer = null;

    function msToCountdown(ms) {
        const total = Math.max(0, Math.floor(ms / 1000));
        const hours = Math.floor(total / 3600);
        const minutes = Math.floor((total % 3600) / 60);
        const seconds = total % 60;
        return [hours, minutes, seconds].map((value) => String(value).padStart(2, "0")).join(":");
    }

    function renderPrayerGrid(prayers) {
        if (!prayerGrid || !Array.isArray(prayers) || prayers.length === 0) return;
        prayerGrid.innerHTML = prayers.map((prayer) => `
            <div class="prayer-time prayer-status-${prayer.status}" data-prayer-name="${prayer.name}">
                <span class="prayer-name">${prayer.name}</span>
                <span class="prayer-clock">${prayer.display_time}</span>
            </div>
        `).join("");
    }

    function parseHHMM(hhmm) {
        if (typeof hhmm !== "string") return null;
        const parts = hhmm.split(":");
        if (parts.length < 2) return null;
        const hours = Number(parts[0]);
        const minutes = Number(parts[1]);
        if (!Number.isInteger(hours) || !Number.isInteger(minutes)) return null;
        if (hours < 0 || hours > 23 || minutes < 0 || minutes > 59) return null;
        return { hours, minutes };
    }

    function normalizeNextPrayer(snapshot) {
        if (!snapshot || !Array.isArray(snapshot.prayers) || snapshot.prayers.length === 0) {
            return snapshot;
        }
        const now = new Date();
        let next = null;

        snapshot.prayers.forEach((prayer) => {
            const parsed = parseHHMM(prayer.time_24);
            if (!parsed) return;
            const prayerTime = new Date(now);
            prayerTime.setHours(parsed.hours, parsed.minutes, 0, 0);
            if (prayerTime <= now) {
                prayerTime.setDate(prayerTime.getDate() + 1);
            }
            if (!next || prayerTime < next.at) {
                next = { prayer, at: prayerTime };
            }
        });

        if (!next) return snapshot;
        return {
            ...snapshot,
            next_prayer: {
                ...snapshot.next_prayer,
                name: next.prayer.name,
                display_time: next.prayer.display_time,
                timestamp: next.at.toISOString(),
                rakat: STATIC_RAKAT[next.prayer.name] || (snapshot.next_prayer && snapshot.next_prayer.rakat) || "4 Farz + 2 Sunnah + 3 Witr",
            },
        };
    }

    function isBadValue(value) {
        const normalized = String(value || "").trim().toLowerCase();
        return !normalized || normalized === "prayer sync" || normalized === "--:--";
    }

    function cacheSnapshot(snapshot) {
        try {
            const payload = { storedAt: Date.now(), snapshot };
            window.localStorage.setItem(CACHE_KEY, JSON.stringify(payload));
        } catch (_) {
            // Ignore storage errors
        }
    }

    function getCachedSnapshot() {
        try {
            const raw = window.localStorage.getItem(CACHE_KEY);
            if (!raw) return null;
            const parsed = JSON.parse(raw);
            if (!parsed || !parsed.snapshot || !parsed.storedAt) return null;
            if ((Date.now() - Number(parsed.storedAt)) > CACHE_TTL_MS) return null;
            return parsed.snapshot;
        } catch (_) {
            return null;
        }
    }

    function applySnapshot(snapshot) {
        if (!snapshot) return;
        const normalized = normalizeNextPrayer(snapshot);
        const currentName = el.nextPrayerName ? (el.nextPrayerName.textContent || "").trim() : "";
        const currentTime = el.nextPrayerTime ? (el.nextPrayerTime.textContent || "").trim() : "";
        const resolvedName = normalized.next_prayer && normalized.next_prayer.name;
        const resolvedTime = normalized.next_prayer && normalized.next_prayer.display_time;
        const safeName = isBadValue(resolvedName) ? (isBadValue(currentName) ? "Isha" : currentName) : resolvedName;
        const safeTime = isBadValue(resolvedTime) ? (isBadValue(currentTime) ? "7:40 PM" : currentTime) : resolvedTime;

        if (el.nextPrayerName) {
            el.nextPrayerName.textContent = safeName;
        }
        if (el.nextPrayerTime) {
            el.nextPrayerTime.textContent = safeTime;
        }
        if (el.salatRakat) {
            el.salatRakat.textContent = STATIC_RAKAT[safeName] || normalized.next_prayer?.rakat || "4 Farz + 2 Sunnah + 3 Witr";
        }
        if (el.dailyAyat) {
            el.dailyAyat.textContent = normalized.daily_ayat || "قُلْ هُوَ ٱللَّهُ أَحَدٌ";
        }
        nextPrayerAt = (normalized.next_prayer && normalized.next_prayer.timestamp) || nextPrayerAt;
        renderPrayerGrid(normalized.prayers);
    }

    function showQiblaDirection(qiblaBearing) {
        if (!qiblaBearing) return;
        
        // Create a simple compass modal
        const modal = document.createElement("div");
        modal.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(10, 12, 28, 0.96);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(140, 130, 255, 0.18);
            border-radius: 24px;
            padding: 2rem;
            z-index: 10000;
            text-align: center;
            color: var(--lg-text);
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        `;
        
        modal.innerHTML = `
            <h3 style="margin: 0 0 1rem 0; color: var(--lg-cyan);">Qibla Direction</h3>
            <div style="width: 120px; height: 120px; margin: 0 auto 1rem; position: relative;">
                <div style="position: absolute; inset: 0; border: 2px solid rgba(140, 130, 255, 0.3); border-radius: 50%;"></div>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(${qiblaBearing}deg);">
                    <div style="position: absolute; top: -8px; left: 0; width: 0; height: 0; border-left: 8px solid transparent; border-right: 8px solid transparent; border-bottom: 16px solid var(--lg-cyan);"></div>
                </div>
                <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 8px; height: 8px; background: var(--lg-cyan); border-radius: 50%;"></div>
            </div>
            <p style="margin: 0; font-size: 1.2rem; font-weight: 600;">${qiblaBearing}°</p>
            <p style="margin: 0.5rem 0 0 0; color: var(--lg-text-muted);">from North</p>
            <button onclick="this.parentElement.remove()" style="margin-top: 1.5rem; padding: 0.5rem 1rem; background: var(--lg-cyan); color: #000; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;">Close</button>
        `;
        
        document.body.appendChild(modal);
        
        // Close on outside click
        setTimeout(() => {
            document.addEventListener('click', function closeQibla(e) {
                if (!modal.contains(e.target)) {
                    modal.remove();
                    document.removeEventListener('click', closeQibla);
                }
            });
        }, 100);
    }

    function tickCountdown() {
        if (!el.countdown) return;
        if (!nextPrayerAt) {
            el.countdown.textContent = "--:--:--";
            return;
        }

        const diff = new Date(nextPrayerAt).getTime() - Date.now();
        if (!Number.isFinite(diff) || diff <= 0) {
            el.countdown.textContent = "00:00:00";
            scheduleRefresh();
            return;
        }

        el.countdown.textContent = msToCountdown(diff);
    }

    function scheduleRefresh() {
        if (refreshTimer) return;
        refreshTimer = window.setTimeout(() => {
            refreshTimer = null;
            refreshPrayerData();
        }, 1500);
    }

    async function fetchSnapshot(coords) {
        if (!apiUrl || apiUrl === "#") {
            throw new Error("Prayer API unavailable");
        }
        const url = new URL(apiUrl, window.location.origin);
        if (coords) {
            url.searchParams.set("lat", String(coords.latitude));
            url.searchParams.set("lon", String(coords.longitude));
        }

        const response = await fetch(url.toString(), {
            credentials: "same-origin",
            headers: { Accept: "application/json" },
        });
        if (!response.ok) {
            throw new Error("Prayer snapshot unavailable");
        }
        const payload = await response.json();
        cacheSnapshot(payload);
        return payload;
    }

    function resolveCoords() {
        return new Promise((resolve) => {
            if (!navigator.geolocation) {
                resolve(null);
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (position) => resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                }),
                () => resolve(null),
                { enableHighAccuracy: false, timeout: 4500, maximumAge: 1000 * 60 * 15 },
            );
        });
    }

    async function refreshPrayerData() {
        const fallbackPromise = fetchSnapshot(null).catch(() => null);

        const coords = await resolveCoords();
        if (!coords) {
            const fallbackSnapshot = await fallbackPromise;
            if (fallbackSnapshot) applySnapshot(fallbackSnapshot);
            return;
        }

        try {
            const locationAware = await fetchSnapshot(coords);
            applySnapshot(locationAware);
        } catch (_) {
            const fallbackSnapshot = await fallbackPromise;
            if (fallbackSnapshot) {
                applySnapshot(fallbackSnapshot);
                return;
            }
            const cachedSnapshot = getCachedSnapshot();
            if (cachedSnapshot) applySnapshot(cachedSnapshot);
        }
    }

    const cachedSnapshot = getCachedSnapshot();
    if (cachedSnapshot) {
        applySnapshot(cachedSnapshot);
    }
    refreshPrayerData();
})();
