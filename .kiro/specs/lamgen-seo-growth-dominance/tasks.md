# Implementation Plan: LamGen SEO Growth Dominance

## Tasks

- [x] 1. Create blog Django app with ContentArticle model and migrations
- [x] 2. Create LongTailVariant model in seo app and migration
- [-] 3. Create ELITE_TOOL_DATA static dict for top 200 tools
- [~] 4. Add longtail_view, embed_view, og_image_view to tools/views.py
- [~] 5. Update tools/urls.py and config/urls.py with new routes, i18n_patterns, blog, og-image
- [~] 6. Update config/settings.py with LANGUAGES, LOCALE_PATHS, blog app, middleware
- [~] 7. Create trust_bar, privacy_badge, perf_head, critical_css partials
- [~] 8. Update tool_base.html with elite content blocks, trust bar, embed modal, prefetch, OG image override
- [~] 9. Create behavioral.js and share-state.js
- [~] 10. Update base.html with hreflang, og:locale, RTL, i18n tags, perf_head
- [~] 11. Create blog templates (index, type index, article)
- [~] 12. Create embed.html minimal template
- [~] 13. Update seo/sitemaps.py with LongTailSitemap and updated priorities
- [~] 14. Create blog/sitemaps.py and blog/admin.py
- [~] 15. Create seo/middleware.py CrawlErrorMiddleware
- [~] 16. Create validate_sitemaps management command
- [~] 17. Scaffold locale .po files for bn, hi, es, ar
- [~] 18. Update robots_txt view to disallow /api/ and /embed/
- [~] 19. Update tool_view to pass elite content to context
- [~] 20. Update homepage index.html with localStorage-driven Recently Used and Most Used sections
