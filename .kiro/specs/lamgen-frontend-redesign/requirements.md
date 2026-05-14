# Requirements Document

## Introduction

This document defines the requirements for a major frontend redesign and UI system upgrade of the LamGen AI SaaS platform. The goal is to transform the current interface into a production-grade, futuristic SaaS experience that feels calm, premium, intelligent, lightweight, and psychologically powerful — inspired by Linear, Vercel, OpenAI, and Stripe.

The redesign covers the global design system, navigation, homepage, tool pages, dashboard, auth pages, and secondary pages. All backend functionality (Django views, Celery tasks, AI generation pipeline, tool logic) must remain intact. Only the frontend layer is being rebuilt.

### Current State Analysis

After deep exploration of the codebase, the following architectural facts and issues were identified:

**Architecture:**
- Django 4.2 with Bootstrap 5.3.2 + Bootstrap Icons + vanilla JS
- Two CSS files: `main.css` (2122 lines, primary design system) and `design-system.css` (secondary utility layer)
- Base template: `templates/base.html` — global header, footer, command palette, mobile menu
- Tool pages: `templates/tools/tool_base.html` (856 lines of inline `<style>`) — all 300+ Tools share this
- Homepage: `templates/home.html` — two separate hero sections with conflicting styles in the same file
- Tools index: `templates/tools/index.html` — bento grid layout with inline styles
- Dashboard: `dashboard/templates/dashboard/dashboard.html` — uses old `var(--surface)`, `var(--border)`, `var(--text)` aliases instead of new `--lg-*` tokens
- Auth pages: `accounts/templates/accounts/login.html` — uses old aliases, heavy glow on submit button
- Fonts: Syne (display) + DM Sans (body) loaded from Google Fonts

**Identified Issues:**
1. **CSS duplication**: `tool_base.html` duplicates the entire input/button system already defined in `main.css` via inline `<style>` blocks — ~400 lines of redundant CSS per tool page
2. **Token inconsistency**: Dashboard uses `var(--surface)`, `var(--border)`, `var(--text)`, `var(--muted)`, `var(--primary)`, `var(--accent)` (old aliases). Auth pages use the same. Tool pages use `--lg-*` tokens. Three different token vocabularies in use simultaneously.
3. **Homepage conflict**: `home.html` contains two separate hero sections — one using `design-system.css` classes (`hero-section`, `btn-nexus`) and one using `main.css` classes (`btn-primary-nexus`, `btn-ghost-nexus`) with inline `<style>` blocks. The page renders both.
4. **Cinematic background overhead**: `main.css` defines `.space-bg` with 8 animated child elements (`.galaxy-cluster`, `.alien-grid`, `.planet`, `.light-beams`, `.stars`, `.particles`, `.rune-particles`, `.nebula`) all using `will-change: transform` and continuous CSS animations — significant paint/composite cost on low-end devices.
5. **Spiritual banner complexity**: The Islamic prayer banner (`spiritual_banner.html`) uses a complex grid layout (`minmax(380px, 1.8fr) repeat(4, minmax(240px, 1fr))`) that breaks on tablet widths (768px–1100px) and causes horizontal overflow on mobile.
6. **Navbar CSS conflict**: The navbar has styles defined in three places — `main.css` (`.app-header`, `.nav-brand`, `.nav-menu`), `design-system.css` (`.header`, `.nav-brand`, `.nav-link`), and an inline `<style>` block at the bottom of `base.html` that overrides both with `!important` declarations. The inline block uses `order: 0 !important` to fix a layout bug caused by `main.css` setting `order: 3` on `.nav-brand`.
7. **Mobile header collapse**: At 640px, `main.css` sets `.header-content { flex-direction: column }` which stacks the brand, nav, and actions vertically — breaking the header layout. The inline override in `base.html` partially fixes this but creates a fragile cascade.
8. **Dashboard uses 3D transforms**: `quick-card` and `ws-module` use `rotateX(4deg) rotateY(4deg)` on hover with `transform-style: preserve-3d` — causes GPU layer promotion and visual jank on mobile.
9. **Auth page glow**: Login submit button uses `box-shadow: 0 0 35px rgba(108,99,255,0.55)` on hover — heavy glow inconsistent with the calm premium direction.
10. **Redundant base templates**: Three base templates exist — `base.html`, `base_backup.html`, `base_fixed.html` — only `base.html` is used; the others are dead files.
11. **Hardcoded tool URLs in dashboard**: Quick actions use hardcoded paths (`/tools/media/image-compressor/`, `/tools/developer/json-formatter/`) instead of Django `{% url %}` tags.
12. **Command palette inline styles**: The command palette in `base.html` uses ~50 lines of inline `style=""` attributes on every element instead of CSS classes.
13. **Missing focus-visible styles**: Interactive elements (nav links, tool cards, action buttons) lack `:focus-visible` outlines — accessibility gap.
14. **No skip-to-content link**: The base template has no skip navigation link for keyboard/screen reader users.
15. **Font loading blocks render**: Google Fonts loaded with `<link rel="stylesheet">` without `font-display: swap` — causes FOIT (flash of invisible text).

---

## Glossary

- **Design_System**: The unified set of CSS custom properties (tokens), component classes, and layout utilities defined in `static/css/main.css` and `static/css/design-system.css`
- **Base_Template**: `templates/base.html` — the root Django template extended by all pages
- **Tool_Base**: `templates/tools/tool_base.html` — the shared template for all 300+ Free Tools individual tool pages
- **Token**: A CSS custom property (e.g., `--lg-violet`, `--lg-card-bg`) used to express design decisions
- **Tool_Canvas**: The `.tool-canvas` wrapper element on tool pages that contains the interactive tool workspace
- **Spiritual_Banner**: The Islamic prayer utilities panel rendered at the top of the tools index page
- **Command_Palette**: The global search overlay triggered by `/` or `Ctrl+K`
- **Nav_Mobile_Menu**: The animated dropdown navigation shown on screens ≤768px
- **Space_Bg**: The fixed cinematic background element with animated stars, particles, and fog layers
- **Bento_Grid**: The 12-column CSS grid layout used on the tools index page
- **LG_Token**: A CSS custom property prefixed with `--lg-` (e.g., `--lg-violet`, `--lg-card-bg`) — the canonical token vocabulary
- **Legacy_Token**: An old CSS alias (`--surface`, `--border`, `--text`, `--muted`, `--primary`, `--accent`) still used in dashboard and auth templates
- **WCAG**: Web Content Accessibility Guidelines — the accessibility standard targeted at WCAG 2.1 AA compliance

---

## Requirements

---

### Requirement 1: Unified CSS Token System

**User Story:** As a developer, I want a single canonical set of CSS custom properties, so that all pages use consistent colors, spacing, and typography without token conflicts.

#### Acceptance Criteria

1. THE Design_System SHALL define all color, spacing, typography, shadow, and border-radius values exclusively as `--lg-*` prefixed CSS custom properties in `static/css/main.css`
2. WHEN a Legacy_Token (`--surface`, `--border`, `--text`, `--muted`, `--primary`, `--accent`, `--glow`, `--danger`) is referenced in any template or CSS file, THE Design_System SHALL provide a backward-compatible alias mapping that resolves to the corresponding LG_Token
3. THE Design_System SHALL consolidate `static/css/design-system.css` and `static/css/main.css` so that no CSS custom property is defined in both files with different values
4. WHEN a new component is added, THE Design_System SHALL require it to use only LG_Tokens — no hardcoded hex values or rgba literals outside of the token definitions
5. THE Design_System SHALL define a complete color palette: deep indigo/navy backgrounds (`--lg-bg`, `--lg-bg-2`, `--lg-bg-3`), soft cyan/violet accents (`--lg-cyan`, `--lg-violet`), warm luminous text (`--lg-text`), and semantic states (success, warning, danger, info)

---

### Requirement 2: CSS Architecture Deduplication

**User Story:** As a developer, I want tool page styles defined once in the global stylesheet, so that the 300+ Free Tools tool pages don't each carry hundreds of lines of redundant inline CSS.

#### Acceptance Criteria

1. THE Tool_Base SHALL NOT contain inline `<style>` blocks that duplicate CSS rules already defined in `static/css/main.css`
2. WHEN the Tool_Canvas input/button/label styles are needed, THE Tool_Base SHALL reference CSS classes from `static/css/main.css` rather than redefining them inline
3. THE Design_System SHALL expose a `.tool-canvas` CSS class that fully styles all child inputs, buttons, labels, textareas, upload zones, and status badges without requiring per-page overrides
4. IF a tool requires unique styling not covered by the global system, THEN THE Tool_Base SHALL use a scoped `{% block tool_css %}` block for that tool's specific overrides only
5. THE Base_Template SHALL NOT contain inline `<style>` blocks for navbar styles — all navbar CSS SHALL be defined in `static/css/main.css`

---

### Requirement 3: Navigation System

**User Story:** As a user, I want a consistent, accessible navigation bar that works correctly on all screen sizes, so that I can move between sections of the platform without confusion.

#### Acceptance Criteria

1. THE Base_Template SHALL render a single sticky header with brand (left), navigation links (center), and action buttons (right) using a CSS grid layout with `grid-template-columns: auto 1fr auto`
2. WHEN the viewport width is ≤768px, THE Base_Template SHALL hide the desktop navigation links and show a hamburger toggle button
3. WHEN the hamburger toggle is activated, THE Nav_Mobile_Menu SHALL animate open using `max-height` transition (0 → content height) within 280ms
4. WHEN a navigation link matches the current page namespace, THE Base_Template SHALL apply an `active` class to that link with visually distinct styling
5. THE Base_Template SHALL include a skip-to-content link as the first focusable element, pointing to `#main-content`
6. WHEN the mobile menu is open and the user clicks outside the menu, THE Nav_Mobile_Menu SHALL close
7. THE Base_Template SHALL render auth state in the navigation: authenticated users see a profile button with dropdown (Dashboard, Sign Out); guests see a Sign In link
8. IF the navbar CSS is defined in multiple locations (inline style blocks, multiple CSS files), THEN THE Design_System SHALL consolidate all navbar styles into a single location in `static/css/main.css`

---

### Requirement 4: Homepage Structure

**User Story:** As a visitor, I want a clear, focused homepage that communicates LamGen's value and guides me to the right tools, so that I can start using the platform immediately.

#### Acceptance Criteria

1. THE Homepage SHALL render exactly one hero section — not two conflicting hero blocks as currently exists
2. THE Homepage SHALL display a hero with: a badge label, a primary headline using the display font (Syne), a subtitle, and two CTA buttons (primary and ghost variants)
3. THE Homepage SHALL display a featured tools panel and a categories panel below the hero using the established card components
4. WHEN the homepage is rendered, THE Homepage SHALL NOT include any inline `<style>` blocks — all styles SHALL come from the global CSS files
5. THE Homepage SHALL use only LG_Tokens for all color and spacing values
6. WHEN the viewport is ≤640px, THE Homepage SHALL stack all grid panels to a single column with appropriate vertical spacing

---

### Requirement 5: Tool Page System

**User Story:** As a user, I want every tool page to feel consistent, fast, and focused, so that I can use any of the 300+ Tools without relearning the interface.

#### Acceptance Criteria

1. THE Tool_Base SHALL render a tool page with: breadcrumb navigation, tool icon badge, tool title (h1), description, trust pills, the Tool_Canvas workspace, SEO content sections, related tools, and a trust footer
2. THE Tool_Canvas SHALL provide a visually distinct workspace area with a subtle gradient background, rounded corners (20px), and a category-colored top accent line
3. WHEN a user focuses any input inside the Tool_Canvas, THE Tool_Canvas SHALL apply a focus ring using `--lg-field-border-focus` and `--lg-field-shadow-focus` tokens
4. WHEN the viewport is ≤640px, THE Tool_Base SHALL apply a sticky bottom action row for the primary action button with backdrop blur
5. THE Tool_Base SHALL render related tools in a responsive grid that collapses to 2 columns on mobile
6. THE Tool_Base SHALL NOT duplicate input, button, or label CSS that is already defined in the global `.tool-canvas` class in `static/css/main.css`
7. WHEN a tool page is loaded, THE Tool_Base SHALL track the tool visit in `localStorage` under `lamgen_recent_tools` for the recently-used feature

---

### Requirement 6: Tools Index Page

**User Story:** As a user, I want a well-organized tools directory that helps me discover tools quickly, so that I can find what I need without scrolling through an overwhelming list.

#### Acceptance Criteria

1. THE Tools_Index SHALL render a bento-style grid layout with named zones: Active Systems (categories + games), Recently Used, Most Used, and Trending Tools
2. WHEN the viewport is ≤1024px, THE Tools_Index SHALL collapse 8-column spans to full-width and 4-column spans to 6-column
3. WHEN the viewport is ≤640px, THE Tools_Index SHALL collapse all spans to full-width with reduced padding
4. THE Tools_Index SHALL render the Spiritual_Banner at the top of the page when `islamic_panel` context is available
5. WHEN the Spiritual_Banner is rendered on mobile (≤768px), THE Spiritual_Banner SHALL use horizontal scroll (`overflow-x: auto`) to prevent layout overflow
6. THE Tools_Index SHALL render category workspace cards with per-category color theming using CSS custom properties (`--cat-color`)
7. WHEN a user has no recently-used tools in localStorage, THE Tools_Index SHALL hide the Recently Used panel gracefully without showing an empty container

---

### Requirement 7: Dashboard Page

**User Story:** As an authenticated user, I want a dashboard that shows my recent activity and provides quick access to tools and AI generation jobs, so that I can resume work efficiently.

#### Acceptance Criteria

1. THE Dashboard SHALL use only LG_Tokens (`--lg-*`) for all color and spacing values — no Legacy_Tokens (`--surface`, `--border`, `--text`, `--muted`, `--primary`, `--accent`)
2. THE Dashboard SHALL render a greeting section, continue-working panel (recent tools), tool category shortcuts, quick actions, trending tools, and favorites
3. WHEN the dashboard renders quick action cards, THE Dashboard SHALL use Django `{% url %}` template tags for all internal links — no hardcoded URL strings
4. WHEN the dashboard renders tool category cards, THE Dashboard SHALL NOT apply 3D perspective transforms (`rotateX`, `rotateY`, `preserve-3d`) — hover effects SHALL use only `translateY(-4px)` and `box-shadow` transitions
5. THE Dashboard SHALL use the `--lg-card-bg`, `--lg-card-border`, and `--lg-card-shadow` tokens for all card surfaces
6. WHEN the viewport is ≤768px, THE Dashboard SHALL render all grids as single-column layouts

---

### Requirement 8: Auth Pages

**User Story:** As a new or returning user, I want clean, focused login and registration pages that feel consistent with the rest of the platform, so that signing in feels like a natural part of the experience.

#### Acceptance Criteria

1. THE Auth_Pages SHALL use only LG_Tokens for all color and spacing values
2. THE Auth_Pages SHALL render a centered card layout with the LamGen brand mark, form fields using `.nexus-input` classes, and a primary submit button using `.btn-primary-nexus`
3. WHEN the submit button is hovered, THE Auth_Pages SHALL apply a `translateY(-2px)` lift and `box-shadow` using `--lg-glow-violet` — NOT a raw `0 0 35px rgba(108,99,255,0.55)` glow
4. THE Auth_Pages SHALL display form validation errors using the `.invalid-msg` class with `--lg-danger` color
5. WHEN the viewport is ≤480px, THE Auth_Pages SHALL reduce card padding to `1.5rem 1.25rem` and maintain full-width layout

---

### Requirement 9: Background and Animation Performance

**User Story:** As a user on any device, I want the platform to feel fast and smooth, so that visual effects don't cause jank or drain battery.

#### Acceptance Criteria

1. THE Space_Bg SHALL limit continuously-animating elements to a maximum of 3 layers — the current 8-layer system (galaxy-cluster, alien-grid, planet, light-beams, stars, particles, rune-particles, nebula) SHALL be reduced
2. WHEN a user has `prefers-reduced-motion: reduce` set in their OS, THE Space_Bg SHALL disable all CSS animations and transitions beyond 0.01ms duration
3. THE Space_Bg SHALL use `will-change: transform` only on elements that are actively animating — not as a blanket optimization on all layers
4. THE Design_System SHALL define animation durations using CSS custom properties (`--duration-fast: 150ms`, `--duration-base: 250ms`, `--duration-slow: 400ms`) so they can be overridden by the reduced-motion media query
5. WHEN the viewport is ≤768px, THE Space_Bg SHALL render a simplified version with at most 2 static gradient layers and no particle animations

---

### Requirement 10: Typography System

**User Story:** As a user, I want consistent, readable typography across all pages, so that the platform feels polished and professional.

#### Acceptance Criteria

1. THE Design_System SHALL define a fluid type scale using `clamp()` for all font size tokens: `--fs-xs` through `--fs-xxl`
2. THE Base_Template SHALL load Google Fonts (Syne + DM Sans) using `font-display: swap` to prevent FOIT
3. THE Design_System SHALL assign font families consistently: `--font-display` (Syne) for headings, brand names, and section labels; `--font-primary` (DM Sans) for body text, inputs, and UI labels
4. WHEN a heading element (h1–h3) is rendered inside a tool page, dashboard, or homepage, THE Design_System SHALL apply `font-family: var(--font-display)` and `font-weight: 700` or `800`
5. THE Design_System SHALL define line-height tokens: `--lh-tight: 1.25` for headings, `--lh-base: 1.7` for body text, `--lh-loose: 1.9` for long-form content

---

### Requirement 11: Responsive and Mobile-First Layout

**User Story:** As a mobile user, I want every page to be fully usable on a small screen, so that I can use LamGen tools on my phone without layout issues.

#### Acceptance Criteria

1. THE Design_System SHALL define breakpoints as CSS custom properties: `--bp-sm: 430px`, `--bp-md: 768px`, `--bp-lg: 1024px`, `--bp-xl: 1280px`
2. WHEN the viewport is ≤768px, THE Base_Template SHALL ensure the header height is `--header-height-mobile: 60px` and the brand name remains visible
3. WHEN the viewport is ≤640px, THE Base_Template SHALL NOT stack the header into a column layout — the brand and hamburger button SHALL remain on the same row
4. THE Tool_Base SHALL ensure the Tool_Canvas is fully usable on screens as narrow as 320px with no horizontal overflow
5. WHEN the viewport is ≤640px, THE Tools_Index SHALL hide the category workspace panel (`.hide-on-mobile`) and show only the games panel, recently used, and trending tools
6. THE Footer SHALL collapse from a 4-column grid to a 2-column grid at ≤900px and maintain readable link spacing at ≤540px
7. WHEN any interactive element is tapped on mobile, THE Design_System SHALL ensure a minimum touch target size of 44×44px

---

### Requirement 12: Accessibility

**User Story:** As a user relying on keyboard navigation or a screen reader, I want the platform to be navigable and understandable, so that I can use LamGen tools regardless of my input method.

#### Acceptance Criteria

1. THE Base_Template SHALL include a visually-hidden skip-to-content link as the first focusable element: `<a href="#main-content" class="skip-link">Skip to main content</a>`
2. WHEN an interactive element receives keyboard focus, THE Design_System SHALL render a visible `:focus-visible` outline using `box-shadow: 0 0 0 3px rgba(139,127,255,0.40)` — not `outline: none`
3. THE Base_Template SHALL set `aria-expanded` on the mobile menu toggle button and update it when the menu opens or closes
4. THE Tool_Base SHALL wrap the tool workspace in `<section aria-label="{{ tool.name }} workspace">` and the tool header in `<header>`
5. THE Base_Template SHALL set `role="navigation"` and `aria-label` on both the desktop nav and mobile nav elements
6. WHEN a form field has an error, THE Auth_Pages SHALL associate the error message with the field using `aria-describedby`
7. THE Design_System SHALL ensure all text/background color combinations meet WCAG 2.1 AA contrast ratio (4.5:1 for normal text, 3:1 for large text)
8. THE Command_Palette SHALL set `role="dialog"`, `aria-modal="true"`, and trap focus within the overlay when open

---

### Requirement 13: Command Palette

**User Story:** As a power user, I want a fast keyboard-accessible search overlay, so that I can navigate to any tool without using the mouse.

#### Acceptance Criteria

1. THE Command_Palette SHALL be triggered by pressing `/` (when not in an input) or `Ctrl+K` from any page
2. WHEN the Command_Palette opens, THE Command_Palette SHALL focus the search input within one animation frame
3. WHEN the user types at least 2 characters, THE Command_Palette SHALL debounce the search request by 250ms and fetch results from `/tools/search/?q=`
4. THE Command_Palette SHALL support keyboard navigation: `ArrowUp`/`ArrowDown` to move selection, `Enter` to open the selected result, `Escape` to close
5. THE Command_Palette SHALL NOT use inline `style=""` attributes on result items — all styles SHALL be defined as CSS classes
6. WHEN the Command_Palette is open, THE Command_Palette SHALL prevent body scroll by setting `overflow: hidden` on `<body>`
7. WHEN the user clicks outside the Command_Palette overlay, THE Command_Palette SHALL close

---

### Requirement 14: Component Standardization

**User Story:** As a developer, I want a documented set of reusable UI components, so that new pages and tools can be built consistently without reinventing patterns.

#### Acceptance Criteria

1. THE Design_System SHALL define a button hierarchy with exactly four variants: `.btn-primary-nexus` (gradient CTA), `.btn-ghost-nexus` (secondary), `.btn-danger-nexus` (destructive), `.btn-sm-nexus` (compact utility)
2. THE Design_System SHALL define a card system with exactly two variants: `.glass-card` (interactive surface with hover state) and `.panel` (static content container)
3. THE Design_System SHALL define a badge system: `.badge-nexus` base class with modifier classes `.badge-completed`, `.badge-processing`, `.badge-pending`, `.badge-failed`, `.badge-new`, `.badge-featured`
4. THE Design_System SHALL define a toast notification component: `.nexus-toast` with `.success` and `.danger` modifiers, rendered in a `.toast-container` fixed to `top: 80px; right: 1.5rem`
5. THE Design_System SHALL define a modal component: `.nexus-modal-overlay` with `.nexus-modal` inner panel, supporting `open` class toggle for visibility
6. WHEN a new tool page is created, THE Tool_Base SHALL provide all necessary component classes without requiring the tool author to write custom CSS for standard patterns

---

### Requirement 15: SEO and Performance Frontend Requirements

**User Story:** As the platform operator, I want the frontend to be optimized for search engine indexing and fast perceived performance, so that LamGen ranks well and users don't abandon slow-loading pages.

#### Acceptance Criteria

1. THE Base_Template SHALL include canonical URL meta tags, Open Graph tags, Twitter Card tags, and JSON-LD schema blocks in the `<head>` for every page
2. THE Base_Template SHALL preconnect to `fonts.googleapis.com` and `fonts.gstatic.com` using `<link rel="preconnect">` before the font stylesheet link
3. THE Tool_Base SHALL render the tool `<h1>` as the first heading on the page with the tool name as its text content
4. THE Base_Template SHALL set `Cache-Control: public, max-age=3600, s-maxage=86400` via meta http-equiv for page-level caching
5. WHEN static assets (CSS, JS, images) are referenced, THE Base_Template SHALL use Django's `{% static %}` tag to generate cache-busted URLs via WhiteNoise's `CompressedManifestStaticFilesStorage`
6. THE Base_Template SHALL load non-critical JavaScript (games scripts, behavioral scripts) with the `defer` attribute
7. THE Design_System SHALL NOT use `@import` inside CSS files — all stylesheets SHALL be linked directly in the `<head>` to avoid render-blocking chains

---

### Requirement 16: URL and Routing Consistency

**User Story:** As a user and search engine, I want consistent, predictable URLs across the platform, so that links work reliably and pages are indexed correctly.

#### Acceptance Criteria

1. THE Dashboard SHALL use Django `{% url %}` template tags for all internal navigation links — no hardcoded URL strings
2. THE Base_Template SHALL use `{% url 'home' %}`, `{% url 'tools:index' %}`, `{% url 'seo:index' %}`, `{% url 'games:index' %}`, `{% url 'blog:index' %}` for all navigation links
3. THE Footer SHALL use Django `{% url %}` tags for all internal links including privacy, terms, about, contact, blog, and tools pages
4. WHEN a tool category URL is referenced in a template, THE Template SHALL use `{{ category.get_absolute_url }}` rather than constructing the URL manually
5. THE Base_Template SHALL include `<link rel="alternate" hreflang="x-default">` and per-language hreflang tags for i18n-enabled pages

---

### Requirement 17: Dead Code Removal

**User Story:** As a developer, I want the codebase free of unused templates and CSS, so that the frontend is maintainable and doesn't confuse future contributors.

#### Acceptance Criteria

1. THE Repository SHALL NOT contain `templates/base_backup.html` or `templates/base_fixed.html` — these unused backup files SHALL be deleted
2. THE Design_System SHALL NOT define CSS classes that are not referenced by any template or JavaScript file
3. WHEN the `.app-sidebar` CSS class is defined in `main.css` as `display: none`, THE Design_System SHALL either remove it entirely or document it as a reserved class for future use
4. THE Dashboard template SHALL NOT contain the `openToolsPanel` JavaScript function that fetches HTML and attempts to parse `.tool-grid` and `.tool-card` selectors that no longer exist in the current template structure

---

### Requirement 18: Visual Design Direction

**User Story:** As a user, I want the platform to feel calm, premium, and intelligent — not overwhelming or visually noisy — so that I can focus on my work.

#### Acceptance Criteria

1. THE Design_System SHALL use deep indigo/navy as the primary background palette: `--lg-bg: #07091A`, `--lg-bg-2: #0C0E22`, `--lg-bg-3: #10132A`
2. THE Design_System SHALL use soft cyan (`--lg-cyan: #3EECD8`) and violet (`--lg-violet: #8B7FFF`) as accent colors — applied sparingly to interactive elements, icons, and highlights
3. THE Design_System SHALL use warm luminous yellow-white as the primary text color (`--lg-text: #F5E9B8`) for a calm, non-harsh reading experience
4. WHEN glow effects are applied to UI elements, THE Design_System SHALL limit glow opacity to a maximum of `0.30` alpha — no full-saturation neon glows
5. THE Design_System SHALL define card surfaces as solid indigo-navy (`--lg-card-bg: #0F1228`) rather than semi-transparent rgba overlays, ensuring consistent rendering across different background contexts
6. WHEN hover states are applied to cards, THE Design_System SHALL use `translateY(-2px)` lift with `box-shadow` increase — NOT scale transforms or 3D rotations
7. THE Design_System SHALL reduce the Space_Bg to a calm ambient gradient with at most 3 subtle radial gradients and 1 optional slow-drifting star layer — removing the alien grid, planet ring, light beams, rune particles, and fog layers

