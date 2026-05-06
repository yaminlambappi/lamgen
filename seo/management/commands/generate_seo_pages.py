"""
Management command: generate_seo_pages
Idempotently seeds 500+ programmatic SEO pages from curated topic lists.
Usage: python manage.py generate_seo_pages [--dry-run]
"""
from django.core.management.base import BaseCommand
from seo.models import SEOCategory, SEOPage
from seo.engine.content_generator import generate_items

# ---------------------------------------------------------------------------
# Topic seeds: (human_topic, slug_suffix)
# Final slug = category_slug + '-' + slug_suffix
# ---------------------------------------------------------------------------
TOPIC_SEEDS: dict[str, list[tuple[str, str]]] = {
    'captions': [
        ('Travel Instagram Captions', 'travel-instagram-captions'),
        ('Birthday Captions', 'birthday-captions'),
        ('Motivational Monday Captions', 'motivational-monday-captions'),
        ('Selfie Captions', 'selfie-captions'),
        ('Beach Captions', 'beach-captions'),
        ('Sunset Captions', 'sunset-captions'),
        ('Food Captions', 'food-captions'),
        ('Friendship Captions', 'friendship-captions'),
        ('Love Captions', 'love-captions'),
        ('Nature Captions', 'nature-captions'),
        ('Gym Workout Captions', 'gym-workout-captions'),
        ('Coffee Captions', 'coffee-captions'),
        ('Night Out Captions', 'night-out-captions'),
        ('Graduation Captions', 'graduation-captions'),
        ('New Year Captions', 'new-year-captions'),
        ('Christmas Captions', 'christmas-captions'),
        ('Wedding Captions', 'wedding-captions'),
        ('Baby Shower Captions', 'baby-shower-captions'),
        ('Road Trip Captions', 'road-trip-captions'),
        ('Hiking Captions', 'hiking-captions'),
        ('Aesthetic Captions', 'aesthetic-captions'),
        ('Funny Captions', 'funny-captions'),
        ('Short Captions', 'short-captions'),
        ('Attitude Captions', 'attitude-captions'),
        ('Couple Captions', 'couple-captions'),
        ('Solo Travel Captions', 'solo-travel-captions'),
        ('Throwback Captions', 'throwback-captions'),
        ('Monday Motivation Captions', 'monday-motivation-captions'),
        ('Fitness Captions', 'fitness-captions'),
        ('Yoga Captions', 'yoga-captions'),
        ('Autumn Fall Captions', 'autumn-fall-captions'),
        ('Winter Captions', 'winter-captions'),
        ('Spring Captions', 'spring-captions'),
        ('Summer Captions', 'summer-captions'),
        ('City Life Captions', 'city-life-captions'),
        ('Countryside Captions', 'countryside-captions'),
        ('Pet Dog Captions', 'pet-dog-captions'),
        ('Cat Captions', 'cat-captions'),
        ('Book Reading Captions', 'book-reading-captions'),
        ('Music Captions', 'music-captions'),
    ],
    'quotes': [
        ('Motivational Quotes', 'motivational-quotes'),
        ('Success Quotes', 'success-quotes'),
        ('Life Quotes', 'life-quotes'),
        ('Inspirational Quotes', 'inspirational-quotes'),
        ('Positive Quotes', 'positive-quotes'),
        ('Hustle Quotes', 'hustle-quotes'),
        ('Mindset Quotes', 'mindset-quotes'),
        ('Leadership Quotes', 'leadership-quotes'),
        ('Entrepreneur Quotes', 'entrepreneur-quotes'),
        ('Happiness Quotes', 'happiness-quotes'),
        ('Friendship Quotes', 'friendship-quotes'),
        ('Love Quotes', 'love-quotes'),
        ('Wisdom Quotes', 'wisdom-quotes'),
        ('Courage Quotes', 'courage-quotes'),
        ('Resilience Quotes', 'resilience-quotes'),
        ('Growth Mindset Quotes', 'growth-mindset-quotes'),
        ('Monday Motivation Quotes', 'monday-motivation-quotes'),
        ('Short Inspirational Quotes', 'short-inspirational-quotes'),
        ('Deep Quotes', 'deep-quotes'),
        ('Funny Quotes', 'funny-quotes'),
        ('Stoic Quotes', 'stoic-quotes'),
        ('Buddha Quotes', 'buddha-quotes'),
        ('Gratitude Quotes', 'gratitude-quotes'),
        ('Self Love Quotes', 'self-love-quotes'),
        ('Confidence Quotes', 'confidence-quotes'),
        ('Hard Work Quotes', 'hard-work-quotes'),
        ('Dream Big Quotes', 'dream-big-quotes'),
        ('Change Quotes', 'change-quotes'),
        ('Focus Quotes', 'focus-quotes'),
        ('Patience Quotes', 'patience-quotes'),
    ],
    'interview-questions': [
        ('Python Interview Questions', 'python-interview-questions'),
        ('JavaScript Interview Questions', 'javascript-interview-questions'),
        ('React Interview Questions', 'react-interview-questions'),
        ('Django Interview Questions', 'django-interview-questions'),
        ('Node.js Interview Questions', 'nodejs-interview-questions'),
        ('SQL Interview Questions', 'sql-interview-questions'),
        ('System Design Interview Questions', 'system-design-interview-questions'),
        ('Data Structures Interview Questions', 'data-structures-interview-questions'),
        ('Algorithms Interview Questions', 'algorithms-interview-questions'),
        ('Java Interview Questions', 'java-interview-questions'),
        ('TypeScript Interview Questions', 'typescript-interview-questions'),
        ('AWS Interview Questions', 'aws-interview-questions'),
        ('Docker Interview Questions', 'docker-interview-questions'),
        ('REST API Interview Questions', 'rest-api-interview-questions'),
        ('Git Interview Questions', 'git-interview-questions'),
        ('CSS Interview Questions', 'css-interview-questions'),
        ('HTML Interview Questions', 'html-interview-questions'),
        ('Vue.js Interview Questions', 'vuejs-interview-questions'),
        ('Angular Interview Questions', 'angular-interview-questions'),
        ('Machine Learning Interview Questions', 'machine-learning-interview-questions'),
        ('Data Science Interview Questions', 'data-science-interview-questions'),
        ('DevOps Interview Questions', 'devops-interview-questions'),
        ('Kubernetes Interview Questions', 'kubernetes-interview-questions'),
        ('MongoDB Interview Questions', 'mongodb-interview-questions'),
        ('PostgreSQL Interview Questions', 'postgresql-interview-questions'),
        ('Redis Interview Questions', 'redis-interview-questions'),
        ('GraphQL Interview Questions', 'graphql-interview-questions'),
        ('Microservices Interview Questions', 'microservices-interview-questions'),
        ('Behavioral Interview Questions', 'behavioral-interview-questions'),
        ('Frontend Interview Questions', 'frontend-interview-questions'),
    ],
    'project-ideas': [
        ('Python Project Ideas', 'python-project-ideas'),
        ('JavaScript Project Ideas', 'javascript-project-ideas'),
        ('React Project Ideas', 'react-project-ideas'),
        ('Django Project Ideas', 'django-project-ideas'),
        ('Machine Learning Project Ideas', 'machine-learning-project-ideas'),
        ('Web Development Project Ideas', 'web-development-project-ideas'),
        ('Mobile App Project Ideas', 'mobile-app-project-ideas'),
        ('Data Science Project Ideas', 'data-science-project-ideas'),
        ('Beginner Project Ideas', 'beginner-project-ideas'),
        ('Advanced Project Ideas', 'advanced-project-ideas'),
        ('Full Stack Project Ideas', 'full-stack-project-ideas'),
        ('API Project Ideas', 'api-project-ideas'),
        ('Open Source Project Ideas', 'open-source-project-ideas'),
        ('Portfolio Project Ideas', 'portfolio-project-ideas'),
        ('Hackathon Project Ideas', 'hackathon-project-ideas'),
        ('Node.js Project Ideas', 'nodejs-project-ideas'),
        ('Flutter Project Ideas', 'flutter-project-ideas'),
        ('Vue.js Project Ideas', 'vuejs-project-ideas'),
        ('Automation Project Ideas', 'automation-project-ideas'),
        ('Blockchain Project Ideas', 'blockchain-project-ideas'),
        ('IoT Project Ideas', 'iot-project-ideas'),
        ('Game Development Project Ideas', 'game-development-project-ideas'),
        ('Chrome Extension Project Ideas', 'chrome-extension-project-ideas'),
        ('CLI Tool Project Ideas', 'cli-tool-project-ideas'),
        ('SaaS Project Ideas', 'saas-project-ideas'),
    ],
    'thesis-topics': [
        ('Computer Science Thesis Topics', 'computer-science-thesis-topics'),
        ('Artificial Intelligence Thesis Topics', 'artificial-intelligence-thesis-topics'),
        ('Machine Learning Thesis Topics', 'machine-learning-thesis-topics'),
        ('Cybersecurity Thesis Topics', 'cybersecurity-thesis-topics'),
        ('Data Science Thesis Topics', 'data-science-thesis-topics'),
        ('Software Engineering Thesis Topics', 'software-engineering-thesis-topics'),
        ('Business Management Thesis Topics', 'business-management-thesis-topics'),
        ('Marketing Thesis Topics', 'marketing-thesis-topics'),
        ('Psychology Thesis Topics', 'psychology-thesis-topics'),
        ('Education Thesis Topics', 'education-thesis-topics'),
        ('Environmental Science Thesis Topics', 'environmental-science-thesis-topics'),
        ('Public Health Thesis Topics', 'public-health-thesis-topics'),
        ('Economics Thesis Topics', 'economics-thesis-topics'),
        ('Finance Thesis Topics', 'finance-thesis-topics'),
        ('Nursing Thesis Topics', 'nursing-thesis-topics'),
        ('Law Thesis Topics', 'law-thesis-topics'),
        ('Sociology Thesis Topics', 'sociology-thesis-topics'),
        ('Political Science Thesis Topics', 'political-science-thesis-topics'),
        ('History Thesis Topics', 'history-thesis-topics'),
        ('Literature Thesis Topics', 'literature-thesis-topics'),
        ('Architecture Thesis Topics', 'architecture-thesis-topics'),
        ('Civil Engineering Thesis Topics', 'civil-engineering-thesis-topics'),
        ('Mechanical Engineering Thesis Topics', 'mechanical-engineering-thesis-topics'),
        ('Electrical Engineering Thesis Topics', 'electrical-engineering-thesis-topics'),
        ('Biotechnology Thesis Topics', 'biotechnology-thesis-topics'),
    ],
    'bios': [
        ('Instagram Bio Ideas', 'instagram-bio-ideas'),
        ('Twitter Bio Ideas', 'twitter-bio-ideas'),
        ('LinkedIn Bio Ideas', 'linkedin-bio-ideas'),
        ('TikTok Bio Ideas', 'tiktok-bio-ideas'),
        ('Developer Bio Ideas', 'developer-bio-ideas'),
        ('Designer Bio Ideas', 'designer-bio-ideas'),
        ('Entrepreneur Bio Ideas', 'entrepreneur-bio-ideas'),
        ('Student Bio Ideas', 'student-bio-ideas'),
        ('Freelancer Bio Ideas', 'freelancer-bio-ideas'),
        ('Content Creator Bio Ideas', 'content-creator-bio-ideas'),
        ('Funny Bio Ideas', 'funny-bio-ideas'),
        ('Short Bio Ideas', 'short-bio-ideas'),
        ('Professional Bio Ideas', 'professional-bio-ideas'),
        ('Aesthetic Bio Ideas', 'aesthetic-bio-ideas'),
        ('Attitude Bio Ideas', 'attitude-bio-ideas'),
    ],
    'usernames': [
        ('Cool Username Ideas', 'cool-username-ideas'),
        ('Gaming Username Ideas', 'gaming-username-ideas'),
        ('Instagram Username Ideas', 'instagram-username-ideas'),
        ('TikTok Username Ideas', 'tiktok-username-ideas'),
        ('Twitter Username Ideas', 'twitter-username-ideas'),
        ('Discord Username Ideas', 'discord-username-ideas'),
        ('YouTube Channel Name Ideas', 'youtube-channel-name-ideas'),
        ('Aesthetic Username Ideas', 'aesthetic-username-ideas'),
        ('Funny Username Ideas', 'funny-username-ideas'),
        ('Short Username Ideas', 'short-username-ideas'),
        ('Dark Username Ideas', 'dark-username-ideas'),
        ('Cute Username Ideas', 'cute-username-ideas'),
        ('Unique Username Ideas', 'unique-username-ideas'),
        ('Gamer Tag Ideas', 'gamer-tag-ideas'),
        ('Streamer Name Ideas', 'streamer-name-ideas'),
    ],
    'hashtags': [
        ('Instagram Hashtags for Travel', 'instagram-hashtags-travel'),
        ('Instagram Hashtags for Food', 'instagram-hashtags-food'),
        ('Instagram Hashtags for Fitness', 'instagram-hashtags-fitness'),
        ('Instagram Hashtags for Business', 'instagram-hashtags-business'),
        ('Instagram Hashtags for Photography', 'instagram-hashtags-photography'),
        ('Instagram Hashtags for Fashion', 'instagram-hashtags-fashion'),
        ('Instagram Hashtags for Beauty', 'instagram-hashtags-beauty'),
        ('Instagram Hashtags for Motivation', 'instagram-hashtags-motivation'),
        ('TikTok Hashtags for Viral', 'tiktok-hashtags-viral'),
        ('Twitter Hashtags for Tech', 'twitter-hashtags-tech'),
        ('LinkedIn Hashtags for Professionals', 'linkedin-hashtags-professionals'),
        ('YouTube Tags for Gaming', 'youtube-tags-gaming'),
        ('Hashtags for Small Business', 'hashtags-small-business'),
        ('Hashtags for Entrepreneurs', 'hashtags-entrepreneurs'),
        ('Hashtags for Content Creators', 'hashtags-content-creators'),
    ],
}

# SEO category slugs that must exist before running this command
REQUIRED_CATEGORIES = [
    ('captions', 'Captions', 'Instagram, TikTok and social media captions for every occasion.'),
    ('quotes', 'Quotes', 'Motivational, inspirational and life quotes for every mood.'),
    ('interview-questions', 'Interview Questions', 'Technical and behavioral interview questions for developers.'),
    ('project-ideas', 'Project Ideas', 'Coding and development project ideas for all skill levels.'),
    ('thesis-topics', 'Thesis Topics', 'Research thesis topics across all academic disciplines.'),
    ('bios', 'Bio Ideas', 'Social media bio ideas for Instagram, Twitter, LinkedIn and more.'),
    ('usernames', 'Username Ideas', 'Creative username ideas for every platform.'),
    ('hashtags', 'Hashtag Sets', 'Curated hashtag sets for Instagram, TikTok, Twitter and more.'),
]


class Command(BaseCommand):
    help = 'Seed 500+ programmatic SEO pages from curated topic lists (idempotent).'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Preview without saving.')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        created_total = updated_total = 0

        # Ensure SEO categories exist
        for slug, name, desc in REQUIRED_CATEGORIES:
            if not dry_run:
                SEOCategory.objects.get_or_create(
                    slug=slug,
                    defaults={'name': name, 'description': desc, 'is_active': True},
                )

        categories = {c.slug: c for c in SEOCategory.objects.filter(is_active=True)}

        for cat_slug, topics in TOPIC_SEEDS.items():
            category = categories.get(cat_slug)
            if not category:
                self.stdout.write(self.style.WARNING(f'  Category "{cat_slug}" not found — skipping.'))
                continue

            for topic_name, topic_slug in topics:
                items = generate_items(cat_slug, topic_name, topic_slug, count=30)

                if dry_run:
                    self.stdout.write(f'  [DRY RUN] Would create/update: {topic_slug} ({len(items)} items)')
                    continue

                page, created = SEOPage.objects.update_or_create(
                    slug=topic_slug,
                    defaults={
                        'category': category,
                        'topic': topic_name,
                        'items': items,
                        'is_active': True,
                    },
                )

                # Link related tools by matching category slug keywords
                try:
                    from tools.models import Tool
                    keyword = cat_slug.split('-')[0]
                    related = Tool.objects.filter(
                        tags__icontains=keyword, is_active=True
                    )[:3]
                    page.related_tools.set(related)
                except Exception:
                    pass

                if created:
                    created_total += 1
                else:
                    updated_total += 1

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'Done. Created: {created_total}, Updated: {updated_total}, '
                f'Total: {created_total + updated_total} SEO pages.'
            ))
