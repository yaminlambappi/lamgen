# Requirements Document

## Introduction

Transform the existing Django-based LamGen assignment generator into a production-grade multi-tool ecosystem platform — **LamGen Tools Ecosystem** — capable of hosting hundreds of zero-API-cost utilities, programmatic SEO pages, and browser-side tools. The platform must preserve all existing assignment generation and thesis functionality as a premium feature category, while adding nine new tool categories, a programmatic SEO content engine, and a unified platform layer covering discovery, bookmarking, analytics, and monetisation readiness.

The target is a platform comparable in scope and quality to Smallpdf, iLovePDF, CodeBeautify, TinyWow, and Ahrefs free tools — with extremely low operating costs, high ad monetisation potential, and a clear path to future SaaS conversion.

---

## Glossary

- **Platform**: The LamGen Tools Ecosystem Django application as a whole.
- **Tool**: A single utility accessible at a URL, backed by a `Tool` database record and a dedicated template.
- **Tool_Registry**: The database-backed catalogue of all Tools and ToolCategories, used for discovery, search, and SEO.
- **Category**: A `ToolCategory` record grouping related Tools (e.g., Developer Tools, Student Tools).
- **Browser_Tool**: A Tool whose processing logic runs entirely in the user's browser via JavaScript, with no server-side computation required.
- **Backend_Tool**: A Tool that requires a Django view or API endpoint for processing (e.g., PDF merge, file conversion).
- **SEO_Engine**: The programmatic content generation subsystem that produces slug-based pages for captions, quotes, bios, snippets, etc.
- **SEO_Page**: A dynamically rendered page produced by the SEO_Engine, indexed in the `SEOPage` model.
- **Metadata_Engine**: The shared subsystem that generates `<title>`, `<meta description>`, OpenGraph, Twitter Card, and JSON-LD schema markup for every page.
- **Search_Index**: The in-database full-text search index over Tool names, descriptions, and tags.
- **Bookmark_System**: The per-user and per-session mechanism for saving favourite Tools.
- **History_System**: The per-user and per-session mechanism for tracking recently used Tools.
- **Analytics_Hook**: A lightweight event-recording mechanism (view count, usage count) that does not depend on any third-party analytics service.
- **Ad_Slot**: A designated, clearly labelled placeholder in templates where advertisement units can be injected without template modification.
- **Design_System**: The shared TailwindCSS-based component library (tokens, colours, typography, dark/light mode) used across all templates.
- **Command_Palette**: The keyboard-accessible global search overlay (triggered by `/` or `Ctrl+K`) that searches the Tool_Registry in real time.
- **Programmatic_SEO_Page**: An SEO_Page generated from a template and a data seed (e.g., "100 Instagram captions for travel").
- **Assignment_Generator**: The existing `generation` Django app providing multi-section academic assignment generation via the Anthropic Claude API.
- **Thesis_Generator**: The existing `thesis` Django app providing multi-pass thesis generation via configurable LLM providers.
- **Guest_User**: An unauthenticated visitor interacting with the Platform via session-based state.
- **Registered_User**: An authenticated user with a `CustomUser` account.
- **SaaS_Tier**: A future paid subscription layer; the architecture must accommodate it without structural refactoring.

---

## Requirements

### Requirement 1: Preserve and Integrate Existing Functionality

**User Story:** As a returning user of the assignment and thesis generators, I want all existing features to continue working exactly as before, so that my workflow is not disrupted by the platform expansion.

#### Acceptance Criteria

1. THE Platform SHALL serve all existing `generation` app URLs under their current paths (`/generation/…`) without modification.
2. THE Platform SHALL serve all existing `thesis` app URLs under their current paths (`/thesis/…`) without modification.
3. THE Platform SHALL serve all existing `accounts` app URLs under their current paths (`/accounts/…`) without modification.
4. WHEN a user navigates to the Assignment Generator tool page, THE Platform SHALL display it as a Tool within the "Academic & Writing" category in the Tool_Registry.
5. WHEN a user navigates to the Thesis Generator tool page, THE Platform SHALL display it as a Tool within the "Academic & Writing" category in the Tool_Registry.
6. THE Assignment_Generator SHALL continue to function with `CLAUDE_MOCK_MODE=True` for zero-cost local development.
7. THE Thesis_Generator SHALL continue to support all four LLM providers (Anthropic, OpenRouter, Groq, Gemini) via the `LLM_PROVIDER` environment variable.

---

### Requirement 2: Tool Registry and Category System

**User Story:** As a platform visitor, I want to browse tools organised by category, so that I can quickly find the utility I need.

#### Acceptance Criteria

1. THE Tool_Registry SHALL store each Tool with: name, slug, category (FK), short description (≤255 chars), full description, icon identifier, template name, active flag, featured flag, new flag, pro flag, view count, tags (comma-separated), meta title (≤70 chars), meta description (≤160 chars), and display order.
2. THE Tool_Registry SHALL support the following nine primary categories: Student Tools, Writing Tools, Developer Tools, SEO Tools, Image Tools, PDF & File Tools, Resume & Career Tools, Utility Tools, Social & Viral Tools.
3. THE Tool_Registry SHALL include the existing Assignment Generator and Thesis Generator as Tools within an "Academic & Writing" category.
4. WHEN a category page is requested, THE Platform SHALL render all active Tools in that category ordered by display order then name.
5. THE Platform SHALL provide a management command `seed_tools` that populates the Tool_Registry with all defined tools and categories from a fixture, without duplicating existing records.
6. WHEN a Tool record is saved without a meta title, THE Tool_Registry SHALL auto-generate the meta title as `"{Tool.name} — Free Online Tool | LamGen"`.
7. WHEN a Tool record is saved without a meta description, THE Tool_Registry SHALL use the first 160 characters of the short description as the meta description.
8. THE Tool_Registry SHALL expose a `get_absolute_url()` method on each Tool returning the canonical URL pattern `/{category_slug}/{tool_slug}/`.

---

### Requirement 3: Tool Discovery and Search

**User Story:** As a visitor, I want to search for tools by name, description, or intent, so that I can find the right tool without browsing every category.

#### Acceptance Criteria

1. THE Platform SHALL provide a search endpoint at `/tools/search/` accepting a `q` query parameter.
2. WHEN a search query of fewer than 2 characters is submitted, THE Platform SHALL return an empty results list without querying the database.
3. WHEN a search query of 2 or more characters is submitted, THE Platform SHALL return up to 15 matching Tools ranked by relevance score.
4. THE Search_Index SHALL match against Tool name, short description, and tags fields.
5. THE Platform SHALL apply intent expansion: queries containing "convert", "format", "validate", or "make" SHALL expand to related synonyms before querying.
6. THE Command_Palette SHALL be accessible via the `/` key or `Ctrl+K` keyboard shortcut on any page.
7. WHEN the Command_Palette is open, THE Platform SHALL display search results within 300 milliseconds of the user stopping typing (debounced at 250ms).
8. THE Platform SHALL display a "Trending Tools" section on the homepage showing the 8 Tools with the highest view counts.
9. THE Platform SHALL display a "Recently Used" section on the homepage showing up to 5 Tools from the current session or user history.
10. THE Platform SHALL display a "New Tools" section on the homepage showing up to 6 Tools flagged as `is_new=True`.

---

### Requirement 4: Browser-Side Tool Processing

**User Story:** As a user, I want tools to process my input instantly in the browser without uploading data to a server, so that my data stays private and results are immediate.

#### Acceptance Criteria

1. THE Platform SHALL implement all Developer Tools (JSON formatter, XML formatter, YAML formatter, SQL beautifier, HTML/CSS/JS beautifier, CSS/JS minifier, JSON↔CSV converter, JWT decoder, Base64 encoder/decoder, Regex tester, Cron builder, UUID generator, Fake data generator, Lorem ipsum generator, Markdown previewer, Diff checker, Hash generator, URL encoder/decoder, Color palette generator, Gradient generator, robots.txt generator, sitemap.xml generator, htaccess generator, env formatter) as Browser_Tools with zero server-side processing.
2. THE Platform SHALL implement all Student Tools (GPA calculator, CGPA calculator, Grade predictor, Word counter, Reading time estimator, Readability checker, Pomodoro timer, Exam countdown, Flashcard generator, Timetable generator, Paragraph organizer, Academic title generator, Research topic generator, Plagiarism checklist) as Browser_Tools.
3. THE Platform SHALL implement all Writing Tools (Case converter, Fancy text generator, Unicode text styles, Duplicate remover, Keyword density checker, Headline generator, Sentence shortener, Text cleaner, Passive-active converter, Readability improver, Text simplifier) as Browser_Tools.
4. THE Platform SHALL implement all Utility Tools (Unit converter, Age calculator, Percentage calculator, EMI calculator, Tax calculator, BMI calculator, Timezone converter, Countdown timer, Stopwatch, Password generator, Password strength checker, Online notepad, Clipboard utility, Random picker, Dice generator) as Browser_Tools.
5. THE Platform SHALL implement all Social & Viral Tools (Fake chat generator, Fake tweet generator, Meme caption generator, Aesthetic font generator, Emoji combiner, Nickname generator, Pickup line generator, Roast generator, Random comment generator) as Browser_Tools.
6. THE Platform SHALL implement all SEO Tools (Meta title/description generator, Slug generator, SERP preview tool, Keyword density analyzer, OpenGraph generator, Twitter card generator, Schema markup generator, FAQ schema generator, Breadcrumb schema generator, robots.txt builder, Sitemap builder) as Browser_Tools.
7. THE Platform SHALL implement Image Tools (Image compressor, WEBP/JPG/PNG converter, Image resize, Crop, Rotate, Flip, Blur, Watermark, Meme generator, QR generator, Barcode generator, Favicon generator, Color extractor, Palette generator) as Browser_Tools using the browser Canvas API and/or WebAssembly libraries.
8. WHEN a Browser_Tool processes input, THE Platform SHALL display the result within the same page without a full page reload.
9. WHEN a Browser_Tool produces downloadable output (e.g., formatted JSON, converted image, generated PDF), THE Platform SHALL provide a download button that triggers a client-side file download.
10. IF a Browser_Tool receives invalid or empty input, THEN THE Platform SHALL display a descriptive inline error message without submitting data to the server.

---

### Requirement 5: Backend-Assisted Tool Processing

**User Story:** As a user, I want file-based tools (PDF merge, split, compress, image-to-PDF) to work reliably even for large files, so that I can process documents without installing software.

#### Acceptance Criteria

1. THE Platform SHALL implement PDF & File Tools (PDF merge, PDF split, Image to PDF, PDF to image, PDF compressor, Text extractor, ZIP extractor, CSV viewer, File rename utility, File compare utility) as Backend_Tools with Django view endpoints.
2. WHEN a file is uploaded to a Backend_Tool, THE Platform SHALL validate the file type using MIME type inspection (not extension alone) before processing.
3. WHEN a Backend_Tool completes processing, THE Platform SHALL return the output file as a downloadable HTTP response with the correct `Content-Disposition` header.
4. IF a Backend_Tool receives a file exceeding the configured size limit, THEN THE Platform SHALL return a descriptive error message without processing the file.
5. THE Platform SHALL implement Resume & Career Tools (Resume builder, ATS checker, Cover letter builder, Portfolio generator, LinkedIn headline generator, Bio generator, Invoice generator, Quotation builder) with client-side rendering where possible and Django endpoints only for PDF export.
6. WHEN a Backend_Tool processes a file, THE Platform SHALL delete the uploaded file from disk within 1 hour of processing completion.

---

### Requirement 6: Programmatic SEO Engine

**User Story:** As the platform operator, I want thousands of SEO-optimised content pages generated automatically from templates and data seeds, so that the platform ranks for long-tail search queries at scale.

#### Acceptance Criteria

1. THE SEO_Engine SHALL generate Programmatic_SEO_Pages for the following content types: Instagram/TikTok/Twitter captions, motivational quotes, birthday/anniversary wishes, social media bios, username ideas, hashtag sets, email templates, thesis topics, project ideas, coding interview questions, Laravel/Django code snippets, resume examples, portfolio examples.
2. EACH Programmatic_SEO_Page SHALL have a unique slug following the pattern `/{content_type}/{topic-slug}/` (e.g., `/captions/travel-instagram-captions/`).
3. THE Metadata_Engine SHALL generate a unique `<title>` and `<meta description>` for each Programmatic_SEO_Page using the page's topic and content type.
4. THE SEO_Engine SHALL support pagination of content lists at 20 items per page, with canonical URLs pointing to the first page.
5. THE SEO_Engine SHALL generate internal links between related Programmatic_SEO_Pages (same content type, adjacent topics).
6. THE Platform SHALL provide a management command `generate_seo_pages` that seeds the database with an initial set of Programmatic_SEO_Pages from a data fixture.
7. WHEN a Programmatic_SEO_Page is rendered, THE Metadata_Engine SHALL inject JSON-LD structured data appropriate to the content type (e.g., `ItemList` for lists, `Article` for long-form content).
8. THE SEO_Engine SHALL support category archive pages at `/{content_type}/` listing all topics within that content type with pagination.
9. THE Platform SHALL generate a dynamic XML sitemap including all active Tools, Categories, and Programmatic_SEO_Pages, updated at most every 24 hours via cache.

---

### Requirement 7: Metadata and SEO Infrastructure

**User Story:** As the platform operator, I want every page to have correct, unique metadata and structured data, so that search engines can index and rank the platform effectively.

#### Acceptance Criteria

1. THE Metadata_Engine SHALL inject a unique `<title>` tag on every page, with a maximum length of 70 characters.
2. THE Metadata_Engine SHALL inject a unique `<meta name="description">` tag on every page, with a maximum length of 160 characters.
3. THE Metadata_Engine SHALL inject OpenGraph tags (`og:title`, `og:description`, `og:url`, `og:type`, `og:image`) on every public page.
4. THE Metadata_Engine SHALL inject Twitter Card tags (`twitter:card`, `twitter:title`, `twitter:description`) on every public page.
5. THE Metadata_Engine SHALL inject a `<link rel="canonical">` tag on every page pointing to the canonical URL.
6. WHEN a Tool page is rendered, THE Metadata_Engine SHALL inject `SoftwareApplication` JSON-LD schema markup.
7. WHEN a Programmatic_SEO_Page of type "FAQ" is rendered, THE Metadata_Engine SHALL inject `FAQPage` JSON-LD schema markup.
8. THE Platform SHALL serve a `robots.txt` at `/robots.txt` that allows all crawlers, disallows `/admin/`, and references the sitemap URL.
9. THE Platform SHALL serve a paginated XML sitemap index at `/sitemap.xml` with per-section sitemaps for tools, categories, and SEO pages, cached for 24 hours.

---

### Requirement 8: Design System and UI/UX

**User Story:** As a user, I want a visually consistent, fast, and accessible interface across all tools, so that I can use any tool without relearning the UI.

#### Acceptance Criteria

1. THE Design_System SHALL implement a dark mode and a light mode, toggled by a persistent user preference stored in `localStorage`.
2. THE Design_System SHALL use TailwindCSS as the primary styling framework, with a custom configuration defining the platform's colour tokens, typography scale, and spacing scale.
3. THE Design_System SHALL implement a glassmorphism-inspired aesthetic with frosted-glass card surfaces, subtle gradients, and a dark-first colour palette.
4. THE Platform SHALL implement a responsive sidebar navigation visible on desktop (≥1024px) and collapsible to a bottom navigation bar on mobile (<1024px).
5. THE Platform SHALL implement a sticky tool action bar at the bottom of each tool page on mobile, containing the primary action button (e.g., "Format", "Convert", "Copy").
6. EVERY tool page SHALL display a loading state while processing and a success state upon completion.
7. THE Platform SHALL implement keyboard accessibility: all interactive elements SHALL be reachable via Tab, and all actions SHALL be triggerable via Enter or Space.
8. THE Platform SHALL achieve a Lighthouse Performance score of ≥85 on tool pages by lazy-loading non-critical JavaScript and deferring third-party scripts.
9. THE Design_System SHALL define reusable template partials for: tool card, category card, breadcrumb, ad slot, tool action bar, and search result item.
10. THE Platform SHALL implement a mobile-first responsive layout with breakpoints at 640px, 768px, 1024px, and 1280px.

---

### Requirement 9: Bookmark and History System

**User Story:** As a user, I want to bookmark my favourite tools and see my recently used tools, so that I can return to them quickly on future visits.

#### Acceptance Criteria

1. THE Bookmark_System SHALL allow Registered_Users to bookmark any Tool via a toggle action, persisted in the `ToolBookmark` database table.
2. THE Bookmark_System SHALL allow Guest_Users to bookmark up to 10 Tools per session, stored in the session cookie.
3. WHEN a Guest_User registers or logs in, THE Bookmark_System SHALL merge session bookmarks into the user's database bookmarks.
4. THE History_System SHALL record each Tool usage in the `ToolUsageHistory` table for Registered_Users, with a unique constraint per user per tool (updating the timestamp on repeat use).
5. THE History_System SHALL record up to 10 recently used Tool slugs in the session for Guest_Users.
6. WHEN a Registered_User views their dashboard, THE Platform SHALL display their bookmarked tools and recently used tools in separate sections.
7. THE Bookmark_System SHALL expose a `/tools/bookmark/toggle/` POST endpoint returning `{"bookmarked": true/false}` for AJAX toggling.
8. IF an unauthenticated user attempts to toggle a bookmark via the API, THEN THE Platform SHALL return HTTP 401 with `{"error": "Login required"}`.

---

### Requirement 10: Analytics and Monetisation Readiness

**User Story:** As the platform operator, I want built-in analytics hooks and ad placement slots, so that I can measure tool usage and monetise the platform without modifying templates later.

#### Acceptance Criteria

1. THE Analytics_Hook SHALL increment the `Tool.view_count` field on every tool page load, using a Redis-backed counter that flushes to the database every 10 views to reduce write load.
2. THE Analytics_Hook SHALL record `ToolUsageHistory` entries for Registered_Users on each tool use.
3. THE Platform SHALL define Ad_Slots in the base template and tool templates at the following positions: below the tool header, between the tool and related tools section, and in the sidebar.
4. EACH Ad_Slot SHALL be a named template partial (`{% include "partials/ad_slot.html" with slot_id="..." %}`) that renders an empty `<div>` with a data attribute, allowing ad network scripts to target it without template changes.
5. THE Platform SHALL expose a `/tools/trending/` page listing the 30 most-viewed Tools, suitable for internal linking and ad placement.
6. THE Platform SHALL track tool usage counts separately from view counts, incrementing a `usage_count` field when a tool's primary action is triggered (via a lightweight AJAX ping to `/tools/usage/record/`).
7. WHERE a SaaS_Tier is configured in future, THE Platform SHALL support marking individual Tools as `is_pro=True`, rendering a paywall overlay instead of the tool interface for unauthenticated or non-subscribed users.

---

### Requirement 11: Caching and Performance

**User Story:** As a user, I want tool pages and the homepage to load quickly even under high traffic, so that I can use the platform without frustration.

#### Acceptance Criteria

1. THE Platform SHALL apply `cache_control(public=True, max_age=600)` to all category pages and `max_age=60` to the homepage and tool index.
2. THE Platform SHALL cache the Tool_Registry query results (all active tools with categories) in Redis for 5 minutes using the `cache` framework.
3. THE Platform SHALL cache the sitemap XML responses for 24 hours using `cache_page(86400)`.
4. THE Platform SHALL serve all static assets (CSS, JS, images) with `Cache-Control: public, immutable` headers via WhiteNoise with `CompressedManifestStaticFilesStorage`.
5. WHEN a Browser_Tool is loaded, THE Platform SHALL lazy-load the tool's JavaScript bundle only when the tool page is visited, not on the homepage.
6. THE Platform SHALL implement a Redis-backed view counter that batches database writes (flush every 10 increments per tool) to avoid per-request DB writes on high-traffic tool pages.
7. THE Platform SHALL target a Time to First Byte (TTFB) of under 200ms for cached tool pages served from the Django application layer.

---

### Requirement 12: Modular Architecture and Extensibility

**User Story:** As a developer maintaining the platform, I want a modular, well-structured codebase, so that I can add new tools and categories without touching unrelated code.

#### Acceptance Criteria

1. THE Platform SHALL organise tool implementations into sub-modules within the `tools` Django app, with one Python module per tool category (e.g., `tools/developer/`, `tools/student/`, `tools/writing/`).
2. THE Platform SHALL define a shared `tools/utils/` module containing reusable processing functions (text cleaning, slug generation, file validation, metadata generation) used across multiple tools.
3. THE Platform SHALL define a shared `tools/templatetags/` module with template tags for rendering tool cards, ad slots, breadcrumbs, and schema markup.
4. WHEN a new Tool is added to the Tool_Registry, THE Platform SHALL require only: a database record (via admin or fixture), a template file at the path specified in `Tool.template_name`, and optionally a view function if the tool is a Backend_Tool.
5. THE Platform SHALL use Django's app registry pattern: each major feature area (tools, seo, accounts, generation, thesis) SHALL remain a separate Django app with its own models, views, URLs, and templates.
6. THE Platform SHALL define a `TOOL_CATEGORIES` configuration dictionary in `config/settings.py` listing all category slugs, names, icons, and colour tokens, used by both the seed command and the frontend Design_System.
7. THE Platform SHALL support adding a new Browser_Tool by creating a single HTML template file with embedded JavaScript — no Python code changes required.

---

### Requirement 13: Security and Data Integrity

**User Story:** As a user, I want my data to be handled securely, so that I can trust the platform with my files and personal information.

#### Acceptance Criteria

1. THE Platform SHALL validate all file uploads using MIME type inspection via `python-magic` before processing, rejecting files whose detected MIME type does not match the expected type for the tool.
2. THE Platform SHALL delete uploaded files from disk within 1 hour of processing completion using a Celery Beat scheduled task.
3. THE Platform SHALL enforce CSRF protection on all POST endpoints, including the bookmark toggle and usage recording endpoints.
4. THE Platform SHALL enforce object-level ownership: Registered_Users SHALL only be able to access their own `ToolUsageHistory` and `ToolBookmark` records via the dashboard.
5. THE Platform SHALL sanitise all user-supplied text inputs rendered in HTML output using Django's auto-escaping, with explicit `mark_safe` usage restricted to pre-validated, server-generated content only.
6. THE Platform SHALL rate-limit the search endpoint to 60 requests per minute per IP using Django's cache-based rate limiting, returning HTTP 429 on excess requests.
7. IF a Backend_Tool endpoint receives a request with a file exceeding the configured `MAX_UPLOAD_SIZE` setting, THEN THE Platform SHALL return HTTP 413 with a descriptive error message before reading the file content.

---

### Requirement 14: Programmatic SEO Content Quality

**User Story:** As a visitor arriving from a search engine, I want the SEO content pages to contain genuinely useful, non-placeholder content, so that I find value and return to the platform.

#### Acceptance Criteria

1. EACH Programmatic_SEO_Page SHALL contain a minimum of 20 content items (captions, quotes, examples, etc.) generated from deterministic rule-based templates — no LLM API calls, no placeholder text.
2. THE SEO_Engine SHALL generate content using Python-based template engines (string formatting, random.seed-based selection from curated word lists) with no external API dependencies.
3. WHEN a Programmatic_SEO_Page is rendered, THE Platform SHALL display the content items in a structured list with copy-to-clipboard functionality for each item.
4. THE SEO_Engine SHALL generate unique content for each topic slug by seeding the random generator with a hash of the slug, ensuring deterministic and reproducible output.
5. THE Platform SHALL implement internal linking: each Programmatic_SEO_Page SHALL link to at least 3 related Tool pages and 3 related SEO_Pages within the same content type.
6. THE SEO_Engine SHALL support at least 500 unique topic slugs across all content types at initial launch, expandable via the `generate_seo_pages` management command.

---

### Requirement 15: Guest and Authenticated User Experience

**User Story:** As a visitor, I want to use all free tools without creating an account, so that I can evaluate the platform before registering.

#### Acceptance Criteria

1. THE Platform SHALL allow Guest_Users to use all Browser_Tools and Backend_Tools without authentication.
2. THE Platform SHALL allow Guest_Users to use the search, browse categories, and view trending tools without authentication.
3. WHEN a Guest_User attempts to access a feature requiring authentication (dashboard, bookmark persistence beyond session), THE Platform SHALL display a non-intrusive prompt to register or log in, without blocking the current tool interaction.
4. THE Platform SHALL preserve Guest_User session state (recent tools, session bookmarks) for the duration of the browser session.
5. WHEN a Registered_User logs in, THE Platform SHALL display a personalised dashboard showing bookmarked tools, recent tool history, and usage statistics.
6. THE Platform SHALL support a "Continue as Guest" flow on the registration prompt, dismissing the prompt and allowing the user to continue without an account.
