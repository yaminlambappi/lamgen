# ---------------------------------------------------------------------------
# Tool Categories Configuration — LamGen Tools Ecosystem
# Core verticals plus merged ecosystem block (see config/tool_categories_ecosystem.py).
# Used by: seed_tools / seed_all, audit, settings. Single source of truth for catalog shape.
# Rules: no duplicate tool slugs globally, slug is the unique key for seeding.
# is_active=False until the tool template is fully implemented (per-tool override).
# ---------------------------------------------------------------------------

_TOOL_CATEGORIES_BASE = [
    # =========================================================================
    # 1. DEVELOPER TOOLS (26 tools)
    # =========================================================================
    {
        'slug': 'developer-tools',
        'name': 'Developer Tools',
        'icon': 'bi-code-slash',
        'color_from': '#6C63FF',
        'color_to': '#00F5D4',
        'order': 1,
        'short_desc': 'Format, validate, convert and debug code and data formats.',
        'tools': [
            {'slug': 'json-formatter', 'name': 'JSON Formatter', 'short_desc': 'Format, validate and beautify JSON online.', 'icon': 'bi-braces', 'template_name': 'tools/developer/json-formatter.html', 'tags': 'json,format,beautify,validate,developer', 'order': 1, 'is_active': True},
            {'slug': 'xml-formatter', 'name': 'XML Formatter', 'short_desc': 'Format and validate XML documents online.', 'icon': 'bi-file-code', 'template_name': 'tools/developer/xml-formatter.html', 'tags': 'xml,format,beautify,validate,developer', 'order': 2, 'is_active': True},
            {'slug': 'yaml-formatter', 'name': 'YAML Formatter', 'short_desc': 'Format and validate YAML files online.', 'icon': 'bi-file-text', 'template_name': 'tools/developer/yaml-formatter.html', 'tags': 'yaml,format,beautify,validate,developer', 'order': 3, 'is_active': True},
            {'slug': 'sql-beautifier', 'name': 'SQL Beautifier', 'short_desc': 'Format and beautify SQL queries online.', 'icon': 'bi-database', 'template_name': 'tools/developer/sql-beautifier.html', 'tags': 'sql,format,beautify,query,developer', 'order': 4, 'is_active': True},
            {'slug': 'html-formatter', 'name': 'HTML Formatter', 'short_desc': 'Format and beautify HTML code online.', 'icon': 'bi-filetype-html', 'template_name': 'tools/developer/html-formatter.html', 'tags': 'html,format,beautify,developer', 'order': 5, 'is_active': True},
            {'slug': 'css-formatter', 'name': 'CSS Formatter', 'short_desc': 'Format and beautify CSS stylesheets online.', 'icon': 'bi-filetype-css', 'template_name': 'tools/developer/css-formatter.html', 'tags': 'css,format,beautify,developer', 'order': 6, 'is_active': True},
            {'slug': 'js-formatter', 'name': 'JavaScript Formatter', 'short_desc': 'Format and beautify JavaScript code online.', 'icon': 'bi-filetype-js', 'template_name': 'tools/developer/js-formatter.html', 'tags': 'javascript,js,format,beautify,developer', 'order': 7, 'is_active': True},
            {'slug': 'css-minifier', 'name': 'CSS Minifier', 'short_desc': 'Minify CSS to reduce file size.', 'icon': 'bi-arrows-collapse', 'template_name': 'tools/developer/css-minifier.html', 'tags': 'css,minify,compress,developer', 'order': 8, 'is_active': True},
            {'slug': 'js-minifier', 'name': 'JavaScript Minifier', 'short_desc': 'Minify JavaScript to reduce file size.', 'icon': 'bi-arrows-collapse', 'template_name': 'tools/developer/js-minifier.html', 'tags': 'javascript,js,minify,compress,developer', 'order': 9, 'is_active': True},
            {'slug': 'json-csv-converter', 'name': 'JSON to CSV Converter', 'short_desc': 'Convert between JSON and CSV formats instantly.', 'icon': 'bi-arrow-left-right', 'template_name': 'tools/developer/json-csv-converter.html', 'tags': 'json,csv,convert,transform,developer', 'order': 10, 'is_active': True},
            {'slug': 'base64-encoder', 'name': 'Base64 Encoder / Decoder', 'short_desc': 'Encode or decode Base64 strings online.', 'icon': 'bi-lock', 'template_name': 'tools/developer/base64-encoder.html', 'tags': 'base64,encode,decode,developer', 'order': 11, 'is_active': True},
            {'slug': 'url-encoder', 'name': 'URL Encoder / Decoder', 'short_desc': 'Encode or decode URL components online.', 'icon': 'bi-link-45deg', 'template_name': 'tools/developer/url-encoder.html', 'tags': 'url,encode,decode,percent,developer', 'order': 12, 'is_active': True},
            {'slug': 'jwt-decoder', 'name': 'JWT Decoder', 'short_desc': 'Decode and inspect JSON Web Tokens.', 'icon': 'bi-shield-lock', 'template_name': 'tools/developer/jwt-decoder.html', 'tags': 'jwt,token,decode,auth,developer', 'order': 13, 'is_active': True},
            {'slug': 'regex-tester', 'name': 'Regex Tester', 'short_desc': 'Test and debug regular expressions with live match highlighting.', 'icon': 'bi-search', 'template_name': 'tools/developer/regex-tester.html', 'tags': 'regex,regexp,test,match,developer', 'order': 14, 'is_active': True},
            {'slug': 'cron-builder', 'name': 'Cron Expression Builder', 'short_desc': 'Build and validate cron schedule expressions visually.', 'icon': 'bi-clock', 'template_name': 'tools/developer/cron-builder.html', 'tags': 'cron,schedule,expression,developer', 'order': 15, 'is_active': True},
            {'slug': 'uuid-generator', 'name': 'UUID Generator', 'short_desc': 'Generate random UUIDs (v4) instantly in bulk.', 'icon': 'bi-fingerprint', 'template_name': 'tools/developer/uuid-generator.html', 'tags': 'uuid,guid,generate,random,developer', 'order': 16, 'is_active': True},
            {'slug': 'hash-generator', 'name': 'Hash Generator', 'short_desc': 'Generate SHA-256, SHA-512 and MD5 hashes online.', 'icon': 'bi-hash', 'template_name': 'tools/developer/hash-generator.html', 'tags': 'hash,sha256,sha512,md5,developer', 'order': 17, 'is_active': True},
            {'slug': 'lorem-ipsum', 'name': 'Lorem Ipsum Generator', 'short_desc': 'Generate placeholder lorem ipsum text by words, sentences or paragraphs.', 'icon': 'bi-paragraph', 'template_name': 'tools/developer/lorem-ipsum.html', 'tags': 'lorem,ipsum,placeholder,text,developer', 'order': 18, 'is_active': True},
            {'slug': 'fake-data-generator', 'name': 'Fake Data Generator', 'short_desc': 'Generate realistic fake names, emails, addresses and more for testing.', 'icon': 'bi-person-badge', 'template_name': 'tools/developer/fake-data-generator.html', 'tags': 'fake,data,mock,test,developer', 'order': 19, 'is_active': True},
            {'slug': 'markdown-previewer', 'name': 'Markdown Previewer', 'short_desc': 'Write and preview Markdown in real time with syntax highlighting.', 'icon': 'bi-markdown', 'template_name': 'tools/developer/markdown-previewer.html', 'tags': 'markdown,preview,render,developer', 'order': 20, 'is_active': True},
            {'slug': 'diff-checker', 'name': 'Diff Checker', 'short_desc': 'Compare two blocks of text and highlight differences line by line.', 'icon': 'bi-file-diff', 'template_name': 'tools/developer/diff-checker.html', 'tags': 'diff,compare,text,developer', 'order': 21, 'is_active': True},
            {'slug': 'color-palette-generator', 'name': 'Color Palette Generator', 'short_desc': 'Extract and generate color palettes from images or hex values.', 'icon': 'bi-palette', 'template_name': 'tools/developer/color-palette-generator.html', 'tags': 'color,palette,extract,design,developer', 'order': 22, 'is_active': True},
            {'slug': 'gradient-generator', 'name': 'CSS Gradient Generator', 'short_desc': 'Build CSS gradients visually with live preview and code output.', 'icon': 'bi-brush', 'template_name': 'tools/developer/gradient-generator.html', 'tags': 'css,gradient,color,design,developer', 'order': 23, 'is_active': True},
            {'slug': 'robots-txt-generator', 'name': 'robots.txt Generator', 'short_desc': 'Generate a robots.txt file for your website with common rules.', 'icon': 'bi-robot', 'template_name': 'tools/developer/robots-txt-generator.html', 'tags': 'robots,txt,seo,crawl,developer', 'order': 24, 'is_active': True},
            {'slug': 'htaccess-generator', 'name': '.htaccess Generator', 'short_desc': 'Generate Apache .htaccess rules for redirects, auth and caching.', 'icon': 'bi-server', 'template_name': 'tools/developer/htaccess-generator.html', 'tags': 'htaccess,apache,redirect,developer', 'order': 25, 'is_active': True},
            {'slug': 'env-formatter', 'name': '.env Formatter', 'short_desc': 'Format, sort and validate .env environment variable files.', 'icon': 'bi-gear', 'template_name': 'tools/developer/env-formatter.html', 'tags': 'env,environment,format,developer', 'order': 26, 'is_active': True},
            {'slug': 'unix-timestamp-converter', 'name': 'Unix Timestamp Converter', 'short_desc': 'Convert Unix timestamps to human-readable dates and back.', 'icon': 'bi-clock-history', 'template_name': 'tools/developer/unix-timestamp-converter.html', 'tags': 'unix,timestamp,date,convert,developer', 'order': 27, 'is_active': True},
            {'slug': 'html-entity-encoder', 'name': 'HTML Entity Encoder', 'short_desc': 'Encode and decode HTML entities in text.', 'icon': 'bi-code', 'template_name': 'tools/developer/html-entity-encoder.html', 'tags': 'html,entity,encode,decode,developer', 'order': 28, 'is_active': True},
            {'slug': 'json-to-typescript', 'name': 'JSON to TypeScript', 'short_desc': 'Generate TypeScript interfaces from JSON objects instantly.', 'icon': 'bi-filetype-tsx', 'template_name': 'tools/developer/json-to-typescript.html', 'tags': 'json,typescript,interface,generate,developer', 'order': 29, 'is_active': True},
            {'slug': 'color-converter', 'name': 'Color Converter', 'short_desc': 'Convert colors between HEX, RGB, HSL and HSV formats.', 'icon': 'bi-eyedropper', 'template_name': 'tools/developer/color-converter.html', 'tags': 'color,hex,rgb,hsl,convert,developer', 'order': 30, 'is_active': True},
            {'slug': 'number-base-converter', 'name': 'Number Base Converter', 'short_desc': 'Convert numbers between binary, octal, decimal and hexadecimal.', 'icon': 'bi-123', 'template_name': 'tools/developer/number-base-converter.html', 'tags': 'binary,hex,octal,decimal,convert,developer', 'order': 31, 'is_active': True},
            {'slug': 'css-box-shadow-generator', 'name': 'CSS Box Shadow Generator', 'short_desc': 'Generate CSS box-shadow values visually with live preview.', 'icon': 'bi-square-half', 'template_name': 'tools/developer/css-box-shadow-generator.html', 'tags': 'css,box-shadow,generate,design,developer', 'order': 32, 'is_active': True},
            {'slug': 'css-border-radius-generator', 'name': 'CSS Border Radius Generator', 'short_desc': 'Generate CSS border-radius values with visual controls.', 'icon': 'bi-square-rounded', 'template_name': 'tools/developer/css-border-radius-generator.html', 'tags': 'css,border-radius,generate,design,developer', 'order': 33, 'is_active': True},
            {'slug': 'image-to-base64', 'name': 'Image to Base64', 'short_desc': 'Convert images to Base64 encoded strings for embedding in code.', 'icon': 'bi-image', 'template_name': 'tools/developer/image-to-base64.html', 'tags': 'image,base64,encode,convert,developer', 'order': 34, 'is_active': True},
            {'slug': 'toml-to-json', 'name': 'TOML to JSON Converter', 'short_desc': 'Convert TOML configuration files to JSON format.', 'icon': 'bi-arrow-left-right', 'template_name': 'tools/developer/toml-to-json.html', 'tags': 'toml,json,convert,config,developer', 'order': 35, 'is_active': True},
        ],
    },

    # =========================================================================
    # 2. STUDENT TOOLS (22 tools)
    # =========================================================================
    {
        'slug': 'student-tools',
        'name': 'Student Tools',
        'icon': 'bi-mortarboard',
        'color_from': '#F59E0B',
        'color_to': '#EF4444',
        'order': 2,
        'short_desc': 'Calculators, timers and study aids for students.',
        'tools': [
            {'slug': 'gpa-calculator', 'name': 'GPA Calculator', 'short_desc': 'Calculate your GPA from grades and credit hours.', 'icon': 'bi-calculator', 'template_name': 'tools/student/gpa-calculator.html', 'tags': 'gpa,grade,calculator,student', 'order': 1, 'is_active': True},
            {'slug': 'cgpa-calculator', 'name': 'CGPA Calculator', 'short_desc': 'Calculate cumulative GPA across multiple semesters.', 'icon': 'bi-calculator', 'template_name': 'tools/student/cgpa-calculator.html', 'tags': 'cgpa,gpa,cumulative,calculator,student', 'order': 2, 'is_active': True},
            {'slug': 'grade-predictor', 'name': 'Grade Predictor', 'short_desc': 'Predict the grade you need on your final exam to pass.', 'icon': 'bi-graph-up', 'template_name': 'tools/student/grade-predictor.html', 'tags': 'grade,predict,exam,student', 'order': 3, 'is_active': True},
            {'slug': 'word-counter', 'name': 'Word Counter', 'short_desc': 'Count words, characters, sentences and paragraphs instantly.', 'icon': 'bi-123', 'template_name': 'tools/student/word-counter.html', 'tags': 'word,count,character,student,writing', 'order': 4, 'is_active': True},
            {'slug': 'reading-time-estimator', 'name': 'Reading Time Estimator', 'short_desc': 'Estimate how long it takes to read any text at your pace.', 'icon': 'bi-clock-history', 'template_name': 'tools/student/reading-time-estimator.html', 'tags': 'reading,time,estimate,student', 'order': 5, 'is_active': True},
            {'slug': 'readability-checker', 'name': 'Readability Checker', 'short_desc': 'Check the Flesch-Kincaid readability score of your text.', 'icon': 'bi-bar-chart', 'template_name': 'tools/student/readability-checker.html', 'tags': 'readability,flesch,kincaid,student,writing', 'order': 6, 'is_active': True},
            {'slug': 'pomodoro-timer', 'name': 'Pomodoro Timer', 'short_desc': 'Stay focused with 25-minute work and 5-minute break cycles.', 'icon': 'bi-stopwatch', 'template_name': 'tools/student/pomodoro-timer.html', 'tags': 'pomodoro,timer,focus,study,student', 'order': 7, 'is_active': True},
            {'slug': 'exam-countdown', 'name': 'Exam Countdown', 'short_desc': 'Count down to your next exam date with days, hours and minutes.', 'icon': 'bi-calendar-event', 'template_name': 'tools/student/exam-countdown.html', 'tags': 'exam,countdown,date,student', 'order': 8, 'is_active': True},
            {'slug': 'flashcard-generator', 'name': 'Flashcard Generator', 'short_desc': 'Create and flip digital flashcards for studying any subject.', 'icon': 'bi-card-text', 'template_name': 'tools/student/flashcard-generator.html', 'tags': 'flashcard,study,memorize,student', 'order': 9, 'is_active': True},
            {'slug': 'timetable-generator', 'name': 'Timetable Generator', 'short_desc': 'Build a weekly study timetable and export it.', 'icon': 'bi-table', 'template_name': 'tools/student/timetable-generator.html', 'tags': 'timetable,schedule,study,student', 'order': 10, 'is_active': True},
            {'slug': 'paragraph-organizer', 'name': 'Paragraph Organizer', 'short_desc': 'Reorder and organize paragraphs by drag and drop.', 'icon': 'bi-list-ol', 'template_name': 'tools/student/paragraph-organizer.html', 'tags': 'paragraph,organize,reorder,student,writing', 'order': 11, 'is_active': True},
            {'slug': 'academic-title-generator', 'name': 'Academic Title Generator', 'short_desc': 'Generate compelling academic paper and essay titles.', 'icon': 'bi-journal-text', 'template_name': 'tools/student/academic-title-generator.html', 'tags': 'academic,title,generate,student,writing', 'order': 12, 'is_active': True},
            {'slug': 'research-topic-generator', 'name': 'Research Topic Generator', 'short_desc': 'Generate research topic ideas for any subject or discipline.', 'icon': 'bi-lightbulb', 'template_name': 'tools/student/research-topic-generator.html', 'tags': 'research,topic,idea,student', 'order': 13, 'is_active': True},
            {'slug': 'plagiarism-checklist', 'name': 'Plagiarism Checklist', 'short_desc': 'Interactive checklist to avoid plagiarism in academic work.', 'icon': 'bi-check2-square', 'template_name': 'tools/student/plagiarism-checklist.html', 'tags': 'plagiarism,checklist,academic,student', 'order': 14, 'is_active': True},
            {'slug': 'apa-citation-generator', 'name': 'APA Citation Generator', 'short_desc': 'Generate APA 7th edition citations for books, websites and journals.', 'icon': 'bi-quote', 'template_name': 'tools/student/apa-citation-generator.html', 'tags': 'apa,citation,reference,academic,student', 'order': 15, 'is_active': True},
            {'slug': 'mla-citation-generator', 'name': 'MLA Citation Generator', 'short_desc': 'Generate MLA 9th edition citations for any source type.', 'icon': 'bi-quote', 'template_name': 'tools/student/mla-citation-generator.html', 'tags': 'mla,citation,reference,academic,student', 'order': 16, 'is_active': True},
            {'slug': 'harvard-citation-generator', 'name': 'Harvard Citation Generator', 'short_desc': 'Generate Harvard style citations and references.', 'icon': 'bi-quote', 'template_name': 'tools/student/harvard-citation-generator.html', 'tags': 'harvard,citation,reference,academic,student', 'order': 17, 'is_active': True},
            {'slug': 'essay-outline-builder', 'name': 'Essay Outline Builder', 'short_desc': 'Build a structured essay outline with introduction, body and conclusion.', 'icon': 'bi-list-nested', 'template_name': 'tools/student/essay-outline-builder.html', 'tags': 'essay,outline,structure,student,writing', 'order': 18, 'is_active': True},
            {'slug': 'study-planner', 'name': 'Study Planner', 'short_desc': 'Plan your study sessions across subjects with time allocation.', 'icon': 'bi-calendar-week', 'template_name': 'tools/student/study-planner.html', 'tags': 'study,plan,schedule,student', 'order': 19, 'is_active': True},
            {'slug': 'thesis-statement-generator', 'name': 'Thesis Statement Generator', 'short_desc': 'Generate strong thesis statements for essays and research papers.', 'icon': 'bi-journal-bookmark', 'template_name': 'tools/student/thesis-statement-generator.html', 'tags': 'thesis,statement,generate,student,writing', 'order': 20, 'is_active': True},
            {'slug': 'bibliography-generator', 'name': 'Bibliography Generator', 'short_desc': 'Generate formatted bibliographies from a list of sources.', 'icon': 'bi-book', 'template_name': 'tools/student/bibliography-generator.html', 'tags': 'bibliography,reference,generate,student', 'order': 21, 'is_active': True},
            {'slug': 'assignment-word-estimator', 'name': 'Assignment Word Estimator', 'short_desc': 'Estimate how many pages your word count will fill.', 'icon': 'bi-file-earmark-ruled', 'template_name': 'tools/student/assignment-word-estimator.html', 'tags': 'word,pages,estimate,assignment,student', 'order': 22, 'is_active': True},
        ],
    },

    # =========================================================================
    # 3. WRITING TOOLS (20 tools)
    # =========================================================================
    {
        'slug': 'writing-tools',
        'name': 'Writing Tools',
        'icon': 'bi-pencil-square',
        'color_from': '#10B981',
        'color_to': '#3B82F6',
        'order': 3,
        'short_desc': 'Text transformation, cleaning and writing enhancement tools.',
        'tools': [
            {'slug': 'case-converter', 'name': 'Case Converter', 'short_desc': 'Convert text to UPPER, lower, Title, camelCase or snake_case.', 'icon': 'bi-type', 'template_name': 'tools/writing/case-converter.html', 'tags': 'case,convert,upper,lower,title,writing', 'order': 1, 'is_active': True},
            {'slug': 'fancy-text-generator', 'name': 'Fancy Text Generator', 'short_desc': 'Generate stylish Unicode text styles for social media bios.', 'icon': 'bi-fonts', 'template_name': 'tools/writing/fancy-text-generator.html', 'tags': 'fancy,text,unicode,style,writing', 'order': 2, 'is_active': True},
            {'slug': 'unicode-text-styles', 'name': 'Unicode Text Styles', 'short_desc': 'Apply bold, italic, strikethrough and other Unicode text styles.', 'icon': 'bi-type-bold', 'template_name': 'tools/writing/unicode-text-styles.html', 'tags': 'unicode,bold,italic,style,writing', 'order': 3, 'is_active': True},
            {'slug': 'duplicate-remover', 'name': 'Duplicate Line Remover', 'short_desc': 'Remove duplicate lines from any text instantly.', 'icon': 'bi-subtract', 'template_name': 'tools/writing/duplicate-remover.html', 'tags': 'duplicate,remove,lines,text,writing', 'order': 4, 'is_active': True},
            {'slug': 'keyword-density', 'name': 'Keyword Density Checker', 'short_desc': 'Analyse keyword frequency and density in your text.', 'icon': 'bi-bar-chart-line', 'template_name': 'tools/writing/keyword-density.html', 'tags': 'keyword,density,frequency,seo,writing', 'order': 5, 'is_active': True},
            {'slug': 'headline-generator', 'name': 'Headline Generator', 'short_desc': 'Generate attention-grabbing headlines for your content.', 'icon': 'bi-newspaper', 'template_name': 'tools/writing/headline-generator.html', 'tags': 'headline,title,generate,writing', 'order': 6, 'is_active': True},
            {'slug': 'sentence-shortener', 'name': 'Sentence Shortener', 'short_desc': 'Shorten long sentences for clearer, more readable writing.', 'icon': 'bi-scissors', 'template_name': 'tools/writing/sentence-shortener.html', 'tags': 'sentence,shorten,simplify,writing', 'order': 7, 'is_active': True},
            {'slug': 'text-cleaner', 'name': 'Text Cleaner', 'short_desc': 'Remove extra spaces, special characters and unwanted formatting.', 'icon': 'bi-eraser', 'template_name': 'tools/writing/text-cleaner.html', 'tags': 'text,clean,remove,format,writing', 'order': 8, 'is_active': True},
            {'slug': 'passive-active-converter', 'name': 'Passive to Active Converter', 'short_desc': 'Identify passive voice sentences and suggest active alternatives.', 'icon': 'bi-arrow-repeat', 'template_name': 'tools/writing/passive-active-converter.html', 'tags': 'passive,active,voice,convert,writing', 'order': 9, 'is_active': True},
            {'slug': 'readability-improver', 'name': 'Readability Improver', 'short_desc': 'Get actionable suggestions to improve your text readability score.', 'icon': 'bi-graph-up-arrow', 'template_name': 'tools/writing/readability-improver.html', 'tags': 'readability,improve,score,writing', 'order': 10, 'is_active': True},
            {'slug': 'text-simplifier', 'name': 'Text Simplifier', 'short_desc': 'Simplify complex text into plain, easy-to-understand language.', 'icon': 'bi-chat-square-text', 'template_name': 'tools/writing/text-simplifier.html', 'tags': 'simplify,text,plain,language,writing', 'order': 11, 'is_active': True},
            {'slug': 'paragraph-expander', 'name': 'Paragraph Expander', 'short_desc': 'Expand short paragraphs into fuller, more detailed content.', 'icon': 'bi-arrows-expand', 'template_name': 'tools/writing/paragraph-expander.html', 'tags': 'paragraph,expand,writing,content', 'order': 12, 'is_active': True},
            {'slug': 'introduction-generator', 'name': 'Introduction Generator', 'short_desc': 'Generate compelling introductions for essays and articles.', 'icon': 'bi-play-circle', 'template_name': 'tools/writing/introduction-generator.html', 'tags': 'introduction,generate,essay,writing', 'order': 13, 'is_active': True},
            {'slug': 'conclusion-generator', 'name': 'Conclusion Generator', 'short_desc': 'Generate strong conclusions for essays and articles.', 'icon': 'bi-stop-circle', 'template_name': 'tools/writing/conclusion-generator.html', 'tags': 'conclusion,generate,essay,writing', 'order': 14, 'is_active': True},
            {'slug': 'email-subject-generator', 'name': 'Email Subject Line Generator', 'short_desc': 'Generate high open-rate email subject lines for any campaign.', 'icon': 'bi-envelope', 'template_name': 'tools/writing/email-subject-generator.html', 'tags': 'email,subject,generate,marketing,writing', 'order': 15, 'is_active': True},
            {'slug': 'bullet-point-generator', 'name': 'Bullet Point Generator', 'short_desc': 'Convert paragraphs into clean, scannable bullet points.', 'icon': 'bi-list-ul', 'template_name': 'tools/writing/bullet-point-generator.html', 'tags': 'bullet,point,list,convert,writing', 'order': 16, 'is_active': True},
            {'slug': 'text-reverser', 'name': 'Text Reverser', 'short_desc': 'Reverse text, words or sentences instantly.', 'icon': 'bi-arrow-left-right', 'template_name': 'tools/writing/text-reverser.html', 'tags': 'reverse,text,mirror,writing', 'order': 17, 'is_active': True},
            {'slug': 'random-sentence-generator', 'name': 'Random Sentence Generator', 'short_desc': 'Generate random sentences for writing prompts and practice.', 'icon': 'bi-shuffle', 'template_name': 'tools/writing/random-sentence-generator.html', 'tags': 'random,sentence,generate,writing,prompt', 'order': 18, 'is_active': True},
            {'slug': 'story-hook-generator', 'name': 'Story Hook Generator', 'short_desc': 'Generate compelling opening hooks for stories and articles.', 'icon': 'bi-lightning-charge', 'template_name': 'tools/writing/story-hook-generator.html', 'tags': 'story,hook,opening,generate,writing', 'order': 19, 'is_active': True},
            {'slug': 'text-to-speech-formatter', 'name': 'Text to Speech Formatter', 'short_desc': 'Format text for optimal text-to-speech reading with pauses and emphasis.', 'icon': 'bi-mic', 'template_name': 'tools/writing/text-to-speech-formatter.html', 'tags': 'text,speech,format,tts,writing', 'order': 20, 'is_active': True},
        ],
    },

    # =========================================================================
    # 4. UTILITY TOOLS (25 tools)
    # =========================================================================
    {
        'slug': 'utility-tools',
        'name': 'Utility Tools',
        'icon': 'bi-tools',
        'color_from': '#8B5CF6',
        'color_to': '#EC4899',
        'order': 4,
        'short_desc': 'Everyday calculators, converters and productivity utilities.',
        'tools': [
            {'slug': 'unit-converter', 'name': 'Unit Converter', 'short_desc': 'Convert length, weight, temperature, volume and speed units.', 'icon': 'bi-arrow-left-right', 'template_name': 'tools/utility/unit-converter.html', 'tags': 'unit,convert,length,weight,temperature,utility', 'order': 1, 'is_active': True},
            {'slug': 'age-calculator', 'name': 'Age Calculator', 'short_desc': 'Calculate exact age in years, months and days from a birthdate.', 'icon': 'bi-calendar3', 'template_name': 'tools/utility/age-calculator.html', 'tags': 'age,calculate,birthday,date,utility', 'order': 2, 'is_active': True},
            {'slug': 'percentage-calculator', 'name': 'Percentage Calculator', 'short_desc': 'Calculate percentages, increases, decreases and differences.', 'icon': 'bi-percent', 'template_name': 'tools/utility/percentage-calculator.html', 'tags': 'percentage,calculate,math,utility', 'order': 3, 'is_active': True},
            {'slug': 'emi-calculator', 'name': 'EMI Calculator', 'short_desc': 'Calculate monthly loan EMI with amortization schedule.', 'icon': 'bi-cash-coin', 'template_name': 'tools/utility/emi-calculator.html', 'tags': 'emi,loan,payment,finance,utility', 'order': 4, 'is_active': True},
            {'slug': 'tax-calculator', 'name': 'Tax Calculator', 'short_desc': 'Estimate income tax based on earnings and deductions.', 'icon': 'bi-receipt', 'template_name': 'tools/utility/tax-calculator.html', 'tags': 'tax,income,calculate,finance,utility', 'order': 5, 'is_active': True},
            {'slug': 'bmi-calculator', 'name': 'BMI Calculator', 'short_desc': 'Calculate Body Mass Index with metric and imperial units.', 'icon': 'bi-person', 'template_name': 'tools/utility/bmi-calculator.html', 'tags': 'bmi,body,mass,index,health,utility', 'order': 6, 'is_active': True},
            {'slug': 'timezone-converter', 'name': 'Timezone Converter', 'short_desc': 'Convert times between any two time zones worldwide.', 'icon': 'bi-globe', 'template_name': 'tools/utility/timezone-converter.html', 'tags': 'timezone,convert,time,world,utility', 'order': 7, 'is_active': True},
            {'slug': 'countdown-timer', 'name': 'Countdown Timer', 'short_desc': 'Set a countdown to any future date or time with alerts.', 'icon': 'bi-hourglass-split', 'template_name': 'tools/utility/countdown-timer.html', 'tags': 'countdown,timer,date,utility', 'order': 8, 'is_active': True},
            {'slug': 'stopwatch', 'name': 'Stopwatch', 'short_desc': 'Online stopwatch with lap times and millisecond precision.', 'icon': 'bi-stopwatch', 'template_name': 'tools/utility/stopwatch.html', 'tags': 'stopwatch,timer,lap,utility', 'order': 9, 'is_active': True},
            {'slug': 'password-generator', 'name': 'Password Generator', 'short_desc': 'Generate strong, random passwords with custom rules.', 'icon': 'bi-key', 'template_name': 'tools/utility/password-generator.html', 'tags': 'password,generate,random,secure,utility', 'order': 10, 'is_active': True},
            {'slug': 'password-strength-checker', 'name': 'Password Strength Checker', 'short_desc': 'Check how strong your password is with entropy analysis.', 'icon': 'bi-shield-check', 'template_name': 'tools/utility/password-strength-checker.html', 'tags': 'password,strength,check,secure,utility', 'order': 11, 'is_active': True},
            {'slug': 'online-notepad', 'name': 'Online Notepad', 'short_desc': 'A distraction-free notepad that auto-saves to your browser.', 'icon': 'bi-journal', 'template_name': 'tools/utility/online-notepad.html', 'tags': 'notepad,note,save,browser,utility', 'order': 12, 'is_active': True},
            {'slug': 'clipboard-utility', 'name': 'Clipboard Manager', 'short_desc': 'Store and manage multiple clipboard entries in one place.', 'icon': 'bi-clipboard', 'template_name': 'tools/utility/clipboard-utility.html', 'tags': 'clipboard,copy,paste,utility', 'order': 13, 'is_active': True},
            {'slug': 'random-picker', 'name': 'Random Picker', 'short_desc': 'Pick a random item from a list — for decisions, giveaways and more.', 'icon': 'bi-shuffle', 'template_name': 'tools/utility/random-picker.html', 'tags': 'random,pick,choose,list,utility', 'order': 14, 'is_active': True},
            {'slug': 'dice-generator', 'name': 'Dice Roller', 'short_desc': 'Roll virtual dice with any number of sides and quantity.', 'icon': 'bi-dice-5', 'template_name': 'tools/utility/dice-generator.html', 'tags': 'dice,roll,random,game,utility', 'order': 15, 'is_active': True},
            {'slug': 'date-calculator', 'name': 'Date Calculator', 'short_desc': 'Calculate the difference between two dates or add/subtract days.', 'icon': 'bi-calendar-range', 'template_name': 'tools/utility/date-calculator.html', 'tags': 'date,calculate,difference,days,utility', 'order': 16, 'is_active': True},
            {'slug': 'tip-calculator', 'name': 'Tip Calculator', 'short_desc': 'Calculate tips and split bills between any number of people.', 'icon': 'bi-cash-stack', 'template_name': 'tools/utility/tip-calculator.html', 'tags': 'tip,bill,split,calculate,utility', 'order': 17, 'is_active': True},
            {'slug': 'loan-calculator', 'name': 'Loan Calculator', 'short_desc': 'Calculate total loan cost, interest and monthly payments.', 'icon': 'bi-bank', 'template_name': 'tools/utility/loan-calculator.html', 'tags': 'loan,interest,calculate,finance,utility', 'order': 18, 'is_active': True},
            {'slug': 'compound-interest-calculator', 'name': 'Compound Interest Calculator', 'short_desc': 'Calculate compound interest growth over time with charts.', 'icon': 'bi-graph-up', 'template_name': 'tools/utility/compound-interest-calculator.html', 'tags': 'compound,interest,investment,calculate,utility', 'order': 19, 'is_active': True},
            {'slug': 'calorie-calculator', 'name': 'Calorie Calculator', 'short_desc': 'Calculate daily calorie needs based on age, weight and activity.', 'icon': 'bi-heart-pulse', 'template_name': 'tools/utility/calorie-calculator.html', 'tags': 'calorie,health,calculate,diet,utility', 'order': 20, 'is_active': True},
            {'slug': 'currency-converter', 'name': 'Currency Converter', 'short_desc': 'Convert between major world currencies with live rates.', 'icon': 'bi-currency-exchange', 'template_name': 'tools/utility/currency-converter.html', 'tags': 'currency,convert,exchange,money,utility', 'order': 21, 'is_active': True},
            {'slug': 'scientific-calculator', 'name': 'Scientific Calculator', 'short_desc': 'Full-featured scientific calculator with trigonometry and logarithms.', 'icon': 'bi-calculator-fill', 'template_name': 'tools/utility/scientific-calculator.html', 'tags': 'scientific,calculator,math,trig,utility', 'order': 22, 'is_active': True},
            {'slug': 'number-to-words', 'name': 'Number to Words Converter', 'short_desc': 'Convert numbers to words in English for cheques and documents.', 'icon': 'bi-123', 'template_name': 'tools/utility/number-to-words.html', 'tags': 'number,words,convert,cheque,utility', 'order': 23, 'is_active': True},
            {'slug': 'roman-numeral-converter', 'name': 'Roman Numeral Converter', 'short_desc': 'Convert between Arabic numbers and Roman numerals.', 'icon': 'bi-fonts', 'template_name': 'tools/utility/roman-numeral-converter.html', 'tags': 'roman,numeral,convert,number,utility', 'order': 24, 'is_active': True},
            {'slug': 'aspect-ratio-calculator', 'name': 'Aspect Ratio Calculator', 'short_desc': 'Calculate and maintain aspect ratios for images and videos.', 'icon': 'bi-aspect-ratio', 'template_name': 'tools/utility/aspect-ratio-calculator.html', 'tags': 'aspect,ratio,calculate,image,video,utility', 'order': 25, 'is_active': True},
        ],
    },

    # =========================================================================
    # 5. SOCIAL & VIRAL TOOLS (14 tools)
    # =========================================================================
    {
        'slug': 'social-viral-tools',
        'name': 'Social & Viral Tools',
        'icon': 'bi-share',
        'color_from': '#F97316',
        'color_to': '#FBBF24',
        'order': 5,
        'short_desc': 'Fun generators and social media content tools.',
        'tools': [
            {'slug': 'fake-chat-generator', 'name': 'Fake Chat Generator', 'short_desc': 'Create fake iMessage-style chat conversation screenshots.', 'icon': 'bi-chat-dots', 'template_name': 'tools/social/fake-chat-generator.html', 'tags': 'fake,chat,conversation,imessage,social', 'order': 1, 'is_active': True},
            {'slug': 'fake-tweet-generator', 'name': 'Fake Tweet Generator', 'short_desc': 'Create a realistic-looking fake tweet card for any username.', 'icon': 'bi-twitter', 'template_name': 'tools/social/fake-tweet-generator.html', 'tags': 'fake,tweet,twitter,social', 'order': 2, 'is_active': True},
            {'slug': 'meme-caption-generator', 'name': 'Meme Caption Generator', 'short_desc': 'Generate funny meme captions from popular templates.', 'icon': 'bi-emoji-laughing', 'template_name': 'tools/social/meme-caption-generator.html', 'tags': 'meme,caption,funny,social', 'order': 3, 'is_active': True},
            {'slug': 'aesthetic-font-generator', 'name': 'Aesthetic Font Generator', 'short_desc': 'Generate aesthetic Unicode fonts for Instagram bios and posts.', 'icon': 'bi-fonts', 'template_name': 'tools/social/aesthetic-font-generator.html', 'tags': 'aesthetic,font,unicode,instagram,social', 'order': 4, 'is_active': True},
            {'slug': 'emoji-combiner', 'name': 'Emoji Combiner', 'short_desc': 'Combine emojis to create unique emoji art and sequences.', 'icon': 'bi-emoji-smile', 'template_name': 'tools/social/emoji-combiner.html', 'tags': 'emoji,combine,art,social', 'order': 5, 'is_active': True},
            {'slug': 'nickname-generator', 'name': 'Nickname Generator', 'short_desc': 'Generate creative nicknames and usernames for any platform.', 'icon': 'bi-person-badge', 'template_name': 'tools/social/nickname-generator.html', 'tags': 'nickname,username,generate,social', 'order': 6, 'is_active': True},
            {'slug': 'pickup-line-generator', 'name': 'Pickup Line Generator', 'short_desc': 'Generate funny and cheesy pickup lines for any occasion.', 'icon': 'bi-heart', 'template_name': 'tools/social/pickup-line-generator.html', 'tags': 'pickup,line,funny,social', 'order': 7, 'is_active': True},
            {'slug': 'roast-generator', 'name': 'Roast Generator', 'short_desc': 'Generate playful, funny roasts for friends.', 'icon': 'bi-fire', 'template_name': 'tools/social/roast-generator.html', 'tags': 'roast,funny,social', 'order': 8, 'is_active': True},
            {'slug': 'random-comment-generator', 'name': 'Random Comment Generator', 'short_desc': 'Generate random social media comments for any post type.', 'icon': 'bi-chat-square', 'template_name': 'tools/social/random-comment-generator.html', 'tags': 'comment,random,social,generate', 'order': 9, 'is_active': True},
            {'slug': 'fake-instagram-post', 'name': 'Fake Instagram Post Generator', 'short_desc': 'Create a realistic fake Instagram post card with likes and caption.', 'icon': 'bi-instagram', 'template_name': 'tools/social/fake-instagram-post.html', 'tags': 'fake,instagram,post,social', 'order': 10, 'is_active': True},
            {'slug': 'twitter-thread-formatter', 'name': 'Twitter Thread Formatter', 'short_desc': 'Format long text into numbered Twitter/X thread posts.', 'icon': 'bi-list-ol', 'template_name': 'tools/social/twitter-thread-formatter.html', 'tags': 'twitter,thread,format,social', 'order': 11, 'is_active': True},
            {'slug': 'hashtag-generator', 'name': 'Hashtag Generator', 'short_desc': 'Generate relevant hashtags for Instagram, TikTok and Twitter posts.', 'icon': 'bi-hash', 'template_name': 'tools/social/hashtag-generator.html', 'tags': 'hashtag,generate,instagram,tiktok,social', 'order': 12, 'is_active': True},
            {'slug': 'social-media-bio-generator', 'name': 'Social Media Bio Generator', 'short_desc': 'Generate catchy bios for Instagram, Twitter and TikTok profiles.', 'icon': 'bi-person-circle', 'template_name': 'tools/social/social-media-bio-generator.html', 'tags': 'bio,generate,instagram,twitter,social', 'order': 13, 'is_active': True},
            {'slug': 'caption-length-checker', 'name': 'Caption Length Checker', 'short_desc': 'Check if your caption fits within platform character limits.', 'icon': 'bi-rulers', 'template_name': 'tools/social/caption-length-checker.html', 'tags': 'caption,length,check,social,character', 'order': 14, 'is_active': True},
        ],
    },

    # =========================================================================
    # 6. SEO TOOLS (18 tools)
    # =========================================================================
    {
        'slug': 'seo-tools',
        'name': 'SEO Tools',
        'icon': 'bi-search',
        'color_from': '#0EA5E9',
        'color_to': '#6366F1',
        'order': 6,
        'short_desc': 'Meta tags, schema markup and on-page SEO utilities.',
        'tools': [
            {'slug': 'meta-title-generator', 'name': 'Meta Title Generator', 'short_desc': 'Generate optimised meta titles under 60 characters for any keyword.', 'icon': 'bi-type-h1', 'template_name': 'tools/seo_tools/meta-title-generator.html', 'tags': 'meta,title,seo,generate', 'order': 1, 'is_active': True},
            {'slug': 'meta-description-generator', 'name': 'Meta Description Generator', 'short_desc': 'Generate compelling meta descriptions under 160 characters.', 'icon': 'bi-card-text', 'template_name': 'tools/seo_tools/meta-description-generator.html', 'tags': 'meta,description,seo,generate', 'order': 2, 'is_active': True},
            {'slug': 'slug-generator', 'name': 'Slug Generator', 'short_desc': 'Convert any text into a clean, SEO-friendly URL slug.', 'icon': 'bi-link', 'template_name': 'tools/seo_tools/slug-generator.html', 'tags': 'slug,url,seo,generate', 'order': 3, 'is_active': True},
            {'slug': 'serp-preview', 'name': 'SERP Preview Tool', 'short_desc': 'Preview how your page looks in Google search results.', 'icon': 'bi-google', 'template_name': 'tools/seo_tools/serp-preview.html', 'tags': 'serp,preview,google,seo', 'order': 4, 'is_active': True},
            {'slug': 'keyword-density-analyzer', 'name': 'Keyword Density Analyzer', 'short_desc': 'Analyse keyword density and frequency in your content.', 'icon': 'bi-bar-chart', 'template_name': 'tools/seo_tools/keyword-density-analyzer.html', 'tags': 'keyword,density,analyze,seo', 'order': 5, 'is_active': True},
            {'slug': 'opengraph-generator', 'name': 'OpenGraph Tag Generator', 'short_desc': 'Generate Open Graph meta tags for social sharing previews.', 'icon': 'bi-share', 'template_name': 'tools/seo_tools/opengraph-generator.html', 'tags': 'opengraph,og,meta,social,seo', 'order': 6, 'is_active': True},
            {'slug': 'twitter-card-generator', 'name': 'Twitter Card Generator', 'short_desc': 'Generate Twitter Card meta tags for rich link previews.', 'icon': 'bi-twitter', 'template_name': 'tools/seo_tools/twitter-card-generator.html', 'tags': 'twitter,card,meta,seo', 'order': 7, 'is_active': True},
            {'slug': 'schema-markup-generator', 'name': 'Schema Markup Generator', 'short_desc': 'Generate JSON-LD schema markup for Article, Product and more.', 'icon': 'bi-code-square', 'template_name': 'tools/seo_tools/schema-markup-generator.html', 'tags': 'schema,json-ld,markup,seo', 'order': 8, 'is_active': True},
            {'slug': 'faq-schema-generator', 'name': 'FAQ Schema Generator', 'short_desc': 'Generate FAQPage JSON-LD schema markup for rich results.', 'icon': 'bi-question-circle', 'template_name': 'tools/seo_tools/faq-schema-generator.html', 'tags': 'faq,schema,json-ld,seo', 'order': 9, 'is_active': True},
            {'slug': 'breadcrumb-schema-generator', 'name': 'Breadcrumb Schema Generator', 'short_desc': 'Generate BreadcrumbList JSON-LD schema markup.', 'icon': 'bi-chevron-right', 'template_name': 'tools/seo_tools/breadcrumb-schema-generator.html', 'tags': 'breadcrumb,schema,json-ld,seo', 'order': 10, 'is_active': True},
            {'slug': 'sitemap-builder', 'name': 'XML Sitemap Builder', 'short_desc': 'Build an XML sitemap for your website with priority settings.', 'icon': 'bi-diagram-3', 'template_name': 'tools/seo_tools/sitemap-builder.html', 'tags': 'sitemap,xml,seo,build', 'order': 11, 'is_active': True},
            {'slug': 'robots-txt-builder', 'name': 'robots.txt Builder', 'short_desc': 'Build a robots.txt file with rules for specific crawlers.', 'icon': 'bi-robot', 'template_name': 'tools/seo_tools/robots-txt-builder.html', 'tags': 'robots,txt,crawl,seo,build', 'order': 12, 'is_active': True},
            {'slug': 'canonical-url-generator', 'name': 'Canonical URL Generator', 'short_desc': 'Generate canonical link tags to prevent duplicate content issues.', 'icon': 'bi-link-45deg', 'template_name': 'tools/seo_tools/canonical-url-generator.html', 'tags': 'canonical,url,duplicate,seo', 'order': 13, 'is_active': True},
            {'slug': 'hreflang-generator', 'name': 'Hreflang Tag Generator', 'short_desc': 'Generate hreflang tags for multilingual and regional SEO.', 'icon': 'bi-globe', 'template_name': 'tools/seo_tools/hreflang-generator.html', 'tags': 'hreflang,international,seo,multilingual', 'order': 14, 'is_active': True},
            {'slug': 'word-count-seo-checker', 'name': 'SEO Word Count Checker', 'short_desc': 'Check if your content meets recommended word count for SEO.', 'icon': 'bi-file-earmark-text', 'template_name': 'tools/seo_tools/word-count-seo-checker.html', 'tags': 'word,count,seo,content,check', 'order': 15, 'is_active': True},
            {'slug': 'internal-link-suggester', 'name': 'Internal Link Suggester', 'short_desc': 'Suggest internal linking opportunities from a list of URLs and keywords.', 'icon': 'bi-diagram-2', 'template_name': 'tools/seo_tools/internal-link-suggester.html', 'tags': 'internal,link,suggest,seo', 'order': 16, 'is_active': True},
            {'slug': 'page-speed-advisor', 'name': 'Page Speed Advisor', 'short_desc': 'Get actionable tips to improve your page speed and Core Web Vitals.', 'icon': 'bi-speedometer2', 'template_name': 'tools/seo_tools/page-speed-advisor.html', 'tags': 'page,speed,core,web,vitals,seo', 'order': 17, 'is_active': True},
            {'slug': 'anchor-text-generator', 'name': 'Anchor Text Generator', 'short_desc': 'Generate SEO-optimised anchor text variations for link building.', 'icon': 'bi-cursor-text', 'template_name': 'tools/seo_tools/anchor-text-generator.html', 'tags': 'anchor,text,link,seo,generate', 'order': 18, 'is_active': True},
        ],
    },

    # =========================================================================
    # 7. IMAGE TOOLS (20 tools)
    # =========================================================================
    {
        'slug': 'image-tools',
        'name': 'Image Tools',
        'icon': 'bi-image',
        'color_from': '#EC4899',
        'color_to': '#F59E0B',
        'order': 7,
        'short_desc': 'Compress, convert, resize and edit images in your browser.',
        'tools': [
            {'slug': 'image-compressor', 'name': 'Image Compressor', 'short_desc': 'Compress JPG, PNG and WebP images without visible quality loss.', 'icon': 'bi-file-zip', 'template_name': 'tools/image/image-compressor.html', 'tags': 'image,compress,optimize,jpg,png', 'order': 1, 'is_active': True},
            {'slug': 'webp-converter', 'name': 'WebP Converter', 'short_desc': 'Convert images to and from WebP format for faster web loading.', 'icon': 'bi-arrow-left-right', 'template_name': 'tools/image/webp-converter.html', 'tags': 'webp,convert,image,format', 'order': 2, 'is_active': True},
            {'slug': 'jpg-to-png', 'name': 'JPG to PNG Converter', 'short_desc': 'Convert JPG images to PNG format with transparency support.', 'icon': 'bi-file-image', 'template_name': 'tools/image/jpg-to-png.html', 'tags': 'jpg,png,convert,image', 'order': 3, 'is_active': True},
            {'slug': 'png-to-jpg', 'name': 'PNG to JPG Converter', 'short_desc': 'Convert PNG images to JPG format with quality control.', 'icon': 'bi-file-image', 'template_name': 'tools/image/png-to-jpg.html', 'tags': 'png,jpg,convert,image', 'order': 4, 'is_active': True},
            {'slug': 'image-resize', 'name': 'Image Resize', 'short_desc': 'Resize images to exact dimensions or by percentage.', 'icon': 'bi-aspect-ratio', 'template_name': 'tools/image/image-resize.html', 'tags': 'image,resize,dimensions,width,height', 'order': 5, 'is_active': True},
            {'slug': 'image-crop', 'name': 'Image Crop', 'short_desc': 'Crop images to any size or aspect ratio with a visual editor.', 'icon': 'bi-crop', 'template_name': 'tools/image/image-crop.html', 'tags': 'image,crop,cut,aspect,ratio', 'order': 6, 'is_active': True},
            {'slug': 'image-rotate', 'name': 'Image Rotate & Flip', 'short_desc': 'Rotate images 90°/180°/270° and flip horizontally or vertically.', 'icon': 'bi-arrow-clockwise', 'template_name': 'tools/image/image-rotate.html', 'tags': 'image,rotate,flip,mirror', 'order': 7, 'is_active': True},
            {'slug': 'image-blur', 'name': 'Image Blur', 'short_desc': 'Apply Gaussian blur effects to images with adjustable intensity.', 'icon': 'bi-droplet-half', 'template_name': 'tools/image/image-blur.html', 'tags': 'image,blur,effect,filter', 'order': 8, 'is_active': True},
            {'slug': 'image-watermark', 'name': 'Image Watermark', 'short_desc': 'Add text or image watermarks to photos with position control.', 'icon': 'bi-shield-shaded', 'template_name': 'tools/image/image-watermark.html', 'tags': 'image,watermark,text,protect', 'order': 9, 'is_active': True},
            {'slug': 'meme-generator', 'name': 'Meme Generator', 'short_desc': 'Create memes with custom top and bottom text on any image.', 'icon': 'bi-emoji-laughing', 'template_name': 'tools/image/meme-generator.html', 'tags': 'meme,generate,image,text,funny', 'order': 10, 'is_active': True},
            {'slug': 'qr-generator', 'name': 'QR Code Generator', 'short_desc': 'Generate QR codes for URLs, text, WiFi and contact cards.', 'icon': 'bi-qr-code', 'template_name': 'tools/image/qr-generator.html', 'tags': 'qr,code,generate,barcode', 'order': 11, 'is_active': True},
            {'slug': 'barcode-generator', 'name': 'Barcode Generator', 'short_desc': 'Generate barcodes in Code128, EAN-13, UPC-A and other formats.', 'icon': 'bi-upc-scan', 'template_name': 'tools/image/barcode-generator.html', 'tags': 'barcode,generate,upc,ean,code128', 'order': 12, 'is_active': True},
            {'slug': 'favicon-generator', 'name': 'Favicon Generator', 'short_desc': 'Generate favicons in all required sizes from any image.', 'icon': 'bi-star', 'template_name': 'tools/image/favicon-generator.html', 'tags': 'favicon,icon,generate,image', 'order': 13, 'is_active': True},
            {'slug': 'color-extractor', 'name': 'Color Extractor', 'short_desc': 'Extract dominant colors from any image with hex codes.', 'icon': 'bi-eyedropper', 'template_name': 'tools/image/color-extractor.html', 'tags': 'color,extract,palette,image', 'order': 14, 'is_active': True},
            {'slug': 'palette-generator', 'name': 'Color Palette Generator', 'short_desc': 'Generate harmonious color palettes from a base color.', 'icon': 'bi-palette2', 'template_name': 'tools/image/palette-generator.html', 'tags': 'palette,color,generate,design', 'order': 15, 'is_active': True},
            {'slug': 'image-to-base64-converter', 'name': 'Image to Base64 Converter', 'short_desc': 'Convert images to Base64 data URIs for embedding in HTML and CSS.', 'icon': 'bi-code', 'template_name': 'tools/image/image-to-base64-converter.html', 'tags': 'image,base64,convert,embed,developer', 'order': 16, 'is_active': True},
            {'slug': 'svg-optimizer', 'name': 'SVG Optimizer', 'short_desc': 'Optimize and minify SVG files to reduce file size.', 'icon': 'bi-vector-pen', 'template_name': 'tools/image/svg-optimizer.html', 'tags': 'svg,optimize,minify,vector,image', 'order': 17, 'is_active': True},
            {'slug': 'image-brightness-contrast', 'name': 'Image Brightness & Contrast', 'short_desc': 'Adjust brightness, contrast and saturation of images online.', 'icon': 'bi-sun', 'template_name': 'tools/image/image-brightness-contrast.html', 'tags': 'image,brightness,contrast,saturation,edit', 'order': 18, 'is_active': True},
            {'slug': 'image-grayscale', 'name': 'Image Grayscale Converter', 'short_desc': 'Convert color images to grayscale or black and white.', 'icon': 'bi-circle-half', 'template_name': 'tools/image/image-grayscale.html', 'tags': 'image,grayscale,black,white,convert', 'order': 19, 'is_active': True},
            {'slug': 'screenshot-to-pdf', 'name': 'Screenshot to PDF', 'short_desc': 'Convert multiple screenshots or images into a single PDF.', 'icon': 'bi-file-earmark-pdf', 'template_name': 'tools/image/screenshot-to-pdf.html', 'tags': 'screenshot,pdf,convert,image', 'order': 20, 'is_active': True},
            {'slug': 'image-enhancer', 'name': 'AI Image Enhancer', 'short_desc': 'Enhance image clarity, sharpness and visual quality online.', 'icon': 'bi-magic', 'template_name': 'tools/image/image-enhancer.html', 'tags': 'image,enhance,quality,sharpness,ai', 'order': 20, 'is_active': True},
        ],
    },

    # =========================================================================
    # 8. PDF & FILE TOOLS (16 tools)
    # =========================================================================
    {
        'slug': 'pdf-file-tools',
        'name': 'PDF & File Tools',
        'icon': 'bi-file-earmark-pdf',
        'color_from': '#EF4444',
        'color_to': '#F97316',
        'order': 8,
        'short_desc': 'Merge, split, compress and convert PDF and file formats.',
        'tools': [
            {'slug': 'pdf-merge', 'name': 'PDF Merge', 'short_desc': 'Merge multiple PDF files into one document.', 'icon': 'bi-files', 'template_name': 'tools/pdf/pdf-merge.html', 'tags': 'pdf,merge,combine,file', 'order': 1, 'is_active': True},
            {'slug': 'pdf-split', 'name': 'PDF Split', 'short_desc': 'Split a PDF into individual pages or custom page ranges.', 'icon': 'bi-scissors', 'template_name': 'tools/pdf/pdf-split.html', 'tags': 'pdf,split,extract,pages,file', 'order': 2, 'is_active': True},
            {'slug': 'image-to-pdf', 'name': 'Image to PDF', 'short_desc': 'Convert one or multiple images into a PDF document.', 'icon': 'bi-file-earmark-image', 'template_name': 'tools/pdf/image-to-pdf.html', 'tags': 'image,pdf,convert,jpg,png', 'order': 3, 'is_active': True},
            {'slug': 'pdf-to-image', 'name': 'PDF to Image', 'short_desc': 'Convert PDF pages to high-quality JPG or PNG images.', 'icon': 'bi-file-earmark-break', 'template_name': 'tools/pdf/pdf-to-image.html', 'tags': 'pdf,image,convert,jpg,png', 'order': 4, 'is_active': True},
            {'slug': 'pdf-compressor', 'name': 'PDF Compressor', 'short_desc': 'Reduce PDF file size while preserving readability.', 'icon': 'bi-file-zip', 'template_name': 'tools/pdf/pdf-compressor.html', 'tags': 'pdf,compress,reduce,size,file', 'order': 5, 'is_active': True},
            {'slug': 'pdf-text-extractor', 'name': 'PDF Text Extractor', 'short_desc': 'Extract all text content from PDF files instantly.', 'icon': 'bi-file-earmark-text', 'template_name': 'tools/pdf/pdf-text-extractor.html', 'tags': 'pdf,text,extract,file', 'order': 6, 'is_active': True},
            {'slug': 'zip-extractor', 'name': 'ZIP Extractor', 'short_desc': 'Extract and preview files from ZIP archives online.', 'icon': 'bi-file-zip', 'template_name': 'tools/pdf/zip-extractor.html', 'tags': 'zip,extract,archive,file', 'order': 7, 'is_active': True},
            {'slug': 'csv-viewer', 'name': 'CSV Viewer', 'short_desc': 'View, sort and filter CSV files in a clean table format.', 'icon': 'bi-table', 'template_name': 'tools/pdf/csv-viewer.html', 'tags': 'csv,view,table,file', 'order': 8, 'is_active': True},
            {'slug': 'file-rename-utility', 'name': 'File Rename Utility', 'short_desc': 'Batch rename files with patterns, numbering and rules.', 'icon': 'bi-pencil', 'template_name': 'tools/pdf/file-rename-utility.html', 'tags': 'file,rename,batch,utility', 'order': 9, 'is_active': True},
            {'slug': 'file-compare', 'name': 'File Compare', 'short_desc': 'Compare two text files and highlight differences side by side.', 'icon': 'bi-file-diff', 'template_name': 'tools/pdf/file-compare.html', 'tags': 'file,compare,diff,text', 'order': 10, 'is_active': True},
            {'slug': 'pdf-rotate', 'name': 'PDF Page Rotator', 'short_desc': 'Rotate individual pages or all pages in a PDF file.', 'icon': 'bi-arrow-clockwise', 'template_name': 'tools/pdf/pdf-rotate.html', 'tags': 'pdf,rotate,page,file', 'order': 11, 'is_active': True},
            {'slug': 'pdf-watermark', 'name': 'PDF Watermark', 'short_desc': 'Add text or image watermarks to PDF documents.', 'icon': 'bi-shield-shaded', 'template_name': 'tools/pdf/pdf-watermark.html', 'tags': 'pdf,watermark,text,protect,file', 'order': 12, 'is_active': True},
            {'slug': 'word-to-pdf', 'name': 'Word to PDF Converter', 'short_desc': 'Convert DOCX Word documents to PDF format.', 'icon': 'bi-filetype-docx', 'template_name': 'tools/pdf/word-to-pdf.html', 'tags': 'word,docx,pdf,convert,file', 'order': 13, 'is_active': True},
            {'slug': 'excel-to-csv', 'name': 'Excel to CSV Converter', 'short_desc': 'Convert Excel XLSX files to CSV format online.', 'icon': 'bi-filetype-xlsx', 'template_name': 'tools/pdf/excel-to-csv.html', 'tags': 'excel,xlsx,csv,convert,file', 'order': 14, 'is_active': True},
            {'slug': 'json-to-excel', 'name': 'JSON to Excel Converter', 'short_desc': 'Convert JSON data to Excel XLSX spreadsheet format.', 'icon': 'bi-filetype-json', 'template_name': 'tools/pdf/json-to-excel.html', 'tags': 'json,excel,xlsx,convert,file', 'order': 15, 'is_active': True},
            {'slug': 'markdown-to-pdf', 'name': 'Markdown to PDF', 'short_desc': 'Convert Markdown documents to formatted PDF files.', 'icon': 'bi-markdown', 'template_name': 'tools/pdf/markdown-to-pdf.html', 'tags': 'markdown,pdf,convert,file', 'order': 16, 'is_active': True},
        ],
    },

    # =========================================================================
    # 9. RESUME & CAREER TOOLS (14 tools)
    # =========================================================================
    {
        'slug': 'resume-career-tools',
        'name': 'Resume & Career Tools',
        'icon': 'bi-briefcase',
        'color_from': '#14B8A6',
        'color_to': '#3B82F6',
        'order': 9,
        'short_desc': 'Build resumes, cover letters and professional documents.',
        'tools': [
            {'slug': 'ai-resume-builder', 'name': 'AI Resume Builder', 'short_desc': 'Build a professional resume with AI.', 'icon': 'bi-file-person', 'template_name': 'ai_tools/resume-builder.html', 'tags': 'resume,cv,build,career,ai', 'order': 1, 'is_active': True, 'is_ai_powered': True},

            {'slug': 'ai-ats-resume-checker', 'name': 'AI ATS Resume Checker', 'short_desc': 'Check if your resume is ATS-friendly with AI.', 'icon': 'bi-check-circle', 'template_name': 'tools/ai_tools/ats-resume-checker.html', 'tags': 'ats,resume,check,career,ai', 'order': 2, 'is_active': False, 'is_ai_powered': True},
            {'slug': 'ai-cover-letter-generator', 'name': 'AI Cover Letter Generator', 'short_desc': 'Generate a cover letter with AI.', 'icon': 'bi-envelope-paper', 'template_name': 'tools/ai_tools/cover-letter-generator.html', 'tags': 'cover,letter,build,career,ai', 'order': 3, 'is_active': False, 'is_ai_powered': True},
            {'slug': 'ai-linkedin-headline-generator', 'name': 'AI LinkedIn Headline Generator', 'short_desc': 'Generate a LinkedIn headline with AI.', 'icon': 'bi-linkedin', 'template_name': 'tools/ai_tools/linkedin-headline-generator.html', 'tags': 'linkedin,headline,generate,career,ai', 'order': 4, 'is_active': False, 'is_ai_powered': True},
            {'slug': 'ai-linkedin-post-generator', 'name': 'AI LinkedIn Post Generator', 'short_desc': 'Generate a LinkedIn post with AI.', 'icon': 'bi-linkedin', 'template_name': 'tools/ai_tools/linkedin-post-generator.html', 'tags': 'linkedin,post,generate,career,ai', 'order': 5, 'is_active': False, 'is_ai_powered': True},
            {'slug': 'resume-builder', 'name': 'Resume Builder', 'short_desc': 'Build a professional resume with live preview and PDF export.', 'icon': 'bi-file-person', 'template_name': 'tools/resume/resume-builder.html', 'tags': 'resume,cv,build,career', 'order': 6, 'is_active': True},
            {'slug': 'ats-checker', 'name': 'ATS Resume Checker', 'short_desc': 'Check if your resume passes ATS keyword screening.', 'icon': 'bi-check-circle', 'template_name': 'tools/resume/ats-checker.html', 'tags': 'ats,resume,check,career', 'order': 7, 'is_active': True},
            {'slug': 'cover-letter-builder', 'name': 'Cover Letter Builder', 'short_desc': 'Write a professional cover letter with customisable templates.', 'icon': 'bi-envelope-paper', 'template_name': 'tools/resume/cover-letter-builder.html', 'tags': 'cover,letter,build,career', 'order': 8, 'is_active': True},
            {'slug': 'portfolio-generator', 'name': 'Portfolio Page Generator', 'short_desc': 'Generate a simple HTML portfolio page from your details.', 'icon': 'bi-collection', 'template_name': 'tools/resume/portfolio-generator.html', 'tags': 'portfolio,generate,career', 'order': 4, 'is_active': True},
            {'slug': 'linkedin-headline-generator', 'name': 'LinkedIn Headline Generator', 'short_desc': 'Generate compelling LinkedIn profile headlines for any role.', 'icon': 'bi-linkedin', 'template_name': 'tools/resume/linkedin-headline-generator.html', 'tags': 'linkedin,headline,generate,career', 'order': 5, 'is_active': True},
            {'slug': 'bio-generator', 'name': 'Professional Bio Generator', 'short_desc': 'Generate professional bios for websites, LinkedIn and press kits.', 'icon': 'bi-person-lines-fill', 'template_name': 'tools/resume/bio-generator.html', 'tags': 'bio,generate,profile,career', 'order': 6, 'is_active': True},
            {'slug': 'invoice-generator', 'name': 'Invoice Generator', 'short_desc': 'Create professional invoices with line items and PDF export.', 'icon': 'bi-receipt-cutoff', 'template_name': 'tools/resume/invoice-generator.html', 'tags': 'invoice,generate,pdf,freelance,career', 'order': 7, 'is_active': True},
            {'slug': 'quotation-builder', 'name': 'Quotation Builder', 'short_desc': 'Build professional quotation documents for clients.', 'icon': 'bi-file-earmark-check', 'template_name': 'tools/resume/quotation-builder.html', 'tags': 'quotation,quote,build,freelance,career', 'order': 8, 'is_active': True},
            {'slug': 'job-description-analyzer', 'name': 'Job Description Analyzer', 'short_desc': 'Extract key skills and requirements from any job description.', 'icon': 'bi-file-earmark-magnify', 'template_name': 'tools/resume/job-description-analyzer.html', 'tags': 'job,description,analyze,skills,career', 'order': 9, 'is_active': True},
            {'slug': 'resume-summary-generator', 'name': 'Resume Summary Generator', 'short_desc': 'Generate a compelling professional summary for your resume.', 'icon': 'bi-file-earmark-person', 'template_name': 'tools/resume/resume-summary-generator.html', 'tags': 'resume,summary,generate,career', 'order': 10, 'is_active': True},
            {'slug': 'skills-list-generator', 'name': 'Skills List Generator', 'short_desc': 'Generate a relevant skills list for any job role or industry.', 'icon': 'bi-stars', 'template_name': 'tools/resume/skills-list-generator.html', 'tags': 'skills,list,generate,resume,career', 'order': 11, 'is_active': True},
            {'slug': 'salary-negotiation-script', 'name': 'Salary Negotiation Script', 'short_desc': 'Generate a salary negotiation script tailored to your situation.', 'icon': 'bi-cash-coin', 'template_name': 'tools/resume/salary-negotiation-script.html', 'tags': 'salary,negotiation,script,career', 'order': 12, 'is_active': True},
            {'slug': 'interview-question-prep', 'name': 'Interview Question Prep', 'short_desc': 'Generate common interview questions for any job role.', 'icon': 'bi-question-circle', 'template_name': 'tools/resume/interview-question-prep.html', 'tags': 'interview,question,prepare,career', 'order': 13, 'is_active': True},
            {'slug': 'email-signature-generator', 'name': 'Email Signature Generator', 'short_desc': 'Create a professional HTML email signature with your details.', 'icon': 'bi-envelope-at', 'template_name': 'tools/resume/email-signature-generator.html', 'tags': 'email,signature,generate,professional,career', 'order': 14, 'is_active': True},
        ],
    },

    # =========================================================================
    # 10. ACADEMIC & WRITING (existing AI tools preserved)
    # =========================================================================
    {
        'slug': 'academic-writing',
        'name': 'Academic & Writing',
        'icon': 'bi-journal-richtext',
        'color_from': '#7C3AED',
        'color_to': '#2563EB',
        'order': 10,
        'short_desc': 'AI-powered assignment and thesis generation tools.',
        'tools': [
            {'slug': 'assignment-generator', 'name': 'Assignment Generator', 'short_desc': 'Generate structured academic assignments with AI assistance.', 'icon': 'bi-file-earmark-text', 'template_name': 'generation/index.html', 'tags': 'assignment,generate,academic,ai,writing', 'order': 1, 'is_active': True},
            {'slug': 'thesis-generator', 'name': 'Thesis Generator', 'short_desc': 'Generate comprehensive thesis documents with AI assistance.', 'icon': 'bi-journal-bookmark', 'template_name': 'thesis/index.html', 'tags': 'thesis,generate,academic,ai,writing', 'order': 2, 'is_active': True},
        ],
    },

    # =========================================================================
    # 11. MATH & SCIENCE TOOLS (20 tools) — NEW CATEGORY
    # =========================================================================
    {
        'slug': 'math-science-tools',
        'name': 'Math & Science Tools',
        'icon': 'bi-calculator',
        'color_from': '#06B6D4',
        'color_to': '#10B981',
        'order': 11,
        'short_desc': 'Calculators and solvers for mathematics and science.',
        'tools': [
            {'slug': 'quadratic-equation-solver', 'name': 'Quadratic Equation Solver', 'short_desc': 'Solve quadratic equations ax²+bx+c=0 with step-by-step working.', 'icon': 'bi-x-square', 'template_name': 'tools/math/quadratic-equation-solver.html', 'tags': 'quadratic,equation,solve,math', 'order': 1, 'is_active': True},
            {'slug': 'fraction-calculator', 'name': 'Fraction Calculator', 'short_desc': 'Add, subtract, multiply and divide fractions with simplification.', 'icon': 'bi-slash-circle', 'template_name': 'tools/math/fraction-calculator.html', 'tags': 'fraction,calculate,math', 'order': 2, 'is_active': True},
            {'slug': 'matrix-calculator', 'name': 'Matrix Calculator', 'short_desc': 'Perform matrix addition, multiplication, transpose and determinant.', 'icon': 'bi-grid-3x3', 'template_name': 'tools/math/matrix-calculator.html', 'tags': 'matrix,calculate,linear,algebra,math', 'order': 3, 'is_active': True},
            {'slug': 'statistics-calculator', 'name': 'Statistics Calculator', 'short_desc': 'Calculate mean, median, mode, variance and standard deviation.', 'icon': 'bi-bar-chart', 'template_name': 'tools/math/statistics-calculator.html', 'tags': 'statistics,mean,median,mode,math', 'order': 4, 'is_active': True},
            {'slug': 'prime-number-checker', 'name': 'Prime Number Checker', 'short_desc': 'Check if a number is prime and find prime factors.', 'icon': 'bi-check-circle', 'template_name': 'tools/math/prime-number-checker.html', 'tags': 'prime,number,check,factor,math', 'order': 5, 'is_active': True},
            {'slug': 'lcm-gcd-calculator', 'name': 'LCM & GCD Calculator', 'short_desc': 'Calculate the Least Common Multiple and Greatest Common Divisor.', 'icon': 'bi-intersect', 'template_name': 'tools/math/lcm-gcd-calculator.html', 'tags': 'lcm,gcd,hcf,math,calculate', 'order': 6, 'is_active': True},
            {'slug': 'percentage-change-calculator', 'name': 'Percentage Change Calculator', 'short_desc': 'Calculate percentage increase, decrease and difference between values.', 'icon': 'bi-percent', 'template_name': 'tools/math/percentage-change-calculator.html', 'tags': 'percentage,change,increase,decrease,math', 'order': 7, 'is_active': True},
            {'slug': 'trigonometry-calculator', 'name': 'Trigonometry Calculator', 'short_desc': 'Calculate sin, cos, tan and inverse trig functions.', 'icon': 'bi-triangle', 'template_name': 'tools/math/trigonometry-calculator.html', 'tags': 'trigonometry,sin,cos,tan,math', 'order': 8, 'is_active': True},
            {'slug': 'logarithm-calculator', 'name': 'Logarithm Calculator', 'short_desc': 'Calculate natural log, log base 10 and custom base logarithms.', 'icon': 'bi-graph-up', 'template_name': 'tools/math/logarithm-calculator.html', 'tags': 'logarithm,log,natural,math', 'order': 9, 'is_active': True},
            {'slug': 'permutation-combination-calculator', 'name': 'Permutation & Combination', 'short_desc': 'Calculate nPr permutations and nCr combinations.', 'icon': 'bi-shuffle', 'template_name': 'tools/math/permutation-combination-calculator.html', 'tags': 'permutation,combination,probability,math', 'order': 10, 'is_active': True},
            {'slug': 'ohms-law-calculator', 'name': "Ohm's Law Calculator", 'short_desc': "Calculate voltage, current, resistance and power using Ohm's Law.", 'icon': 'bi-lightning', 'template_name': 'tools/math/ohms-law-calculator.html', 'tags': 'ohm,law,voltage,current,resistance,physics', 'order': 11, 'is_active': True},
            {'slug': 'speed-distance-time-calculator', 'name': 'Speed Distance Time Calculator', 'short_desc': 'Calculate speed, distance or time given the other two values.', 'icon': 'bi-speedometer', 'template_name': 'tools/math/speed-distance-time-calculator.html', 'tags': 'speed,distance,time,physics,math', 'order': 12, 'is_active': True},
            {'slug': 'area-calculator', 'name': 'Area Calculator', 'short_desc': 'Calculate the area of circles, rectangles, triangles and more.', 'icon': 'bi-bounding-box', 'template_name': 'tools/math/area-calculator.html', 'tags': 'area,calculate,geometry,math', 'order': 13, 'is_active': True},
            {'slug': 'volume-calculator', 'name': 'Volume Calculator', 'short_desc': 'Calculate the volume of spheres, cylinders, cones and cubes.', 'icon': 'bi-box', 'template_name': 'tools/math/volume-calculator.html', 'tags': 'volume,calculate,geometry,math', 'order': 14, 'is_active': True},
            {'slug': 'pythagorean-theorem-calculator', 'name': 'Pythagorean Theorem Calculator', 'short_desc': 'Calculate the missing side of a right triangle using a²+b²=c².', 'icon': 'bi-triangle-half', 'template_name': 'tools/math/pythagorean-theorem-calculator.html', 'tags': 'pythagorean,theorem,triangle,math', 'order': 15, 'is_active': True},
            {'slug': 'binary-calculator', 'name': 'Binary Calculator', 'short_desc': 'Perform arithmetic operations on binary numbers.', 'icon': 'bi-code-slash', 'template_name': 'tools/math/binary-calculator.html', 'tags': 'binary,calculate,arithmetic,math,developer', 'order': 16, 'is_active': True},
            {'slug': 'scientific-notation-converter', 'name': 'Scientific Notation Converter', 'short_desc': 'Convert numbers to and from scientific notation.', 'icon': 'bi-superscript', 'template_name': 'tools/math/scientific-notation-converter.html', 'tags': 'scientific,notation,convert,math', 'order': 17, 'is_active': True},
            {'slug': 'probability-calculator', 'name': 'Probability Calculator', 'short_desc': 'Calculate basic probability, odds and expected values.', 'icon': 'bi-dice-3', 'template_name': 'tools/math/probability-calculator.html', 'tags': 'probability,odds,calculate,math', 'order': 18, 'is_active': True},
            {'slug': 'equation-balancer', 'name': 'Chemical Equation Balancer', 'short_desc': 'Balance chemical equations by entering reactants and products.', 'icon': 'bi-flask', 'template_name': 'tools/math/equation-balancer.html', 'tags': 'chemical,equation,balance,chemistry,science', 'order': 19, 'is_active': True},
            {'slug': 'molar-mass-calculator', 'name': 'Molar Mass Calculator', 'short_desc': 'Calculate the molar mass of any chemical compound.', 'icon': 'bi-atom', 'template_name': 'tools/math/molar-mass-calculator.html', 'tags': 'molar,mass,chemistry,calculate,science', 'order': 20, 'is_active': True},
        ],
    },

    # =========================================================================
    # 12. HEALTH & FITNESS TOOLS (15 tools) — NEW CATEGORY
    # =========================================================================
    {
        'slug': 'health-fitness-tools',
        'name': 'Health & Fitness Tools',
        'icon': 'bi-heart-pulse',
        'color_from': '#EF4444',
        'color_to': '#F97316',
        'order': 12,
        'short_desc': 'Health calculators and fitness planning tools.',
        'tools': [
            {'slug': 'bmr-calculator', 'name': 'BMR Calculator', 'short_desc': 'Calculate your Basal Metabolic Rate and daily calorie needs.', 'icon': 'bi-fire', 'template_name': 'tools/health/bmr-calculator.html', 'tags': 'bmr,calorie,metabolism,health,fitness', 'order': 1, 'is_active': True},
            {'slug': 'ideal-weight-calculator', 'name': 'Ideal Weight Calculator', 'short_desc': 'Calculate your ideal body weight based on height and frame.', 'icon': 'bi-person-check', 'template_name': 'tools/health/ideal-weight-calculator.html', 'tags': 'weight,ideal,calculate,health,fitness', 'order': 2, 'is_active': True},
            {'slug': 'body-fat-calculator', 'name': 'Body Fat Calculator', 'short_desc': 'Estimate body fat percentage using measurements.', 'icon': 'bi-person', 'template_name': 'tools/health/body-fat-calculator.html', 'tags': 'body,fat,calculate,health,fitness', 'order': 3, 'is_active': True},
            {'slug': 'water-intake-calculator', 'name': 'Water Intake Calculator', 'short_desc': 'Calculate your daily water intake needs based on weight and activity.', 'icon': 'bi-droplet', 'template_name': 'tools/health/water-intake-calculator.html', 'tags': 'water,intake,hydration,health,fitness', 'order': 4, 'is_active': True},
            {'slug': 'macro-calculator', 'name': 'Macro Calculator', 'short_desc': 'Calculate daily protein, carb and fat macros for your fitness goals.', 'icon': 'bi-pie-chart', 'template_name': 'tools/health/macro-calculator.html', 'tags': 'macro,protein,carb,fat,fitness,health', 'order': 5, 'is_active': True},
            {'slug': 'one-rep-max-calculator', 'name': 'One Rep Max Calculator', 'short_desc': 'Calculate your 1RM for any lift using weight and reps.', 'icon': 'bi-trophy', 'template_name': 'tools/health/one-rep-max-calculator.html', 'tags': 'one,rep,max,1rm,strength,fitness', 'order': 6, 'is_active': True},
            {'slug': 'running-pace-calculator', 'name': 'Running Pace Calculator', 'short_desc': 'Calculate running pace, speed and finish time for any distance.', 'icon': 'bi-person-walking', 'template_name': 'tools/health/running-pace-calculator.html', 'tags': 'running,pace,speed,distance,fitness', 'order': 7, 'is_active': True},
            {'slug': 'sleep-calculator', 'name': 'Sleep Calculator', 'short_desc': 'Calculate the best bedtime or wake-up time based on sleep cycles.', 'icon': 'bi-moon-stars', 'template_name': 'tools/health/sleep-calculator.html', 'tags': 'sleep,cycle,bedtime,wake,health', 'order': 8, 'is_active': True},
            {'slug': 'pregnancy-due-date-calculator', 'name': 'Pregnancy Due Date Calculator', 'short_desc': 'Calculate your estimated due date from last menstrual period.', 'icon': 'bi-calendar-heart', 'template_name': 'tools/health/pregnancy-due-date-calculator.html', 'tags': 'pregnancy,due,date,calculate,health', 'order': 9, 'is_active': True},
            {'slug': 'ovulation-calculator', 'name': 'Ovulation Calculator', 'short_desc': 'Calculate your ovulation window and fertile days.', 'icon': 'bi-calendar3', 'template_name': 'tools/health/ovulation-calculator.html', 'tags': 'ovulation,fertile,cycle,health', 'order': 10, 'is_active': True},
            {'slug': 'heart-rate-zone-calculator', 'name': 'Heart Rate Zone Calculator', 'short_desc': 'Calculate your target heart rate zones for cardio training.', 'icon': 'bi-heart', 'template_name': 'tools/health/heart-rate-zone-calculator.html', 'tags': 'heart,rate,zone,cardio,fitness', 'order': 11, 'is_active': True},
            {'slug': 'steps-to-calories-calculator', 'name': 'Steps to Calories Calculator', 'short_desc': 'Convert daily step count to calories burned.', 'icon': 'bi-activity', 'template_name': 'tools/health/steps-to-calories-calculator.html', 'tags': 'steps,calories,burned,fitness,health', 'order': 12, 'is_active': True},
            {'slug': 'workout-rest-timer', 'name': 'Workout Rest Timer', 'short_desc': 'Configurable rest timer for gym sets with audio alerts.', 'icon': 'bi-stopwatch', 'template_name': 'tools/health/workout-rest-timer.html', 'tags': 'workout,rest,timer,gym,fitness', 'order': 13, 'is_active': True},
            {'slug': 'bmi-calculator-health', 'name': 'BMI Calculator', 'short_desc': 'Calculate Body Mass Index with health category interpretation.', 'icon': 'bi-person-bounding-box', 'template_name': 'tools/health/bmi-calculator-health.html', 'tags': 'bmi,body,mass,index,health', 'order': 14, 'is_active': True},
            {'slug': 'alcohol-unit-calculator', 'name': 'Alcohol Unit Calculator', 'short_desc': 'Calculate alcohol units in drinks and weekly consumption.', 'icon': 'bi-cup', 'template_name': 'tools/health/alcohol-unit-calculator.html', 'tags': 'alcohol,unit,calculate,health', 'order': 15, 'is_active': True},
        ],
    },

    # =========================================================================
    # 13. FINANCE & BUSINESS TOOLS (18 tools) — NEW CATEGORY
    # =========================================================================
    {
        'slug': 'finance-business-tools',
        'name': 'Finance & Business Tools',
        'icon': 'bi-graph-up-arrow',
        'color_from': '#16A34A',
        'color_to': '#0EA5E9',
        'order': 13,
        'short_desc': 'Financial calculators and business planning utilities.',
        'tools': [
            {'slug': 'roi-calculator', 'name': 'ROI Calculator', 'short_desc': 'Calculate Return on Investment for any business decision.', 'icon': 'bi-graph-up', 'template_name': 'tools/finance/roi-calculator.html', 'tags': 'roi,return,investment,calculate,finance', 'order': 1, 'is_active': True},
            {'slug': 'break-even-calculator', 'name': 'Break-Even Calculator', 'short_desc': 'Calculate the break-even point for your product or business.', 'icon': 'bi-intersect', 'template_name': 'tools/finance/break-even-calculator.html', 'tags': 'break,even,calculate,business,finance', 'order': 2, 'is_active': True},
            {'slug': 'profit-margin-calculator', 'name': 'Profit Margin Calculator', 'short_desc': 'Calculate gross, net and operating profit margins.', 'icon': 'bi-percent', 'template_name': 'tools/finance/profit-margin-calculator.html', 'tags': 'profit,margin,calculate,business,finance', 'order': 3, 'is_active': True},
            {'slug': 'markup-calculator', 'name': 'Markup Calculator', 'short_desc': 'Calculate selling price from cost and desired markup percentage.', 'icon': 'bi-tag', 'template_name': 'tools/finance/markup-calculator.html', 'tags': 'markup,price,calculate,business,finance', 'order': 4, 'is_active': True},
            {'slug': 'vat-calculator', 'name': 'VAT Calculator', 'short_desc': 'Add or remove VAT from any price with configurable rate.', 'icon': 'bi-receipt', 'template_name': 'tools/finance/vat-calculator.html', 'tags': 'vat,tax,calculate,business,finance', 'order': 5, 'is_active': True},
            {'slug': 'discount-calculator', 'name': 'Discount Calculator', 'short_desc': 'Calculate discounted price and savings from any percentage off.', 'icon': 'bi-tag-fill', 'template_name': 'tools/finance/discount-calculator.html', 'tags': 'discount,price,calculate,sale,finance', 'order': 6, 'is_active': True},
            {'slug': 'savings-goal-calculator', 'name': 'Savings Goal Calculator', 'short_desc': 'Calculate how long to reach a savings goal with monthly contributions.', 'icon': 'bi-piggy-bank', 'template_name': 'tools/finance/savings-goal-calculator.html', 'tags': 'savings,goal,calculate,finance', 'order': 7, 'is_active': True},
            {'slug': 'mortgage-calculator', 'name': 'Mortgage Calculator', 'short_desc': 'Calculate monthly mortgage payments with amortization schedule.', 'icon': 'bi-house', 'template_name': 'tools/finance/mortgage-calculator.html', 'tags': 'mortgage,loan,payment,calculate,finance', 'order': 8, 'is_active': True},
            {'slug': 'retirement-calculator', 'name': 'Retirement Calculator', 'short_desc': 'Estimate retirement savings needed based on age and lifestyle.', 'icon': 'bi-umbrella', 'template_name': 'tools/finance/retirement-calculator.html', 'tags': 'retirement,savings,calculate,finance', 'order': 9, 'is_active': True},
            {'slug': 'freelance-rate-calculator', 'name': 'Freelance Rate Calculator', 'short_desc': 'Calculate your minimum hourly rate as a freelancer.', 'icon': 'bi-laptop', 'template_name': 'tools/finance/freelance-rate-calculator.html', 'tags': 'freelance,rate,hourly,calculate,business', 'order': 10, 'is_active': True},
            {'slug': 'business-name-generator', 'name': 'Business Name Generator', 'short_desc': 'Generate creative business name ideas for any industry.', 'icon': 'bi-building', 'template_name': 'tools/finance/business-name-generator.html', 'tags': 'business,name,generate,brand,startup', 'order': 11, 'is_active': True},
            {'slug': 'startup-cost-estimator', 'name': 'Startup Cost Estimator', 'short_desc': 'Estimate startup costs with a categorised checklist.', 'icon': 'bi-rocket', 'template_name': 'tools/finance/startup-cost-estimator.html', 'tags': 'startup,cost,estimate,business,finance', 'order': 12, 'is_active': True},
            {'slug': 'cash-flow-calculator', 'name': 'Cash Flow Calculator', 'short_desc': 'Calculate monthly cash flow from income and expenses.', 'icon': 'bi-cash-stack', 'template_name': 'tools/finance/cash-flow-calculator.html', 'tags': 'cash,flow,calculate,business,finance', 'order': 13, 'is_active': True},
            {'slug': 'net-worth-calculator', 'name': 'Net Worth Calculator', 'short_desc': 'Calculate your net worth from assets and liabilities.', 'icon': 'bi-wallet2', 'template_name': 'tools/finance/net-worth-calculator.html', 'tags': 'net,worth,assets,liabilities,finance', 'order': 14, 'is_active': True},
            {'slug': 'inflation-calculator', 'name': 'Inflation Calculator', 'short_desc': 'Calculate the real value of money adjusted for inflation over time.', 'icon': 'bi-arrow-up-right', 'template_name': 'tools/finance/inflation-calculator.html', 'tags': 'inflation,value,money,calculate,finance', 'order': 15, 'is_active': True},
            {'slug': 'stock-return-calculator', 'name': 'Stock Return Calculator', 'short_desc': 'Calculate total return on a stock investment including dividends.', 'icon': 'bi-graph-up-arrow', 'template_name': 'tools/finance/stock-return-calculator.html', 'tags': 'stock,return,investment,calculate,finance', 'order': 16, 'is_active': True},
            {'slug': 'budget-planner', 'name': 'Budget Planner', 'short_desc': 'Plan your monthly budget with income, expenses and savings goals.', 'icon': 'bi-journal-check', 'template_name': 'tools/finance/budget-planner.html', 'tags': 'budget,plan,income,expense,finance', 'order': 17, 'is_active': True},
            {'slug': 'invoice-tax-calculator', 'name': 'Invoice Tax Calculator', 'short_desc': 'Calculate tax amounts on invoices for different tax rates.', 'icon': 'bi-receipt-cutoff', 'template_name': 'tools/finance/invoice-tax-calculator.html', 'tags': 'invoice,tax,calculate,business,finance', 'order': 18, 'is_active': True},
        ],
    },

    # =========================================================================
    # 14. TEXT ANALYSIS & NLP TOOLS (16 tools) — NEW CATEGORY
    # =========================================================================
    {
        'slug': 'text-analysis-tools',
        'name': 'Text Analysis Tools',
        'icon': 'bi-file-earmark-bar-graph',
        'color_from': '#7C3AED',
        'color_to': '#EC4899',
        'order': 14,
        'short_desc': 'Analyse, extract and process text with intelligent tools.',
        'tools': [
            {'slug': 'character-frequency-analyzer', 'name': 'Character Frequency Analyzer', 'short_desc': 'Analyse the frequency of each character in any text.', 'icon': 'bi-bar-chart-steps', 'template_name': 'tools/text/character-frequency-analyzer.html', 'tags': 'character,frequency,analyze,text', 'order': 1, 'is_active': True},
            {'slug': 'sentence-counter', 'name': 'Sentence Counter', 'short_desc': 'Count sentences, clauses and average sentence length in text.', 'icon': 'bi-123', 'template_name': 'tools/text/sentence-counter.html', 'tags': 'sentence,count,analyze,text', 'order': 2, 'is_active': True},
            {'slug': 'text-statistics', 'name': 'Text Statistics', 'short_desc': 'Get comprehensive statistics: words, chars, sentences, paragraphs, density.', 'icon': 'bi-clipboard-data', 'template_name': 'tools/text/text-statistics.html', 'tags': 'text,statistics,analyze,words,chars', 'order': 3, 'is_active': True},
            {'slug': 'email-extractor', 'name': 'Email Extractor', 'short_desc': 'Extract all email addresses from any block of text.', 'icon': 'bi-envelope', 'template_name': 'tools/text/email-extractor.html', 'tags': 'email,extract,text,parse', 'order': 4, 'is_active': True},
            {'slug': 'url-extractor', 'name': 'URL Extractor', 'short_desc': 'Extract all URLs and links from any block of text.', 'icon': 'bi-link', 'template_name': 'tools/text/url-extractor.html', 'tags': 'url,link,extract,text,parse', 'order': 5, 'is_active': True},
            {'slug': 'phone-number-extractor', 'name': 'Phone Number Extractor', 'short_desc': 'Extract phone numbers from any text in multiple formats.', 'icon': 'bi-telephone', 'template_name': 'tools/text/phone-number-extractor.html', 'tags': 'phone,number,extract,text,parse', 'order': 6, 'is_active': True},
            {'slug': 'text-sorter', 'name': 'Text Line Sorter', 'short_desc': 'Sort lines of text alphabetically, numerically or by length.', 'icon': 'bi-sort-alpha-down', 'template_name': 'tools/text/text-sorter.html', 'tags': 'sort,lines,text,alphabetical', 'order': 7, 'is_active': True},
            {'slug': 'text-to-list', 'name': 'Text to List Converter', 'short_desc': 'Convert comma-separated or line-separated text into formatted lists.', 'icon': 'bi-list-ul', 'template_name': 'tools/text/text-to-list.html', 'tags': 'text,list,convert,format', 'order': 8, 'is_active': True},
            {'slug': 'find-replace-tool', 'name': 'Find & Replace Tool', 'short_desc': 'Find and replace text with support for regex patterns.', 'icon': 'bi-search', 'template_name': 'tools/text/find-replace-tool.html', 'tags': 'find,replace,text,regex', 'order': 9, 'is_active': True},
            {'slug': 'text-truncator', 'name': 'Text Truncator', 'short_desc': 'Truncate text to a specific character or word limit with ellipsis.', 'icon': 'bi-scissors', 'template_name': 'tools/text/text-truncator.html', 'tags': 'truncate,text,limit,shorten', 'order': 10, 'is_active': True},
            {'slug': 'whitespace-remover', 'name': 'Whitespace Remover', 'short_desc': 'Remove all extra whitespace, tabs and blank lines from text.', 'icon': 'bi-eraser', 'template_name': 'tools/text/whitespace-remover.html', 'tags': 'whitespace,remove,clean,text', 'order': 11, 'is_active': True},
            {'slug': 'number-extractor', 'name': 'Number Extractor', 'short_desc': 'Extract all numbers from any text or document.', 'icon': 'bi-123', 'template_name': 'tools/text/number-extractor.html', 'tags': 'number,extract,text,parse', 'order': 12, 'is_active': True},
            {'slug': 'text-to-columns', 'name': 'Text to Columns', 'short_desc': 'Split text into columns by delimiter for spreadsheet use.', 'icon': 'bi-layout-three-columns', 'template_name': 'tools/text/text-to-columns.html', 'tags': 'text,columns,split,delimiter,csv', 'order': 13, 'is_active': True},
            {'slug': 'palindrome-checker', 'name': 'Palindrome Checker', 'short_desc': 'Check if a word or phrase is a palindrome.', 'icon': 'bi-arrow-left-right', 'template_name': 'tools/text/palindrome-checker.html', 'tags': 'palindrome,check,text,word', 'order': 14, 'is_active': True},
            {'slug': 'anagram-generator', 'name': 'Anagram Generator', 'short_desc': 'Generate anagrams from any word or phrase.', 'icon': 'bi-shuffle', 'template_name': 'tools/text/anagram-generator.html', 'tags': 'anagram,generate,word,text', 'order': 15, 'is_active': True},
            {'slug': 'text-encryption', 'name': 'Text Encryption Tool', 'short_desc': 'Encrypt and decrypt text using Caesar cipher and ROT13.', 'icon': 'bi-lock', 'template_name': 'tools/text/text-encryption.html', 'tags': 'encrypt,decrypt,caesar,rot13,text', 'order': 16, 'is_active': True},
        ],
    },
]

from config.tool_categories_ecosystem import ECOSYSTEM_TOOL_CATEGORIES

TOOL_CATEGORIES = _TOOL_CATEGORIES_BASE + ECOSYSTEM_TOOL_CATEGORIES