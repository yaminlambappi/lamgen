# config/homepage_data.py

HERO_CHIPS = [
    'Resume AI',
    'AI ATS Checker',
    'AI Cover Letter',
    'AI Humanizer',
    'AI Essay Writer',
    'SQL Generator',
    'Regex Generator',
    'SEO Writer',
    'LinkedIn AI Tools',
    'Image Prompt Generator',
]

AI_TOOLS = [
    {
        'name': 'Career AI',
        'tools': [
            {'name': 'AI Resume Builder', 'description': 'Build a job-winning resume with AI.', 'route': '/tools/resume-career-tools/ai-resume-builder/', 'icon': 'briefcase'},
            {'name': 'AI ATS Resume Checker', 'description': 'Check if your resume beats ATS scanners.', 'route': '/tools/resume-career-tools/ai-ats-resume-checker/', 'icon': 'check-circle'},
            {'name': 'AI Cover Letter Generator', 'description': 'Create tailored cover letters in seconds.', 'route': '/tools/resume-career-tools/ai-cover-letter-generator/', 'icon': 'envelope-paper'},
            {'name': 'AI LinkedIn Headline Generator', 'description': 'Craft a standout LinkedIn headline with AI.', 'route': '/tools/resume-career-tools/ai-linkedin-headline-generator/', 'icon': 'linkedin'},
            {'name': 'AI LinkedIn Post Generator', 'description': 'Generate engaging LinkedIn posts with AI.', 'route': '/tools/resume-career-tools/ai-linkedin-post-generator/', 'icon': 'linkedin'},
        ]
    },
    {
        'name': 'Writing & Student AI',
        'tools': [
            {'name': 'AI Humanizer', 'description': 'Humanize AI-generated text instantly.', 'route': '/tools/writing-tools/ai-humanizer/', 'icon': 'person-hearts'},
            {'name': 'AI Essay Writer', 'description': 'Write high-quality essays with AI.', 'route': '/tools/writing-tools/essay-writer/', 'icon': 'journal-text'},
            {'name': 'AI Paraphrasing Tool', 'description': 'Rephrase text to avoid plagiarism.', 'route': '/tools/writing-tools/paraphrasing-tool/', 'icon': 'arrow-repeat'},
            {'name': 'AI Grammar Checker', 'description': 'Correct grammar and spelling with AI.', 'route': '/tools/writing-tools/grammar-checker/', 'icon': 'check2-all'},
            {'name': 'AI Email Writer', 'description': 'Compose professional emails instantly.', 'route': '/tools/writing-tools/email-writer/', 'icon': 'envelope-open'},
            {'name': 'Cold Email Generator', 'description': 'Generate personalized cold emails.', 'route': '/tools/writing-tools/cold-email-generator/', 'icon': 'envelope-plus'},
            {'name': 'AI Notes Generator', 'description': 'Summarize your notes with AI.', 'route': '/tools/student-tools/notes-generator/', 'icon': 'journal-plus'},
            {'name': 'AI Quiz Generator', 'description': 'Create quizzes on any topic with AI.', 'route': '/tools/student-tools/quiz-generator/', 'icon': 'patch-question'},
        ]
    },
    {
        'name': 'SEO & Content AI',
        'tools': [
            {'name': 'AI Blog Writer', 'description': 'Generate complete blog posts with AI.', 'route': '/tools/seo-tools/blog-writer/', 'icon': 'newspaper'},
            {'name': 'SEO Article Generator', 'description': 'Write SEO-optimized articles with AI.', 'route': '/tools/seo-tools/seo-article-generator/', 'icon': 'file-earmark-richtext'},
            {'name': 'AI Meta Description Generator', 'description': 'Create compelling meta descriptions.', 'route': '/tools/seo-tools/meta-description-generator/', 'icon': 'search'},
            {'name': 'Keyword Cluster Generator', 'description': 'Group keywords into semantic clusters.', 'route': '/tools/seo-tools/keyword-cluster-generator/', 'icon': 'diagram-3'},
            {'name': 'AI YouTube Title Generator', 'description': 'Generate catchy titles for YouTube.', 'route': '/tools/social-viral-tools/ai-youtube-title-generator/', 'icon': 'youtube'},
            {'name': 'Thumbnail Prompt Generator', 'description': 'Get AI prompts for eye-catching thumbnails.', 'route': '/tools/social-viral-tools/thumbnail-prompt-generator/', 'icon': 'card-image'},
            {'name': 'Instagram Caption Generator', 'description': 'Generate creative Instagram captions.', 'route': '/tools/social-viral-tools/instagram-caption-generator/', 'icon': 'instagram'},
        ]
    },
    {
        'name': 'Developer AI',
        'tools': [
            {'name': 'AI SQL Generator', 'description': 'Generate SQL queries from plain text.', 'route': '/tools/developer-tools/sql-generator/', 'icon': 'database-gear'},
            {'name': 'AI Regex Generator', 'description': 'Create regular expressions with ease.', 'route': '/tools/developer-tools/regex-generator/', 'icon': 'search'},
            {'name': 'AI Code Debugger', 'description': 'Debug your code with the help of AI.', 'route': '/tools/developer-tools/code-debugger/', 'icon': 'bug'},
            {'name': 'SQL Query Generator', 'description': 'Generate complex SQL from plain descriptions.', 'route': '/tools/developer-tools/sql-query-generator/', 'icon': 'database'},
        ]
    },
    {
        'name': 'Creator & Business AI',
        'tools': [
            {'name': 'YouTube Script Generator', 'description': 'Write engaging scripts for YouTube videos.', 'route': '/tools/social-viral-tools/youtube-script-generator/', 'icon': 'camera-video'},
            {'name': 'AI Tweet Generator', 'description': 'Generate tweets and X posts with AI.', 'route': '/tools/social-viral-tools/tweet-generator/', 'icon': 'twitter-x'},
            {'name': 'AI Startup Name Generator', 'description': 'Generate creative startup names with AI.', 'route': '/tools/finance-business-tools/startup-name-generator/', 'icon': 'stars'},
            {'name': 'AI Business Plan Generator', 'description': 'Generate a business plan outline with AI.', 'route': '/tools/finance-business-tools/business-plan-generator/', 'icon': 'briefcase'},
            {'name': 'Image Prompt Generator', 'description': 'Generate creative AI image prompts.', 'route': '/tools/finance-business-tools/image-prompt-generator/', 'icon': 'image-alt'},
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
    {'name': 'Writing AI', 'icon': 'pencil-square', 'tool_count': 9, 'description': 'Elevate your writing.', 'route': '/tools/writing-tools/'},
    {'name': 'Student AI', 'icon': 'journal-bookmark', 'tool_count': 9, 'description': 'Ace your studies with AI.', 'route': '/tools/student-tools/'},
    {'name': 'SEO AI', 'icon': 'bar-chart-line', 'tool_count': 7, 'description': 'Boost your search rankings.', 'route': '/tools/seo-tools/'},
    {'name': 'Creator AI', 'icon': 'youtube', 'tool_count': 5, 'description': 'Fuel your creative process.', 'route': '/tools/social-viral-tools/'},
    {'name': 'Business AI', 'icon': 'lightbulb', 'tool_count': 4, 'description': 'Launch your venture faster.', 'route': '/tools/finance-business-tools/'},
    {'name': 'Developer AI', 'icon': 'code-slash', 'tool_count': 4, 'description': 'Code smarter, not harder.', 'route': '/tools/developer-tools/'},
    {'name': 'Utility Tools', 'icon': 'tools', 'tool_count': 18, 'description': 'Handy tools for everyday tasks.', 'route': '/tools/utility-tools/'},
]

TRENDING_TOOLS = [
    {'name': 'AI Resume Builder', 'category': 'Career AI', 'route': '/tools/resume-career-tools/ai-resume-builder/'},
    {'name': 'AI ATS Resume Checker', 'category': 'Career AI', 'route': '/tools/resume-career-tools/ai-ats-resume-checker/'},
    {'name': 'AI Humanizer', 'category': 'Writing AI', 'route': '/tools/writing-tools/ai-humanizer/'},
    {'name': 'AI SQL Generator', 'category': 'Developer AI', 'route': '/tools/developer-tools/sql-generator/'},
    {'name': 'Image Prompt Generator', 'category': 'Business AI', 'route': '/tools/finance-business-tools/image-prompt-generator/'},
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
        'answer': 'We offer a variety of AI tools, including an AI Resume Builder, AI ATS Resume Checker, AI Cover Letter Generator, AI Humanizer, AI Essay Writer, AI SQL Generator, and many more. Explore our tool categories to see the full list.'
    },
    {
        'question': 'How does the AI ATS checker work?',
        'answer': 'Our AI ATS (Applicant Tracking System) checker analyzes your resume using AI and provides feedback on how well it is optimized for ATS software. It checks for keywords, formatting, and other factors that can affect your resume\'s chances of being seen by a recruiter.'
    },
    {
        'question': 'Can I generate resumes with AI?',
        'answer': 'Yes, our AI Resume Builder helps you create professional, job-winning resumes in minutes. It provides suggestions for content, formatting, and keywords to make your resume stand out.'
    },
    {
        'question': 'Is LamGen useful for developers?',
        'answer': 'Absolutely. We have a dedicated set of developer AI tools, including an AI SQL Generator, AI Regex Generator, AI Code Debugger, and various formatters and minifiers to streamline your development workflow.'
    },
    {
        'question': 'Does LamGen support content creators?',
        'answer': 'Yes, we have a suite of AI tools for content creators, including an AI Blog Writer, SEO Article Generator, YouTube Script Generator, AI Tweet Generator, and more.'
    },
    {
        'question': 'Which SEO tools are included?',
        'answer': 'Our AI SEO tools include an AI Meta Description Generator, Keyword Cluster Generator, AI Blog Writer, and SEO Article Generator, among others. These tools are designed to help you improve your website\'s ranking in search results.'
    },
]

FOOTER_DATA = {
    'ai_tools': {
        'name': 'AI Tools',
        'links': [
            {'name': 'AI Resume Builder', 'route': '/tools/resume-career-tools/ai-resume-builder/'},
            {'name': 'AI ATS Resume Checker', 'route': '/tools/resume-career-tools/ai-ats-resume-checker/'},
            {'name': 'AI Humanizer', 'route': '/tools/writing-tools/ai-humanizer/'},
            {'name': 'AI Blog Writer', 'route': '/tools/seo-tools/blog-writer/'},
            {'name': 'AI SQL Generator', 'route': '/tools/developer-tools/sql-generator/'},
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
            {'name': 'Developer Tools', 'route': '/tools/developer-tools/'},
            {'name': 'SEO Tools', 'route': '/tools/seo-tools/'},
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
