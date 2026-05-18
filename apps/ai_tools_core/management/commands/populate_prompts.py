from django.core.management.base import BaseCommand
from apps.ai_tools_core.models import PromptTemplate

class Command(BaseCommand):
    help = "Populates the database with initial prompt templates."

    def handle(self, *args, **options):
        prompts = [
            # Career AI
            {"tool_slug": "ai-resume-builder", "system_prompt": "You are an expert resume builder.", "user_prompt_template": "Build a professional resume based on the following information: {user_input}"},
            {"tool_slug": "ats-checker", "system_prompt": "You are an expert ATS checker.", "user_prompt_template": "Check if the following resume is ATS-friendly: {user_input}"},
            {"tool_slug": "cover-letter-generator", "system_prompt": "You are an expert cover letter writer.", "user_prompt_template": "Write a cover letter for the following job: {user_input}"},
            {"tool_slug": "linkedin-headline-generator", "system_prompt": "You are an expert in writing LinkedIn headlines.", "user_prompt_template": "Generate a LinkedIn headline for the following profile: {user_input}"},
            {"tool_slug": "linkedin-post-generator", "system_prompt": "You are an expert in writing engaging LinkedIn posts.", "user_prompt_template": "Write a LinkedIn post about the following topic: {user_input}"},
            # Writing AI
            {"tool_slug": "ai-humanizer", "system_prompt": "You are an expert in making text sound more human.", "user_prompt_template": "Humanize the following text: {user_input}"},
            {"tool_slug": "essay-writer", "system_prompt": "You are an expert essay writer.", "user_prompt_template": "Write an essay on the following topic: {user_input}"},
            {"tool_slug": "paraphrasing-tool", "system_prompt": "You are an expert in paraphrasing text.", "user_prompt_template": "Paraphrase the following text: {user_input}"},
            {"tool_slug": "grammar-checker", "system_prompt": "You are an expert in grammar.", "user_prompt_template": "Check the grammar of the following text: {user_input}"},
            {"tool_slug": "email-writer", "system_prompt": "You are an expert in writing emails.", "user_prompt_template": "Write an email for the following purpose: {user_input}"},
            {"tool_slug": "cold-email-generator", "system_prompt": "You are an expert in writing cold emails.", "user_prompt_template": "Write a cold email for the following purpose: {user_input}"},
            # SEO / Content AI
            {"tool_slug": "blog-writer", "system_prompt": "You are an expert blog writer.", "user_prompt_template": "Write a blog post on the following topic: {user_input}"},
            {"tool_slug": "seo-article-generator", "system_prompt": "You are an expert in writing SEO-optimized articles.", "user_prompt_template": "Write an SEO article on the following topic: {user_input}"},
            {"tool_slug": "meta-description-generator", "system_prompt": "You are an expert in writing meta descriptions.", "user_prompt_template": "Write a meta description for the following page: {user_input}"},
            {"tool_slug": "keyword-cluster-generator", "system_prompt": "You are an expert in keyword clustering.", "user_prompt_template": "Generate keyword clusters for the following keywords: {user_input}"},
            # Creator AI
            {"tool_slug": "youtube-script-generator", "system_prompt": "You are an expert in writing YouTube scripts.", "user_prompt_template": "Write a YouTube script for the following video idea: {user_input}"},
            {"tool_slug": "youtube-title-generator", "system_prompt": "You are an expert in writing YouTube titles.", "user_prompt_template": "Generate YouTube titles for the following video idea: {user_input}"},
            {"tool_slug": "thumbnail-prompt-generator", "system_prompt": "You are an expert in creating prompts for thumbnails.", "user_prompt_template": "Generate a thumbnail prompt for the following video idea: {user_input}"},
            {"tool_slug": "instagram-caption-generator", "system_prompt": "You are an expert in writing Instagram captions.", "user_prompt_template": "Write an Instagram caption for the following post: {user_input}"},
            {"tool_slug": "tweet-generator", "system_prompt": "You are an expert in writing tweets.", "user_prompt_template": "Write a tweet about the following topic: {user_input}"},
            # Business AI
            {"tool_slug": "startup-name-generator", "system_prompt": "You are an expert in generating startup names.", "user_prompt_template": "Generate startup names for the following idea: {user_input}"},
            {"tool_slug": "business-plan-generator", "system_prompt": "You are an expert in writing business plans.", "user_prompt_template": "Write a business plan for the following idea: {user_input}"},
            {"tool_slug": "logo-prompt-generator", "system_prompt": "You are an expert in creating prompts for logos.", "user_prompt_template": "Generate a logo prompt for the following company: {user_input}"},
            {"tool_slug": "image-prompt-generator", "system_prompt": "You are an expert in creating prompts for images.", "user_prompt_template": "Generate an image prompt for the following idea: {user_input}"},
            # Student AI
            {"tool_slug": "notes-generator", "system_prompt": "You are an expert in generating notes.", "user_prompt_template": "Generate notes for the following topic: {user_input}"},
            {"tool_slug": "quiz-generator", "system_prompt": "You are an expert in creating quizzes.", "user_prompt_template": "Create a quiz for the following topic: {user_input}"},
            {"tool_slug": "flashcard-generator", "system_prompt": "You are an expert in creating flashcards.", "user_prompt_template": "Create flashcards for the following topic: {user_input}"},
            # Developer AI
            {"tool_slug": "sql-query-generator", "system_prompt": "You are an expert in SQL.", "user_prompt_template": "Generate a SQL query for the following request: {user_input}"},
            {"tool_slug": "regex-generator", "system_prompt": "You are an expert in regular expressions.", "user_prompt_template": "Generate a regex for the following pattern: {user_input}"},
            {"tool_slug": "code-debugger", "system_prompt": "You are an expert in debugging code.", "user_prompt_template": "Debug the following code: {user_input}"},
        ]

        for prompt_data in prompts:
            PromptTemplate.objects.get_or_create(
                tool_slug=prompt_data["tool_slug"],
                defaults=prompt_data
            )

        self.stdout.write(self.style.SUCCESS("Successfully populated prompts."))
