from django.urls import path
from .views import (
    AIResumeBuilderView, ATSCheckerView, CoverLetterGeneratorView, LinkedInHeadlineGeneratorView, LinkedInPostGeneratorView,
    AIHumanizerView, EssayWriterView, ParaphrasingToolView, GrammarCheckerView, EmailWriterView, ColdEmailGeneratorView,
    BlogWriterView, SEOArticleGeneratorView, MetaDescriptionGeneratorView, KeywordClusterGeneratorView,
    YouTubeScriptGeneratorView, YouTubeTitleGeneratorView, ThumbnailPromptGeneratorView, InstagramCaptionGeneratorView, TweetGeneratorView,
    StartupNameGeneratorView, BusinessPlanGeneratorView, LogoPromptGeneratorView, ImagePromptGeneratorView,
    NotesGeneratorView, QuizGeneratorView, FlashcardGeneratorView,
    SQLQueryGeneratorView, RegexGeneratorView, CodeDebuggerView
)

urlpatterns = [
    # Career AI
    path("resume-builder/", AIResumeBuilderView.as_view(), name="ai_resume_builder"),
    path("ats-checker/", ATSCheckerView.as_view(), name="ats_checker"),
    path("cover-letter-generator/", CoverLetterGeneratorView.as_view(), name="cover_letter_generator"),
    path("linkedin-headline-generator/", LinkedInHeadlineGeneratorView.as_view(), name="linkedin_headline_generator"),
    path("linkedin-post-generator/", LinkedInPostGeneratorView.as_view(), name="linkedin_post_generator"),
    # Writing AI
    path("ai-humanizer/", AIHumanizerView.as_view(), name="ai_humanizer"),
    path("essay-writer/", EssayWriterView.as_view(), name="essay_writer"),
    path("paraphrasing-tool/", ParaphrasingToolView.as_view(), name="paraphrasing_tool"),
    path("grammar-checker/", GrammarCheckerView.as_view(), name="grammar_checker"),
    path("email-writer/", EmailWriterView.as_view(), name="email_writer"),
    path("cold-email-generator/", ColdEmailGeneratorView.as_view(), name="cold_email_generator"),
    # SEO / Content AI
    path("blog-writer/", BlogWriterView.as_view(), name="blog_writer"),
    path("seo-article-generator/", SEOArticleGeneratorView.as_view(), name="seo_article_generator"),
    path("meta-description-generator/", MetaDescriptionGeneratorView.as_view(), name="meta_description_generator"),
    path("keyword-cluster-generator/", KeywordClusterGeneratorView.as_view(), name="keyword_cluster_generator"),
    # Creator AI
    path("youtube-script-generator/", YouTubeScriptGeneratorView.as_view(), name="youtube_script_generator"),
    path("youtube-title-generator/", YouTubeTitleGeneratorView.as_view(), name="youtube_title_generator"),
    path("thumbnail-prompt-generator/", ThumbnailPromptGeneratorView.as_view(), name="thumbnail_prompt_generator"),
    path("instagram-caption-generator/", InstagramCaptionGeneratorView.as_view(), name="instagram_caption_generator"),
    path("tweet-generator/", TweetGeneratorView.as_view(), name="tweet_generator"),
    # Business AI
    path("startup-name-generator/", StartupNameGeneratorView.as_view(), name="startup_name_generator"),
    path("business-plan-generator/", BusinessPlanGeneratorView.as_view(), name="business_plan_generator"),
    path("logo-prompt-generator/", LogoPromptGeneratorView.as_view(), name="logo_prompt_generator"),
    path("image-prompt-generator/", ImagePromptGeneratorView.as_view(), name="image_prompt_generator"),
    # Student AI
    path("notes-generator/", NotesGeneratorView.as_view(), name="notes_generator"),
    path("quiz-generator/", QuizGeneratorView.as_view(), name="quiz_generator"),
    path("flashcard-generator/", FlashcardGeneratorView.as_view(), name="flashcard_generator"),
    # Developer AI
    path("sql-query-generator/", SQLQueryGeneratorView.as_view(), name="sql_query_generator"),
    path("regex-generator/", RegexGeneratorView.as_view(), name="regex_generator"),
    path("code-debugger/", CodeDebuggerView.as_view(), name="code_debugger"),
]
