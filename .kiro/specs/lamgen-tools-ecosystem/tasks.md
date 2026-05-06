# Implementation Tasks

## Overview

This document outlines the implementation tasks for transforming the existing Django assignment generator into the **LamGen Tools Ecosystem** — a production-grade multi-tool platform hosting hundreds of browser-side and backend utilities, a programmatic SEO content engine, and a unified discovery/monetisation layer.

**Implementation Philosophy**: Every tool must be production-ready before being marked `is_active=True`. No placeholders, no fake outputs, no demo logic. Incomplete tools remain hidden from navigation and search.

---

## Task 1: Foundation & Database Schema

### 1.1 Add missing fields to Tool model

- [x] Add `usage_count` field to `Tool` model (`BigIntegerField`, default=0)
- [x] Create and run migration for `usage_count` field
- [x] Verify migration applied successfully

### 1.2 Add UniqueConstraint to ToolUsageHistory

- [x] Add `UniqueConstraint` to `ToolUsageHistory` model for `(user, tool)` where `user__isnull=False`
- [x] Create data migration to deduplicate existing `ToolUsageHistory` records (keep most recent per user+tool)
- [x] Create and run schema migration for the constraint
- [x] Verify constraint works (attempt to create duplicate should fail)

### 1.3 Add related_tools ManyToManyField to SEOPage

- [x] Add `related_tools = models.ManyToManyField('tools.Tool', blank=True, related_name='seo_pages')` to `SEOPage` model
- [x] Create and run migration
- [x] Verify field exists in admin

### 1.4 Add schema_type field to SEOCategory

- [x] Add `schema_type` field to `SEOCategory` model (CharField, max_length=30, default='ItemList', choices=[('ItemList', 'ItemList'), ('FAQPage', 'FAQPage'), ('Article', 'Article')])
- [ ] Create and run migration
- [x] Verify field appears in admin

### 1.5 Create TOOL_CATEGORIES configuration

- [x] Define `TOOL_CATEGORIES` dict in `config/settings.py` with all 10 categories (Developer Tools, Student Tools, Writing Tools, Utility Tools, Social & Viral Tools, SEO Tools, Image Tools, PDF & File Tools, Resume & Career Tools, Academic & Writing)
- [ ] Each category entry must include: slug, name, icon, color_from, color_to, order, short_desc, tools list
- [ ] Include Assignment Generator and Thesis Generator in "Academic & Writing" category
- [ ] Verify settings file loads without errors

---

## Task 2: Tool Registry Seeding System

### 2.1 Create seed_tools management command

- [ ] Create `tools/management/commands/seed_tools.py`
- [ ] Implement idempotent seeding using `update_or_create` on category slug and tool slug
- [ ] Read from `settings.TOOL_CATEGORIES` dict
- [ ] Create/update ToolCategory records
- [ ] Create/update Tool records with all fields from config
- [ ] Add `--dry-run` flag to preview changes without committing
- [ ] Add verbose output showing created/updated counts

### 2.2 Populate initial tool definitions in TOOL_CATEGORIES

- [ ] Define all Developer Tools (25+ tools) in settings with: slug, name, short_desc, icon, template_name, tags, order
- [ ] Define all Student Tools (14+ tools)
- [ ] Define all Writing Tools (11+ tools)
- [ ] Define all Utility Tools (15+ tools)
- [ ] Define all Social & Viral Tools (9 tools)
- [ ] Define all SEO Tools (11+ tools)
- [ ] Define all Image Tools (14+ tools)
- [ ] Define PDF & File Tools (10 tools)
- [ ] Define Resume & Career Tools (8 tools)
- [ ] Define Academic & Writing category with Assignment Generator and Thesis Generator
- [ ] All tools initially marked `is_active=False` until templates are implemented

### 2.3 Run seed_tools and verify

- [ ] Run `python manage.py seed_tools`
- [ ] Verify all 10 categories created in database
- [ ] Verify 100+ tool records created
- [ ] Verify no duplicate slugs
- [ ] Verify meta_title and meta_description auto-generated correctly
- [ ] Verify Assignment Generator and Thesis Generator appear in Academic & Writing category

---

## Task 3: Shared Utilities & Template Tags

### 3.1 Create tools/utils/ module

- [ ] Create `tools/utils/__init__.py`
- [ ] Create `tools/utils/file_validation.py` with `validate_mime(file_obj, expected_type)` function using python-magic
- [ ] Create `tools/utils/slug_utils.py` with slug generation helpers
- [ ] Create `tools/utils/metadata.py` with meta title/description truncation helpers
- [ ] Create `tools/utils/rate_limit.py` with cache-based rate limiter decorator
- [ ] Write unit tests for each utility function

### 3.2 Create tools/templatetags/tools_tags.py

- [ ] Create `tools/templatetags/__init__.py`
- [ ] Create `tools/templatetags/tools_tags.py`
- [ ] Implement `@register.inclusion_tag` for `tool_card` (renders `partials/tool_card.html`)
- [ ] Implement `@register.inclusion_tag` for `category_card` (renders `partials/category_card.html`)
- [ ] Implement `@register.inclusion_tag` for `breadcrumb` (renders `partials/breadcrumb.html`)
- [ ] Implement `@register.inclusion_tag` for `ad_slot` (renders `partials/ad_slot.html`)
- [ ] Implement `@register.simple_tag` for `software_application_schema(tool, request)` returning JSON-LD
- [ ] Implement `@register.simple_tag` for `faq_schema(page)` returning JSON-LD
- [ ] Implement `@register.simple_tag` for `item_list_schema(page, request)` returning JSON-LD
- [ ] Write template tag tests

---

## Task 4: Template Partials & Design System

### 4.1 Create template partials

- [ ] Create `templates/partials/tool_card.html` (displays tool with icon, name, short_desc, bookmark toggle)
- [ ] Create `templates/partials/category_card.html` (displays category with gradient, icon, tool count)
- [ ] Create `templates/partials/breadcrumb.html` (renders breadcrumb navigation)
- [ ] Create `templates/partials/ad_slot.html` (empty div with data-ad-slot attribute)
- [ ] Create `templates/partials/tool_action_bar.html` (sticky mobile action bar)
- [ ] Create `templates/partials/search_result_item.html` (used in Command Palette)
- [ ] Create `templates/partials/paywall_overlay.html` (pro tool gate for unauthenticated users)
- [ ] Create `templates/partials/auth_prompt.html` (non-intrusive login nudge)
- [ ] Verify all partials render without errors

### 4.2 Update base.html with metadata engine

- [ ] Add `{% if schema_json %}` block in `<head>` for JSON-LD injection
- [ ] Add `canonical_url` meta tag rendering
- [ ] Add OpenGraph tags rendering from context variables
- [ ] Add Twitter Card tags rendering from context variables
- [ ] Verify metadata renders correctly on test page

### 4.3 Create TailwindCSS config (optional enhancement)

- [ ] Create `tailwind.config.js` with custom tokens matching existing CSS variables
- [ ] Define dark mode class strategy
- [ ] Define custom colors, fonts, spacing matching design system
- [ ] Document how to compile Tailwind (if using build step)

---

## Task 5: Command Palette & Search

### 5.1 Implement search endpoint enhancements

- [ ] Add intent expansion logic to `search_view` (convert → converter/transform/to, format → formatter/beautify, etc.)
- [ ] Add relevance scoring (exact name match = 100pts, name contains = 50pts, desc/tags = 10pts)
- [ ] Sort results by relevance score descending, then alphabetically
- [ ] Cap results at 15
- [ ] Add rate limiting decorator (`@rate_limit('search', limit=60, window=60)`)
- [ ] Return HTTP 429 on rate limit exceeded
- [ ] Write tests for intent expansion and relevance scoring

### 5.2 Create Command Palette JavaScript

- [ ] Create `static/js/command-palette.js`
- [ ] Implement keyboard listener for `/` and `Ctrl+K` to open palette
- [ ] Implement overlay with search input
- [ ] Implement debounced search (250ms) calling `/tools/search/`
- [ ] Render results within 300ms of debounce firing
- [ ] Implement keyboard navigation (ArrowUp/ArrowDown, Enter to navigate)
- [ ] Implement Escape to close
- [ ] Add loading state during search
- [ ] Test on desktop and mobile

### 5.3 Integrate Command Palette into base.html

- [ ] Add Command Palette HTML structure to `base.html`
- [ ] Load `command-palette.js` at bottom of `<body>`
- [ ] Add CSS for overlay, search input, results list
- [ ] Verify palette opens on `/` and `Ctrl+K`
- [ ] Verify search works and results are clickable

---

## Task 6: Bookmark & History System Enhancements

### 6.1 Implement session bookmark merge on login

- [ ] Create `merge_session_bookmarks(request, user)` function in `tools/utils/bookmarks.py`
- [ ] Call merge function in `accounts/views.py` after successful login
- [ ] Pop `session_bookmarks` from session after merge
- [ ] Invalidate bookmark cache for user
- [ ] Write test for merge logic (session bookmarks → DB bookmarks)

### 6.2 Add session bookmark limit enforcement

- [ ] Update `toggle_bookmark` view to enforce 10-bookmark limit for guests
- [ ] Return `{"error": "Session bookmark limit reached (10)"}` with HTTP 400 if limit exceeded
- [ ] Write test for limit enforcement

### 6.3 Implement usage_count recording endpoint

- [ ] Create `/tools/usage/record/` POST endpoint in `tools/views.py`
- [ ] Accept `tool_slug` in request body (JSON or POST data)
- [ ] Increment `Tool.usage_count` using `F('usage_count') + 1`
- [ ] If user authenticated, update or create `ToolUsageHistory` record (timestamp auto-updates)
- [ ] Return `{"ok": True}`
- [ ] Add CSRF exemption for AJAX (but require CSRF token in header)
- [ ] Write test for usage recording

---

## Task 7: Programmatic SEO Engine

### 7.1 Create SEO content generator module

- [ ] Create `seo/engine/__init__.py`
- [ ] Create `seo/engine/content_generator.py` with `generate_items(category_slug, topic, slug, count=30)` function
- [ ] Implement deterministic seeding using `hashlib.md5(slug.encode()).hexdigest()`
- [ ] Use isolated `random.Random(seed)` instance (not global random)
- [ ] Implement deduplication while preserving order
- [ ] Ensure minimum 20 items after deduplication (generate more if needed)
- [ ] Write property test for determinism (same slug → same output)
- [ ] Write property test for minimum count

### 7.2 Create word lists and templates

- [ ] Create `seo/engine/word_lists.py` with `WORD_LISTS` dict
- [ ] Define word lists for: captions (adjectives, nouns, verbs, emotions), quotes, interview-questions, bios, usernames, hashtags, email-templates, thesis-topics, project-ideas, code-snippets, resume-examples
- [ ] Create `seo/engine/templates.py` with `CONTENT_TEMPLATES` dict
- [ ] Define 20+ templates per content type using placeholders ({topic}, {adj}, {noun}, {verb}, {emotion}, {number})
- [ ] Verify templates render without errors

### 7.3 Create generate_seo_pages management command

- [ ] Create `seo/management/commands/generate_seo_pages.py`
- [ ] Define `TOPIC_SEEDS` dict with 500+ topic slugs across all content types
- [ ] Implement idempotent seeding using `update_or_create` on slug
- [ ] Call `generate_items()` for each topic
- [ ] Link 3 related tools per page using tags matching
- [ ] Add `--dry-run` flag
- [ ] Add verbose output
- [ ] Run command and verify 500+ SEOPage records created

### 7.4 Update SEO views for internal linking

- [ ] Update `seo/views.py` `page_view` to query 3 related SEO pages in same category
- [ ] Update `seo/views.py` `page_view` to query 3 related Tool pages using `page.related_tools.all()`
- [ ] Update `seo/templates/seo/page.html` to render related tools and related pages sections
- [ ] Verify internal links render correctly

---

## Task 8: Analytics & Monetisation Infrastructure

### 8.1 Implement Redis-backed view counter batching

- [ ] Verify existing view counter logic in `tool_view` (already implemented)
- [ ] Add optional Celery task `flush_view_counters` to batch-flush all cached counters every 5 minutes
- [ ] Add Celery Beat schedule entry for flush task
- [ ] Write test for view counter batching

### 8.2 Add trending tools page

- [ ] Verify `/tools/trending/` route exists (already implemented)
- [ ] Create `templates/tools/trending.html` template
- [ ] Display 30 most-viewed tools in grid layout
- [ ] Add breadcrumb navigation
- [ ] Add ad slots
- [ ] Verify page renders and caches correctly

### 8.3 Integrate ad slots into templates

- [ ] Add ad slot below tool header in `templates/tools/generic_tool.html`
- [ ] Add ad slot between tool output and related tools
- [ ] Add ad slot in sidebar (desktop only)
- [ ] Verify ad slots render as empty divs with correct data attributes

---

## Task 9: Browser-Side Tools Implementation

### 9.1 Developer Tools (Priority 1 — High Value)

- [ ] Create `templates/tools/developer/json-formatter.html` (JSON.parse + JSON.stringify with error handling)
- [ ] Create `templates/tools/developer/xml-formatter.html` (DOMParser + XMLSerializer)
- [ ] Create `templates/tools/developer/yaml-formatter.html` (js-yaml library via CDN)
- [ ] Create `templates/tools/developer/base64-encoder.html` (btoa/atob with UTF-8 handling)
- [ ] Create `templates/tools/developer/url-encoder.html` (encodeURIComponent/decodeURIComponent)
- [ ] Create `templates/tools/developer/jwt-decoder.html` (base64 decode + JSON.parse header/payload)
- [ ] Create `templates/tools/developer/hash-generator.html` (Web Crypto API for SHA-256, SHA-512, MD5 via worker)
- [ ] Create `templates/tools/developer/uuid-generator.html` (crypto.randomUUID())
- [ ] Create `templates/tools/developer/lorem-ipsum.html` (deterministic word list generator)
- [ ] Create `templates/tools/developer/regex-tester.html` (RegExp with match highlighting)
- [ ] Create `templates/tools/developer/diff-checker.html` (diff library via CDN)
- [ ] Create `templates/tools/developer/markdown-previewer.html` (marked.js via CDN)
- [ ] Create `templates/tools/developer/color-palette-generator.html` (Canvas API color extraction)
- [ ] Create `templates/tools/developer/gradient-generator.html` (CSS gradient builder with preview)
- [ ] Mark all implemented tools as `is_active=True` in database
- [ ] Test each tool on desktop and mobile
- [ ] Verify copy/download functionality works

### 9.2 Student Tools (Priority 2)

- [ ] Create `templates/tools/student/gpa-calculator.html` (grade points × credits / total credits)
- [ ] Create `templates/tools/student/cgpa-calculator.html` (cumulative GPA across semesters)
- [ ] Create `templates/tools/student/word-counter.html` (split by whitespace, count)
- [ ] Create `templates/tools/student/reading-time-estimator.html` (word count / 200 wpm)
- [ ] Create `templates/tools/student/readability-checker.html` (Flesch-Kincaid formula)
- [ ] Create `templates/tools/student/pomodoro-timer.html` (25min work / 5min break timer)
- [ ] Create `templates/tools/student/flashcard-generator.html` (input Q&A pairs, flip cards)
- [ ] Create `templates/tools/student/academic-title-generator.html` (rule-based title templates)
- [ ] Mark implemented tools as `is_active=True`
- [ ] Test all tools

### 9.3 Writing Tools (Priority 2)

- [ ] Create `templates/tools/writing/case-converter.html` (UPPER, lower, Title, camelCase, snake_case)
- [ ] Create `templates/tools/writing/fancy-text-generator.html` (Unicode text styles: bold, italic, strikethrough, etc.)
- [ ] Create `templates/tools/writing/duplicate-remover.html` (split lines, deduplicate, join)
- [ ] Create `templates/tools/writing/keyword-density.html` (word frequency counter)
- [ ] Create `templates/tools/writing/text-cleaner.html` (trim, remove extra spaces, normalize)
- [ ] Mark implemented tools as `is_active=True`
- [ ] Test all tools

### 9.4 Utility Tools (Priority 2)

- [ ] Create `templates/tools/utility/password-generator.html` (crypto.getRandomValues with charset)
- [ ] Create `templates/tools/utility/password-strength-checker.html` (entropy calculation + zxcvbn-like scoring)
- [ ] Create `templates/tools/utility/age-calculator.html` (date diff in years/months/days)
- [ ] Create `templates/tools/utility/percentage-calculator.html` (X is Y% of Z formulas)
- [ ] Create `templates/tools/utility/bmi-calculator.html` (weight / height² with unit conversion)
- [ ] Create `templates/tools/utility/unit-converter.html` (length, weight, temperature, volume)
- [ ] Create `templates/tools/utility/timezone-converter.html` (Intl.DateTimeFormat API)
- [ ] Create `templates/tools/utility/countdown-timer.html` (target date countdown)
- [ ] Create `templates/tools/utility/stopwatch.html` (start/stop/reset with milliseconds)
- [ ] Mark implemented tools as `is_active=True`
- [ ] Test all tools

### 9.5 SEO Tools (Priority 3)

- [ ] Create `templates/tools/seo/meta-title-generator.html` (input keyword, generate 10 title variations)
- [ ] Create `templates/tools/seo/meta-description-generator.html` (input keyword, generate 10 desc variations)
- [ ] Create `templates/tools/seo/slug-generator.html` (slugify with preview)
- [ ] Create `templates/tools/seo/serp-preview.html` (live preview of title/desc in Google SERP)
- [ ] Create `templates/tools/seo/opengraph-generator.html` (form → OG meta tags)
- [ ] Create `templates/tools/seo/schema-markup-generator.html` (form → JSON-LD for common types)
- [ ] Mark implemented tools as `is_active=True`
- [ ] Test all tools

### 9.6 Social & Viral Tools (Priority 3)

- [ ] Create `templates/tools/social/fake-tweet-generator.html` (Twitter-like card with custom text/username/timestamp)
- [ ] Create `templates/tools/social/meme-caption-generator.html` (rule-based meme text templates)
- [ ] Create `templates/tools/social/aesthetic-font-generator.html` (Unicode font variations)
- [ ] Create `templates/tools/social/nickname-generator.html` (random name combinations)
- [ ] Mark implemented tools as `is_active=True`
- [ ] Test all tools

### 9.7 Image Tools (Priority 4 — Complex)

- [ ] Create `templates/tools/image/image-compressor.html` (Canvas API + toBlob with quality slider)
- [ ] Create `templates/tools/image/webp-converter.html` (Canvas toBlob with 'image/webp')
- [ ] Create `templates/tools/image/image-resize.html` (Canvas drawImage with width/height inputs)
- [ ] Create `templates/tools/image/qr-generator.html` (qrcode.js library via CDN)
- [ ] Create `templates/tools/image/color-extractor.html` (Canvas getImageData + color quantization)
- [ ] Mark implemented tools as `is_active=True`
- [ ] Test all tools on desktop and mobile
- [ ] Verify download functionality works

---

## Task 10: Backend Tools Implementation

### 10.1 PDF & File Tools infrastructure

- [ ] Create `tools/pdf/` module directory
- [ ] Create `tools/pdf/views.py` with file upload handling base class
- [ ] Implement MIME validation using `tools/utils/file_validation.py`
- [ ] Implement file size check (HTTP 413 if > MAX_UPLOAD_SIZE)
- [ ] Implement UUID-based upload directory isolation
- [ ] Create Celery task `cleanup_uploaded_files` in `tools/tasks.py`
- [ ] Add Celery Beat schedule for cleanup task (every 30 minutes)
- [ ] Write tests for file upload pipeline

### 10.2 PDF Tools implementation

- [ ] Create `/tools/pdf/merge/` endpoint (PyMuPDF merge multiple PDFs)
- [ ] Create `/tools/pdf/split/` endpoint (PyMuPDF split PDF by page range)
- [ ] Create `/tools/pdf/compress/` endpoint (PyMuPDF with reduced image quality)
- [ ] Create `/tools/pdf/image-to-pdf/` endpoint (Pillow → PyMuPDF)
- [ ] Create templates for each PDF tool
- [ ] Mark implemented tools as `is_active=True`
- [ ] Test each tool with various file sizes and formats
- [ ] Verify cleanup task deletes files after 1 hour

### 10.3 Resume & Career Tools (client-side rendering + PDF export)

- [ ] Create `templates/tools/resume/resume-builder.html` (form-based resume builder with live preview)
- [ ] Create `/tools/resume/export-pdf/` endpoint (WeasyPrint HTML → PDF)
- [ ] Create `templates/tools/resume/bio-generator.html` (rule-based bio templates)
- [ ] Create `templates/tools/resume/invoice-generator.html` (form → HTML invoice with PDF export)
- [ ] Mark implemented tools as `is_active=True`
- [ ] Test all tools

---

## Task 11: Property-Based Tests

### 11.1 Create test file and fixtures

- [ ] Create `tests/test_tools_properties.py`
- [ ] Create test fixtures for ToolCategory and Tool
- [ ] Configure Hypothesis settings (max_examples=100)

### 11.2 Implement Property 1: Tool metadata auto-generation

- [ ] Write `test_tool_metadata_autogeneration` using `@given(name=st.text(), short_desc=st.text())`
- [ ] Assert `meta_title == f"{name} — Free Online Tool | LamGen"[:70]`
- [ ] Assert `meta_description == short_desc[:160]`
- [ ] Assert lengths ≤ 70 and ≤ 160
- [ ] Run test and verify passes

### 11.3 Implement Property 2: Tool canonical URL pattern

- [ ] Write `test_tool_canonical_url` using `@given(cat_slug=st.from_regex(...), tool_slug=st.from_regex(...))`
- [ ] Assert `tool.get_absolute_url() == f"/tools/{cat_slug}/{tool_slug}/"`
- [ ] Run test and verify passes

### 11.4 Implement Property 3: Search result bounds

- [ ] Write `test_search_short_query_returns_empty` using `@given(q=st.text(min_size=0, max_size=1))`
- [ ] Assert response returns `{"results": []}`
- [ ] Write `test_search_result_count_bounded` using `@given(q=st.text(min_size=2, max_size=100))`
- [ ] Assert `len(results) <= 15`
- [ ] Run tests and verify pass

### 11.5 Implement Property 4: Metadata length invariants

- [ ] Write `test_metadata_length_invariants` using `@given(name=st.text(max_size=300), short_desc=st.text(max_size=1000))`
- [ ] Assert `len(tool.meta_title) <= 70`
- [ ] Assert `len(tool.meta_description) <= 160`
- [ ] Run test and verify passes

### 11.6 Implement Property 5: Bookmark toggle idempotence

- [ ] Write `test_bookmark_toggle_idempotence` (example-based, not property-based)
- [ ] Call toggle twice, assert returns to original state
- [ ] Run test and verify passes

### 11.7 Implement Property 6: Unauthenticated bookmark rejection

- [ ] Write `test_unauthenticated_bookmark_returns_401` using `@given(tool_slug=st.from_regex(...))`
- [ ] Assert response status 401
- [ ] Assert response body `{"error": "Login required"}`
- [ ] Run test and verify passes

### 11.8 Implement Property 7: Session bookmark merge completeness

- [ ] Write `test_session_bookmark_merge` (example-based)
- [ ] Create session with 5 bookmarks
- [ ] Login user
- [ ] Assert all 5 bookmarks exist in DB for user
- [ ] Run test and verify passes

### 11.9 Implement Property 8: SEO content determinism

- [ ] Write `test_seo_content_determinism` using `@given(slug=st.from_regex(...))`
- [ ] Call `generate_items()` twice with same slug
- [ ] Assert outputs are identical
- [ ] Run test and verify passes

### 11.10 Implement Property 9: SEO content minimum count

- [ ] Write `test_seo_content_minimum_count` using `@given(slug=st.from_regex(...))`
- [ ] Assert `len(generate_items(...)) >= 20`
- [ ] Run test and verify passes

### 11.11 Implement Property 10: MIME validation

- [ ] Write `test_mime_validation_rejects_non_pdf_as_pdf` using `@given(content=st.binary())`
- [ ] Assert `validate_mime()` returns `(False, detected_mime)` for non-PDF content
- [ ] Run test and verify passes

### 11.12 Run full property test suite

- [ ] Run `pytest tests/test_tools_properties.py -v`
- [ ] Verify all 10 properties pass
- [ ] Fix any failures
- [ ] Commit passing test suite

---

## Task 12: Integration & Polish

### 12.1 Update homepage with discovery sections

- [ ] Update `templates/home.html` to render trending tools section
- [ ] Update `templates/home.html` to render new tools section
- [ ] Update `templates/home.html` to render recent tools section
- [ ] Update `templates/home.html` to render all categories grid
- [ ] Add breadcrumb navigation
- [ ] Add ad slots
- [ ] Verify homepage renders correctly

### 12.2 Create dashboard for registered users

- [ ] Create `templates/dashboard/index.html`
- [ ] Display bookmarked tools section
- [ ] Display recent tool history section
- [ ] Display usage statistics (total tools used, most used tool)
- [ ] Add link to dashboard in profile dropdown
- [ ] Verify dashboard renders correctly for authenticated users

### 12.3 Update robots.txt and sitemap

- [ ] Verify `robots.txt` view disallows `/admin/` and references sitemap
- [ ] Verify sitemap includes all active tools, categories, and SEO pages
- [ ] Verify sitemap caches for 24 hours
- [ ] Test sitemap XML renders correctly

### 12.4 Performance optimization

- [ ] Verify WhiteNoise serves static files with immutable cache headers
- [ ] Verify category pages cache for 10 minutes
- [ ] Verify homepage caches for 1 minute
- [ ] Verify SEO pages cache for 24 hours
- [ ] Run Lighthouse audit on 3 tool pages, target score ≥85
- [ ] Fix any performance issues identified

### 12.5 Mobile responsiveness verification

- [ ] Test homepage on mobile (< 768px)
- [ ] Test category page on mobile
- [ ] Test 5 browser tools on mobile
- [ ] Test Command Palette on mobile
- [ ] Test bottom dock navigation on mobile
- [ ] Fix any layout issues

### 12.6 Accessibility verification

- [ ] Run axe DevTools on homepage
- [ ] Run axe DevTools on 3 tool pages
- [ ] Verify all interactive elements reachable via Tab
- [ ] Verify all actions triggerable via Enter/Space
- [ ] Fix any accessibility issues

### 12.7 Final QA pass

- [ ] Test bookmark toggle on 3 tools (authenticated and guest)
- [ ] Test search with 10 different queries
- [ ] Test Command Palette keyboard shortcuts
- [ ] Test 10 browser tools end-to-end (input → output → download)
- [ ] Test 2 backend tools end-to-end (upload → process → download)
- [ ] Test SEO page rendering and internal links
- [ ] Verify no console errors on any page
- [ ] Verify no broken links in navigation
- [ ] Verify all active tools have working templates

### 12.8 Documentation

- [ ] Update PROJECT_OVERVIEW.md with new architecture
- [ ] Document how to add a new browser tool (create template, add to TOOL_CATEGORIES, run seed_tools)
- [ ] Document how to add a new backend tool (create view, add route, add to TOOL_CATEGORIES)
- [ ] Document how to add new SEO content types (add to word_lists, templates, TOPIC_SEEDS)
- [ ] Document Celery setup for file cleanup

---

## Completion Criteria

A task is considered complete when:
- All sub-tasks are checked off
- All tests pass
- Code is committed to version control
- Feature works on desktop and mobile
- No console errors
- Lighthouse performance score ≥85 (for user-facing pages)
- Accessibility audit passes (no critical issues)

The entire spec is complete when:
- All 12 tasks are complete
- All 10 property-based tests pass
- 100+ tools are seeded in database
- At least 50 browser tools are fully implemented and active
- At least 5 backend tools are fully implemented and active
- 500+ SEO pages are generated
- Platform is production-ready for deployment
