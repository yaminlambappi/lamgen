# config/homepage_data.py

HERO_CHIPS = [
    'Resume AI',
    'ATS Checker',
    'Cover Letter Generator',
    'AI Humanizer',
    'Essay Writer',
    'SQL Generator',
    'Regex Generator',
    'SEO Writer',
    'LinkedIn Tools',
    'Image Prompt Generator',
]

AI_TOOLS = [
    {
        'name': 'Career AI',
        'tools': [
            {'name': 'AI Resume Builder', 'description': 'Build a job-winning resume with AI.', 'route': '/tools/resume-career-tools/ai-resume-builder/', 'icon': 'briefcase'},
            {'name': 'ATS Checker', 'description': 'Optimize your resume for ATS scanners.', 'route': '/tools/resume-career-tools/ats-checker/', 'icon': 'check-circle'},
            {'name': 'Cover Letter Generator', 'description': 'Create tailored cover letters in seconds.', 'route': '/tools/resume-career-tools/ai-cover-letter-generator/', 'icon': 'envelope'},
            {'name': 'LinkedIn Headline Generator', 'description': 'Craft a standout LinkedIn headline.', 'route': '/tools/resume-career-tools/linkedin-headline-generator/', 'icon': 'linkedin'},
            {'name': 'LinkedIn Post Generator', 'description': 'Generate engaging posts for LinkedIn.', 'route': '/tools/resume-career-tools/ai-linkedin-post-generator/', 'icon': 'linkedin'},
        ]
    },
    {
        'name': 'Writing & Student AI',
        'tools': [
            {'name': 'AI Humanizer', 'description': 'Humanize AI-generated text.', 'route': '/tools/writing-tools/ai-humanizer/', 'icon': 'user'},
            {'name': 'Essay Writer', 'description': 'Write high-quality essays with AI.', 'route': '/tools/student-tools/essay-writer/', 'icon': 'edit-3'},
            {'name': 'Paraphrasing Tool', 'description': 'Rephrase text to avoid plagiarism.', 'route': '/tools/writing-tools/paraphrasing-tool/', 'icon': 'repeat'},
            {'name': 'Grammar Checker', 'description': 'Correct grammar and spelling mistakes.', 'route': '/tools/writing-tools/grammar-checker/', 'icon': 'check-square'},
            {'name': 'Email Writer', 'description': 'Compose professional emails instantly.', 'route': '/tools/writing-tools/email-writer/', 'icon': 'mail'},
            {'name': 'Cold Email Generator', 'description': 'Generate personalized cold emails.', 'route': '/tools/writing-tools/cold-email-generator/', 'icon': 'send'},
            {'name': 'Notes Generator', 'description': 'Summarize your notes with AI.', 'route': '/tools/student-tools/notes-generator/', 'icon': 'book'},
            {'name': 'Quiz Generator', 'description': 'Create quizzes on any topic.', 'route': '/tools/student-tools/quiz-generator/', 'icon': 'help-circle'},
            {'name': 'Flashcard Generator', 'description': 'Generate flashcards for effective learning.', 'route': '/tools/student-tools/flashcard-generator/', 'icon': 'layers'},
        ]
    },
    {
        'name': 'SEO & Content AI',
        'tools': [
            {'name': 'Blog Writer', 'description': 'Generate complete blog posts with AI.', 'route': '/tools/seo-content/blog-writer/', 'icon': 'file-text'},
            {'name': 'SEO Article Generator', 'description': 'Write SEO-optimized articles.', 'route': '/tools/seo-content/seo-article-generator/', 'icon': 'bar-chart-2'},
            {'name': 'Meta Description Generator', 'description': 'Create compelling meta descriptions.', 'route': '/tools/seo-tools/meta-description-generator/', 'icon': 'search'},
            {'name': 'Keyword Cluster Generator', 'description': 'Group keywords into semantic clusters.', 'route': '/tools/seo-content/keyword-cluster-generator/', 'icon': 'folder'},
            {'name': 'YouTube Script Generator', 'description': 'Write engaging scripts for YouTube videos.', 'route': '/tools/seo-content/youtube-script-generator/', 'icon': 'youtube'},
            {'name': 'YouTube Title Generator', 'description': 'Generate catchy titles for YouTube.', 'route': '/tools/seo-content/ai-youtube-title-generator/', 'icon': 'youtube'},
            {'name': 'Thumbnail Prompt Generator', 'description': 'Get ideas for eye-catching thumbnails.', 'route': '/tools/seo-content/thumbnail-prompt-generator/', 'icon': 'image'},
            {'name': 'Instagram Caption Generator', 'description': 'Generate creative Instagram captions.', 'route': '/tools/social-viral/instagram-caption-generator/', 'icon': 'instagram'},
        ]
    },
    {
        'name': 'Developer AI',
        'tools': [
            {'name': 'SQL Generator', 'description': 'Generate SQL queries from plain text.', 'route': '/tools/developer-tools/sql-generator/', 'icon': 'database'},
            {'name': 'Regex Generator', 'description': 'Create regular expressions with ease.', 'route': '/tools/developer-tools/regex-generator/', 'icon': 'code'},
            {'name': 'Code Debugger', 'description': 'Debug your code with the help of AI.', 'route': '/tools/developer-tools/code-debugger/', 'icon': 'bug'},
        ]
    },
    {
        'name': 'Creator AI',
        'tools': [
            {'name': 'YouTube Script Generator', 'description': 'Write engaging scripts for YouTube videos.', 'route': '/tools/social-viral/youtube-script-generator/', 'icon': 'youtube'},
            {'name': 'Instagram Caption Generator', 'description': 'Generate creative Instagram captions.', 'route': '/tools/social-viral/instagram-caption-generator/', 'icon': 'instagram'},
            {'name': 'Meme Generator', 'description': 'Create memes with custom text on any image.', 'route': '/tools/image-tools/meme-generator/', 'icon': 'emoji-laughing'},
        ]
    },
]

BROWSER_UTILITIES = [
    {
        'name': 'Developer Utilities',
        'tools': [
            {'name': 'JSON Formatter', 'route': '/tools/developer-tools/json-formatter/'},
            {'name': 'XML Formatter', 'route': '/tools/developer-tools/xml-formatter/'},
            {'name': 'YAML Formatter', 'route': '/tools/developer-tools/yaml-formatter/'},
            {'name': 'Regex Tester', 'route': '/tools/developer-tools/regex-tester/'},
            {'name': 'UUID Generator', 'route': '/tools/developer-tools/uuid-generator/'},
            {'name': 'Hash Generator', 'route': '/tools/developer-tools/hash-generator/'},
        ]
    },
    {
        'name': 'Code Formatting',
        'tools': [
            {'name': 'HTML Formatter', 'route': '/tools/developer-tools/html-formatter/'},
            {'name': 'CSS Formatter', 'route': '/tools/developer-tools/css-formatter/'},
            {'name': 'JS Formatter', 'route': '/tools/developer-tools/js-formatter/'},
            {'name': 'SQL Beautifier', 'route': '/tools/developer-tools/sql-beautifier/'},
            {'name': 'CSS Minifier', 'route': '/tools/developer-tools/css-minifier/'},
            {'name': 'HTML Minifier', 'route': '/tools/developer-tools/html-minifier/'},
            {'name': 'JS Minifier', 'route': '/tools/developer-tools/js-minifier/'},
        ]
    },
    {
        'name': 'Browser Utilities',
        'tools': [
            {'name': 'Markdown Previewer', 'route': '/tools/developer-tools/markdown-previewer/'},
            {'name': 'Diff Checker', 'route': '/tools/developer-tools/diff-checker/'},
            {'name': 'Word Counter', 'route': '/tools/student-tools/word-counter/'},
            {'name': 'Case Converter', 'route': '/tools/writing-tools/case-converter/'},
        ]
    },
]

CATEGORIES = [
    {'name': 'Career AI', 'icon': 'briefcase', 'tool_count': 5, 'description': 'Supercharge your job search.', 'route': '/tools/resume-career-tools/'},
    {'name': 'Writing AI', 'icon': 'edit-3', 'tool_count': 9, 'description': 'Elevate your writing.', 'route': '/tools/writing-tools/'},
    {'name': 'Student AI', 'icon': 'book-open', 'tool_count': 9, 'description': 'Ace your studies with AI.', 'route': '/tools/student-tools/'},
    {'name': 'SEO AI', 'icon': 'bar-chart-2', 'tool_count': 7, 'description': 'Boost your search rankings.', 'route': '/tools/seo-content/'},
    {'name': 'Creator AI', 'icon': 'youtube', 'tool_count': 4, 'description': 'Fuel your creative process.', 'route': '/tools/social-viral/'},
    {'name': 'Startup AI', 'icon': 'lightbulb', 'tool_count': 4, 'description': 'Launch your venture faster.', 'route': '/tools/startup-tools/'},
    {'name': 'Developer AI', 'icon': 'code', 'tool_count': 3, 'description': 'Code smarter, not harder.', 'route': '/tools/developer-tools/'},
    {'name': 'Utility Tools', 'icon': 'tool', 'tool_count': 18, 'description': 'Handy tools for everyday tasks.', 'route': '/tools/utility-tools/'},
]

TRENDING_TOOLS = [
    {'name': 'AI Resume Builder', 'category': 'Career AI', 'route': '/tools/resume-career-tools/ai-resume-builder/'},
    {'name': 'ATS Checker', 'category': 'Career AI', 'route': '/tools/resume-career-tools/ats-checker/'},
    {'name': 'AI Humanizer', 'category': 'Writing AI', 'route': '/tools/writing-tools/ai-humanizer/'},
    {'name': 'SQL Generator', 'category': 'Developer AI', 'route': '/tools/developer-tools/sql-generator/'},
    {'name': 'Image Prompt Generator', 'category': 'Creator AI', 'route': '/tools/social-viral/image-prompt-generator/'},
]

FAQS = [
    {
        'question': 'What is LamGen?',
        'answer': 'LamGen is an AI-powered productivity ecosystem with a wide range of tools for career, content creation, development, and more. Our goal is to provide a comprehensive suite of tools to help you be more productive in your personal and professional life.'
    },
    {
        'question': 'Are the tools free to use?',
        'answer': 'Many of our tools are available for free. We also offer premium features and plans for users who need more advanced capabilities and higher usage limits.'
    },
    {
        'question': 'What AI tools are available?',
        'answer': 'We offer a variety of AI tools, including an AI Resume Builder, ATS Resume Checker, Cover Letter Generator, AI Humanizer, Essay Writer, SQL Generator, and many more. Explore our tool categories to see the full list.'
    },
    {
        'question': 'How does the ATS checker work?',
        'answer': 'Our ATS (Applicant Tracking System) checker analyzes your resume and provides feedback on how well it is optimized for ATS software. It checks for keywords, formatting, and other factors that can affect your resume\'s chances of being seen by a recruiter.'
    },
    {
        'question': 'Can I generate resumes with AI?',
        'answer': 'Yes, our AI Resume Builder helps you create professional, job-winning resumes in minutes. It provides suggestions for content, formatting, and keywords to make your resume stand out.'
    },
    {
        'question': 'Is LamGen useful for developers?',
        'answer': 'Absolutely. We have a dedicated set of developer tools, including a SQL Query Generator, Regex Generator, Code Debugger, and various formatters and minifiers to streamline your development workflow.'
    },
    {
        'question': 'Does LamGen support content creators?',
        'answer': 'Yes, we have a suite of tools for content creators, including a Blog Writer, SEO Article Generator, YouTube Script Generator, and more. These tools can help you generate ideas, create content, and optimize it for search engines and social media.'
    },
    {
        'question': 'Which SEO tools are included?',
        'answer': 'Our SEO tools include a Meta Description Generator, Keyword Cluster Generator, and SEO Article Generator, among others. These tools are designed to help you improve your website\'s ranking in search results.'
    },
]

FOOTER_DATA = {
    'ai_tools': {
        'name': 'AI Tools',
        'links': [
            {'name': 'AI Resume Builder', 'route': '/tools/resume-career-tools/ai-resume-builder/'},
            {'name': 'ATS Checker', 'route': '/tools/resume-career-tools/ats-checker/'},
            {'name': 'AI Humanizer', 'route': '/tools/writing-tools/ai-humanizer/'},
            {'name': 'SEO Article Generator', 'route': '/tools/seo-content/seo-article-generator/'},
        ]
    },
    'utilities': {
        'name': 'Utilities',
        'links': [
            {'name': 'JSON Formatter', 'route': '/tools/developer-tools/json-formatter/'},
            {'name': 'SQL Beautifier', 'route': '/tools/developer-tools/sql-beautifier/'},
            {'name': 'Regex Tester', 'route': '/tools/developer-tools/regex-tester/'},
            {'name': 'Word Counter', 'route': '/tools/student-tools/word-counter/'},
        ]
    },
    'categories': {
        'name': 'Categories',
        'links': [
            {'name': 'Career AI', 'route': '/tools/resume-career-tools/'},
            {'name': 'Writing AI', 'route': '/tools/writing-tools/'},
            {'name': 'Developer AI', 'route': '/tools/developer-tools/'},
            {'name': 'SEO AI', 'route': '/tools/seo-content/'},
        ]
    },
    'resources': {
        'name': 'Resources',
        'links': [
            {'name': 'Blog', 'route': '/blog'},
            {'name': 'About Us', 'route': '/about'},
            {'name': 'Contact Us', 'route': '/contact'},
        ]
    },
    'legal': {
        'name': 'Legal',
        'links': [
            {'name': 'Privacy Policy', 'route': '/privacy'},
            {'name': 'Terms of Service', 'route': '/terms'},
        ]
    },
}
