from django.core.management.base import BaseCommand
from seo.models import SEOCategory, SEOPage
import random


class Command(BaseCommand):
    help = 'Seeds massive programmatic SEO library across all categories'

    def handle(self, *args, **kwargs):
        categories = [
            {'name': 'Captions', 'slug': 'captions', 'template_title': '100+ {topic} Captions for Instagram & TikTok', 'template_desc': 'Best {topic} captions for social media. Copy and paste viral captions.'},
            {'name': 'Hashtags', 'slug': 'hashtags', 'template_title': 'Top {topic} Hashtags for Growth', 'template_desc': 'Trending {topic} hashtags. Boost your reach with these selected tags.'},
            {'name': 'Usernames', 'slug': 'usernames', 'template_title': '50+ Aesthetic {topic} Usernames', 'template_desc': 'Unique {topic} username ideas for gaming, social, and professional accounts.'},
            {'name': 'Startup Ideas', 'slug': 'startup-ideas', 'template_title': '10+ Profitable {topic} Startup Ideas', 'template_desc': 'Innovative business and startup ideas in the {topic} niche.'},
            {'name': 'Thesis Topics', 'slug': 'thesis-topics', 'template_title': 'Top 20 {topic} Thesis Topics & Research Ideas', 'template_desc': 'Academic research topics for your {topic} thesis.'},
            {'name': 'Motivational Quotes', 'slug': 'motivational-quotes', 'template_title': '50+ Inspiring {topic} Quotes', 'template_desc': 'Best motivational quotes about {topic} to keep you inspired.'},
            {'name': 'Study Tips', 'slug': 'study-tips', 'template_title': 'How to Study {topic} Effectively', 'template_desc': 'Scientific study tips and hacks for mastering {topic}.'},
            {'name': 'Interview Questions', 'slug': 'interview-questions', 'template_title': 'Common {topic} Interview Questions & Answers', 'template_desc': 'Prepare for your {topic} interview with these expert questions.'},
            {'name': 'Resume Summaries', 'slug': 'resume-summaries', 'template_title': 'Professional {topic} Resume Summary Examples', 'template_desc': 'Winning resume summaries for {topic} professionals.'},
            {'name': 'Code Snippets', 'slug': 'snippets', 'template_title': 'Useful {topic} Code Snippets & Hacks', 'template_desc': 'Ready-to-use {topic} code snippets for developers.'},
            {'name': 'Pickup Lines', 'slug': 'pickup-lines', 'template_title': '50+ Smooth {topic} Pickup Lines', 'template_desc': 'Fun and cheesy {topic} pickup lines for social interaction.'},
        ]

        topics = [
            'AI', 'Tech', 'Nature', 'Travel', 'Coding', 'Fitness', 'Food', 'Gaming', 
            'Business', 'Design', 'Minimalism', 'Productivity', 'Self Care', 'Adventure',
            'SaaS', 'Web Development', 'Python', 'React', 'Cybersecurity', 'Blockchain',
            'Psychology', 'History', 'Physics', 'Biology', 'Literature', 'Philosophy'
        ]

        for cat_data in categories:
            cat, _ = SEOCategory.objects.update_or_create(
                slug=cat_data['slug'], 
                defaults={
                    'name': cat_data['name'],
                    'title_template': cat_data['template_title'],
                    'meta_desc_template': cat_data['template_desc']
                }
            )
            
            for topic in topics:
                slug = f"{cat.slug}-{topic.lower().replace(' ', '-')}"
                
                SEOPage.objects.update_or_create(
                    slug=slug,
                    defaults={
                        'category': cat,
                        'topic': topic,
                        'content_intro': f"Here is a curated list of {topic} content for your {cat.name} needs...",
                        'items': [f"Example {cat.name} item for {topic}", f"Another cool {topic} idea"],
                        'is_active': True
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"Successfully seeded {len(categories) * len(topics)} programmatic SEO pages."))
