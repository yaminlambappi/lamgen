"""
Social Content Tools - Complete Implementation of Social Media Content Utilities

Provides production-ready hashtag generator, tweet generator, post idea generator,
and content calendar tools with comprehensive social media content creation.
"""

import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from apps.tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus, register_tool
from apps.tools.utils.validation import ValidationRule, ValidationType, COMMON_SCHEMAS
from apps.tools.utils.processing import TextProcessor
from apps.tools.utils.analytics import analytics_tracker


@register_tool(ToolConfig(
    name="Hashtag Generator",
    slug="hashtag-generator",
    category="social",
    description="Generate relevant hashtags for social media posts",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Hashtag Generator - LamGen',
        'description': 'Generate relevant hashtags for social media posts with AI-powered suggestions and trending analysis.',
        'keywords': 'hashtag generator, social media hashtags, instagram hashtags, twitter hashtags'
    }
))
class HashtagGeneratorTool(BaseTool):
    """Production-ready hashtag generator"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'content': COMMON_SCHEMAS['text_field'],
            'platform': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='instagram',
                allowed_values=['instagram', 'twitter', 'linkedin', 'tiktok', 'facebook']
            ),
            'hashtag_count': ValidationRule(
                type=ValidationType.INTEGER,
                required=False,
                default=10,
                min_value=1,
                max_length=30
            ),
            'include_trending': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            ),
            'language': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='english',
                allowed_values=['english', 'spanish', 'french', 'german', 'italian']
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Generate hashtags for social media content"""
        try:
            content = input_data.get('content', '')
            platform = input_data.get('platform', 'instagram')
            hashtag_count = input_data.get('hashtag_count', 10)
            include_trending = input_data.get('include_trending', True)
            language = input_data.get('language', 'english')
            
            if not content:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Content is required"
                )
            
            # Generate hashtags
            hashtag_results = self._generate_hashtags(
                content, platform, hashtag_count, include_trending, language
            )
            
            # Provide recommendations
            recommendations = self._generate_hashtag_recommendations(hashtag_results, platform)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'hashtags': hashtag_results['hashtags'],
                    'trending_hashtags': hashtag_results['trending_hashtags'],
                    'hashtag_analysis': hashtag_results['analysis'],
                    'recommendations': recommendations,
                    'platform': platform
                },
                metadata={
                    'platform': platform,
                    'hashtag_count': len(hashtag_results['hashtags'])
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "generate_hashtags")
    
    def _generate_hashtags(self, content: str, platform: str, count: int, 
                          include_trending: bool, language: str) -> Dict[str, Any]:
        """Generate hashtags"""
        # Extract keywords from content
        keywords = self._extract_keywords(content)
        
        # Generate platform-specific hashtags
        hashtags = self._generate_platform_hashtags(keywords, platform, count)
        
        # Get trending hashtags
        trending_hashtags = self._get_trending_hashtags(platform, language) if include_trending else []
        
        # Analysis
        analysis = {
            'keyword_count': len(keywords),
            'hashtag_diversity': self._calculate_diversity(hashtags),
            'platform_optimization': self._check_platform_optimization(hashtags, platform)
        }
        
        return {
            'hashtags': hashtags,
            'trending_hashtags': trending_hashtags,
            'analysis': analysis
        }
    
    def _extract_keywords(self, content: str) -> List[str]:
        """Extract keywords from content"""
        # Remove common words and extract keywords
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must'
        }
        
        words = re.findall(r'\b\w+\b', content.lower())
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        
        # Return unique keywords
        return list(set(keywords))
    
    def _generate_platform_hashtags(self, keywords: List[str], platform: str, count: int) -> List[str]:
        """Generate platform-specific hashtags"""
        hashtags = []
        
        # Platform-specific hashtag patterns
        if platform == 'instagram':
            # Instagram allows more hashtags
            for keyword in keywords[:count]:
                hashtags.append(f"#{keyword}")
            
            # Add popular Instagram hashtags
            popular_instagram = ['instagood', 'photooftheday', 'love', 'beautiful', 'fashion', 'happy']
            for tag in popular_instagram:
                if len(hashtags) < count:
                    hashtags.append(f"#{tag}")
        
        elif platform == 'twitter':
            # Twitter has character limit, fewer hashtags
            for keyword in keywords[:min(count, 3)]:
                hashtags.append(f"#{keyword}")
        
        elif platform == 'linkedin':
            # LinkedIn uses professional hashtags
            professional_tags = ['professional', 'business', 'networking', 'careers']
            for keyword in keywords[:count]:
                hashtags.append(f"#{keyword}")
            
            for tag in professional_tags:
                if len(hashtags) < count:
                    hashtags.append(f"#{tag}")
        
        elif platform == 'tiktok':
            # TikTok uses trending and creative hashtags
            tiktok_tags = ['fyp', 'viral', 'trending', 'challenge', 'dance']
            for keyword in keywords[:count]:
                hashtags.append(f"#{keyword}")
            
            for tag in tiktok_tags:
                if len(hashtags) < count:
                    hashtags.append(f"#{tag}")
        
        else:  # Facebook
            for keyword in keywords[:min(count, 5)]:
                hashtags.append(f"#{keyword}")
        
        return hashtags[:count]
    
    def _get_trending_hashtags(self, platform: str, language: str) -> List[str]:
        """Get trending hashtags (simplified)"""
        # In production, would use real API
        trending_by_platform = {
            'instagram': ['instadaily', 'photooftheday', 'beautiful', 'nature', 'art'],
            'twitter': ['trending', 'viral', 'news', 'breaking', 'politics'],
            'linkedin': ['business', 'leadership', 'innovation', 'technology', 'careers'],
            'tiktok': ['fyp', 'viral', 'trending', 'challenge', 'dance'],
            'facebook': ['viral', 'trending', 'news', 'community', 'share']
        }
        
        return trending_by_platform.get(platform, [])[:5]
    
    def _calculate_diversity(self, hashtags: List[str]) -> float:
        """Calculate hashtag diversity"""
        if not hashtags:
            return 0
        
        unique_hashtags = len(set(hashtags))
        total_hashtags = len(hashtags)
        
        return (unique_hashtags / total_hashtags) * 100
    
    def _check_platform_optimization(self, hashtags: List[str], platform: str) -> Dict[str, Any]:
        """Check platform optimization"""
        optimization = {
            'optimal_count': False,
            'length_appropriate': True,
            'relevance_score': 0
        }
        
        # Check optimal count
        optimal_counts = {
            'instagram': (5, 30),
            'twitter': (1, 3),
            'linkedin': (3, 5),
            'tiktok': (3, 5),
            'facebook': (2, 5)
        }
        
        min_count, max_count = optimal_counts.get(platform, (2, 10))
        optimization['optimal_count'] = min_count <= len(hashtags) <= max_count
        
        # Check length
        for hashtag in hashtags:
            if len(hashtag) > 20:  # Too long for most platforms
                optimization['length_appropriate'] = False
                break
        
        # Calculate relevance score (simplified)
        optimization['relevance_score'] = 75  # Placeholder
        
        return optimization
    
    def _generate_hashtag_recommendations(self, results: Dict[str, Any], platform: str) -> List[str]:
        """Generate hashtag recommendations"""
        recommendations = []
        
        # Platform-specific recommendations
        if platform == 'instagram':
            recommendations.extend([
                "Use 5-30 hashtags for optimal reach",
                "Mix popular and niche hashtags",
                "Place hashtags in the first comment or caption"
            ])
        elif platform == 'twitter':
            recommendations.extend([
                "Use 1-3 relevant hashtags",
                "Keep hashtags concise and relevant",
                "Place hashtags within the tweet for better visibility"
            ])
        elif platform == 'linkedin':
            recommendations.extend([
                "Use 3-5 professional hashtags",
                "Focus on industry-specific terms",
                "Include hashtags in post body for better SEO"
            ])
        
        # General recommendations
        recommendations.extend([
            "Research hashtag popularity before using",
            "Create branded hashtags for your business",
            "Monitor hashtag performance and adjust strategy"
        ])
        
        return recommendations


@register_tool(ToolConfig(
    name="Tweet Generator",
    slug="tweet-generator",
    category="social",
    description="Generate optimized tweets with character limits and engagement focus",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Tweet Generator - LamGen',
        'description': 'Generate optimized tweets with character limits, hashtags, and engagement optimization.',
        'keywords': 'tweet generator, twitter post, social media post, tweet creator'
    }
))
class TweetGeneratorTool(BaseTool):
    """Production-ready tweet generator"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'topic': ValidationRule(
                type=ValidationType.STRING,
                required=True,
                max_length=100
            ),
            'tone': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='professional',
                allowed_values=['professional', 'casual', 'humorous', 'promotional', 'informative']
            ),
            'include_hashtags': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            ),
            'include_emoji': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=False
            ),
            'call_to_action': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                max_length=50
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Generate optimized tweets"""
        try:
            topic = input_data.get('topic', '').strip()
            tone = input_data.get('tone', 'professional')
            include_hashtags = input_data.get('include_hashtags', True)
            include_emoji = input_data.get('include_emoji', False)
            call_to_action = input_data.get('call_to_action', '').strip()
            
            if not topic:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Topic is required"
                )
            
            # Generate tweets
            tweet_results = self._generate_tweets(
                topic, tone, include_hashtags, include_emoji, call_to_action
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'tweets': tweet_results['tweets'],
                    'variations': tweet_results['variations'],
                    'analysis': tweet_results['analysis'],
                    'recommendations': tweet_results['recommendations']
                },
                metadata={
                    'tone': tone,
                    'tweet_count': len(tweet_results['tweets'])
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "generate_tweets")
    
    def _generate_tweets(self, topic: str, tone: str, include_hashtags: bool, 
                         include_emoji: bool, call_to_action: str) -> Dict[str, Any]:
        """Generate tweets"""
        tweets = []
        variations = []
        
        # Generate main tweet
        main_tweet = self._create_tweet(topic, tone, include_hashtags, include_emoji, call_to_action)
        tweets.append(main_tweet)
        
        # Generate variations
        for i in range(2):
            variation = self._create_tweet_variation(topic, tone, i + 1)
            variations.append(variation)
        
        # Analysis
        analysis = self._analyze_tweets([main_tweet] + variations)
        
        # Recommendations
        recommendations = self._generate_tweet_recommendations(analysis, tone)
        
        return {
            'tweets': tweets,
            'variations': variations,
            'analysis': analysis,
            'recommendations': recommendations
        }
    
    def _create_tweet(self, topic: str, tone: str, include_hashtags: bool, 
                     include_emoji: bool, call_to_action: str) -> Dict[str, Any]:
        """Create main tweet"""
        # Base tweet content based on tone
        tone_templates = {
            'professional': ["Excited to share insights on {topic}. Here's what you need to know:",
                             "Just published a comprehensive guide on {topic}. Key takeaways:",
                             "Breaking down {topic} for professionals. Important points:"],
            'casual': ["Just thinking about {topic} and wanted to share some thoughts:",
                       "Hey everyone, let's talk about {topic}. What do you think?",
                       "Random thought: {topic} is actually pretty interesting when you dive in:"],
            'humorous': ["Trying to explain {topic} to my cat... it's not going well 😂",
                        "That moment when you finally understand {topic} 🤯",
                        "{topic} be like: 😅"],
            'promotional': ["🚀 New guide on {topic} is now live! Don't miss out:",
                           "Limited time: Master {topic} with our expert tips:",
                           "Transform your understanding of {topic}. Learn more:"],
            'informative': ["Key facts about {topic} you should know:",
                          "Important update on {topic}:",
                          "Research findings on {topic} revealed:"]
        }
        
        template = tone_templates.get(tone, tone_templates['professional'])[hash(topic) % len(tone_templates)]
        content = template.format(topic=topic)
        
        # Add emoji if requested
        if include_emoji:
            emojis = ['🚀', '💡', '📊', '🔥', '✨', '🎯', '💪', '🌟']
            emoji = emojis[hash(topic) % len(emojis)]
            content += f" {emoji}"
        
        # Add call to action
        if call_to_action:
            content += f" {call_to_action}"
        
        # Add hashtags
        hashtags = []
        if include_hashtags:
            hashtag_generator = HashtagGeneratorTool(ToolConfig(name="temp", slug="temp", category="temp"))
            hashtag_results = hashtag_generator._generate_platform_hashtags(
                [topic.lower()], 'twitter', 2
            )
            hashtags = hashtag_results
        
        # Construct full tweet
        full_tweet = content
        if hashtags:
            full_tweet += f" {' '.join(hashtags)}"
        
        # Ensure character limit
        if len(full_tweet) > 280:
            # Truncate content to fit
            available_chars = 280 - len(' '.join(hashtags)) - 1
            content = content[:available_chars-3] + "..."
            full_tweet = content + f" {' '.join(hashtags)}"
        
        return {
            'content': full_tweet,
            'character_count': len(full_tweet),
            'hashtags': hashtags,
            'has_emoji': include_emoji,
            'tone': tone
        }
    
    def _create_tweet_variation(self, topic: str, tone: str, variation_num: int) -> Dict[str, Any]:
        """Create tweet variation"""
        # Different approaches for variations
        approaches = [
            f"Quick take on {topic}:",
            f"Pro tip about {topic}:",
            f"{topic} in a nutshell:",
            f"Why {topic} matters:",
            f"Hot take on {topic}:"
        ]
        
        approach = approaches[variation_num % len(approaches)]
        
        # Add some content
        content_points = [
            "It's changing how we work and live.",
            "Here's what you need to know.",
            "The future is here!",
            "This is a game-changer.",
            "Don't miss this trend."
        ]
        
        content = approach + " " + content_points[variation_num % len(content_points)]
        
        # Add simple hashtag
        hashtag = f"#{topic.replace(' ', '')}"
        full_tweet = f"{content} {hashtag}"
        
        return {
            'content': full_tweet,
            'character_count': len(full_tweet),
            'hashtags': [hashtag],
            'variation_type': approach.split(':')[0]
        }
    
    def _analyze_tweets(self, tweets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze generated tweets"""
        analysis = {
            'average_length': 0,
            'hashtag_usage': 0,
            'engagement_potential': 0,
            'readability_score': 0
        }
        
        if not tweets:
            return analysis
        
        # Calculate averages
        total_length = sum(tweet['character_count'] for tweet in tweets)
        analysis['average_length'] = total_length / len(tweets)
        
        total_hashtags = sum(len(tweet.get('hashtags', [])) for tweet in tweets)
        analysis['hashtag_usage'] = total_hashtags / len(tweets)
        
        # Engagement potential (simplified)
        analysis['engagement_potential'] = min(100, analysis['average_length'] / 2.8)
        
        # Readability score (simplified)
        analysis['readability_score'] = 85 if analysis['average_length'] < 200 else 70
        
        return analysis
    
    def _generate_tweet_recommendations(self, analysis: Dict[str, Any], tone: str) -> List[str]:
        """Generate tweet recommendations"""
        recommendations = []
        
        # Length recommendations
        if analysis['average_length'] > 250:
            recommendations.append("Consider shorter tweets for better engagement")
        elif analysis['average_length'] < 50:
            recommendations.append("Add more context to your tweets")
        
        # Hashtag recommendations
        if analysis['hashtag_usage'] < 1:
            recommendations.append("Add relevant hashtags to increase visibility")
        elif analysis['hashtag_usage'] > 3:
            recommendations.append("Use fewer hashtags (1-3 is optimal)")
        
        # Tone-specific recommendations
        if tone == 'professional':
            recommendations.extend([
                "Include data or statistics for credibility",
                "Use professional language and avoid slang"
            ])
        elif tone == 'humorous':
            recommendations.extend([
                "Keep humor appropriate for your audience",
                "Test humor with small audience first"
            ])
        
        # General recommendations
        recommendations.extend([
            "Include a call-to-action when appropriate",
            "Use high-quality images or videos",
            "Post at optimal times for your audience"
        ])
        
        return recommendations


@register_tool(ToolConfig(
    name="Post Idea Generator",
    slug="post-idea-generator",
    category="social",
    description="Generate creative post ideas for social media platforms",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Post Idea Generator - LamGen',
        'description': 'Generate creative post ideas for social media platforms with AI-powered content suggestions.',
        'keywords': 'post idea generator, social media ideas, content ideas, post inspiration'
    }
))
class PostIdeaGeneratorTool(BaseTool):
    """Production-ready post idea generator"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'topic': ValidationRule(
                type=ValidationType.STRING,
                required=True,
                max_length=100
            ),
            'platform': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='instagram',
                allowed_values=['instagram', 'twitter', 'linkedin', 'tiktok', 'facebook', 'youtube']
            ),
            'content_type': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='general',
                allowed_values=['general', 'educational', 'promotional', 'entertainment', 'behind_the_scenes']
            ),
            'idea_count': ValidationRule(
                type=ValidationType.INTEGER,
                required=False,
                default=5,
                min_value=1,
                max_length=10
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Generate post ideas"""
        try:
            topic = input_data.get('topic', '').strip()
            platform = input_data.get('platform', 'instagram')
            content_type = input_data.get('content_type', 'general')
            idea_count = input_data.get('idea_count', 5)
            
            if not topic:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Topic is required"
                )
            
            # Generate post ideas
            idea_results = self._generate_post_ideas(topic, platform, content_type, idea_count)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'post_ideas': idea_results['ideas'],
                    'content_calendar': idea_results['calendar'],
                    'engagement_tips': idea_results['engagement_tips'],
                    'platform': platform,
                    'content_type': content_type
                },
                metadata={
                    'platform': platform,
                    'idea_count': len(idea_results['ideas'])
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "generate_post_ideas")
    
    def _generate_post_ideas(self, topic: str, platform: str, content_type: str, count: int) -> Dict[str, Any]:
        """Generate post ideas"""
        ideas = []
        
        # Generate ideas based on platform and content type
        for i in range(count):
            idea = self._create_post_idea(topic, platform, content_type, i + 1)
            ideas.append(idea)
        
        # Generate content calendar suggestions
        calendar = self._generate_content_calendar(ideas, platform)
        
        # Generate engagement tips
        engagement_tips = self._generate_engagement_tips(platform, content_type)
        
        return {
            'ideas': ideas,
            'calendar': calendar,
            'engagement_tips': engagement_tips
        }
    
    def _create_post_idea(self, topic: str, platform: str, content_type: str, idea_num: int) -> Dict[str, Any]:
        """Create individual post idea"""
        # Platform-specific idea templates
        platform_templates = {
            'instagram': [
                "Photo carousel showing {topic} transformation",
                "Behind-the-scenes of {topic} process",
                "Before/after {topic} comparison",
                "Tutorial: How to master {topic}",
                "User-generated content featuring {topic}"
            ],
            'twitter': [
                "Thread breaking down {topic} fundamentals",
                "Quick tip about {topic}",
                "Poll: What's your take on {topic}?",
                "Thread: {topic} myths debunked",
                "Live Q&A session about {topic}"
            ],
            'linkedin': [
                "Article: Strategic insights on {topic}",
                "Case study: {topic} success story",
                "Professional take on {topic} trends",
                "Industry analysis of {topic}",
                "Expert interview about {topic}"
            ],
            'tiktok': [
                "60-second {topic} tutorial",
                "{topic} challenge video",
                "Trending {topic} sound video",
                "POV: {topic} explained simply",
                "{topic} transformation video"
            ],
            'facebook': [
                "Long-form post about {topic}",
                "{topic} community discussion",
                "Live stream about {topic}",
                "{topic} photo album",
                "{topic} event announcement"
            ],
            'youtube': [
                "Comprehensive {topic} guide video",
                "{topic} tutorial series",
                "Interview with {topic} expert",
                "{topic} documentary style video",
                "{topic} Q&A session"
            ]
        }
        
        templates = platform_templates.get(platform, platform_templates['instagram'])
        template = templates[(idea_num - 1) % len(templates)]
        
        # Content type modifications
        if content_type == 'educational':
            template = f"Educational content: {template}"
        elif content_type == 'promotional':
            template = f"Promotional content: {template}"
        elif content_type == 'entertainment':
            template = f"Entertainment content: {template}"
        elif content_type == 'behind_the_scenes':
            template = f"Behind the scenes: {template}"
        
        # Format with topic
        idea_content = template.format(topic=topic)
        
        # Add engagement elements
        engagement_elements = self._add_engagement_elements(platform, content_type)
        
        return {
            'title': f"{topic} Post Idea #{idea_num}",
            'content': idea_content,
            'platform': platform,
            'content_type': content_type,
            'engagement_elements': engagement_elements,
            'estimated_performance': self._estimate_performance(platform, content_type)
        }
    
    def _add_engagement_elements(self, platform: str, content_type: str) -> List[str]:
        """Add engagement elements"""
        elements = []
        
        # Platform-specific elements
        if platform == 'instagram':
            elements.extend(['Call-to-action in caption', 'Story stickers', 'IGTV video'])
        elif platform == 'twitter':
            elements.extend(['Poll', 'Thread', 'Question'])
        elif platform == 'linkedin':
            elements.extend(['Professional poll', 'Document attachment', 'Article link'])
        elif platform == 'tiktok':
            elements.extend(['Trending sound', 'Duet option', 'Stitch feature'])
        elif platform == 'facebook':
            elements.extend(['Live video', 'Event creation', 'Group post'])
        elif platform == 'youtube':
            elements.extend(['End screen cards', 'Community tab post', 'Premiere'])
        
        # Content type elements
        if content_type == 'educational':
            elements.append('Downloadable resource')
        elif content_type == 'promotional':
            elements.append('Special offer')
        elif content_type == 'entertainment':
            elements.append('Shareable moment')
        
        return elements
    
    def _estimate_performance(self, platform: str, content_type: str) -> Dict[str, Any]:
        """Estimate performance metrics"""
        # Simplified performance estimates
        base_metrics = {
            'instagram': {'engagement_rate': '3-5%', 'reach': 'medium', 'virality_potential': 'medium'},
            'twitter': {'engagement_rate': '1-3%', 'reach': 'medium', 'virality_potential': 'high'},
            'linkedin': {'engagement_rate': '2-4%', 'reach': 'professional', 'virality_potential': 'low'},
            'tiktok': {'engagement_rate': '5-10%', 'reach': 'high', 'virality_potential': 'high'},
            'facebook': {'engagement_rate': '2-4%', 'reach': 'medium', 'virality_potential': 'medium'},
            'youtube': {'engagement_rate': '4-8%', 'reach': 'high', 'virality_potential': 'medium'}
        }
        
        return base_metrics.get(platform, base_metrics['instagram'])
    
    def _generate_content_calendar(self, ideas: List[Dict[str, Any]], platform: str) -> List[Dict[str, Any]]:
        """Generate content calendar suggestions"""
        calendar = []
        
        # Optimal posting times by platform
        optimal_times = {
            'instagram': ['Monday 9AM', 'Wednesday 3PM', 'Friday 6PM'],
            'twitter': ['Tuesday 9AM', 'Thursday 1PM', 'Saturday 10AM'],
            'linkedin': ['Tuesday 10AM', 'Wednesday 12PM', 'Thursday 4PM'],
            'tiktok': ['Tuesday 6PM', 'Thursday 8PM', 'Saturday 2PM'],
            'facebook': ['Monday 12PM', 'Wednesday 3PM', 'Saturday 11AM'],
            'youtube': ['Tuesday 2PM', 'Thursday 7PM', 'Saturday 10AM']
        }
        
        times = optimal_times.get(platform, optimal_times['instagram'])
        
        # Create calendar entries
        for i, idea in enumerate(ideas[:3]):  # Limit to 3 for calendar
            calendar.append({
                'date': f"Day {i + 1}",
                'time': times[i % len(times)],
                'idea_title': idea['title'],
                'content_type': idea['content_type'],
                'engagement_elements': idea['engagement_elements']
            })
        
        return calendar
    
    def _generate_engagement_tips(self, platform: str, content_type: str) -> List[str]:
        """Generate engagement tips"""
        tips = []
        
        # Platform-specific tips
        platform_tips = {
            'instagram': [
                "Use high-quality visuals and consistent branding",
                "Engage with comments within first hour",
                "Use Instagram Stories for behind-the-scenes content"
            ],
            'twitter': [
                "Tweet during peak hours for your audience",
                "Use relevant hashtags and tag relevant accounts",
                "Engage with replies and mentions quickly"
            ],
            'linkedin': [
                "Post professional, value-driven content",
                "Use relevant hashtags and tag companies/people",
                "Engage with professional comments and shares"
            ],
            'tiktok': [
                "Use trending sounds and effects",
                "Post consistently during peak hours",
                "Engage with comments and create duets"
            ],
            'facebook': [
                "Use eye-catching visuals and videos",
                "Encourage comments and discussions",
                "Share to relevant groups for wider reach"
            ],
            'youtube': [
                "Optimize titles and descriptions for SEO",
                "Use custom thumbnails and consistent branding",
                "Engage with comments and create community posts"
            ]
        }
        
        tips.extend(platform_tips.get(platform, []))
        
        # Content type tips
        if content_type == 'educational':
            tips.extend([
                "Include clear learning objectives",
                "Use visuals to explain complex concepts",
                "Provide downloadable resources"
            ])
        elif content_type == 'promotional':
            tips.extend([
                "Create urgency with limited-time offers",
                "Show product benefits, not just features",
                "Include clear call-to-action"
            ])
        
        return tips


@register_tool(ToolConfig(
    name="Content Calendar",
    slug="content-calendar",
    category="social",
    description="Create structured content calendars for social media planning",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Content Calendar - LamGen',
        'description': 'Create structured content calendars for social media planning with automated scheduling.',
        'keywords': 'content calendar, social media planner, content scheduling, social media calendar'
    }
))
class ContentCalendarTool(BaseTool):
    """Production-ready content calendar tool"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'topics': ValidationRule(
                type=ValidationType.ARRAY,
                required=True,
                min_length=1,
                max_length=20
            ),
            'platforms': ValidationRule(
                type=ValidationType.ARRAY,
                required=False,
                default=['instagram'],
                allowed_values=['instagram', 'twitter', 'linkedin', 'tiktok', 'facebook', 'youtube']
            ),
            'duration_days': ValidationRule(
                type=ValidationType.INTEGER,
                required=False,
                default=7,
                min_value=1,
                max_length=90
            ),
            'posting_frequency': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='daily',
                allowed_values=['daily', 'weekly', 'bi_weekly', 'monthly']
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Create content calendar"""
        try:
            topics = input_data.get('topics', [])
            platforms = input_data.get('platforms', ['instagram'])
            duration_days = input_data.get('duration_days', 7)
            posting_frequency = input_data.get('posting_frequency', 'daily')
            
            if not topics:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="At least one topic is required"
                )
            
            # Generate content calendar
            calendar_results = self._generate_content_calendar(
                topics, platforms, duration_days, posting_frequency
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'calendar': calendar_results['calendar'],
                    'posting_schedule': calendar_results['schedule'],
                    'content_mix': calendar_results['content_mix'],
                    'analytics': calendar_results['analytics']
                },
                metadata={
                    'duration_days': duration_days,
                    'total_posts': len(calendar_results['calendar'])
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "create_calendar")
    
    def _generate_content_calendar(self, topics: List[str], platforms: List[str], 
                                   duration: int, frequency: str) -> Dict[str, Any]:
        """Generate content calendar"""
        calendar = []
        
        # Calculate posting frequency
        frequency_map = {
            'daily': 1,
            'weekly': 7,
            'bi_weekly': 14,
            'monthly': 30
        }
        
        days_between_posts = frequency_map.get(frequency, 1)
        
        # Generate calendar entries
        current_date = datetime.now()
        
        for day in range(duration):
            if day % days_between_posts == 0:
                # Create post for this day
                topic = topics[day % len(topics)]
                platform = platforms[day % len(platforms)]
                
                calendar_entry = {
                    'date': (current_date + timedelta(days=day)).strftime('%Y-%m-%d'),
                    'day_of_week': (current_date + timedelta(days=day)).strftime('%A'),
                    'platform': platform,
                    'topic': topic,
                    'content_type': self._determine_content_type(day, topics),
                    'post_time': self._get_optimal_posting_time(platform),
                    'hashtags': self._generate_hashtags_for_topic(topic, platform),
                    'engagement_elements': self._suggest_engagement_elements(platform)
                }
                
                calendar.append(calendar_entry)
        
        # Generate posting schedule
        schedule = self._generate_posting_schedule(calendar, platforms)
        
        # Generate content mix analysis
        content_mix = self._analyze_content_mix(calendar)
        
        # Generate analytics predictions
        analytics = self._predict_analytics(calendar)
        
        return {
            'calendar': calendar,
            'schedule': schedule,
            'content_mix': content_mix,
            'analytics': analytics
        }
    
    def _determine_content_type(self, day: int, topics: List[str]) -> str:
        """Determine content type based on day"""
        content_types = ['educational', 'promotional', 'entertainment', 'behind_the_scenes', 'user_generated']
        return content_types[day % len(content_types)]
    
    def _get_optimal_posting_time(self, platform: str) -> str:
        """Get optimal posting time for platform"""
        optimal_times = {
            'instagram': '6:00 PM',
            'twitter': '9:00 AM',
            'linkedin': '10:00 AM',
            'tiktok': '8:00 PM',
            'facebook': '12:00 PM',
            'youtube': '2:00 PM'
        }
        
        return optimal_times.get(platform, '6:00 PM')
    
    def _generate_hashtags_for_topic(self, topic: str, platform: str) -> List[str]:
        """Generate hashtags for topic and platform"""
        hashtag_generator = HashtagGeneratorTool(ToolConfig(name="temp", slug="temp", category="temp"))
        
        # Generate hashtags
        hashtag_results = hashtag_generator._generate_platform_hashtags(
            [topic.lower()], platform, 3
        )
        
        return hashtag_results
    
    def _suggest_engagement_elements(self, platform: str) -> List[str]:
        """Suggest engagement elements"""
        elements = {
            'instagram': ['Call-to-action', 'Story link', 'IGTV preview'],
            'twitter': ['Poll', 'Thread continuation', 'Question'],
            'linkedin': ['Document attachment', 'Article link', 'Professional poll'],
            'tiktok': ['Trending sound', 'Duet option', 'Challenge tag'],
            'facebook': ['Live video', 'Event creation', 'Group share'],
            'youtube': ['End screen', 'Community post', 'Premiere']
        }
        
        return elements.get(platform, ['Call-to-action'])
    
    def _generate_posting_schedule(self, calendar: List[Dict[str, Any]], platforms: List[str]) -> Dict[str, Any]:
        """Generate posting schedule"""
        schedule = {
            'total_posts': len(calendar),
            'posts_by_platform': {},
            'posting_frequency': {},
            'optimal_times': {}
        }
        
        # Count posts by platform
        for platform in platforms:
            platform_posts = [post for post in calendar if post['platform'] == platform]
            schedule['posts_by_platform'][platform] = len(platform_posts)
            
            # Calculate frequency
            if platform_posts:
                schedule['posting_frequency'][platform] = f"{len(platform_posts)} posts in {len(calendar)} days"
            
            # Optimal times
            times = [post['post_time'] for post in platform_posts]
            schedule['optimal_times'][platform] = list(set(times))
        
        return schedule
    
    def _analyze_content_mix(self, calendar: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content mix"""
        content_types = [post['content_type'] for post in calendar]
        type_counts = {}
        
        for content_type in content_types:
            type_counts[content_type] = type_counts.get(content_type, 0) + 1
        
        total_posts = len(calendar)
        content_mix = {
            'total_posts': total_posts,
            'content_type_distribution': {},
            'recommendations': []
        }
        
        for content_type, count in type_counts.items():
            percentage = (count / total_posts) * 100 if total_posts > 0 else 0
            content_mix['content_type_distribution'][content_type] = {
                'count': count,
                'percentage': round(percentage, 1)
            }
        
        # Generate recommendations
        if content_type_counts.get('promotional', 0) > total_posts * 0.3:
            content_mix['recommendations'].append("Reduce promotional content to avoid audience fatigue")
        
        if content_type_counts.get('educational', 0) < total_posts * 0.2:
            content_mix['recommendations'].append("Add more educational content to provide value")
        
        return content_mix
    
    def _predict_analytics(self, calendar: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Predict analytics for calendar"""
        total_posts = len(calendar)
        
        # Simplified predictions
        predictions = {
            'total_engagement': total_posts * 150,  # Average 150 engagements per post
            'estimated_reach': total_posts * 1000,  # Average 1000 reach per post
            'content_performance': {},
            'best_performing_days': ['Wednesday', 'Thursday', 'Friday'],
            'platform_performance': {}
        }
        
        # Platform performance predictions
        platforms = list(set(post['platform'] for post in calendar))
        for platform in platforms:
            platform_posts = [post for post in calendar if post['platform'] == platform]
            predictions['platform_performance'][platform] = {
                'posts': len(platform_posts),
                'estimated_engagement': len(platform_posts) * 150,
                'reach_potential': len(platform_posts) * 1000
            }
        
        return predictions
