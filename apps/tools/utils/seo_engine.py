"""
LamGen SEO Content Engine — Full Production SEO Package Generator.

Generates a complete, unique SEO content package for every tool page:
  1. meta (title, description, primary/secondary keywords)
  2. hero (headline, subheading, cta_text)
  3. intro (200-300 word long-form intro)
  4. use_cases (5-10 real-world use cases)
  5. features (6-12 benefit-focused features)
  6. how_to_use (3-6 step guide)
  7. faqs (7-10 long-tail FAQ items)
  8. keywords (primary, semantic, LSI)
  9. internal_links (related tool slugs + cross-link suggestions)
  10. schema (SoftwareApplication + FAQPage JSON-LD dicts)

All content is generated statically from tool metadata — no AI API calls,
instant execution, scales to 300+ tools.

Usage:
    from apps.tools.utils.seo_engine import SEOContentEngine
    engine = SEOContentEngine()
    package = engine.generate(tool_name, category, short_desc, slug, tags)
"""
from __future__ import annotations
import re
from typing import Any

# ---------------------------------------------------------------------------
# Per-category content profiles
# ---------------------------------------------------------------------------
_CATEGORY_PROFILES: dict[str, dict[str, Any]] = {
    "career": {
        "audience": "job seekers, professionals, and career changers",
        "pain_point": "standing out in a competitive job market",
        "benefit": "land more interviews and advance your career faster",
        "action_verb": "Build",
        "category_kw": "free career tool",
        "trust_signal": "Used by thousands of job seekers every month",
        "cta": "Start building your career advantage — free, instant, no signup.",
        "related_category": "writing",
    },
    "writing": {
        "audience": "writers, bloggers, students, and content creators",
        "pain_point": "producing high-quality written content quickly",
        "benefit": "write better content in a fraction of the time",
        "action_verb": "Write",
        "category_kw": "free writing tool",
        "trust_signal": "Trusted by writers and content teams worldwide",
        "cta": "Start writing smarter — free, no account needed.",
        "related_category": "seo",
    },
    "seo": {
        "audience": "SEO professionals, content marketers, and website owners",
        "pain_point": "ranking higher on Google and driving organic traffic",
        "benefit": "improve your search rankings and grow organic traffic",
        "action_verb": "Optimize",
        "category_kw": "free SEO tool",
        "trust_signal": "Trusted by SEO teams and digital marketers",
        "cta": "Start optimizing for search — free, instant results.",
        "related_category": "writing",
    },
    "creator": {
        "audience": "content creators, YouTubers, and social media managers",
        "pain_point": "consistently creating engaging content across platforms",
        "benefit": "grow your audience and boost engagement faster",
        "action_verb": "Create",
        "category_kw": "free content creation tool",
        "trust_signal": "Used by creators across YouTube, Instagram, and TikTok",
        "cta": "Start creating viral content — free, no signup required.",
        "related_category": "writing",
    },
    "business": {
        "audience": "entrepreneurs, startup founders, and business owners",
        "pain_point": "building a brand and launching a business efficiently",
        "benefit": "launch and grow your business with professional-grade output",
        "action_verb": "Launch",
        "category_kw": "free business tool",
        "trust_signal": "Trusted by founders and entrepreneurs worldwide",
        "cta": "Start building your business — free, instant, no signup.",
        "related_category": "creator",
    },
    "education": {
        "audience": "students, teachers, and academic researchers",
        "pain_point": "studying effectively and producing quality academic work",
        "benefit": "study smarter, write better, and achieve higher grades",
        "action_verb": "Study",
        "category_kw": "free student tool",
        "trust_signal": "Used by students at universities worldwide",
        "cta": "Start studying smarter — free, instant, no account needed.",
        "related_category": "writing",
    },
    "developer": {
        "audience": "developers, engineers, and technical professionals",
        "pain_point": "writing, debugging, and optimizing code efficiently",
        "benefit": "ship better code faster with zero friction",
        "action_verb": "Build",
        "category_kw": "free developer tool",
        "trust_signal": "Trusted by developers and engineering teams",
        "cta": "Start coding smarter — free, runs in your browser.",
        "related_category": "seo",
    },
    "developer-tools": {
        "audience": "developers, engineers, and technical professionals",
        "pain_point": "formatting, validating, and transforming data and code",
        "benefit": "work faster with instant browser-based developer utilities",
        "action_verb": "Format",
        "category_kw": "free online developer tool",
        "trust_signal": "Trusted by developers and engineering teams worldwide",
        "cta": "Start using it free — no install, no signup, instant results.",
        "related_category": "writing-tools",
    },
    "writing-tools": {
        "audience": "writers, bloggers, students, and content creators",
        "pain_point": "editing, formatting, and improving written content",
        "benefit": "produce polished, professional writing in seconds",
        "action_verb": "Write",
        "category_kw": "free writing tool",
        "trust_signal": "Trusted by writers and content teams worldwide",
        "cta": "Start writing better — free, instant, no account needed.",
        "related_category": "seo-tools",
    },
    "seo-tools": {
        "audience": "SEO professionals, content marketers, and website owners",
        "pain_point": "optimizing content and metadata for search engines",
        "benefit": "improve your search rankings with data-driven insights",
        "action_verb": "Optimize",
        "category_kw": "free SEO tool",
        "trust_signal": "Trusted by SEO teams and digital marketers",
        "cta": "Start optimizing — free, instant, no signup required.",
        "related_category": "writing-tools",
    },
    "image-tools": {
        "audience": "designers, developers, and content creators",
        "pain_point": "compressing, converting, and editing images for the web",
        "benefit": "optimize images instantly without Photoshop or uploads",
        "action_verb": "Optimize",
        "category_kw": "free image tool",
        "trust_signal": "Trusted by designers and web developers worldwide",
        "cta": "Start optimizing images — free, private, runs in your browser.",
        "related_category": "developer-tools",
    },
    "student-tools": {
        "audience": "students, teachers, and academic researchers",
        "pain_point": "managing study time and producing quality academic work",
        "benefit": "study smarter and achieve better results with less stress",
        "action_verb": "Study",
        "category_kw": "free student tool",
        "trust_signal": "Used by students at universities worldwide",
        "cta": "Start studying smarter — free, instant, no account needed.",
        "related_category": "writing-tools",
    },
    "utility-tools": {
        "audience": "professionals, students, and everyday users",
        "pain_point": "performing quick calculations and conversions online",
        "benefit": "get instant, accurate results without installing software",
        "action_verb": "Calculate",
        "category_kw": "free online utility",
        "trust_signal": "Used by millions of people worldwide",
        "cta": "Start using it free — instant results, no signup required.",
        "related_category": "developer-tools",
    },
    "social-tools": {
        "audience": "social media managers, marketers, and content creators",
        "pain_point": "creating engaging social media content at scale",
        "benefit": "grow your social presence with high-performing content",
        "action_verb": "Create",
        "category_kw": "free social media tool",
        "trust_signal": "Trusted by social media managers and marketers",
        "cta": "Start creating — free, instant, no account needed.",
        "related_category": "writing-tools",
    },
    "pdf-tools": {
        "audience": "office workers, students, and professionals",
        "pain_point": "managing, merging, and converting PDF documents",
        "benefit": "handle PDF files instantly without desktop software",
        "action_verb": "Process",
        "category_kw": "free PDF tool",
        "trust_signal": "Trusted by professionals and students worldwide",
        "cta": "Start processing PDFs — free, private, no upload required.",
        "related_category": "developer-tools",
    },
}

_DEFAULT_PROFILE: dict[str, Any] = {
    "audience": "professionals, students, and everyday users",
    "pain_point": "getting things done quickly and efficiently online",
    "benefit": "save time and work smarter with instant browser-based tools",
    "action_verb": "Use",
    "category_kw": "free online tool",
    "trust_signal": "Trusted by users worldwide",
    "cta": "Start using it free — instant results, no signup required.",
    "related_category": "developer-tools",
}

# ---------------------------------------------------------------------------
# Per-tool overrides for highest-traffic tools
# ---------------------------------------------------------------------------
_TOOL_OVERRIDES: dict[str, dict[str, Any]] = {
    "resume-builder": {
        "primary_keyword": "AI resume builder free",
        "hero_headline": "Build a Professional Resume in Minutes with AI",
        "hero_subheading": "Generate ATS-optimized resumes tailored to any job description — free, instant, no signup.",
        "intro_hook": "Getting past Applicant Tracking Systems is the first battle in any job search.",
        "secondary_keywords": [
            "free AI resume builder online", "ATS-friendly resume generator",
            "resume builder no signup", "professional resume maker free",
            "AI-powered resume writer", "resume builder for job seekers",
            "free resume creator online",
        ],
    },
    "ats-checker": {
        "primary_keyword": "ATS resume checker free",
        "hero_headline": "Check If Your Resume Passes ATS Screening — Instantly",
        "hero_subheading": "Analyze your resume against ATS algorithms and get a score, issues, and actionable fixes.",
        "intro_hook": "Over 75% of resumes are rejected by ATS before a human ever reads them.",
        "secondary_keywords": [
            "ATS resume scanner free", "resume ATS score checker",
            "applicant tracking system checker", "ATS optimization tool",
            "resume keyword checker", "free ATS resume analyzer",
        ],
    },
    "cover-letter-generator": {
        "primary_keyword": "AI cover letter generator free",
        "hero_headline": "Generate a Tailored Cover Letter in Seconds",
        "hero_subheading": "AI-powered cover letters customized to the job description and your background.",
        "intro_hook": "A generic cover letter gets ignored. A tailored one gets interviews.",
        "secondary_keywords": [
            "free cover letter writer online", "AI cover letter maker",
            "cover letter generator no signup", "professional cover letter template",
            "cover letter builder free",
        ],
    },
    "ai-humanizer": {
        "primary_keyword": "AI text humanizer free",
        "hero_headline": "Make AI-Generated Text Sound Human — Instantly",
        "hero_subheading": "Rewrite ChatGPT, Gemini, or any AI output to pass AI detectors and read naturally.",
        "intro_hook": "AI-generated content is everywhere — but it still sounds robotic. Until now.",
        "secondary_keywords": [
            "humanize AI text free", "AI content humanizer online",
            "bypass AI detection tool", "make AI writing sound human",
            "AI text rewriter free", "ChatGPT humanizer tool",
            "AI to human text converter",
        ],
    },
    "grammar-checker": {
        "primary_keyword": "free grammar checker online",
        "hero_headline": "Check and Fix Grammar Errors Instantly",
        "hero_subheading": "AI-powered grammar checker that catches errors, improves style, and scores your writing.",
        "intro_hook": "Grammar mistakes cost you credibility — whether in a job application, email, or essay.",
        "secondary_keywords": [
            "grammar checker free online", "AI grammar corrector",
            "spell and grammar check", "grammar fixer tool",
            "English grammar checker", "writing grammar tool free",
        ],
    },
    "blog-writer": {
        "primary_keyword": "AI blog writer free",
        "hero_headline": "Generate Full SEO Blog Posts with AI",
        "hero_subheading": "Write keyword-optimized, long-form blog content in seconds — free, no signup.",
        "intro_hook": "Consistent, high-quality blog content is the backbone of organic SEO growth.",
        "secondary_keywords": [
            "free AI blog post generator", "AI content writer online",
            "SEO blog writer tool", "blog post generator free",
            "AI article writer no signup", "automated blog writing tool",
        ],
    },
    "youtube-script-generator": {
        "primary_keyword": "YouTube script generator free",
        "hero_headline": "Generate Engaging YouTube Scripts in Seconds",
        "hero_subheading": "AI-written video scripts with hooks, structure, and CTAs — optimized for watch time.",
        "intro_hook": "The first 30 seconds of your video determine whether viewers stay or leave.",
        "secondary_keywords": [
            "free YouTube script writer", "AI video script generator",
            "YouTube script template free", "video script writer online",
            "AI YouTube content creator",
        ],
    },
    "sql-query-generator": {
        "primary_keyword": "AI SQL query generator free",
        "hero_headline": "Generate SQL Queries from Plain English",
        "hero_subheading": "Describe what you need in plain language — get optimized SQL instantly.",
        "intro_hook": "Writing complex SQL queries from scratch is slow and error-prone.",
        "secondary_keywords": [
            "SQL generator from text free", "natural language to SQL",
            "AI SQL writer online", "SQL query builder free",
            "text to SQL converter", "SQL generator no signup",
        ],
    },
    "paraphrasing-tool": {
        "primary_keyword": "free paraphrasing tool online",
        "hero_headline": "Paraphrase Any Text Instantly — Free",
        "hero_subheading": "Rewrite sentences and paragraphs with different words while keeping the original meaning.",
        "intro_hook": "Whether you are avoiding plagiarism or just refreshing stale content, paraphrasing is essential.",
        "secondary_keywords": [
            "paraphrase tool free online", "AI paraphraser no signup",
            "sentence rewriter free", "text paraphraser online",
            "reword text free tool", "plagiarism rewriter tool",
        ],
    },
    "flashcard-generator": {
        "primary_keyword": "AI flashcard generator free",
        "hero_headline": "Turn Any Topic into Study Flashcards Instantly",
        "hero_subheading": "AI-generated flashcards for spaced repetition learning — free, instant, no signup.",
        "intro_hook": "Spaced repetition is the most scientifically proven study method — and flashcards are its foundation.",
        "secondary_keywords": [
            "free flashcard maker online", "AI study flashcard generator",
            "digital flashcard creator free", "flashcard generator from notes",
            "study card maker free",
        ],
    },
    "email-writer": {
        "primary_keyword": "AI email writer free",
        "hero_headline": "Write Professional Emails in Seconds with AI",
        "hero_subheading": "Generate clear, effective emails for any purpose — free, instant, no signup.",
        "intro_hook": "The average professional spends 28% of their workday on email. AI can change that.",
        "secondary_keywords": [
            "free AI email generator", "professional email writer online",
            "email writing tool free", "AI email composer",
            "business email generator free",
        ],
    },
    "keyword-cluster-generator": {
        "primary_keyword": "keyword cluster generator free",
        "hero_headline": "Generate Keyword Clusters for Topical SEO Authority",
        "hero_subheading": "Build comprehensive keyword clusters from any seed keyword — free, instant, no signup.",
        "intro_hook": "Topical authority is how modern SEO works. Keyword clusters are how you build it.",
        "secondary_keywords": [
            "keyword clustering tool free", "SEO keyword cluster builder",
            "topical authority keyword tool", "keyword grouping tool",
            "semantic keyword cluster generator",
        ],
    },
    "linkedin-headline-generator": {
        "primary_keyword": "LinkedIn headline generator free",
        "hero_headline": "Generate a LinkedIn Headline That Gets You Noticed",
        "hero_subheading": "AI-crafted LinkedIn headlines optimized for recruiter searches and profile views.",
        "intro_hook": "Your LinkedIn headline is the first thing recruiters see — make it count.",
        "secondary_keywords": [
            "free LinkedIn headline maker", "AI LinkedIn profile optimizer",
            "LinkedIn headline ideas free", "professional LinkedIn headline generator",
            "LinkedIn headline for job seekers",
        ],
    },
    "code-debugger": {
        "primary_keyword": "AI code debugger free",
        "hero_headline": "Debug Your Code Instantly with AI",
        "hero_subheading": "Paste your code, describe the bug — get the fix, explanation, and suggestions instantly.",
        "intro_hook": "Debugging is where developers spend most of their time. AI can cut that dramatically.",
        "secondary_keywords": [
            "free AI code debugger online", "AI bug finder tool",
            "code error fixer free", "AI code analyzer",
            "debug code online free",
        ],
    },
    "quiz-generator": {
        "primary_keyword": "AI quiz generator free",
        "hero_headline": "Generate Multiple-Choice Quizzes from Any Topic",
        "hero_subheading": "AI-powered quiz maker with questions, options, answers, and explanations — free, instant.",
        "intro_hook": "Active recall through quizzing is proven to improve retention by up to 50%.",
        "secondary_keywords": [
            "free quiz maker online", "AI quiz creator tool",
            "multiple choice question generator", "quiz generator from text",
            "study quiz maker free",
        ],
    },
    "startup-name-generator": {
        "primary_keyword": "startup name generator free",
        "hero_headline": "Generate Creative Startup Names with AI",
        "hero_subheading": "Get 10 unique, memorable startup name ideas with rationale — free, instant, no signup.",
        "intro_hook": "Your startup name is your first impression. It needs to be memorable, available, and meaningful.",
        "secondary_keywords": [
            "free business name generator", "AI startup name ideas",
            "company name generator free", "brand name generator online",
            "startup naming tool free",
        ],
    },
}


# ---------------------------------------------------------------------------
# Internal linking map — category-level cross-links
# ---------------------------------------------------------------------------
_INTERNAL_LINK_MAP: dict[str, list[str]] = {
    "career": [
        "resume-builder", "ats-checker", "cover-letter-generator",
        "linkedin-headline-generator", "linkedin-post-generator",
        "salary-negotiation-script", "ai-resume-builder",
    ],
    "writing": [
        "ai-humanizer", "essay-writer", "paraphrasing-tool", "grammar-checker",
        "email-writer", "cold-email-generator", "readability-improver",
        "text-simplifier",
    ],
    "seo": [
        "blog-writer", "seo-article-generator", "meta-description-generator",
        "keyword-cluster-generator", "ai-meta-description-generator",
        "ai-blog-title-generator", "ai-keyword-intent-analyzer", "ai-faq-generator",
    ],
    "creator": [
        "youtube-script-generator", "youtube-title-generator",
        "instagram-caption-generator", "tweet-generator",
        "ai-viral-hook-generator", "ai-carousel-copy-generator",
        "ai-reels-script-outline", "social-content-calendar-planner",
    ],
    "business": [
        "startup-name-generator", "business-plan-generator",
        "logo-prompt-generator", "image-prompt-generator",
    ],
    "education": [
        "notes-generator", "quiz-generator", "flashcard-generator",
        "ai-essay-outline-generator", "ai-thesis-statement-generator",
        "ai-notes-summarizer", "ai-flashcard-generator", "ai-study-planner",
        "ai-citation-generator", "grade-predictor", "research-topic-generator",
    ],
    "developer": [
        "sql-query-generator", "regex-generator", "code-debugger",
        "sql-generator", "html-minifier",
    ],
}

# ---------------------------------------------------------------------------
# Feature templates per category
# ---------------------------------------------------------------------------
_CATEGORY_FEATURES: dict[str, list[dict[str, str]]] = {
    "career": [
        {"title": "ATS-Optimized Output", "desc": "Every result is structured to pass Applicant Tracking Systems used by top employers."},
        {"title": "Tailored to Your Background", "desc": "Input your experience and get content personalized to your specific career history."},
        {"title": "Professional Tone", "desc": "AI-crafted language that matches industry standards and recruiter expectations."},
        {"title": "Instant Generation", "desc": "Get professional-quality career content in seconds, not hours."},
        {"title": "No Templates Required", "desc": "Skip the blank page — AI generates a complete, ready-to-use draft instantly."},
        {"title": "Free Forever", "desc": "No subscription, no credits, no paywalls. Full access at zero cost."},
        {"title": "Privacy First", "desc": "Your career data is never stored or shared. Everything stays in your browser session."},
        {"title": "Mobile Friendly", "desc": "Works perfectly on any device — phone, tablet, or desktop."},
    ],
    "writing": [
        {"title": "Natural, Human-Sounding Output", "desc": "AI-generated content that reads like it was written by a skilled human writer."},
        {"title": "Multiple Tone Options", "desc": "Adjust the tone from formal to casual to match your audience and context."},
        {"title": "Instant Rewriting", "desc": "Transform any text in seconds — no waiting, no queues."},
        {"title": "Plagiarism-Safe", "desc": "All output is uniquely generated, reducing plagiarism risk in academic and professional work."},
        {"title": "Grammar and Style Aware", "desc": "Output follows proper grammar rules and stylistic best practices."},
        {"title": "Free to Use", "desc": "No account, no subscription, no limits. Write as much as you need."},
        {"title": "Works for Any Format", "desc": "Emails, essays, blog posts, social captions — one tool handles them all."},
        {"title": "Browser-Based Privacy", "desc": "Your text never leaves your device. Zero server-side storage."},
    ],
    "seo": [
        {"title": "Keyword-Rich Output", "desc": "Every piece of content is optimized with target keywords placed naturally for maximum SEO impact."},
        {"title": "Search Intent Aligned", "desc": "Content is structured to match informational, navigational, and transactional search intent."},
        {"title": "Long-Tail Keyword Coverage", "desc": "Automatically surfaces long-tail variations that drive qualified organic traffic."},
        {"title": "Schema-Ready Content", "desc": "Output is structured to support FAQ, HowTo, and Article schema markup."},
        {"title": "Instant Generation", "desc": "Generate SEO content in seconds — no waiting for writers or agencies."},
        {"title": "Free Forever", "desc": "No subscription required. Full SEO content generation at zero cost."},
        {"title": "Unique Per Use", "desc": "Every generation produces unique content — no duplicate content penalties."},
        {"title": "Competitor-Level Quality", "desc": "Output matches the depth and quality of content ranking on Google page one."},
    ],
    "creator": [
        {"title": "Platform-Optimized Content", "desc": "Content is tailored to the specific format, tone, and algorithm of each platform."},
        {"title": "Hook-First Structure", "desc": "Every piece starts with a scroll-stopping hook designed to maximize engagement."},
        {"title": "Viral Potential", "desc": "Techniques from top-performing creators are baked into every output."},
        {"title": "Multi-Platform Ready", "desc": "Adapt content for YouTube, Instagram, TikTok, LinkedIn, and Twitter in one click."},
        {"title": "CTA Included", "desc": "Every script and caption includes a clear call-to-action to drive follows, clicks, or conversions."},
        {"title": "Free to Use", "desc": "No subscription, no credits. Create unlimited content at zero cost."},
        {"title": "Instant Output", "desc": "Get production-ready content in seconds — no creative blocks, no delays."},
        {"title": "Niche-Aware", "desc": "Input your niche and audience for content that resonates with your specific community."},
    ],
    "business": [
        {"title": "Professional-Grade Output", "desc": "Business content that matches the quality of agency-produced work — at zero cost."},
        {"title": "Brand-Aware Generation", "desc": "Input your brand details for output that reflects your unique identity and positioning."},
        {"title": "Investor-Ready Language", "desc": "Business plans and pitches use language that resonates with investors and stakeholders."},
        {"title": "Instant Ideation", "desc": "Generate 10+ name ideas, prompts, or plan sections in seconds."},
        {"title": "No Business Expertise Required", "desc": "AI handles the structure and language — you just provide the idea."},
        {"title": "Free Forever", "desc": "No subscription, no agency fees. Full business content generation at zero cost."},
        {"title": "Unique Every Time", "desc": "Every generation is unique — no cookie-cutter templates or recycled ideas."},
        {"title": "Privacy Protected", "desc": "Your business ideas are never stored or shared. Complete confidentiality."},
    ],
    "education": [
        {"title": "Curriculum-Aligned Output", "desc": "Content follows academic standards and is appropriate for all education levels."},
        {"title": "Active Recall Optimized", "desc": "Flashcards and quizzes are designed using proven spaced repetition principles."},
        {"title": "Citation-Accurate", "desc": "References and citations follow APA, MLA, and Chicago style guidelines precisely."},
        {"title": "Instant Study Materials", "desc": "Generate notes, flashcards, and outlines in seconds from any topic or content."},
        {"title": "Plagiarism-Safe", "desc": "All generated content is unique and properly structured for academic submission."},
        {"title": "Free for Students", "desc": "No subscription, no credits. Full access for every student at zero cost."},
        {"title": "Works for Any Subject", "desc": "From STEM to humanities — the tool adapts to any academic discipline."},
        {"title": "Mobile Friendly", "desc": "Study anywhere — works perfectly on phones, tablets, and laptops."},
    ],
    "developer": [
        {"title": "Optimized Code Output", "desc": "Generated code follows best practices for performance, readability, and maintainability."},
        {"title": "Multi-Language Support", "desc": "Works with SQL, Python, JavaScript, regex, HTML, and more."},
        {"title": "Explanation Included", "desc": "Every output includes a plain-English explanation of what the code does and why."},
        {"title": "Error Detection", "desc": "Identifies bugs, anti-patterns, and potential issues in submitted code."},
        {"title": "Instant Results", "desc": "Get production-ready code in seconds — no waiting, no setup."},
        {"title": "Free Forever", "desc": "No subscription, no API keys required. Full developer tooling at zero cost."},
        {"title": "Browser-Based", "desc": "No installation, no IDE required. Works in any modern browser."},
        {"title": "Privacy First", "desc": "Your code is never stored or sent to third parties. Fully private."},
    ],
}

_DEFAULT_FEATURES = [
    {"title": "Instant Results", "desc": "Get accurate output in seconds — no waiting, no queues."},
    {"title": "100% Free", "desc": "No subscription, no credits, no paywalls. Full access at zero cost."},
    {"title": "No Signup Required", "desc": "Open the page and start immediately. No account needed."},
    {"title": "Browser-Based Privacy", "desc": "All processing happens in your browser. Your data never leaves your device."},
    {"title": "Mobile Responsive", "desc": "Works perfectly on any device — phone, tablet, or desktop."},
    {"title": "No Installation", "desc": "Nothing to download or install. Works in any modern browser."},
    {"title": "Unlimited Usage", "desc": "Use it as many times as you need with no daily limits or caps."},
    {"title": "Always Up to Date", "desc": "Cloud-based tool — always running the latest version automatically."},
]

# ---------------------------------------------------------------------------
# How-to-use steps per category
# ---------------------------------------------------------------------------
_CATEGORY_HOW_TO: dict[str, list[dict[str, str]]] = {
    "career": [
        {"step": "1", "title": "Describe Your Background", "desc": "Enter your job title, key skills, experience, and the role you are targeting."},
        {"step": "2", "title": "Generate Your Content", "desc": "Click Generate and let the AI produce professional, ATS-optimized career content instantly."},
        {"step": "3", "title": "Review and Customize", "desc": "Read through the output and make any personal adjustments to match your voice."},
        {"step": "4", "title": "Copy and Use", "desc": "Copy the result directly into your resume, cover letter, or LinkedIn profile."},
    ],
    "writing": [
        {"step": "1", "title": "Enter Your Text or Topic", "desc": "Paste the text you want to improve, or describe the content you need written."},
        {"step": "2", "title": "Generate", "desc": "Click Generate and get polished, professional writing output in seconds."},
        {"step": "3", "title": "Review the Output", "desc": "Read through the result and check it matches your intended tone and message."},
        {"step": "4", "title": "Copy and Publish", "desc": "Copy the final text and use it in your document, email, or content platform."},
    ],
    "seo": [
        {"step": "1", "title": "Enter Your Keyword or Topic", "desc": "Type your target keyword, page topic, or content brief into the input field."},
        {"step": "2", "title": "Generate SEO Content", "desc": "Click Generate and get keyword-optimized content structured for search engines."},
        {"step": "3", "title": "Review for Accuracy", "desc": "Check the output for factual accuracy and brand alignment before publishing."},
        {"step": "4", "title": "Publish and Track", "desc": "Add the content to your page and monitor rankings in Google Search Console."},
    ],
    "creator": [
        {"step": "1", "title": "Describe Your Content", "desc": "Enter your video topic, niche, target audience, and platform."},
        {"step": "2", "title": "Generate", "desc": "Click Generate and get platform-optimized content with hooks, structure, and CTAs."},
        {"step": "3", "title": "Customize Your Voice", "desc": "Adjust the output to match your personal style and brand tone."},
        {"step": "4", "title": "Publish and Engage", "desc": "Post your content and track engagement metrics to refine future output."},
    ],
    "business": [
        {"step": "1", "title": "Describe Your Business", "desc": "Enter your business idea, industry, target market, and any specific requirements."},
        {"step": "2", "title": "Generate", "desc": "Click Generate and get professional business content tailored to your concept."},
        {"step": "3", "title": "Review and Refine", "desc": "Evaluate the output and adjust any details to match your vision."},
        {"step": "4", "title": "Use in Your Business", "desc": "Apply the output to your pitch deck, website, branding, or business plan."},
    ],
    "education": [
        {"step": "1", "title": "Enter Your Topic or Content", "desc": "Type your subject, paste lecture notes, or describe the academic task."},
        {"step": "2", "title": "Generate Study Materials", "desc": "Click Generate and get structured notes, flashcards, outlines, or citations instantly."},
        {"step": "3", "title": "Review for Accuracy", "desc": "Check the output against your course materials to ensure accuracy."},
        {"step": "4", "title": "Study and Submit", "desc": "Use the materials for active recall, exam prep, or academic submission."},
    ],
    "developer": [
        {"step": "1", "title": "Describe Your Requirement", "desc": "Explain what the code should do, or paste the code you need help with."},
        {"step": "2", "title": "Generate", "desc": "Click Generate and get optimized code with explanation and notes."},
        {"step": "3", "title": "Review the Output", "desc": "Read the explanation and test the code in your development environment."},
        {"step": "4", "title": "Integrate", "desc": "Copy the code into your project and adapt it to your specific codebase."},
    ],
}

_DEFAULT_HOW_TO = [
    {"step": "1", "title": "Open the Tool", "desc": "Navigate to the tool page — no signup or installation required."},
    {"step": "2", "title": "Enter Your Input", "desc": "Type or paste your content into the input field."},
    {"step": "3", "title": "Process", "desc": "Click the action button and get instant results."},
    {"step": "4", "title": "Copy or Download", "desc": "Copy the output to your clipboard or download the result."},
]

# ---------------------------------------------------------------------------
# FAQ templates per category
# ---------------------------------------------------------------------------
_CATEGORY_FAQS: dict[str, list[dict[str, str]]] = {
    "career": [
        {"q": "Is this tool free to use?", "a": "Yes, completely free. No subscription, no credits, no hidden fees. LamGen is committed to keeping all career tools free forever."},
        {"q": "Is my resume data safe?", "a": "Absolutely. Your data is processed in your browser session and never stored on our servers. We do not log, save, or share any content you enter."},
        {"q": "Can I use this for ATS optimization?", "a": "Yes. The output is specifically structured to pass Applicant Tracking Systems used by major employers, with proper formatting and keyword density."},
        {"q": "Do I need to create an account?", "a": "No account is required. Open the page and start immediately. An optional account lets you save your history across devices."},
        {"q": "How accurate is the AI output?", "a": "The AI produces high-quality, professional output based on your input. We recommend reviewing and personalizing the result before submitting to employers."},
        {"q": "Can I use this for multiple job applications?", "a": "Yes. You can generate tailored content for each job application by adjusting your input to match different job descriptions."},
        {"q": "Does it work on mobile?", "a": "Yes. The tool is fully responsive and works on smartphones, tablets, and desktops."},
        {"q": "What format is the output in?", "a": "Output is provided as formatted text you can copy directly into Word, Google Docs, or any application."},
    ],
    "writing": [
        {"q": "Is this writing tool free?", "a": "Yes, 100% free with no usage limits. No subscription or account required."},
        {"q": "Will the output pass plagiarism checkers?", "a": "Yes. All output is uniquely generated by AI and is not copied from existing sources. It will pass standard plagiarism detection tools."},
        {"q": "Can I use this for academic writing?", "a": "Yes. The tool produces well-structured, grammatically correct writing suitable for academic use. Always review and personalize the output before submission."},
        {"q": "Is my text kept private?", "a": "Yes. All processing happens in your browser. Your text is never sent to or stored on our servers."},
        {"q": "How long can my input be?", "a": "The tool supports inputs up to several thousand characters. For very long documents, process them in sections."},
        {"q": "Can I adjust the tone of the output?", "a": "Yes. Specify the desired tone (formal, casual, persuasive, etc.) in your input and the AI will adapt accordingly."},
        {"q": "Does it work for non-English text?", "a": "The tool is optimized for English but can handle other languages. Quality may vary for non-English inputs."},
        {"q": "How many times can I use it?", "a": "Unlimited. There are no daily limits or usage caps."},
    ],
    "seo": [
        {"q": "Is this SEO tool free?", "a": "Yes, completely free. No subscription, no API key, no usage limits."},
        {"q": "Will this content rank on Google?", "a": "The tool generates SEO-optimized content following current best practices. Rankings depend on many factors including domain authority, competition, and backlinks."},
        {"q": "Is the output unique enough to avoid duplicate content penalties?", "a": "Yes. Every generation produces unique content. We recommend reviewing and adding your own insights before publishing."},
        {"q": "Can I use this for client SEO work?", "a": "Yes. The tool is suitable for agencies and freelancers producing SEO content for clients."},
        {"q": "Does it support long-tail keywords?", "a": "Yes. The tool naturally incorporates long-tail keyword variations that target specific search intent."},
        {"q": "How do I use the output for on-page SEO?", "a": "Copy the generated content into your CMS, add your target keyword to the title and first paragraph, and publish. Then submit to Google Search Console for indexing."},
        {"q": "Is my keyword data kept private?", "a": "Yes. Your inputs are never stored or shared. All processing is private."},
        {"q": "Can I generate content for multiple pages?", "a": "Yes. Use the tool as many times as needed — there are no limits."},
    ],
    "creator": [
        {"q": "Is this content creation tool free?", "a": "Yes, 100% free with no usage limits or account required."},
        {"q": "Will the content perform well on social media?", "a": "The tool uses proven content frameworks from top-performing creators. Performance depends on your audience, posting time, and consistency."},
        {"q": "Can I use this for client social media management?", "a": "Yes. The tool is suitable for agencies and freelancers managing social media for clients."},
        {"q": "Does it support all social platforms?", "a": "Yes. Content can be generated and adapted for YouTube, Instagram, TikTok, LinkedIn, Twitter/X, and Facebook."},
        {"q": "Is the output copyright-free?", "a": "Yes. All generated content is original and you own the rights to use it however you choose."},
        {"q": "Can I customize the output?", "a": "Yes. The output is a starting point — edit it to match your personal voice and brand style."},
        {"q": "How many content pieces can I generate?", "a": "Unlimited. Generate as many scripts, captions, and hooks as you need."},
        {"q": "Is my content idea kept private?", "a": "Yes. Your inputs are never stored or shared with third parties."},
    ],
    "business": [
        {"q": "Is this business tool free?", "a": "Yes, completely free. No subscription, no agency fees, no hidden costs."},
        {"q": "Can I use the output for investor pitches?", "a": "Yes. The output is structured with professional language suitable for investor presentations. Always review and customize before presenting."},
        {"q": "Is my business idea kept confidential?", "a": "Yes. Your inputs are never stored, logged, or shared. Complete confidentiality is guaranteed."},
        {"q": "How unique are the generated names or ideas?", "a": "Every generation produces unique output. We recommend checking domain availability and trademark status for any names you plan to use."},
        {"q": "Can I use this for multiple business ideas?", "a": "Yes. Use the tool as many times as needed — there are no limits."},
        {"q": "Does it work for any industry?", "a": "Yes. The AI adapts to any industry or business type based on your input."},
        {"q": "Can I edit the output?", "a": "Yes. The output is a professional starting point — customize it to match your specific vision and requirements."},
        {"q": "Does it work on mobile?", "a": "Yes. Fully responsive and works on any device."},
    ],
    "education": [
        {"q": "Is this study tool free?", "a": "Yes, 100% free for all students. No subscription, no account required."},
        {"q": "Is the academic content accurate?", "a": "The AI produces high-quality academic content based on your input. Always verify facts against your course materials and textbooks."},
        {"q": "Can I submit AI-generated content as my own work?", "a": "Always follow your institution's academic integrity policy. Use the output as a study aid, outline, or starting point — not as a direct submission."},
        {"q": "Does it support all academic subjects?", "a": "Yes. The tool works for any subject from STEM to humanities, adapting to your specific topic and requirements."},
        {"q": "Is my academic content kept private?", "a": "Yes. Your inputs are never stored or shared. All processing is private."},
        {"q": "Can I use this for exam preparation?", "a": "Yes. Generate flashcards, quizzes, and study notes to prepare for any exam."},
        {"q": "Does it follow citation style guidelines?", "a": "Yes. Citation tools follow APA, MLA, and Chicago style guidelines. Always double-check formatting against the official style guide."},
        {"q": "How many study materials can I generate?", "a": "Unlimited. Generate as many notes, flashcards, and outlines as you need."},
    ],
    "developer": [
        {"q": "Is this developer tool free?", "a": "Yes, completely free. No subscription, no API key, no usage limits."},
        {"q": "Is the generated code production-ready?", "a": "The output follows best practices and is suitable as a starting point. Always review, test, and adapt code before deploying to production."},
        {"q": "What programming languages does it support?", "a": "The tool supports SQL, Python, JavaScript, TypeScript, HTML, CSS, regex, and more. Specify your language in the input for best results."},
        {"q": "Is my code kept private?", "a": "Yes. Your code is never stored, logged, or shared. All processing is private."},
        {"q": "Can I use this for commercial projects?", "a": "Yes. All generated code is yours to use in any project, commercial or personal."},
        {"q": "How accurate is the SQL/regex output?", "a": "The AI produces accurate output for standard use cases. Always test queries and patterns against your actual data before using in production."},
        {"q": "Can it debug complex code?", "a": "Yes. Paste your code and describe the issue — the AI will identify the bug, provide a fix, and explain the root cause."},
        {"q": "Does it work without an internet connection?", "a": "An internet connection is required to process AI requests. Once the page loads, browser-based tools work offline."},
    ],
}

_DEFAULT_FAQS = [
    {"q": "Is this tool free to use?", "a": "Yes, completely free. No subscription, no credits, no hidden fees."},
    {"q": "Do I need to create an account?", "a": "No account is required. Open the page and start immediately."},
    {"q": "Is my data safe?", "a": "Yes. All processing happens in your browser. Your data is never stored on our servers."},
    {"q": "Does it work on mobile?", "a": "Yes. Fully responsive and works on any device."},
    {"q": "Are there any usage limits?", "a": "No. Use the tool as many times as you need with no daily limits or caps."},
    {"q": "How accurate is the output?", "a": "The tool produces high-quality output. We recommend reviewing results before use."},
    {"q": "Can I use the output commercially?", "a": "Yes. All output is yours to use in any project, commercial or personal."},
]


# ---------------------------------------------------------------------------
# LSI / semantic keyword banks per category
# ---------------------------------------------------------------------------
_CATEGORY_LSI: dict[str, list[str]] = {
    "career": [
        "job application", "resume writing", "career development", "job search",
        "professional profile", "interview preparation", "LinkedIn optimization",
        "ATS keywords", "career advancement", "employment",
    ],
    "writing": [
        "content writing", "text editing", "proofreading", "copywriting",
        "creative writing", "academic writing", "professional writing",
        "content creation", "writing assistant", "text improvement",
    ],
    "seo": [
        "search engine optimization", "organic traffic", "keyword research",
        "content marketing", "on-page SEO", "meta tags", "SERP ranking",
        "Google ranking", "search intent", "topical authority",
    ],
    "creator": [
        "content creation", "social media marketing", "video content",
        "audience growth", "engagement rate", "viral content", "content strategy",
        "influencer marketing", "brand building", "content calendar",
    ],
    "business": [
        "entrepreneurship", "startup", "business strategy", "brand identity",
        "market research", "business planning", "go-to-market", "branding",
        "product launch", "business development",
    ],
    "education": [
        "studying", "academic performance", "exam preparation", "learning",
        "student productivity", "academic writing", "research skills",
        "note-taking", "spaced repetition", "active recall",
    ],
    "developer": [
        "software development", "programming", "coding", "debugging",
        "database queries", "web development", "code optimization",
        "developer productivity", "technical tools", "engineering",
    ],
}

_DEFAULT_LSI = [
    "free online tool", "browser-based", "no signup", "instant results",
    "productivity tool", "web utility", "free tool", "online tool",
]


# ---------------------------------------------------------------------------
# Main SEO Content Engine
# ---------------------------------------------------------------------------
class SEOContentEngine:
    """
    Generates a complete 10-block SEO content package for any tool.

    All generation is deterministic and instant — no AI API calls.
    Designed to scale to 300+ tools with unique, non-duplicate output.
    """

    def generate(
        self,
        tool_name: str,
        category: str,
        short_desc: str,
        slug: str,
        tags: str = "",
        is_ai_tool: bool = True,
    ) -> dict[str, Any]:
        """
        Generate the full SEO content package for a tool.

        Returns a dict with keys:
            tool_name, meta, hero, intro, use_cases, features,
            how_to_use, faqs, keywords, internal_links, schema
        """
        profile = _CATEGORY_PROFILES.get(category, _DEFAULT_PROFILE)
        overrides = _TOOL_OVERRIDES.get(slug, {})
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]
        name_lower = tool_name.lower()

        meta = self._build_meta(tool_name, category, short_desc, slug, profile, overrides)
        hero = self._build_hero(tool_name, category, short_desc, profile, overrides)
        intro = self._build_intro(tool_name, category, short_desc, profile, overrides, is_ai_tool)
        use_cases = self._build_use_cases(tool_name, category, short_desc, tag_list, name_lower, profile)
        features = self._build_features(category, tool_name, is_ai_tool)
        how_to_use = self._build_how_to(category, tool_name, is_ai_tool)
        faqs = self._build_faqs(tool_name, category, short_desc, slug)
        keywords = self._build_keywords(tool_name, category, slug, profile, overrides)
        internal_links = self._build_internal_links(slug, category)
        schema = self._build_schema(tool_name, short_desc, slug, faqs)

        return {
            "tool_name": tool_name,
            "meta": meta,
            "hero": hero,
            "intro": intro,
            "use_cases": use_cases,
            "features": features,
            "how_to_use": how_to_use,
            "faqs": faqs,
            "keywords": keywords,
            "internal_links": internal_links,
            "schema": schema,
        }

    # ── Block 1: Meta ────────────────────────────────────────────────────────

    def _build_meta(self, tool_name, category, short_desc, slug, profile, overrides):
        primary_kw = overrides.get("primary_keyword") or f"{tool_name.lower()} free online"
        cat_kw = profile["category_kw"]

        # Title: keyword-rich, ≤60 chars
        title_candidates = [
            f"{tool_name} — Free Online {cat_kw.title().replace('Free ', '')} | LamGen",
            f"{tool_name} — Free {cat_kw.title().replace('Free ', '')} | LamGen",
            f"{tool_name} | Free Online Tool — LamGen",
            f"{tool_name} | LamGen",
        ]
        meta_title = next((t for t in title_candidates if len(t) <= 60), title_candidates[-1])

        # Description: 150-160 chars, compelling
        desc_clean = short_desc.rstrip(".")
        desc_candidates = [
            f"{desc_clean}. Free, instant, no signup. {profile['trust_signal']}.",
            f"Free {tool_name.lower()} online. {desc_clean}. No account needed — instant results.",
            f"{tool_name}: {desc_clean}. Free online tool. No signup, no install, instant results.",
        ]
        meta_desc = next((d for d in desc_candidates if 140 <= len(d) <= 160), None)
        if not meta_desc:
            meta_desc = desc_candidates[0][:160]

        secondary_kws = overrides.get("secondary_keywords") or self._generate_secondary_keywords(
            tool_name, category, primary_kw
        )

        return {
            "meta_title": meta_title,
            "meta_description": meta_desc,
            "primary_keyword": primary_kw,
            "secondary_keywords": secondary_kws[:8],
            "slug_suggestion": slug,
        }

    def _generate_secondary_keywords(self, tool_name, category, primary_kw):
        name_lower = tool_name.lower()
        base = [
            f"{name_lower} free",
            f"{name_lower} online",
            f"free {name_lower}",
            f"{name_lower} no signup",
            f"best {name_lower}",
            f"{name_lower} tool",
            f"online {name_lower} free",
        ]
        # Add category-specific variations
        cat_variations = {
            "career": [f"{name_lower} for job seekers", f"AI {name_lower}"],
            "writing": [f"AI {name_lower}", f"{name_lower} for students"],
            "seo": [f"SEO {name_lower}", f"{name_lower} for bloggers"],
            "creator": [f"{name_lower} for YouTube", f"{name_lower} for Instagram"],
            "business": [f"{name_lower} for startups", f"free {name_lower} generator"],
            "education": [f"{name_lower} for students", f"free {name_lower} for school"],
            "developer": [f"{name_lower} for developers", f"free {name_lower} tool online"],
        }
        base.extend(cat_variations.get(category, []))
        return base[:8]

    # ── Block 2: Hero ────────────────────────────────────────────────────────

    def _build_hero(self, tool_name, category, short_desc, profile, overrides):
        headline = overrides.get("hero_headline") or (
            f"{profile['action_verb']} {tool_name.replace('AI ', '').replace('Generator', 'Content').strip()} "
            f"Instantly — Free"
        )
        subheading = overrides.get("hero_subheading") or (
            f"{short_desc} — free, instant, no signup required."
        )
        return {
            "headline": headline,
            "subheading": subheading,
            "cta_text": profile["cta"],
            "trust_signal": profile["trust_signal"],
        }

    # ── Block 3: Intro ───────────────────────────────────────────────────────

    def _build_intro(self, tool_name, category, short_desc, profile, overrides, is_ai_tool):
        hook = overrides.get("intro_hook") or (
            f"For {profile['audience']}, {profile['pain_point']} is one of the biggest challenges."
        )
        ai_clause = (
            "Powered by advanced AI, it understands context and produces output that matches "
            "professional standards — without requiring any technical expertise."
            if is_ai_tool else
            "Built for speed and accuracy, it runs entirely in your browser with no installation required."
        )
        desc_clean = short_desc.rstrip(".")

        intro = (
            f"{hook} {tool_name} is a {profile['category_kw']} designed to help you "
            f"{profile['benefit']}.

"
            f"{desc_clean}. {ai_clause}

"
            f"Whether you are a {profile['audience'].split(',')[0].strip()} or just getting started, "
            f"{tool_name} removes the friction from the process. There is no software to install, "
            f"no account to create, and no cost involved. Open the page, enter your input, and get "
            f"professional-quality results in seconds.

"
            f"{profile['trust_signal']}. Every result is unique, private, and ready to use immediately. "
            f"Your data never leaves your browser — we do not store, log, or share anything you enter. "
            f"This makes {tool_name} one of the most private and accessible {profile['category_kw']}s available online."
        )
        return intro

    # ── Block 4: Use Cases ───────────────────────────────────────────────────

    def _build_use_cases(self, tool_name, category, short_desc, tag_list, name_lower, profile):
        # Category-specific use cases
        use_case_banks: dict[str, list[str]] = {
            "career": [
                f"Generate ATS-friendly resumes for job applications at top companies",
                f"Tailor your resume to specific job descriptions to increase interview rates",
                f"Create professional cover letters for cold applications and referrals",
                f"Optimize your LinkedIn profile to appear in recruiter searches",
                f"Prepare salary negotiation scripts before compensation discussions",
                f"Build a career portfolio with consistent, professional language",
                f"Refresh outdated resumes with modern formatting and keywords",
                f"Apply to multiple roles with customized content for each position",
            ],
            "writing": [
                f"Rewrite AI-generated content to sound natural and pass AI detectors",
                f"Improve academic essays before submission to avoid plagiarism flags",
                f"Draft professional emails for client communication and outreach",
                f"Create blog post drafts that can be refined and published quickly",
                f"Simplify complex technical content for general audiences",
                f"Paraphrase source material for research papers and reports",
                f"Generate social media captions from existing long-form content",
                f"Proofread and correct grammar in documents before sharing",
            ],
            "seo": [
                f"Generate meta descriptions for every page on a website",
                f"Create keyword clusters for topical authority content strategies",
                f"Write SEO-optimized blog posts targeting long-tail keywords",
                f"Produce FAQ sections that target voice search and featured snippets",
                f"Generate title tags for product pages and landing pages",
                f"Build content briefs for freelance writers and content teams",
                f"Analyze keyword intent to prioritize content production",
                f"Create SEO content for client websites at scale",
            ],
            "creator": [
                f"Write YouTube video scripts with hooks, structure, and CTAs",
                f"Generate Instagram captions with relevant hashtags for every post",
                f"Create TikTok and Reels script outlines for short-form video",
                f"Plan a month of social media content with a content calendar",
                f"Generate viral hook ideas for any topic or niche",
                f"Rewrite content for different platforms with the right tone",
                f"Create carousel slide copy for LinkedIn and Instagram",
                f"Draft influencer collaboration pitches for brand partnerships",
            ],
            "business": [
                f"Generate startup name ideas with rationale and brand fit analysis",
                f"Create a business plan outline for investor presentations",
                f"Generate logo design prompts for AI image tools like Midjourney",
                f"Produce image prompts for marketing materials and social content",
                f"Brainstorm product names and taglines for new launches",
                f"Create pitch deck copy for fundraising rounds",
                f"Generate brand voice guidelines from a business description",
                f"Produce competitive positioning statements for sales teams",
            ],
            "education": [
                f"Generate study notes from lecture content or textbook chapters",
                f"Create flashcard sets for spaced repetition exam preparation",
                f"Build essay outlines for argumentative and analytical papers",
                f"Generate multiple-choice quizzes for self-testing and revision",
                f"Produce properly formatted citations in APA, MLA, and Chicago",
                f"Create a personalized study plan based on exam dates and subjects",
                f"Generate thesis statements for research papers and essays",
                f"Predict final grades based on current performance and remaining assessments",
            ],
            "developer": [
                f"Generate SQL queries from plain English descriptions",
                f"Debug code by pasting the problematic function and describing the issue",
                f"Create regex patterns for form validation and data parsing",
                f"Minify HTML for production deployments to improve page speed",
                f"Generate boilerplate code for common programming patterns",
                f"Explain complex code to non-technical stakeholders",
                f"Optimize slow database queries with AI-suggested improvements",
                f"Generate test cases and edge cases for unit testing",
            ],
        }

        cases = use_case_banks.get(category, [
            f"Anyone who needs a fast, reliable {tool_name.lower()} without installing software",
            f"Professionals who need browser-based productivity tools",
            f"Students and researchers working on academic projects",
            f"Freelancers and remote workers who need instant online utilities",
            f"Teams that need to process content quickly without enterprise software",
        ])

        return cases[:8]

    # ── Block 5: Features ────────────────────────────────────────────────────

    def _build_features(self, category, tool_name, is_ai_tool):
        features = list(_CATEGORY_FEATURES.get(category, _DEFAULT_FEATURES))
        if is_ai_tool:
            features.insert(0, {
                "title": "AI-Powered Generation",
                "desc": f"Uses advanced AI to generate high-quality, contextually relevant output tailored to your specific input.",
            })
        return features[:10]

    # ── Block 6: How To Use ──────────────────────────────────────────────────

    def _build_how_to(self, category, tool_name, is_ai_tool):
        steps = list(_CATEGORY_HOW_TO.get(category, _DEFAULT_HOW_TO))
        return steps

    # ── Block 7: FAQs ────────────────────────────────────────────────────────

    def _build_faqs(self, tool_name, category, short_desc, slug):
        base_faqs = list(_CATEGORY_FAQS.get(category, _DEFAULT_FAQS))
        # Add tool-specific FAQs based on name patterns
        extra = []
        name_lower = tool_name.lower()
        if "generator" in name_lower:
            extra.append({
                "q": f"How many results does {tool_name} generate at once?",
                "a": f"{tool_name} generates multiple options per request so you can choose the best fit. You can regenerate as many times as needed.",
            })
        if "checker" in name_lower or "analyzer" in name_lower:
            extra.append({
                "q": f"How does {tool_name} score or analyze my content?",
                "a": f"{tool_name} uses AI to evaluate your content against established criteria and provides a score, issues list, and actionable recommendations.",
            })
        if "ai" in name_lower or "ai-" in slug:
            extra.append({
                "q": f"Which AI model powers {tool_name}?",
                "a": f"{tool_name} is powered by state-of-the-art large language models optimized for this specific task. The model is automatically selected for best quality and speed.",
            })
        if "resume" in name_lower or "cv" in name_lower:
            extra.append({
                "q": f"Can I download the output as a PDF or Word file?",
                "a": f"You can copy the output and paste it into any word processor like Google Docs or Microsoft Word, then export as PDF. Direct PDF export is on our roadmap.",
            })
        return (base_faqs + extra)[:10]

    # ── Block 8: Keywords ────────────────────────────────────────────────────

    def _build_keywords(self, tool_name, category, slug, profile, overrides):
        primary = overrides.get("primary_keyword") or f"{tool_name.lower()} free online"
        secondary = overrides.get("secondary_keywords") or self._generate_secondary_keywords(
            tool_name, category, primary
        )
        lsi = _CATEGORY_LSI.get(category, _DEFAULT_LSI)
        semantic = [
            f"free {tool_name.lower()}",
            f"{tool_name.lower()} online",
            f"best {tool_name.lower()}",
            f"{tool_name.lower()} tool",
            f"AI {tool_name.lower()}",
            f"{tool_name.lower()} no signup",
        ]
        return {
            "primary": primary,
            "secondary": secondary[:8],
            "semantic": semantic[:6],
            "lsi": lsi[:10],
        }

    # ── Block 9: Internal Links ──────────────────────────────────────────────

    def _build_internal_links(self, slug, category):
        category_tools = _INTERNAL_LINK_MAP.get(category, [])
        # Exclude self
        related = [s for s in category_tools if s != slug][:6]
        return {
            "same_category": related,
            "cross_category": _INTERNAL_LINK_MAP.get(
                _CATEGORY_PROFILES.get(category, _DEFAULT_PROFILE)["related_category"], []
            )[:4],
            "category_page": f"/tools/{category}/",
        }

    # ── Block 10: Schema ─────────────────────────────────────────────────────

    def _build_schema(self, tool_name, short_desc, slug, faqs):
        software_schema = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": tool_name,
            "description": short_desc,
            "applicationCategory": "UtilitiesApplication",
            "operatingSystem": "Web Browser",
            "browserRequirements": "Requires JavaScript",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
            },
            "provider": {
                "@type": "Organization",
                "name": "LamGen",
                "url": "https://lamgen.com",
            },
            "featureList": [
                "Free to use",
                "No signup required",
                "Browser-based processing",
                "No data uploaded to servers",
                "Mobile responsive",
                "Unlimited usage",
            ],
        }

        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item["a"],
                    },
                }
                for item in faqs[:8]
            ],
        }

        return {
            "software_application": software_schema,
            "faq_page": faq_schema,
        }


# ---------------------------------------------------------------------------
# Convenience function — generate package for a Tool model instance
# ---------------------------------------------------------------------------
def generate_seo_package(tool) -> dict[str, Any]:
    """
    Generate a full SEO content package from a Tool model instance.

    Args:
        tool: apps.tools.models.Tool instance

    Returns:
        Complete SEO package dict
    """
    engine = SEOContentEngine()
    category_slug = tool.category.slug if hasattr(tool.category, "slug") else str(tool.category)
    return engine.generate(
        tool_name=tool.name,
        category=category_slug,
        short_desc=tool.short_desc or tool.description[:200],
        slug=tool.slug,
        tags=tool.tags or "",
        is_ai_tool=tool.is_ai_powered,
    )


# ---------------------------------------------------------------------------
# Batch generator — yields (tool, package) for all active tools
# ---------------------------------------------------------------------------
def batch_generate(queryset=None, category_filter: str | None = None):
    """
    Generator that yields (tool, seo_package) for all active tools.

    Args:
        queryset: Optional Tool queryset. Defaults to all active tools.
        category_filter: Optional category slug to filter by.

    Yields:
        (tool, package) tuples
    """
    from apps.tools.models import Tool

    qs = queryset or Tool.objects.filter(is_active=True).select_related("category")
    if category_filter:
        qs = qs.filter(category__slug=category_filter)

    engine = SEOContentEngine()
    for tool in qs.iterator():
        try:
            category_slug = tool.category.slug if hasattr(tool.category, "slug") else str(tool.category)
            package = engine.generate(
                tool_name=tool.name,
                category=category_slug,
                short_desc=tool.short_desc or tool.description[:200],
                slug=tool.slug,
                tags=tool.tags or "",
                is_ai_tool=tool.is_ai_powered,
            )
            yield tool, package
        except Exception as exc:
            yield tool, {"error": str(exc)}


# ---------------------------------------------------------------------------
# LSI / semantic keyword banks per category
# ---------------------------------------------------------------------------
_LSI_KEYWORDS: dict[str, list[str]] = {
    "career": ["job search", "resume tips", "career advice", "job application", "interview preparation",
               "professional development", "LinkedIn optimization", "ATS resume", "job offer", "career growth"],
    "writing": ["content writing", "copywriting", "proofreading", "editing tool", "writing assistant",
                "text editor", "writing improvement", "content creation", "writing software", "grammar tool"],
    "seo": ["search engine optimization", "keyword research", "on-page SEO", "content marketing",
            "organic traffic", "SERP ranking", "meta tags", "backlink strategy", "SEO audit", "Google ranking"],
    "creator": ["content strategy", "social media marketing", "video marketing", "audience growth",
                "engagement rate", "content calendar", "viral content", "influencer marketing", "brand building"],
    "business": ["entrepreneurship", "startup funding", "business strategy", "brand identity",
                 "market research", "go-to-market", "business model", "pitch deck", "product launch"],
    "education": ["study tips", "academic writing", "exam preparation", "learning strategies",
                  "student productivity", "note-taking", "spaced repetition", "academic research", "essay writing"],
    "developer": ["software development", "code review", "debugging", "database optimization",
                  "web development", "API development", "code quality", "programming tools", "DevOps"],
}

_DEFAULT_LSI = ["online tool", "free tool", "browser tool", "no signup", "instant results",
                "productivity tool", "web app", "free utility", "online utility"]


# ---------------------------------------------------------------------------
# Main SEO Content Engine
# ---------------------------------------------------------------------------

class SEOContentEngine:
    """
    Generates a complete 10-block SEO content package for any tool.

    All generation is deterministic and instant — no external API calls.
    Designed to scale across 300+ tools with unique, non-duplicate output.
    """

    def generate(
        self,
        tool_name: str,
        category: str,
        short_desc: str = "",
        slug: str = "",
        tags: str = "",
        is_ai_tool: bool = True,
    ) -> dict[str, Any]:
        """
        Generate the full SEO content package for a tool.

        Returns a dict with keys:
            tool_name, meta, hero, intro, use_cases, features,
            how_to_use, faqs, keywords, internal_links, schema
        """
        cat_key = category.lower().replace(" ", "-")
        profile = _CATEGORY_PROFILES.get(cat_key, _DEFAULT_PROFILE)
        override = _TOOL_OVERRIDES.get(slug, {})
        tag_list = [t.strip().lower() for t in tags.split(",") if t.strip()]

        meta = self._build_meta(tool_name, category, short_desc, slug, profile, override, tag_list)
        hero = self._build_hero(tool_name, short_desc, profile, override)
        intro = self._build_intro(tool_name, short_desc, category, profile, override, is_ai_tool)
        use_cases = self._build_use_cases(tool_name, category, short_desc, tag_list, profile)
        features = self._build_features(tool_name, category, profile, is_ai_tool)
        how_to_use = self._build_how_to_use(tool_name, category, profile)
        faqs = self._build_faqs(tool_name, category, short_desc, profile)
        keywords = self._build_keywords(tool_name, category, slug, profile, override, tag_list)
        internal_links = self._build_internal_links(slug, category)
        schema = self._build_schema(tool_name, short_desc, slug, meta, faqs)

        return {
            "tool_name": tool_name,
            "meta": meta,
            "hero": hero,
            "intro": intro,
            "use_cases": use_cases,
            "features": features,
            "how_to_use": how_to_use,
            "faqs": faqs,
            "keywords": keywords,
            "internal_links": internal_links,
            "schema": schema,
        }

    # ------------------------------------------------------------------
    # Block 1: Meta
    # ------------------------------------------------------------------
    def _build_meta(self, tool_name, category, short_desc, slug, profile, override, tag_list):
        cat_kw = profile["category_kw"]
        primary_kw = override.get("primary_keyword") or f"{tool_name.lower()} free online"

        # Title: keyword-rich, ≤60 chars
        title_candidate = f"{tool_name} — Free Online {category.title()} Tool | LamGen"
        if len(title_candidate) > 60:
            title_candidate = f"{tool_name} — Free {cat_kw.title()} | LamGen"
        if len(title_candidate) > 60:
            title_candidate = f"{tool_name} | Free Online Tool — LamGen"
        meta_title = title_candidate[:60]

        # Description: 150-160 chars
        desc_base = short_desc.rstrip(".") if short_desc else f"Use {tool_name} online"
        meta_desc_candidate = (
            f"{desc_base}. Free online tool — no signup, instant results, 100% private. "
            f"Works in your browser."
        )
        if len(meta_desc_candidate) > 160:
            meta_desc_candidate = f"{tool_name}: {desc_base}. Free, instant, no account needed."
        meta_description = meta_desc_candidate[:160]

        secondary_kws = override.get("secondary_keywords") or self._derive_secondary_keywords(
            tool_name, category, primary_kw, tag_list
        )

        return {
            "meta_title": meta_title,
            "meta_description": meta_description,
            "primary_keyword": primary_kw,
            "secondary_keywords": secondary_kws[:10],
            "slug_suggestion": slug or re.sub(r"[^a-z0-9]+", "-", tool_name.lower()).strip("-"),
        }

    def _derive_secondary_keywords(self, tool_name, category, primary_kw, tag_list):
        name_lower = tool_name.lower()
        kws = [
            f"{name_lower} free",
            f"{name_lower} online",
            f"free {name_lower}",
            f"{name_lower} no signup",
            f"best {name_lower} online",
            f"{name_lower} tool",
            f"AI {name_lower}" if "ai" not in name_lower else f"free AI {name_lower}",
            f"{category} {name_lower}",
            f"{name_lower} generator" if "generator" not in name_lower else f"free {name_lower}",
            f"online {name_lower}",
        ]
        return list(dict.fromkeys(kws))[:10]

    # ------------------------------------------------------------------
    # Block 2: Hero
    # ------------------------------------------------------------------
    def _build_hero(self, tool_name, short_desc, profile, override):
        headline = override.get("hero_headline") or f"{tool_name} — Free, Instant, No Signup"
        subheading = override.get("hero_subheading") or (
            f"{short_desc}. {profile['trust_signal']}."
            if short_desc else
            f"{profile['benefit'].capitalize()}. {profile['trust_signal']}."
        )
        return {
            "headline": headline,
            "subheading": subheading[:200],
            "cta_text": profile["cta"],
            "trust_signal": profile["trust_signal"],
        }

    # ------------------------------------------------------------------
    # Block 3: Intro (200-300 words)
    # ------------------------------------------------------------------
    def _build_intro(self, tool_name, short_desc, category, profile, override, is_ai_tool):
        hook = override.get("intro_hook") or f"When it comes to {profile['pain_point']}, every second counts."
        ai_note = (
            "Powered by advanced AI, it understands context and intent — not just keywords."
            if is_ai_tool else
            "Built for speed and accuracy, it runs entirely in your browser with zero latency."
        )
        desc = short_desc.rstrip(".") if short_desc else f"perform {category}-related tasks"

        intro = (
            f"{hook} "
            f"{tool_name} is a {profile['category_kw']} designed for {profile['audience']}. "
            f"It lets you {desc.lower()}. "
            f"{ai_note} "
            f"Unlike desktop software or expensive SaaS platforms, {tool_name} is completely free — "
            f"no account, no installation, no subscription. "
            f"Open the page, enter your input, and get results in seconds. "
            f"Whether you are a {profile['audience'].split(',')[0].strip()} or just someone who needs "
            f"a reliable tool to {profile['benefit']}, this is built for you. "
            f"All processing happens locally in your browser, so your data never leaves your device. "
            f"There are no usage limits, no paywalls, and no hidden costs. "
            f"{profile['trust_signal']}. "
            f"It works on any device — desktop, tablet, or mobile — and requires nothing more than "
            f"a modern web browser. "
            f"Start using {tool_name} today and see why it is the go-to choice for "
            f"{profile['audience']} who need fast, reliable results without the friction."
        )
        return intro

    # ------------------------------------------------------------------
    # Block 4: Use Cases
    # ------------------------------------------------------------------
    def _build_use_cases(self, tool_name, category, short_desc, tag_list, profile):
        cat_key = category.lower().replace(" ", "-")
        name_lower = tool_name.lower()

        # Category-specific use cases
        use_case_map: dict[str, list[str]] = {
            "career": [
                f"Craft an ATS-optimized resume for a {name_lower.replace('resume', '').replace('builder','').strip() or 'software engineer'} role",
                "Tailor your application materials for each job description to increase interview rates",
                "Prepare professional career documents in minutes before a job application deadline",
                "Update your LinkedIn profile to attract recruiter outreach and inbound opportunities",
                "Generate a salary negotiation script before a compensation discussion",
                "Create a cover letter that highlights your unique value proposition to hiring managers",
                "Build a career portfolio narrative that stands out in a competitive applicant pool",
            ],
            "writing": [
                f"Rewrite AI-generated content to sound natural and pass AI detection tools",
                "Improve the readability of blog posts before publishing to increase dwell time",
                "Paraphrase academic sources to avoid plagiarism in essays and research papers",
                "Write professional emails faster without spending time on phrasing and tone",
                "Generate engaging social media captions from a topic or image description",
                "Simplify complex technical writing for a non-technical audience",
                "Proofread and correct grammar in client-facing documents and reports",
            ],
            "seo": [
                "Generate SEO-optimized blog posts targeting high-volume long-tail keywords",
                "Create meta descriptions for every page on a website in bulk",
                "Build keyword clusters to establish topical authority in a niche",
                "Write FAQ sections that target featured snippet positions on Google",
                "Produce SEO article drafts for client websites at scale",
                "Optimize existing content by identifying keyword gaps and adding semantic terms",
                "Generate title tags that improve click-through rates from search results",
            ],
            "creator": [
                "Write a YouTube video script with a strong hook to maximize watch time",
                "Generate 10 YouTube title variations to A/B test for higher CTR",
                "Create a 4-week social media content calendar for a brand or client",
                "Write Instagram captions with hashtags optimized for reach and engagement",
                "Generate viral hook ideas for TikTok and Reels to stop the scroll",
                "Produce carousel slide copy for LinkedIn thought leadership posts",
                "Write an influencer collaboration pitch to send to brand partners",
            ],
            "business": [
                "Generate startup name ideas with rationale before registering a domain",
                "Create a business plan outline for a pitch deck or investor meeting",
                "Generate logo design prompts to brief a designer or use with AI image tools",
                "Brainstorm product names for a new launch or rebrand",
                "Write a one-page business summary for a grant or accelerator application",
                "Generate image prompts for marketing materials and social media visuals",
                "Create a brand positioning statement for a new product or service",
            ],
            "education": [
                "Generate study flashcards from lecture notes before an exam",
                "Create a structured essay outline from a topic in minutes",
                "Summarize dense academic papers into clear, concise bullet points",
                "Generate a personalized study plan based on exam dates and available hours",
                "Produce properly formatted citations in APA, MLA, and Chicago style",
                "Create multiple-choice quiz questions to test knowledge retention",
                "Generate a strong thesis statement for an argumentative essay",
            ],
            "developer": [
                "Generate a complex SQL query from a plain-English description",
                "Debug a failing function by pasting the code and describing the error",
                "Generate a regex pattern for email validation or data extraction",
                "Minify HTML before deploying a web page to improve load speed",
                "Generate boilerplate code for common patterns to speed up development",
                "Explain what an unfamiliar piece of code does before modifying it",
                "Generate SQL for database migrations and schema changes",
            ],
        }

        cases = use_case_map.get(cat_key, [
            f"Use {tool_name} to complete {category} tasks faster and more accurately",
            f"Professionals using {tool_name} to save time on repetitive {category} work",
            f"Students and researchers using {tool_name} for academic projects",
            f"Freelancers using {tool_name} to deliver client work more efficiently",
            f"Teams using {tool_name} to standardize output quality across projects",
        ])

        # Always append two universal cases
        cases.append(f"Anyone who needs a fast, reliable {name_lower} without installing software")
        cases.append(f"Remote workers and freelancers who need browser-based {category} tools")

        return cases[:8]

    # ------------------------------------------------------------------
    # Block 5: Features
    # ------------------------------------------------------------------
    def _build_features(self, tool_name, category, profile, is_ai_tool):
        cat_key = category.lower().replace(" ", "-")
        base_features = list(_CATEGORY_FEATURES.get(cat_key, _DEFAULT_FEATURES))

        if is_ai_tool:
            base_features.insert(0, {
                "title": "AI-Powered Generation",
                "desc": f"Uses advanced language models to generate high-quality {category} content tailored to your specific input.",
            })

        return base_features[:12]

    # ------------------------------------------------------------------
    # Block 6: How to Use
    # ------------------------------------------------------------------
    def _build_how_to_use(self, tool_name, category, profile):
        cat_key = category.lower().replace(" ", "-")
        steps = list(_CATEGORY_HOW_TO.get(cat_key, _DEFAULT_HOW_TO))
        return steps

    # ------------------------------------------------------------------
    # Block 7: FAQs
    # ------------------------------------------------------------------
    def _build_faqs(self, tool_name, category, short_desc, profile):
        cat_key = category.lower().replace(" ", "-")
        base_faqs = list(_CATEGORY_FAQS.get(cat_key, _DEFAULT_FAQS))

        # Inject tool-specific FAQ at position 0
        tool_faq = {
            "q": f"What is {tool_name} and what does it do?",
            "a": (
                f"{tool_name} is a free online {profile['category_kw']} for {profile['audience']}. "
                f"{short_desc.rstrip('.') + '.' if short_desc else ''} "
                f"It runs entirely in your browser — no signup, no installation, instant results."
            ).strip(),
        }
        base_faqs.insert(0, tool_faq)
        return base_faqs[:10]

    # ------------------------------------------------------------------
    # Block 8: Keywords
    # ------------------------------------------------------------------
    def _build_keywords(self, tool_name, category, slug, profile, override, tag_list):
        cat_key = category.lower().replace(" ", "-")
        primary = override.get("primary_keyword") or f"{tool_name.lower()} free online"
        secondary = override.get("secondary_keywords") or self._derive_secondary_keywords(
            tool_name, category, primary, tag_list
        )
        lsi = _LSI_KEYWORDS.get(cat_key, _DEFAULT_LSI)

        semantic = [
            f"free {tool_name.lower()}",
            f"{tool_name.lower()} online",
            f"best {tool_name.lower()}",
            f"{tool_name.lower()} tool",
            f"{profile['category_kw']}",
            f"AI {category} tool",
            f"free {category} tool online",
        ]

        return {
            "primary": primary,
            "secondary": secondary[:10],
            "semantic": list(dict.fromkeys(semantic))[:8],
            "lsi": lsi[:10],
        }

    # ------------------------------------------------------------------
    # Block 9: Internal Links
    # ------------------------------------------------------------------
    def _build_internal_links(self, slug, category):
        cat_key = category.lower().replace(" ", "-")
        same_cat = [s for s in _INTERNAL_LINK_MAP.get(cat_key, []) if s != slug][:6]

        # Cross-category suggestions
        profile = _CATEGORY_PROFILES.get(cat_key, _DEFAULT_PROFILE)
        related_cat = profile.get("related_category", "")
        cross_cat = [s for s in _INTERNAL_LINK_MAP.get(related_cat, []) if s != slug][:3]

        return {
            "same_category": same_cat,
            "cross_category": cross_cat,
            "category_page": f"/tools/{cat_key}/",
        }

    # ------------------------------------------------------------------
    # Block 10: Schema
    # ------------------------------------------------------------------
    def _build_schema(self, tool_name, short_desc, slug, meta, faqs):
        software_schema = {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "name": tool_name,
            "description": meta["meta_description"],
            "url": f"https://lamgen.com/tools/{slug}/",
            "applicationCategory": "UtilitiesApplication",
            "operatingSystem": "Web Browser",
            "browserRequirements": "Requires JavaScript",
            "offers": {
                "@type": "Offer",
                "price": "0",
                "priceCurrency": "USD",
                "availability": "https://schema.org/InStock",
            },
            "provider": {
                "@type": "Organization",
                "name": "LamGen",
                "url": "https://lamgen.com",
            },
            "featureList": [
                "Free to use",
                "No signup required",
                "Browser-based processing",
                "No data uploaded to servers",
                "Mobile responsive",
                "Unlimited usage",
            ],
            "keywords": meta["primary_keyword"],
        }

        faq_schema = {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": item["q"],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": item["a"],
                    },
                }
                for item in faqs
            ],
        }

        return {
            "software_application": software_schema,
            "faq_page": faq_schema,
        }


# ---------------------------------------------------------------------------
# Convenience function — generate package for a Tool model instance
# ---------------------------------------------------------------------------
def generate_seo_package(tool) -> dict[str, Any]:
    """
    Generate a full SEO package from a Tool model instance.

    Args:
        tool: apps.tools.models.Tool instance

    Returns:
        Full SEO content package dict
    """
    engine = SEOContentEngine()
    return engine.generate(
        tool_name=tool.name,
        category=tool.category.slug if tool.category else "",
        short_desc=tool.short_desc or tool.description[:200] if tool.description else "",
        slug=tool.slug,
        tags=tool.tags or "",
        is_ai_tool=tool.is_ai_powered,
    )


def apply_seo_package_to_tool(tool, package: dict, overwrite: bool = False) -> list[str]:
    """
    Apply a generated SEO package to a Tool model instance.

    Only populates fields that are empty (or all fields if overwrite=True).
    Returns list of field names that were updated.

    Does NOT call tool.save() — caller is responsible for saving.
    """
    updated = []

    meta = package.get("meta", {})
    hero = package.get("hero", {})
    keywords_block = package.get("keywords", {})

    # meta_title
    if overwrite or not tool.meta_title:
        tool.meta_title = meta.get("meta_title", "")[:70]
        updated.append("meta_title")

    # meta_description
    if overwrite or not tool.meta_description:
        tool.meta_description = meta.get("meta_description", "")[:160]
        updated.append("meta_description")

    # seo_intro
    if overwrite or not tool.seo_intro or len(tool.seo_intro) < 150:
        tool.seo_intro = package.get("intro", "")
        updated.append("seo_intro")

    # use_cases
    if overwrite or not tool.use_cases or len(tool.use_cases) < 3:
        tool.use_cases = package.get("use_cases", [])
        updated.append("use_cases")

    # faq_items
    if overwrite or not tool.faq_items or len(tool.faq_items) < 5:
        tool.faq_items = package.get("faqs", [])
        updated.append("faq_items")

    # keywords
    if overwrite or not tool.keywords or len(tool.keywords) < 3:
        kw = keywords_block
        all_kws = [kw.get("primary", "")] + kw.get("secondary", []) + kw.get("semantic", [])
        tool.keywords = [k for k in all_kws if k][:20]
        updated.append("keywords")

    # searchable_tags
    if overwrite or not tool.searchable_tags or len(tool.searchable_tags) < 3:
        tool.searchable_tags = meta.get("secondary_keywords", [])[:10]
        updated.append("searchable_tags")

    return updated
