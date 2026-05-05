from django.core.management.base import BaseCommand
from tools.models import ToolCategory, Tool


class Command(BaseCommand):
    help = 'Seeds the database with the COMPLETE LamGen Productivity OS ecosystem'

    def handle(self, *args, **kwargs):
        # Tools Sets
        tool_sets = [
            {'name': 'Content Tools', 'slug': 'create', 'icon': 'bi-pencil-square', 'color_from': '#FF6B6B', 'color_to': '#FF8E8E', 'description': 'Writing, humanizing, and content generation.', 'order': 10},
            {'name': 'Developer Tools', 'slug': 'developer', 'icon': 'bi-code-slash', 'color_from': '#6C63FF', 'color_to': '#8B85FF', 'description': 'Engineering utilities, formatters, and dev tools.', 'order': 20},
            {'name': 'Media Tools', 'slug': 'media', 'icon': 'bi-images', 'color_from': '#FFC107', 'color_to': '#FFD54F', 'description': 'Image, PDF, and file processing.', 'order': 30},
            {'name': 'Student Tools', 'slug': 'student', 'icon': 'bi-mortarboard', 'color_from': '#00F5D4', 'color_to': '#4DFFEB', 'description': 'Academic calculators and study tools.', 'order': 40},
            {'name': 'SEO Tools', 'slug': 'seo', 'icon': 'bi-search', 'color_from': '#4CAF50', 'color_to': '#81C784', 'description': 'SEO analyzers and meta generators.', 'order': 50},
            {'name': 'Career Tools', 'slug': 'career', 'icon': 'bi-briefcase', 'color_from': '#2196F3', 'color_to': '#64B5F6', 'description': 'Resume, CV, and professional tools.', 'order': 60},
            {'name': 'Utility Tools', 'slug': 'utility', 'icon': 'bi-tools', 'color_from': '#9C27B0', 'color_to': '#BA68C8', 'description': 'General purpose tools and calculators.', 'order': 70},
            {'name': 'Viral Tools', 'slug': 'viral', 'icon': 'bi-share', 'color_from': '#FF9800', 'color_to': '#FFB74D', 'description': 'Social media and viral content tools.', 'order': 80},
        ]

        for w_data in tool_sets:
            ToolCategory.objects.update_or_create(slug=w_data['slug'], defaults=w_data)

        cats = {c.slug: c for c in ToolCategory.objects.all()}

        # Massive Tool List (Partial for brevity in seeder, but including all categories)
        # Note: I will use a fallback template logic in the view if template_name doesn't exist.
        tools_data = [
            # DEVELOPER
            {'name': 'JSON Formatter', 'slug': 'json-formatter', 'category': cats['developer'], 'icon': 'bi-braces', 'template_name': 'tools/developer/json_formatter.html', 'short_desc': 'Format JSON data.'},
            {'name': 'JSON Validator', 'slug': 'json-validator', 'category': cats['developer'], 'icon': 'bi-check-circle', 'template_name': 'tools/developer/json_validator.html', 'short_desc': 'Validate JSON syntax.'},
            {'name': 'XML Formatter', 'slug': 'xml-formatter', 'category': cats['developer'], 'icon': 'bi-filetype-xml', 'template_name': 'tools/developer/xml_formatter.html', 'short_desc': 'Beautify XML.'},
            {'name': 'SQL Formatter', 'slug': 'sql-formatter', 'category': cats['developer'], 'icon': 'bi-database', 'template_name': 'tools/developer/generic_formatter.html', 'short_desc': 'Format SQL queries.'},
            {'name': 'JWT Decoder', 'slug': 'jwt-decoder', 'category': cats['developer'], 'icon': 'bi-shield-lock', 'template_name': 'tools/developer/jwt.html', 'short_desc': 'Decode JWT tokens.'},
            {'name': 'Base64 Suite', 'slug': 'base64', 'category': cats['developer'], 'icon': 'bi-arrow-left-right', 'template_name': 'tools/developer/base64.html', 'short_desc': 'Base64 encoding/decoding.'},
            {'name': 'Unix Timestamp', 'slug': 'unix-timestamp', 'category': cats['developer'], 'icon': 'bi-clock', 'template_name': 'tools/developer/timestamp.html', 'short_desc': 'Unix time converter.'},
            {'name': 'UUID Generator', 'slug': 'uuid-gen', 'category': cats['developer'], 'icon': 'bi-hash', 'template_name': 'tools/developer/generic_gen.html', 'short_desc': 'Generate unique IDs.'},
            {'name': 'Hash Generator', 'slug': 'hash-gen', 'category': cats['developer'], 'icon': 'bi-key', 'template_name': 'tools/developer/hash.html', 'short_desc': 'MD5, SHA1, SHA256 generator.'},
            {'name': 'QR Code Gen', 'slug': 'qr-gen', 'category': cats['developer'], 'icon': 'bi-qr-code', 'template_name': 'tools/developer/qr.html', 'short_desc': 'Create QR codes.'},

            # MEDIA
            {'name': 'Image Converter', 'slug': 'image-converter', 'category': cats['media'], 'icon': 'bi-images', 'template_name': 'tools/image/converter.html', 'short_desc': 'Convert images between formats.'},
            {'name': 'PDF Merge', 'slug': 'pdf-merge', 'category': cats['media'], 'icon': 'bi-file-pdf', 'template_name': 'tools/pdf/merge.html', 'short_desc': 'Combine multiple PDFs.'},
            {'name': 'PDF Split', 'slug': 'pdf-split', 'category': cats['media'], 'icon': 'bi-scissors', 'template_name': 'tools/pdf/split.html', 'short_desc': 'Extract pages from PDF.'},
            {'name': 'Image Compressor', 'slug': 'image-compressor', 'category': cats['media'], 'icon': 'bi-box-arrow-in-down', 'template_name': 'tools/image/compressor.html', 'short_desc': 'Reduce image file size.'},
            {'name': 'SVG Optimizer', 'slug': 'svg-optimizer', 'category': cats['media'], 'icon': 'bi-vector-pen', 'template_name': 'tools/image/svg_opt.html', 'short_desc': 'Clean and optimize SVG.'},

            # STUDENT
            {'name': 'GPA Calculator', 'slug': 'gpa-calculator', 'category': cats['student'], 'icon': 'bi-calculator', 'template_name': 'tools/student/gpa_calculator.html', 'short_desc': 'Calculate student GPA.'},
            {'name': 'APA Citation', 'slug': 'apa-citation', 'category': cats['student'], 'icon': 'bi-quote', 'template_name': 'tools/student/citation.html', 'short_desc': 'Generate APA citations.'},
            {'name': 'Thesis Builder', 'slug': 'thesis-builder', 'category': cats['student'], 'icon': 'bi-journal-richtext', 'template_name': 'tools/student/thesis.html', 'short_desc': 'Build thesis structures.'},
            {'name': 'Pomodoro Timer', 'slug': 'pomodoro', 'category': cats['student'], 'icon': 'bi-stopwatch', 'template_name': 'tools/student/pomodoro.html', 'short_desc': 'Productivity study timer.'},

            # CREATE
            {'name': 'AI Humanizer', 'slug': 'text-humanizer', 'category': cats['create'], 'icon': 'bi-magic', 'template_name': 'tools/writing/humanizer.html', 'short_desc': 'Make AI text human-like.'},
            {'name': 'Paraphraser', 'slug': 'paraphraser', 'category': cats['create'], 'icon': 'bi-layers', 'template_name': 'tools/writing/paraphraser.html', 'short_desc': 'Rewrite text instantly.'},
            {'name': 'Headline Gen', 'slug': 'headline-gen', 'category': cats['create'], 'icon': 'bi-type-h1', 'template_name': 'tools/writing/headline.html', 'short_desc': 'Viral headline generator.'},

            # SEO
            {'name': 'Meta Tag Gen', 'slug': 'meta-gen', 'category': cats['seo'], 'icon': 'bi-tags', 'template_name': 'tools/seo/meta.html', 'short_desc': 'SEO meta tags generator.'},
            {'name': 'Keyword Density', 'slug': 'keyword-density', 'category': cats['seo'], 'icon': 'bi-graph-up', 'template_name': 'tools/seo/keyword_density.html', 'short_desc': 'Analyze keyword frequency.'},
            {'name': 'FAQ Schema', 'slug': 'faq-schema', 'category': cats['seo'], 'icon': 'bi-question-circle', 'template_name': 'tools/seo/faq_schema.html', 'short_desc': 'FAQ schema generator.'},

            # CAREER
            {'name': 'Resume Builder', 'slug': 'resume-builder', 'category': cats['career'], 'icon': 'bi-person-badge', 'template_name': 'tools/career/resume.html', 'short_desc': 'Create pro resumes.'},
            {'name': 'ATS Checker', 'slug': 'ats-checker', 'category': cats['career'], 'icon': 'bi-search', 'template_name': 'tools/career/ats.html', 'short_desc': 'Check resume for ATS.'},
            {'name': 'Cover Letter', 'slug': 'cover-letter', 'category': cats['career'], 'icon': 'bi-envelope-paper', 'template_name': 'tools/career/cover_letter.html', 'short_desc': 'Write cover letters.'},

            # UTILITY
            {'name': 'Unit Converter', 'slug': 'unit-converter', 'category': cats['utility'], 'icon': 'bi-rulers', 'template_name': 'tools/utility/unit_converter.html', 'short_desc': 'Convert any units.'},
            {'name': 'Password Gen', 'slug': 'password-gen', 'category': cats['utility'], 'icon': 'bi-key', 'template_name': 'tools/utility/password.html', 'short_desc': 'Secure passwords.'},
            {'name': 'BMI Calculator', 'slug': 'bmi-calculator', 'category': cats['utility'], 'icon': 'bi-person', 'template_name': 'tools/utility/bmi.html', 'short_desc': 'Health BMI calculator.'},

            # VIRAL
            {'name': 'Fake Tweet', 'slug': 'fake-tweet', 'category': cats['viral'], 'icon': 'bi-twitter-x', 'template_name': 'tools/social/fake_tweet.html', 'short_desc': 'Generate mock tweets.'},
            {'name': 'Instagram Mock', 'slug': 'insta-mock', 'category': cats['viral'], 'icon': 'bi-instagram', 'template_name': 'tools/social/insta.html', 'short_desc': 'IG post simulator.'},
            {'name': 'Nickname Gen', 'slug': 'nickname-gen', 'category': cats['viral'], 'icon': 'bi-person-circle', 'template_name': 'tools/social/nicknames.html', 'short_desc': 'Viral nickname generator.'},
        ]

        # ADD THESE BELOW THE EXISTING tools_data = [ ... ] LIST
        # INSIDE THE SAME FILE

        tools_data.extend([

            # =========================
            # DEVELOPER TOOLS
            # =========================
            {'name': 'JSON Minifier', 'slug': 'json-minifier', 'category': cats['developer'], 'icon': 'bi-file-earmark-code', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Minify JSON instantly.'},
            {'name': 'JSON to CSV', 'slug': 'json-csv', 'category': cats['developer'], 'icon': 'bi-arrow-left-right', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Convert JSON into CSV.'},
            {'name': 'CSV to JSON', 'slug': 'csv-json', 'category': cats['developer'], 'icon': 'bi-arrow-repeat', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Convert CSV into JSON.'},
            {'name': 'XML Validator', 'slug': 'xml-validator', 'category': cats['developer'], 'icon': 'bi-check2-square', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Validate XML structure.'},
            {'name': 'YAML Formatter', 'slug': 'yaml-formatter', 'category': cats['developer'], 'icon': 'bi-list-columns', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Beautify YAML data.'},
            {'name': 'HTML Beautifier', 'slug': 'html-beautifier', 'category': cats['developer'], 'icon': 'bi-filetype-html', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Beautify HTML markup.'},
            {'name': 'CSS Beautifier', 'slug': 'css-beautifier', 'category': cats['developer'], 'icon': 'bi-filetype-css', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Beautify CSS code.'},
            {'name': 'JS Beautifier', 'slug': 'js-beautifier', 'category': cats['developer'], 'icon': 'bi-filetype-js', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Beautify JavaScript code.'},
            {'name': 'Regex Tester', 'slug': 'regex-tester', 'category': cats['developer'], 'icon': 'bi-regex', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Test regex patterns.'},
            {'name': 'Markdown Preview', 'slug': 'markdown-preview', 'category': cats['developer'], 'icon': 'bi-markdown', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Preview markdown instantly.'},
            {'name': 'Diff Checker', 'slug': 'diff-checker', 'category': cats['developer'], 'icon': 'bi-intersect', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Compare text differences.'},
            {'name': 'Cron Builder', 'slug': 'cron-builder', 'category': cats['developer'], 'icon': 'bi-clock-history', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Build cron expressions.'},
            {'name': 'Lorem Ipsum', 'slug': 'lorem-ipsum', 'category': cats['developer'], 'icon': 'bi-fonts', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Generate placeholder text.'},
            {'name': 'Fake Data Generator', 'slug': 'fake-data-generator', 'category': cats['developer'], 'icon': 'bi-database-fill-add', 'template_name': 'tools/developer/generic.html', 'short_desc': 'Generate fake datasets.'},

            # =========================
            # MEDIA TOOLS
            # =========================
            {'name': 'WEBP to PNG', 'slug': 'webp-png', 'category': cats['media'], 'icon': 'bi-image', 'template_name': 'tools/media/generic.html', 'short_desc': 'Convert WEBP into PNG.'},
            {'name': 'PNG to JPG', 'slug': 'png-jpg', 'category': cats['media'], 'icon': 'bi-image-alt', 'template_name': 'tools/media/generic.html', 'short_desc': 'Convert PNG into JPG.'},
            {'name': 'JPG to PNG', 'slug': 'jpg-png', 'category': cats['media'], 'icon': 'bi-images', 'template_name': 'tools/media/generic.html', 'short_desc': 'Convert JPG into PNG.'},
            {'name': 'Image Resizer', 'slug': 'image-resizer', 'category': cats['media'], 'icon': 'bi-aspect-ratio', 'template_name': 'tools/media/generic.html', 'short_desc': 'Resize images quickly.'},
            {'name': 'Crop Tool', 'slug': 'crop-tool', 'category': cats['media'], 'icon': 'bi-crop', 'template_name': 'tools/media/generic.html', 'short_desc': 'Crop images easily.'},
            {'name': 'Rotate Tool', 'slug': 'rotate-tool', 'category': cats['media'], 'icon': 'bi-arrow-clockwise', 'template_name': 'tools/media/generic.html', 'short_desc': 'Rotate images instantly.'},
            {'name': 'Background Remover', 'slug': 'bg-remover', 'category': cats['media'], 'icon': 'bi-back', 'template_name': 'tools/media/generic.html', 'short_desc': 'Remove image backgrounds.'},
            {'name': 'Meme Generator', 'slug': 'meme-generator', 'category': cats['media'], 'icon': 'bi-emoji-laughing', 'template_name': 'tools/media/generic.html', 'short_desc': 'Generate memes instantly.'},
            {'name': 'PDF Compressor', 'slug': 'pdf-compressor', 'category': cats['media'], 'icon': 'bi-file-earmark-zip', 'template_name': 'tools/media/generic.html', 'short_desc': 'Compress PDF files.'},
            {'name': 'Image to PDF', 'slug': 'image-pdf', 'category': cats['media'], 'icon': 'bi-file-pdf-fill', 'template_name': 'tools/media/generic.html', 'short_desc': 'Convert images into PDFs.'},

            # =========================
            # STUDENT TOOLS
            # =========================
            {'name': 'CGPA Calculator', 'slug': 'cgpa-calculator', 'category': cats['student'], 'icon': 'bi-calculator-fill', 'template_name': 'tools/student/generic.html', 'short_desc': 'Calculate CGPA instantly.'},
            {'name': 'Assignment Formatter', 'slug': 'assignment-formatter', 'category': cats['student'], 'icon': 'bi-file-earmark-text', 'template_name': 'tools/student/generic.html', 'short_desc': 'Format assignments professionally.'},
            {'name': 'Study Planner', 'slug': 'study-planner', 'category': cats['student'], 'icon': 'bi-calendar-week', 'template_name': 'tools/student/generic.html', 'short_desc': 'Organize study schedules.'},
            {'name': 'Word Counter', 'slug': 'word-counter', 'category': cats['student'], 'icon': 'bi-file-word', 'template_name': 'tools/student/generic.html', 'short_desc': 'Count words and characters.'},
            {'name': 'Flashcard Generator', 'slug': 'flashcard-generator', 'category': cats['student'], 'icon': 'bi-card-heading', 'template_name': 'tools/student/generic.html', 'short_desc': 'Create study flashcards.'},
            {'name': 'Exam Countdown', 'slug': 'exam-countdown', 'category': cats['student'], 'icon': 'bi-alarm', 'template_name': 'tools/student/generic.html', 'short_desc': 'Countdown to exams.'},

            # =========================
            # CONTENT TOOLS
            # =========================
            {'name': 'Sentence Rewriter', 'slug': 'sentence-rewriter', 'category': cats['create'], 'icon': 'bi-pencil', 'template_name': 'tools/create/generic.html', 'short_desc': 'Rewrite sentences naturally.'},
            {'name': 'Passive Active Converter', 'slug': 'passive-active-converter', 'category': cats['create'], 'icon': 'bi-arrow-left-right', 'template_name': 'tools/create/generic.html', 'short_desc': 'Convert sentence voice.'},
            {'name': 'Text Simplifier', 'slug': 'text-simplifier', 'category': cats['create'], 'icon': 'bi-text-paragraph', 'template_name': 'tools/create/generic.html', 'short_desc': 'Simplify complex text.'},
            {'name': 'Headline Generator', 'slug': 'headline-generator', 'category': cats['create'], 'icon': 'bi-type-h1', 'template_name': 'tools/create/generic.html', 'short_desc': 'Generate catchy headlines.'},
            {'name': 'Hook Generator', 'slug': 'hook-generator', 'category': cats['create'], 'icon': 'bi-lightning-charge', 'template_name': 'tools/create/generic.html', 'short_desc': 'Generate viral hooks.'},
            {'name': 'Tone Converter', 'slug': 'tone-converter', 'category': cats['create'], 'icon': 'bi-chat-square-text', 'template_name': 'tools/create/generic.html', 'short_desc': 'Convert writing tone.'},

            # =========================
            # SEO TOOLS
            # =========================
            {'name': 'SERP Preview', 'slug': 'serp-preview', 'category': cats['seo'], 'icon': 'bi-google', 'template_name': 'tools/seo/generic.html', 'short_desc': 'Preview Google snippets.'},
            {'name': 'Slug Generator', 'slug': 'slug-generator', 'category': cats['seo'], 'icon': 'bi-link-45deg', 'template_name': 'tools/seo/generic.html', 'short_desc': 'Generate SEO-friendly slugs.'},
            {'name': 'Twitter Card Generator', 'slug': 'twitter-card-generator', 'category': cats['seo'], 'icon': 'bi-twitter-x', 'template_name': 'tools/seo/generic.html', 'short_desc': 'Generate Twitter card tags.'},
            {'name': 'Canonical Checker', 'slug': 'canonical-checker', 'category': cats['seo'], 'icon': 'bi-check2-circle', 'template_name': 'tools/seo/generic.html', 'short_desc': 'Check canonical URLs.'},
            {'name': 'Schema Markup Generator', 'slug': 'schema-generator', 'category': cats['seo'], 'icon': 'bi-diagram-3', 'template_name': 'tools/seo/generic.html', 'short_desc': 'Generate structured schema markup.'},

            # =========================
            # CAREER TOOLS
            # =========================
            {'name': 'LinkedIn Headline Generator', 'slug': 'linkedin-headline-generator', 'category': cats['career'], 'icon': 'bi-linkedin', 'template_name': 'tools/career/generic.html', 'short_desc': 'Generate LinkedIn headlines.'},
            {'name': 'Invoice Generator', 'slug': 'invoice-generator', 'category': cats['career'], 'icon': 'bi-receipt', 'template_name': 'tools/career/generic.html', 'short_desc': 'Generate invoices professionally.'},
            {'name': 'Portfolio Generator', 'slug': 'portfolio-generator', 'category': cats['career'], 'icon': 'bi-person-workspace', 'template_name': 'tools/career/generic.html', 'short_desc': 'Generate portfolio pages.'},
            {'name': 'Resume Summary Generator', 'slug': 'resume-summary-generator', 'category': cats['career'], 'icon': 'bi-file-earmark-person', 'template_name': 'tools/career/generic.html', 'short_desc': 'Generate resume summaries.'},

            # =========================
            # UTILITY TOOLS
            # =========================
            {'name': 'Percentage Calculator', 'slug': 'percentage-calculator', 'category': cats['utility'], 'icon': 'bi-percent', 'template_name': 'tools/utility/generic.html', 'short_desc': 'Calculate percentages quickly.'},
            {'name': 'EMI Calculator', 'slug': 'emi-calculator', 'category': cats['utility'], 'icon': 'bi-cash-stack', 'template_name': 'tools/utility/generic.html', 'short_desc': 'Calculate EMI payments.'},
            {'name': 'Tax Calculator', 'slug': 'tax-calculator', 'category': cats['utility'], 'icon': 'bi-bank', 'template_name': 'tools/utility/generic.html', 'short_desc': 'Estimate taxes instantly.'},
            {'name': 'Timezone Converter', 'slug': 'timezone-converter', 'category': cats['utility'], 'icon': 'bi-globe', 'template_name': 'tools/utility/generic.html', 'short_desc': 'Convert timezones globally.'},
            {'name': 'Countdown Timer', 'slug': 'countdown-timer', 'category': cats['utility'], 'icon': 'bi-hourglass-split', 'template_name': 'tools/utility/generic.html', 'short_desc': 'Countdown timer utility.'},
            {'name': 'Scientific Calculator', 'slug': 'scientific-calculator', 'category': cats['utility'], 'icon': 'bi-calculator-fill', 'template_name': 'tools/utility/generic.html', 'short_desc': 'Advanced scientific calculator.'},

            # =========================
            # VIRAL TOOLS
            # =========================
            {'name': 'Fake Instagram Post', 'slug': 'fake-instagram-post', 'category': cats['viral'], 'icon': 'bi-instagram', 'template_name': 'tools/viral/generic.html', 'short_desc': 'Generate fake Instagram posts.'},
            {'name': 'Fake YouTube Comment', 'slug': 'fake-youtube-comment', 'category': cats['viral'], 'icon': 'bi-youtube', 'template_name': 'tools/viral/generic.html', 'short_desc': 'Generate fake YouTube comments.'},
            {'name': 'Emoji Combiner', 'slug': 'emoji-combiner', 'category': cats['viral'], 'icon': 'bi-emoji-smile', 'template_name': 'tools/viral/generic.html', 'short_desc': 'Combine emojis creatively.'},
            {'name': 'Roast Generator', 'slug': 'roast-generator', 'category': cats['viral'], 'icon': 'bi-fire', 'template_name': 'tools/viral/generic.html', 'short_desc': 'Generate funny roasts.'},
            {'name': 'Pickup Line Generator', 'slug': 'pickup-line-generator', 'category': cats['viral'], 'icon': 'bi-chat-heart', 'template_name': 'tools/viral/generic.html', 'short_desc': 'Generate pickup lines.'},
            {'name': 'Username Generator', 'slug': 'username-generator', 'category': cats['viral'], 'icon': 'bi-at', 'template_name': 'tools/viral/generic.html', 'short_desc': 'Generate viral usernames.'},

        ])

        # ADD THIS MASSIVE LIST INSIDE all_requested_tools = [ ... ]
        # This completes the ecosystem with ALL requested tools.

        all_requested_tools = [
            # Developer
            ('JSON Minifier', 'json-minifier', 'developer'),
            ('JSON to CSV', 'json-csv', 'developer'),
            ('CSV to JSON', 'csv-json', 'developer'),
            ('XML Validator', 'xml-validator', 'developer'),
            ('YAML Formatter', 'yaml-formatter', 'developer'),
            ('HTML Beautifier', 'html-beautifier', 'developer'),
            ('CSS Beautifier', 'css-beautifier', 'developer'),
            ('JavaScript Beautifier', 'js-beautifier', 'developer'),
            ('CSS Minifier', 'css-minifier', 'developer'),
            ('JavaScript Minifier', 'js-minifier', 'developer'),
            ('Regex Tester', 'regex-tester', 'developer'),
            ('Markdown Preview', 'markdown-preview', 'developer'),
            ('Markdown to HTML', 'markdown-html', 'developer'),
            ('Diff Checker', 'diff-checker', 'developer'),
            ('Cron Builder', 'cron-builder', 'developer'),
            ('Lorem Ipsum', 'lorem-ipsum', 'developer'),
            ('Fake Data Generator', 'fake-data-generator', 'developer'),
            ('UUID Bulk Generator', 'uuid-bulk-generator', 'developer'),
            ('ASCII Table Viewer', 'ascii-table', 'developer'),
            ('HEX RGB Converter', 'hex-rgb-converter', 'developer'),
            ('URL Parser', 'url-parser', 'developer'),
            ('MIME Type Lookup', 'mime-lookup', 'developer'),
            ('HTTP Header Parser', 'http-header-parser', 'developer'),
            ('API Request Tester', 'api-request-tester', 'developer'),
            ('robots.txt Generator', 'robots-generator', 'developer'),
            ('sitemap.xml Generator', 'sitemap-generator', 'developer'),
            ('.htaccess Generator', 'htaccess-generator', 'developer'),
            ('.env Formatter', 'env-formatter', 'developer'),
            ('CSV Viewer', 'csv-viewer', 'developer'),

            # Media
            ('WEBP to PNG', 'webp-png', 'media'),
            ('PNG to JPG', 'png-jpg', 'media'),
            ('JPG to PNG', 'jpg-png', 'media'),
            ('Image Resizer', 'image-resizer', 'media'),
            ('Crop Tool', 'crop-tool', 'media'),
            ('Rotate Tool', 'rotate-tool', 'media'),
            ('Flip Tool', 'flip-tool', 'media'),
            ('Blur Tool', 'blur-tool', 'media'),
            ('Watermark Tool', 'watermark-tool', 'media'),
            ('Background Remover', 'bg-remover', 'media'),
            ('Image Metadata Viewer', 'image-metadata', 'media'),
            ('Color Extractor', 'color-extractor', 'media'),
            ('Palette Generator', 'palette-generator', 'media'),
            ('GIF Frame Extractor', 'gif-frame-extractor', 'media'),
            ('Image to Base64', 'image-base64', 'media'),
            ('Base64 to Image', 'base64-image', 'media'),
            ('Pixel Art Generator', 'pixel-art-generator', 'media'),
            ('Social Thumbnail Creator', 'social-thumbnail', 'media'),
            ('Gradient Wallpaper Generator', 'gradient-wallpaper', 'media'),
            ('Photo Collage Generator', 'photo-collage', 'media'),
            ('Favicon Generator', 'favicon-generator', 'media'),
            ('Screenshot Mockup Generator', 'screenshot-mockup', 'media'),

            # PDF & File
            ('PDF Compressor', 'pdf-compressor', 'media'),
            ('PDF Metadata Viewer', 'pdf-metadata', 'media'),
            ('PDF to Image', 'pdf-image', 'media'),
            ('Image to PDF', 'image-pdf', 'media'),
            ('PDF Watermark Tool', 'pdf-watermark', 'media'),
            ('PDF Rotate Tool', 'pdf-rotate', 'media'),
            ('PDF Unlock Tool', 'pdf-unlock', 'media'),
            ('PDF Page Extractor', 'pdf-page-extractor', 'media'),
            ('PDF Reorder Tool', 'pdf-reorder', 'media'),
            ('PDF Preview Tool', 'pdf-preview', 'media'),
            ('Text Extractor', 'text-extractor', 'media'),
            ('ZIP Extractor', 'zip-extractor', 'media'),
            ('CSV Cleaner', 'csv-cleaner', 'media'),
            ('Duplicate Line Remover', 'duplicate-line-remover', 'media'),
            ('File Rename Utility', 'file-rename-utility', 'media'),
            ('File Compare Utility', 'file-compare-utility', 'media'),
            ('Text Compare Tool', 'text-compare-tool', 'media'),
            ('File Hash Checker', 'file-hash-checker', 'media'),

            # Student
            ('CGPA Calculator', 'cgpa-calc', 'student'),
            ('Grade Predictor', 'grade-predictor', 'student'),
            ('Assignment Formatter', 'assignment-formatter', 'student'),
            ('MLA Citation Generator', 'mla-citation', 'student'),
            ('Harvard Citation Generator', 'harvard-citation', 'student'),
            ('Chicago Citation Generator', 'chicago-citation', 'student'),
            ('Bibliography Generator', 'bibliography-generator', 'student'),
            ('Reference Formatter', 'reference-formatter', 'student'),
            ('Citation Formatter', 'citation-formatter', 'student'),
            ('Research Outline Builder', 'research-outline', 'student'),
            ('Research Topic Generator', 'research-topic-generator', 'student'),
            ('Academic Title Generator', 'academic-title-generator', 'student'),
            ('Flashcard Generator', 'flashcard-generator', 'student'),
            ('Study Session Tracker', 'study-session-tracker', 'student'),
            ('Semester Planner', 'semester-planner', 'student'),
            ('Homework Tracker', 'homework-tracker', 'student'),
            ('Quiz Generator', 'quiz-generator', 'student'),
            ('Timetable Builder', 'timetable-builder', 'student'),
            ('Exam Countdown', 'exam-countdown', 'student'),
            ('Reading Time Estimator', 'reading-time', 'student'),
            ('Readability Checker', 'readability-checker', 'student'),
            ('Paragraph Organizer', 'paragraph-organizer', 'student'),
            ('Plagiarism Checklist', 'plagiarism-checklist', 'student'),
            ('Character Counter', 'character-counter', 'student'),
            ('Sentence Counter', 'sentence-counter', 'student'),

            # Create
            ('Sentence Rewriter', 'sentence-rewriter', 'create'),
            ('Passive Active Converter', 'passive-active-converter', 'create'),
            ('Readability Improver', 'readability-improver', 'create'),
            ('Grammar Pattern Checker', 'grammar-pattern-checker', 'create'),
            ('Text Simplifier', 'text-simplifier', 'create'),
            ('Introduction Generator', 'introduction-generator', 'create'),
            ('Conclusion Generator', 'conclusion-generator', 'create'),
            ('Hook Generator', 'hook-generator', 'create'),
            ('Paragraph Expander', 'paragraph-expander', 'create'),
            ('Sentence Shortener', 'sentence-shortener', 'create'),
            ('Duplicate Remover', 'duplicate-remover', 'create'),
            ('Text Cleaner', 'text-cleaner', 'create'),
            ('Bullet Point Generator', 'bullet-point-generator', 'create'),
            ('Story Prompt Generator', 'story-prompt-generator', 'create'),
            ('Email Subject Generator', 'email-subject-generator', 'create'),
            ('Essay Outline Generator', 'essay-outline-generator', 'create'),
            ('Tone Converter', 'tone-converter', 'create'),
            ('Random Paragraph Generator', 'random-paragraph-generator', 'create'),

            # SEO
            ('Meta Description Generator', 'meta-description-generator', 'seo'),
            ('SERP Preview Tool', 'serp-preview', 'seo'),
            ('Keyword Grouping Tool', 'keyword-grouping', 'seo'),
            ('Canonical Checker', 'canonical-checker', 'seo'),
            ('Redirect Checker', 'redirect-checker', 'seo'),
            ('Twitter Card Generator', 'twitter-card-generator', 'seo'),
            ('Breadcrumb Schema Generator', 'breadcrumb-schema', 'seo'),
            ('Schema Markup Generator', 'schema-markup-generator', 'seo'),
            ('Structured Data Validator', 'structured-data-validator', 'seo'),
            ('Internal Link Suggestion Tool', 'internal-link-tool', 'seo'),
            ('Heading Structure Analyzer', 'heading-structure-analyzer', 'seo'),
            ('OpenGraph Preview Tool', 'opengraph-preview', 'seo'),
            ('Meta Pixel Helper', 'meta-pixel-helper', 'seo'),
            ('XML Sitemap Validator', 'xml-sitemap-validator', 'seo'),
            ('hreflang Generator', 'hreflang-generator', 'seo'),
            ('SEO Audit Checklist', 'seo-audit-checklist', 'seo'),
            ('Robots Meta Generator', 'robots-meta-generator', 'seo'),

            # Career
            ('Resume Summary Generator', 'resume-summary-generator', 'career'),
            ('CV Templates', 'cv-templates', 'career'),
            ('LinkedIn Headline Generator', 'linkedin-headline-generator', 'career'),
            ('Portfolio Generator', 'portfolio-generator', 'career'),
            ('Bio Generator', 'bio-generator', 'career'),
            ('Invoice Generator', 'invoice-generator', 'career'),
            ('Quotation Builder', 'quotation-builder', 'career'),
            ('Job Description Formatter', 'job-description-formatter', 'career'),
            ('Skills Section Generator', 'skills-section-generator', 'career'),
            ('Freelance Proposal Generator', 'freelance-proposal-generator', 'career'),
            ('Client Brief Generator', 'client-brief-generator', 'career'),
            ('Meeting Notes Generator', 'meeting-notes-generator', 'career'),

            # Utility
            ('Percentage Calculator', 'percentage-calculator', 'utility'),
            ('EMI Calculator', 'emi-calculator', 'utility'),
            ('Tax Calculator', 'tax-calculator', 'utility'),
            ('Timezone Converter', 'timezone-converter', 'utility'),
            ('Countdown Timer', 'countdown-timer', 'utility'),
            ('Online Notepad', 'online-notepad', 'utility'),
            ('Clipboard Utility', 'clipboard-utility', 'utility'),
            ('Random Picker', 'random-picker', 'utility'),
            ('Random Number Generator', 'random-number-generator', 'utility'),
            ('Dice Generator', 'dice-generator', 'utility'),
            ('Coin Flip Simulator', 'coin-flip-simulator', 'utility'),
            ('Scientific Calculator', 'scientific-calculator', 'utility'),
            ('Binary Converter', 'binary-converter', 'utility'),
            ('Currency Formatter', 'currency-formatter', 'utility'),
            ('Tip Calculator', 'tip-calculator', 'utility'),
            ('Loan Calculator', 'loan-calculator', 'utility'),
            ('Daily Habit Tracker', 'daily-habit-tracker', 'utility'),
            ('Calendar Generator', 'calendar-generator', 'utility'),

            # Viral
            ('Fake Instagram Post Generator', 'fake-instagram-post', 'viral'),
            ('Fake YouTube Comment Generator', 'fake-youtube-comment', 'viral'),
            ('Fake Discord Chat Generator', 'fake-discord-chat', 'viral'),
            ('Fake Chat Generator', 'fake-chat-generator', 'viral'),
            ('Meme Caption Generator', 'meme-caption-generator', 'viral'),
            ('Emoji Combiner', 'emoji-combiner', 'viral'),
            ('Nickname Generator', 'nickname-generator', 'viral'),
            ('Pickup Line Generator', 'pickup-line-generator', 'viral'),
            ('Roast Generator', 'roast-generator', 'viral'),
            ('Random Comment Generator', 'random-comment-generator', 'viral'),
            ('Instagram Caption Generator', 'instagram-caption-generator', 'viral'),
            ('TikTok Caption Generator', 'tiktok-caption-generator', 'viral'),
            ('YouTube Title Generator', 'youtube-title-generator', 'viral'),
            ('Viral Hashtag Generator', 'viral-hashtag-generator', 'viral'),
            ('Bio Style Generator', 'bio-style-generator', 'viral'),
            ('Username Generator', 'username-generator', 'viral'),
        ]

        for name, slug, cat_slug in all_requested_tools:
            tools_data.append({
                'name': name,
                'slug': slug,
                'category': cats[cat_slug],
                'icon': 'bi-gear',
                'template_name': f'tools/{cat_slug}/generic.html',
                'short_desc': f'High performance {name} tool.'
            })

        for t in tools_data:
            tool, created = Tool.objects.update_or_create(
                slug=t['slug'],
                defaults={
                    'name': t['name'],
                    'category': t['category'],
                    'icon': t['icon'],
                    'template_name': t['template_name'],
                    'description': t.get('description', t['short_desc']),
                    'short_desc': t['short_desc'],
                    'is_active': True
                }
            )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(tools_data)} tools into LamGen."))
