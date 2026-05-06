(function () {
  const BehavioralTracker = {
    RECENT_KEY: "lamgen_recent_tools",
    MAX_RECENT: 10,
    recordVisit(slug) {
      if (!slug) return;
      const cur = this.getRecent().filter((s) => s !== slug);
      cur.unshift(slug);
      localStorage.setItem(this.RECENT_KEY, JSON.stringify(cur.slice(0, this.MAX_RECENT)));
      const visitsKey = `lamgen_visits_${slug}`;
      localStorage.setItem(visitsKey, String((parseInt(localStorage.getItem(visitsKey) || "0", 10) + 1)));
    },
    recordAction(slug, action) {
      if (!slug || !action) return;
      const key = `lamgen_tool_stats_${slug}`;
      const cur = JSON.parse(localStorage.getItem(key) || "{}");
      cur[action] = (cur[action] || 0) + 1;
      localStorage.setItem(key, JSON.stringify(cur));
    },
    trackDwell(slug) {
      const start = Date.now();
      const save = () => {
        const secs = Math.max(0, Math.floor((Date.now() - start) / 1000));
        localStorage.setItem(`lamgen_dwell_${slug}`, String(secs));
      };
      window.addEventListener("pagehide", save, { once: true });
      document.addEventListener("visibilitychange", () => {
        if (document.visibilityState === "hidden") save();
      });
    },
    getRecent() {
      try { return JSON.parse(localStorage.getItem(this.RECENT_KEY) || "[]"); } catch { return []; }
    }
  };
  window.BehavioralTracker = BehavioralTracker;
})();
