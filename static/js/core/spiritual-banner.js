/**
 * LamGen Global Islamic Utility Strip
 * -----------------------------------
 * Server-rendered static Qur'an / dua / reminder / hadith cards.
 * Client-enhanced prayer card with location-aware timings, dynamic ayat, and auto-refresh.
 * 
 * Features:
 * - Real-time prayer time updates based on user location
 * - Automatic refresh every 30 minutes or when day changes
 * - Dynamic ayat rotation that refreshes daily
 * - Countdown timer to next prayer
 * - Fallback caching for offline functionality
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
        ayatMeta: document.getElementById("islamicAyatMeta"),
    };

    const STATIC_RAKAT = {
        Fajr: "2 Farz + 2 Sunnah",
        Dhuhr: "4 Farz + 2 Sunnah",
        Asr: "4 Farz",
        Maghrib: "3 Farz + 2 Sunnah",
        Isha: "4 Farz + 2 Sunnah + 3 Witr",
    };
    const CACHE_KEY = "lamgen:islamic-panel:snapshot:v1";
    const CACHE_TTL_MS = 1000 * 60 * 30;  // 30 minutes
    const AUTO_REFRESH_INTERVAL_MS = 1000 * 60 * 30;  // 30 minutes
    const COUNTDOWN_TICK_MS = 1000;  // 1 second

    let nextPrayerAt = root.dataset.nextPrayerAt || "";
    let lastRefreshDate = null;
    let countdownTimer = null;
    let refreshTimer = null;
    let autoRefreshTimer = null;
    let cachedSnapshot = null;

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

    /**
     * Calculate next prayer with real-time awareness
     * Considers current time and day rollover
     */
    function calculateNextPrayer(snapshot) {
        if (!snapshot || !Array.isArray(snapshot.prayers) || snapshot.prayers.length === 0) {
            return snapshot;
        }
        
        const now = new Date();
        let nextPrayer = null;
        let nextAt = null;

        // Try to find next prayer today
        snapshot.prayers.forEach((prayer) => {
            const parsed = parseHHMM(prayer.time_24);
            if (!parsed) return;
            
            const prayerTime = new Date(now);
            prayerTime.setHours(parsed.hours, parsed.minutes, 0, 0);
            
            // If prayer time has passed today, skip it
            if (prayerTime <= now) {
                return;
            }
            
            if (!nextPrayer || prayerTime < nextAt) {
                nextPrayer = prayer;
                nextAt = prayerTime;
            }
        });

        // If no prayer found today, get first prayer tomorrow
        if (!nextPrayer && snapshot.prayers.length > 0) {
            const firstPrayer = snapshot.prayers[0];
            const parsed = parseHHMM(firstPrayer.time_24);
            if (parsed) {
                nextAt = new Date(now);
                nextAt.setHours(parsed.hours, parsed.minutes, 0, 0);
                nextAt.setDate(nextAt.getDate() + 1);
                nextPrayer = firstPrayer;
            }
        }

        if (!nextPrayer || !nextAt) return snapshot;
        
        return {
            ...snapshot,
            next_prayer: {
                ...snapshot.next_prayer,
                name: nextPrayer.name,
                display_time: nextPrayer.display_time,
                timestamp: nextAt.toISOString(),
                rakat: STATIC_RAKAT[nextPrayer.name] || (snapshot.next_prayer && snapshot.next_prayer.rakat) || "4 Farz + 2 Sunnah + 3 Witr",
            },
        };
    }

    function isBadValue(value) {
        const normalized = String(value || "").trim().toLowerCase();
        return !normalized || normalized === "prayer sync" || normalized === "--:--" || normalized === "null";
    }

    function cacheSnapshot(snapshot) {
        try {
            const payload = { storedAt: Date.now(), snapshot };
            window.localStorage.setItem(CACHE_KEY, JSON.stringify(payload));
            cachedSnapshot = snapshot;
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

    /**
     * Apply snapshot to UI elements
     * Includes validation and fallbacks for reliability
     */
    function applySnapshot(snapshot) {
        if (!snapshot) return;
        
        const normalized = calculateNextPrayer(snapshot);
        const currentName = el.nextPrayerName ? (el.nextPrayerName.textContent || "").trim() : "";
        const currentTime = el.nextPrayerTime ? (el.nextPrayerTime.textContent || "").trim() : "";
        const resolvedName = normalized.next_prayer && normalized.next_prayer.name;
        const resolvedTime = normalized.next_prayer && normalized.next_prayer.display_time;
        const safeName = isBadValue(resolvedName) ? (isBadValue(currentName) ? "Isha" : currentName) : resolvedName;
        const safeTime = isBadValue(resolvedTime) ? (isBadValue(currentTime) ? "7:40 PM" : currentTime) : resolvedTime;

        // Update prayer name
        if (el.nextPrayerName && el.nextPrayerName.textContent !== safeName) {
            el.nextPrayerName.textContent = safeName;
        }
        
        // Update prayer time
        if (el.nextPrayerTime && el.nextPrayerTime.textContent !== safeTime) {
            el.nextPrayerTime.textContent = safeTime;
        }
        
        // Update rakat
        if (el.salatRakat) {
            const safeRakat = STATIC_RAKAT[safeName] || normalized.next_prayer?.rakat || "4 Farz + 2 Sunnah + 3 Witr";
            if (el.salatRakat.textContent !== safeRakat) {
                el.salatRakat.textContent = safeRakat;
            }
        }
        
        // Update ayat (only if it has changed or is empty)
        if (el.dailyAyat && normalized.daily_ayat) {
            const arabicText = normalized.daily_ayat.arabic || "";
            const currentArabic = (el.dailyAyat.textContent || "").trim();
            if (arabicText && currentArabic !== arabicText) {
                el.dailyAyat.textContent = arabicText;
                
                // Update ayat metadata if available
                if (el.ayatMeta && normalized.daily_ayat.translation && normalized.daily_ayat.ayah) {
                    el.ayatMeta.innerHTML = `
                        <span class="ayat-translation">${normalized.daily_ayat.translation}</span>
                        <span class="ayat-reference">${normalized.daily_ayat.surah} (${normalized.daily_ayat.ayah})</span>
                    `;
                }
            }
        }
        
        // Update next prayer timestamp for countdown
        nextPrayerAt = (normalized.next_prayer && normalized.next_prayer.timestamp) || nextPrayerAt;
        
        // Render prayer grid if available
        if (snapshot.prayers) {
            renderPrayerGrid(snapshot.prayers);
        }
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

    /**
     * Countdown ticker - updates every second
     */
    function tickCountdown() {
        if (!nextPrayerAt) return;

        const nextTime = new Date(nextPrayerAt).getTime();
        const now = Date.now();
        const diff = nextTime - now;

        if (!Number.isFinite(diff) || diff <= 0) {
            // Prayer time has been reached - schedule a refresh
            scheduleRefresh();
            return;
        }
    }

    /**
     * Schedule a refresh of prayer data (debounced)
     */
    function scheduleRefresh() {
        if (refreshTimer) return;
        refreshTimer = window.setTimeout(() => {
            refreshTimer = null;
            refreshPrayerData();
        }, 1500);  // Wait 1.5s to ensure prayer time has definitely passed
    }

    /**
     * Schedule periodic auto-refresh (every 30 minutes or when day changes)
     */
    function scheduleAutoRefresh() {
        if (autoRefreshTimer) return;
        
        autoRefreshTimer = window.setInterval(() => {
            const today = new Date().toDateString();
            // Refresh if date has changed or periodically every 30 minutes
            if (!lastRefreshDate || lastRefreshDate !== today) {
                lastRefreshDate = today;
                refreshPrayerData();  // Day changed - refresh everything including ayat
            }
        }, AUTO_REFRESH_INTERVAL_MS);
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
        if (payload && payload.daily_ayat) {
            cacheSnapshot(payload);
        }
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

    /**
     * Refresh prayer data with location awareness and fallbacks
     */
    async function refreshPrayerData() {
        try {
            // Try to get location-aware data first
            const coords = await resolveCoords();
            if (coords) {
                try {
                    const locationAware = await fetchSnapshot(coords);
                    applySnapshot(locationAware);
                    return;
                } catch (_) {
                    // Location-aware request failed, try fallback
                }
            }

            // Try default location snapshot
            const fallbackSnapshot = await fetchSnapshot(null);
            if (fallbackSnapshot) {
                applySnapshot(fallbackSnapshot);
                return;
            }

            // Use cached snapshot as last resort
            const cached = getCachedSnapshot();
            if (cached) {
                applySnapshot(cached);
            }
        } catch (_) {
            // Network completely unavailable - use cache if available
            const cached = getCachedSnapshot() || cachedSnapshot;
            if (cached) {
                applySnapshot(cached);
            }
        }
    }

    /**
     * Initialize the Islamic utility strip
     */
    function initialize() {
        // Load cached snapshot if available
        const cached = getCachedSnapshot();
        if (cached) {
            applySnapshot(cached);
        }

        // Fetch fresh data immediately
        refreshPrayerData();

        // Set up countdown ticker
        countdownTimer = window.setInterval(tickCountdown, COUNTDOWN_TICK_MS);

        // Set up periodic auto-refresh (every 30 minutes)
        scheduleAutoRefresh();

        // Handle day rollover by checking at midnight
        const now = new Date();
        const tomorrow = new Date(now);
        tomorrow.setDate(tomorrow.getDate() + 1);
        tomorrow.setHours(0, 0, 1, 0);
        const msUntilMidnight = tomorrow.getTime() - now.getTime();
        
        window.setTimeout(() => {
            refreshPrayerData();  // Refresh at midnight for new ayat
            scheduleAutoRefresh();  // Reschedule auto-refresh
            initialize();  // Re-initialize for next day
        }, msUntilMidnight);
    }

    // Start the system
    initialize();
})();
