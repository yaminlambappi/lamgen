"""
Social Optimization Tools - Complete Implementation of Social Media Optimization Utilities

Provides production-ready social media optimizer, aging post tool, cross-platform tool,
and social proof tool with comprehensive social media optimization.
"""

import re
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta

from apps.tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus, register_tool
from apps.tools.utils.validation import ValidationRule, ValidationType, COMMON_SCHEMAS
from apps.tools.utils.processing import TextProcessor
from apps.tools.utils.analytics import analytics_tracker


@register_tool(ToolConfig(
    name="Social Media Optimizer",
    slug="social-media-optimizer",
    category="social",
    description="Optimize social media content for better performance and engagement",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Social Media Optimizer - LamGen',
        'description': 'Optimize social media content for better performance, engagement, and reach with AI-powered suggestions.',
        'keywords': 'social media optimizer, content optimization, social media marketing, engagement optimization'
    }
))
class SocialMediaOptimizerTool(BaseTool):
    """Production-ready social media optimizer"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'content': COMMON_SCHEMAS['text_field'],
            'platform': ValidationRule(
                type=ValidationType.STRING,
                required=True,
                allowed_values=['instagram', 'twitter', 'linkedin', 'tiktok', 'facebook', 'youtube']
            ),
            'optimization_goals': ValidationRule(
                type=ValidationType.ARRAY,
                required=False,
                max_length=10
            ),
            'target_audience': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='general',
                max_length=50
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Optimize social media content"""
        try:
            content = input_data.get('content', '')
            platform = input_data.get('platform', '')
            optimization_goals = input_data.get('optimization_goals', [])
            target_audience = input_data.get('target_audience', 'general')
            
            if not content or not platform:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Content and platform are required"
                )
            
            # Optimize content
            optimization_results = self._optimize_content(
                content, platform, optimization_goals, target_audience
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'optimized_content': optimization_results['optimized_content'],
                    'improvements': optimization_results['improvements'],
                    'analysis': optimization_results['analysis'],
                    'recommendations': optimization_results['recommendations']
                },
                metadata={
                    'platform': platform,
                    'original_length': len(content),
                    'optimized_length': len(optimization_results['optimized_content'])
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "optimize_content")
    
    def _optimize_content(self, content: str, platform: str, 
                          goals: List[str], audience: str) -> Dict[str, Any]:
        """Optimize social media content"""
        # Analyze current content
        current_analysis = self._analyze_current_content(content, platform)
        
        # Generate improvements
        improvements = self._generate_improvements(
            content, platform, goals, audience, current_analysis
        )
        
        # Create optimized content
        optimized_content = self._create_optimized_content(content, improvements, platform)
        
        # Analyze optimized content
        optimized_analysis = self._analyze_optimized_content(optimized_content, platform)
        
        # Generate recommendations
        recommendations = self._generate_optimization_recommendations(
            current_analysis, optimized_analysis, platform
        )
        
        return {
            'optimized_content': optimized_content,
            'improvements': improvements,
            'analysis': {
                'original': current_analysis,
                'optimized': optimized_analysis
            },
            'recommendations': recommendations
        }
    
    def _analyze_current_content(self, content: str, platform: str) -> Dict[str, Any]:
        """Analyze current content"""
        analysis = {
            'length': len(content),
            'hashtags': 0,
            'mentions': 0,
            'links': 0,
            'emoji': 0,
            'questions': 0,
            'call_to_action': False,
            'structure_score': 0,
            'engagement_score': 0,
            'issues': []
        }
        
        # Count elements
        analysis['hashtags'] = len(re.findall(r'#\w+', content))
        analysis['mentions'] = len(re.findall(r'@\w+', content))
        analysis['links'] = len(re.findall(r'https?://[^\s]+', content))
        analysis['emoji'] = len(re.findall(r'[\U0001F600-\U0001F64F]', content))
        analysis['questions'] = len(re.findall(r'\?', content))
        
        # Check for call to action
        cta_phrases = ['click here', 'link in bio', 'shop now', 'learn more', 'visit', 'check out']
        analysis['call_to_action'] = any(phrase in content.lower() for phrase in cta_phrases)
        
        # Calculate structure score
        structure_score = 50  # Base score
        if analysis['hashtags'] > 0:
            structure_score += 10
        if analysis['mentions'] > 0:
            structure_score += 10
        if analysis['call_to_action']:
            structure_score += 15
        if analysis['questions'] > 0:
            structure_score += 10
        
        analysis['structure_score'] = min(100, structure_score)
        
        # Calculate engagement score
        engagement_score = 50  # Base score
        if analysis['emoji'] > 0:
            engagement_score += 10
        if analysis['questions'] > 0:
            engagement_score += 15
        if content.count('!') > 0:
            engagement_score += 10
        
        analysis['engagement_score'] = min(100, engagement_score)
        
        # Identify issues
        if len(content) > self._get_max_length(platform):
            analysis['issues'].append("Content too long for platform")
        
        if analysis['hashtags'] > self._get_optimal_hashtags(platform):
            analysis['issues'].append("Too many hashtags")
        
        if analysis['hashtags'] < self._get_min_hashtags(platform):
            analysis['issues'].append("Too few hashtags")
        
        return analysis
    
    def _get_max_length(self, platform: str) -> int:
        """Get max content length for platform"""
        lengths = {
            'twitter': 280,
            'instagram': 2200,
            'linkedin': 3000,
            'facebook': 80000,
            'tiktok': 150,
            'youtube': 5000
        }
        return lengths.get(platform, 280)
    
    def _get_optimal_hashtags(self, platform: str) -> int:
        """Get optimal hashtag count for platform"""
        optimal = {
            'twitter': 2,
            'instagram': 30,
            'linkedin': 3,
            'facebook': 3,
            'tiktok': 5,
            'youtube': 3
        }
        return optimal.get(platform, 3)
    
    def _get_min_hashtags(self, platform: str) -> int:
        """Get minimum hashtag count for platform"""
        minimum = {
            'twitter': 0,
            'instagram': 5,
            'linkedin': 1,
            'facebook': 0,
            'tiktok': 1,
            'youtube': 0
        }
        return minimum.get(platform, 0)
    
    def _generate_improvements(self, content: str, platform: str, 
                             goals: List[str], audience: str, analysis: Dict[str, Any]) -> List[str]:
        """Generate content improvements"""
        improvements = []
        
        # Length improvements
        if len(content) > self._get_max_length(platform):
            improvements.append(f"Shorten content to {self._get_max_length(platform)} characters")
        
        # Hashtag improvements
        current_hashtags = analysis['hashtags']
        optimal_hashtags = self._get_optimal_hashtags(platform)
        
        if current_hashtags < optimal_hashtags:
            needed = optimal_hashtags - current_hashtags
            improvements.append(f"Add {needed} relevant hashtags")
        elif current_hashtags > optimal_hashtags:
            excess = current_hashtags - optimal_hashtags
            improvements.append(f"Remove {excess} hashtags")
        
        # Engagement improvements
        if not analysis['call_to_action']:
            improvements.append("Add a clear call to action")
        
        if analysis['questions'] == 0:
            improvements.append("Add a question to encourage engagement")
        
        if analysis['emoji'] == 0 and platform in ['instagram', 'tiktok', 'facebook']:
            improvements.append("Add relevant emojis for visual appeal")
        
        # Goal-specific improvements
        if 'engagement' in goals:
            improvements.extend([
                "Add interactive elements like polls or questions",
                "Use emotional language to connect with audience"
            ])
        
        if 'reach' in goals:
            improvements.extend([
                "Use trending hashtags",
                "Tag relevant accounts or brands",
                "Include location tags if applicable"
            ])
        
        if 'conversion' in goals:
            improvements.extend([
                "Include clear call to action",
                "Add link to landing page",
                "Create urgency with time-sensitive offers"
            ])
        
        return improvements
    
    def _create_optimized_content(self, original: str, improvements: List[str], platform: str) -> str:
        """Create optimized content"""
        optimized = original
        
        # Apply improvements (simplified)
        for improvement in improvements:
            if "Shorten content" in improvement:
                max_length = self._get_max_length(platform)
                optimized = optimized[:max_length-3] + "..."
            elif "Add hashtags" in improvement:
                # Add relevant hashtags (simplified)
                hashtags = self._generate_relevant_hashtags(original, platform)
                optimized += f" {' '.join(hashtags)}"
            elif "Remove hashtags" in improvement:
                # Remove excess hashtags
                words = optimized.split()
                hashtag_count = 0
                new_words = []
                for word in words:
                    if word.startswith('#'):
                        hashtag_count += 1
                        if hashtag_count <= self._get_optimal_hashtags(platform):
                            new_words.append(word)
                    else:
                        new_words.append(word)
                optimized = ' '.join(new_words)
            elif "Add call to action" in improvement:
                if not any(cta in optimized.lower() for cta in ['link in bio', 'shop now', 'learn more']):
                    optimized += " Link in bio for more!"
            elif "Add question" in improvement:
                if '?' not in optimized:
                    optimized += " What do you think?"
            elif "Add emojis" in improvement:
                if not any(char in optimized for char in '😀😊😎🔥👍💯'):
                    optimized += " 😊"
        
        return optimized
    
    def _generate_relevant_hashtags(self, content: str, platform: str) -> List[str]:
        """Generate relevant hashtags"""
        # Extract keywords from content
        words = re.findall(r'\b\w+\b', content.lower())
        
        # Filter for relevant keywords
        relevant_words = [word for word in words if len(word) > 3 and word not in 
                          ['the', 'and', 'for', 'with', 'that', 'this', 'from', 'have', 'been']]
        
        # Generate hashtags
        hashtags = []
        for word in relevant_words[:5]:  # Limit to top 5
            hashtags.append(f"#{word}")
        
        return hashtags
    
    def _analyze_optimized_content(self, content: str, platform: str) -> Dict[str, Any]:
        """Analyze optimized content"""
        return self._analyze_current_content(content, platform)
    
    def _generate_optimization_recommendations(self, original: Dict[str, Any], 
                                               optimized: Dict[str, Any], platform: str) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []
        
        # Compare scores
        if optimized['structure_score'] > original['structure_score']:
            recommendations.append("Structure improved significantly")
        
        if optimized['engagement_score'] > original['engagement_score']:
            recommendations.append("Engagement potential increased")
        
        # Platform-specific recommendations
        platform_tips = {
            'instagram': [
                "Post consistently at optimal times",
                "Use Instagram Stories for behind-the-scenes content",
                "Engage with comments quickly"
            ],
            'twitter': [
                "Tweet during peak hours",
                "Use relevant hashtags and tag accounts",
                "Engage in conversations"
            ],
            'linkedin': [
                "Post during business hours",
                "Share professional, value-driven content",
                "Network with industry professionals"
            ],
            'tiktok': [
                "Post at peak times (6-9 PM)",
                "Use trending sounds and effects",
                "Create short, engaging videos"
            ],
            'facebook': [
                "Post when audience is most active",
                "Use eye-catching visuals",
                "Encourage comments and shares"
            ],
            'youtube': [
                "Optimize titles and descriptions",
                "Use custom thumbnails",
                "Engage with comments"
            ]
        }
        
        recommendations.extend(platform_tips.get(platform, []))
        
        return recommendations


@register_tool(ToolConfig(
    name="Aging Post",
    slug="aging-post",
    category="social",
    description="Age and repost social media content for extended reach",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Aging Post Tool - LamGen',
        'description': 'Age and repost social media content for extended reach and audience engagement.',
        'keywords': 'aging post, repost content, social media recycling, content repurposing'
    }
))
class AgingPostTool(BaseTool):
    """Production-ready aging post tool"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'original_post': COMMON_SCHEMAS['text_field'],
            'platform': ValidationRule(
                type=ValidationType.STRING,
                required=True,
                allowed_values=['instagram', 'twitter', 'linkedin', 'facebook']
            ),
            'aging_strategy': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='repost',
                allowed_values=['repost', 'recreate', 'archive', 'boost']
            ),
            'time_since_post': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='1_week',
                allowed_values=['1_day', '3_days', '1_week', '2_weeks', '1_month', '3_months', '6_months']
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Age and repost content"""
        try:
            original_post = input_data.get('original_post', '')
            platform = input_data.get('platform', '')
            aging_strategy = input_data.get('aging_strategy', 'repost')
            time_since_post = input_data.get('time_since_post', '1_week')
            
            if not original_post or not platform:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Original post and platform are required"
                )
            
            # Process aging post
            aging_results = self._process_aging_post(
                original_post, platform, aging_strategy, time_since_post
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'aged_content': aging_results['aged_content'],
                    'strategy': aging_results['strategy'],
                    'timing': aging_results['timing'],
                    'analysis': aging_results['analysis'],
                    'recommendations': aging_results['recommendations']
                },
                metadata={
                    'platform': platform,
                    'strategy': aging_strategy
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "age_post")
    
    def _process_aging_post(self, original: str, platform: str, 
                          strategy: str, time_since: str) -> Dict[str, Any]:
        """Process aging post"""
        # Analyze original post
        original_analysis = self._analyze_original_post(original, platform)
        
        # Determine optimal timing
        timing = self._determine_optimal_timing(platform, time_since)
        
        # Create aged content
        aged_content = self._create_aged_content(original, strategy, platform)
        
        # Analyze aged content
        aged_analysis = self._analyze_aged_content(aged_content, platform)
        
        # Generate recommendations
        recommendations = self._generate_aging_recommendations(
            original_analysis, aged_analysis, strategy, platform
        )
        
        return {
            'aged_content': aged_content,
            'strategy': strategy,
            'timing': timing,
            'analysis': {
                'original': original_analysis,
                'aged': aged_analysis
            },
            'recommendations': recommendations
        }
    
    def _analyze_original_post(self, content: str, platform: str) -> Dict[str, Any]:
        """Analyze original post"""
        analysis = {
            'performance_score': 0,
            'engagement_rate': 0,
            'virality_score': 0,
            'content_type': 'unknown',
            'optimal_for_repost': True
        }
        
        # Simplified performance analysis
        length = len(content)
        if platform == 'twitter':
            analysis['performance_score'] = 80 if length < 200 else 60
        elif platform == 'instagram':
            analysis['performance_score'] = 85 if length < 1500 else 70
        else:
            analysis['performance_score'] = 75
        
        # Content type identification
        if 'http' in content:
            analysis['content_type'] = 'link'
        elif '#' in content:
            analysis['content_type'] = 'hashtag_heavy'
        elif '@' in content:
            analysis['content_type'] = 'mention_heavy'
        else:
            analysis['content_type'] = 'text'
        
        # Determine if optimal for repost
        analysis['optimal_for_repost'] = analysis['performance_score'] > 60
        
        return analysis
    
    def _determine_optimal_timing(self, platform: str, time_since: str) -> Dict[str, Any]:
        """Determine optimal timing for reposting"""
        timing = {
            'optimal_days': [],
            'best_times': [],
            'frequency': '',
            'reasoning': ''
        }
        
        # Platform-specific timing
        if platform == 'instagram':
            if time_since in ['1_day', '3_days']:
                timing['optimal_days'] = ['Wait longer']
                timing['reasoning'] = 'Too recent for repost'
            elif time_since in ['1_week', '2_weeks']:
                timing['optimal_days'] = ['Saturday', 'Sunday']
                timing['best_times'] = ['9 AM', '6 PM']
                timing['frequency'] = 'Weekly'
                timing['reasoning'] = 'Optimal time for reposting'
            else:
                timing['optimal_days'] = ['Any day']
                timing['best_times'] = ['12 PM', '6 PM']
                timing['frequency'] = 'Monthly'
                timing['reasoning'] = 'Content is aged enough for repost'
        
        elif platform == 'twitter':
            if time_since in ['1_day']:
                timing['optimal_days'] = ['Wait longer']
                timing['reasoning'] = 'Too recent for repost'
            else:
                timing['optimal_days'] ['Any day']
                timing['best_times'] = ['9 AM', '12 PM', '6 PM']
                timing['frequency'] = 'Every 3-4 days'
                timing['reasoning'] = 'Twitter content has short lifespan'
        
        elif platform == 'linkedin':
            if time_since in ['1_day', '3_days']:
                timing['optimal_days'] = ['Wait longer']
                timing['reasoning'] = 'Too recent for repost'
            else:
                timing['optimal_days'] ['Tuesday', 'Wednesday', 'Thursday']
                timing['best_times'] = ['10 AM', '2 PM']
                timing['frequency'] = 'Bi-weekly'
                timing['reasoning'] = 'LinkedIn content has longer lifespan'
        
        elif platform == 'facebook':
            if time_since in ['1_day']:
                timing['optimal_days'] = ['Wait longer']
                timing['reasoning'] = 'Too recent for repost'
            else:
                timing['optimal_days'] ['Any day']
                timing['best_times'] = ['12 PM', '6 PM']
                timing['frequency'] = 'Weekly'
                timing['reasoning'] = 'Facebook content has good longevity'
        
        return timing
    
    def _create_aged_content(self, original: str, strategy: str, platform: str) -> str:
        """Create aged content based on strategy"""
        if strategy == 'repost':
            return self._create_repost(original, platform)
        elif strategy == 'recreate':
            return self._recreate_content(original, platform)
        elif strategy == 'archive':
            return self._archive_content(original, platform)
        elif strategy == 'boost':
            return self._boost_content(original, platform)
        else:
            return original
    
    def _create_repost(self, original: str, platform: str) -> str:
        """Create repost"""
        # Add repost indicator
        if platform == 'twitter':
            return f"🔄 Repost: {original}"
        elif platform == 'instagram':
            return f"🔄 {original}\n\n#repost #throwback"
        elif platform == 'linkedin':
            return f"🔄 Reposting this valuable content:\n\n{original}"
        elif platform == 'facebook':
            return f"🔄 Sharing this again:\n\n{original}"
        else:
            return f"🔄 {original}"
    
    def _recreate_content(self, original: str, platform: str) -> str:
        """Recreate content with new angle"""
        # Simplified recreation
        recreation_phrases = [
            "Looking back at this...",
            "This still holds true:",
            "Timeless wisdom:",
            "Still relevant:",
            "Worth sharing again:"
        ]
        
        phrase = recreation_phrases[hash(original) % len(recreation_phrases)]
        return f"{phrase} {original}"
    
    def _archive_content(self, original: str, platform: str) -> str:
        """Archive content"""
        return f"📚 Archived from {platform.title()}:\n\n{original}"
    
    def _boost_content(self, original: str, platform: str) -> str:
        """Boost content with promotion"""
        boost_phrases = [
            "🚀 Boosting this amazing content:",
            "⭐ Highlighting this again:",
            "🔥 This deserves more attention:",
            "💫 Bringing this back to the top:"
        ]
        
        phrase = boost_phrases[hash(original) % len(boost_phrases)]
        return f"{phrase} {original}"
    
    def _analyze_aged_content(self, content: str, platform: str) -> Dict[str, Any]:
        """Analyze aged content"""
        return self._analyze_original_post(content, platform)
    
    def _generate_aging_recommendations(self, original: Dict[str, Any], 
                                           aged: Dict[str, Any], strategy: str, platform: str) -> List[str]:
        """Generate aging recommendations"""
        recommendations = []
        
        # Strategy-specific recommendations
        if strategy == 'repost':
            recommendations.extend([
                f"Monitor engagement after reposting on {platform}",
                "Engage with new comments quickly",
                "Consider slight variations for future reposts"
            ])
        elif strategy == 'recreate':
            recommendations.extend([
                "Add new insights or perspectives",
                "Update with current context",
                "Consider different visual elements"
            ])
        elif strategy == 'boost':
            recommendations.extend([
                "Consider promoting with paid advertising",
                "Share to different audience segments",
                "Use platform boosting features"
            ])
        
        # Platform-specific recommendations
        platform_recommendations = {
            'instagram': [
                "Use Instagram Stories to promote reposted content",
                "Tag relevant accounts in reposts",
                "Use relevant hashtags for increased reach"
            ],
            'twitter': [
                "Quote tweet instead of direct repost",
                "Add your own commentary",
                "Use relevant hashtags"
            ],
            'linkedin': [
                "Share with your own insights",
                "Tag relevant people or companies",
                "Add relevant hashtags"
            ],
            'facebook': [
                "Add your own commentary",
                "Share to relevant groups",
                "Use Facebook's boost feature"
            ]
        }
        
        recommendations.extend(platform_recommendations.get(platform, []))
        
        return recommendations


@register_tool(ToolConfig(
    name="Cross Platform",
    slug="cross-platform",
    category="social",
    description="Adapt and optimize content for multiple social media platforms",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Cross Platform Tool - LamGen',
        'description': 'Adapt and optimize content for multiple social media platforms with platform-specific formatting.',
        'keywords': 'cross platform, social media adaptation, multi-platform, content optimization'
    }
))
class CrossPlatformTool(BaseTool):
    """Production-ready cross-platform tool"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'content': COMMON_SCHEMAS['text_field'],
            'platforms': ValidationRule(
                type=ValidationType.ARRAY,
                required=True,
                min_length=2,
                max_length=6
            ),
            'adaptation_level': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='moderate',
                allowed_values=['light', 'moderate', 'heavy']
            ),
            'maintain_core_message': ValidationRule(
                type=ValidationType.BOOLEAN,
                required=False,
                default=True
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Adapt content for multiple platforms"""
        try:
            content = input_data.get('content', '')
            platforms = input_data.get('platforms', [])
            adaptation_level = input_data.get('adaptation_level', 'moderate')
            maintain_core = input_data.get('maintain_core_message', True)
            
            if not content or not platforms:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Content and platforms are required"
                )
            
            # Adapt for cross-platform
            cross_platform_results = self._adapt_cross_platform(
                content, platforms, adaptation_level, maintain_core
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'platform_adaptations': cross_platform_results['adaptations'],
                    'comparison': cross_platform_results['comparison'],
                    'recommendations': cross_platform_results['recommendations'],
                    'platforms': platforms
                },
                metadata={
                    'platform_count': len(platforms),
                    'adaptation_level': adaptation_level
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "adapt_cross_platform")
    
    def _adapt_cross_platform(self, content: str, platforms: List[str], 
                              adaptation_level: str, maintain_core: bool) -> Dict[str, Any]:
        """Adapt content for multiple platforms"""
        adaptations = {}
        
        # Core message extraction
        core_message = self._extract_core_message(content) if maintain_core else content
        
        # Adapt for each platform
        for platform in platforms:
            adaptation = self._adapt_for_platform(
                core_message, platform, adaptation_level, content
            )
            adaptations[platform] = adaptation
        
        # Generate comparison
        comparison = self._compare_platform_adaptations(adaptations)
        
        # Generate recommendations
        recommendations = self._generate_cross_platform_recommendations(adaptations, platforms)
        
        return {
            'adaptations': adaptations,
            'comparison': comparison,
            'recommendations': recommendations
        }
    
    def _extract_core_message(self, content: str) -> str:
        """Extract core message from content"""
        # Remove platform-specific elements
        core = content
        
        # Remove hashtags
        core = re.sub(r'#\w+', '', core)
        
        # Remove mentions
        core = re.sub(r'@\w+', '', core)
        
        # Remove links
        core = re.sub(r'https?://[^\s]+', '', core)
        
        # Remove emojis
        core = re.sub(r'[\U0001F600-\U0001F64F]', '', core)
        
        # Clean up extra whitespace
        core = ' '.join(core.split())
        
        return core
    
    def _adapt_for_platform(self, core_message: str, platform: str, 
                           level: str, original: str) -> Dict[str, Any]:
        """Adapt content for specific platform"""
        adaptation = {
            'platform': platform,
            'adapted_content': '',
            'changes': [],
            'character_count': 0,
            'engagement_elements': []
        }
        
        # Platform-specific adaptations
        if platform == 'twitter':
            adapted = self._adapt_for_twitter(core_message, level)
        elif platform == 'instagram':
            adapted = self._adapt_for_instagram(core_message, level)
        elif platform == 'linkedin':
            adapted = self._adapt_for_linkedin(core_message, level)
        elif platform == 'tiktok':
            adapted = self._adapt_for_tiktok(core_message, level)
        elif platform == 'facebook':
            adapted = self._adapt_for_facebook(core_message, level)
        elif platform == 'youtube':
            adapted = self._adapt_for_youtube(core_message, level)
        else:
            adapted = {'content': core_message, 'changes': ['No adaptation needed']}
        
        adaptation.update(adapted)
        
        return adaptation
    
    def _adapt_for_twitter(self, content: str, level: str) -> Dict[str, Any]:
        """Adapt for Twitter"""
        adapted = {'content': content, 'changes': []}
        
        # Twitter has 280 character limit
        if len(content) > 280:
            adapted['content'] = content[:277] + "..."
            adapted['changes'].append("Shortened for 280 character limit")
        
        # Add hashtags based on level
        if level in ['moderate', 'heavy']:
            hashtags = ['#socialmedia', '#marketing', '#digital']
            adapted['content'] += f" {' '.join(hashtags)}"
            adapted['changes'].append("Added relevant hashtags")
        
        # Add engagement elements
        adapted['engagement_elements'] = ['Call to action', 'Question', 'Poll option']
        
        return adapted
    
    def _adapt_for_instagram(self, content: str, level: str) -> Dict[str, Any]:
        """Adapt for Instagram"""
        adapted = {'content': content, 'changes': []}
        
        # Instagram allows longer content
        if level == 'heavy':
            # Add more detail
            adapted['content'] += f"\n\n📸 More details in comments"
            adapted['changes'].append("Added call to action for comments")
        
        # Add hashtags
        if level in ['moderate', 'heavy']:
            hashtags = ['#instagram', '#socialmedia', '#marketing', '#digital']
            adapted['content'] += f"\n\n{' '.join(hashtags)}"
            adapted['changes'].append("Added relevant hashtags")
        
        # Add engagement elements
        adapted['engagement_elements'] = ['Call to action', 'Question', 'Location tag']
        
        return adapted
    
    def _adapt_for_linkedin(self, content: str, level: str) -> Dict[str, Any]:
        """Adapt for LinkedIn"""
        adapted = {'content': content, 'changes': []}
        
        # LinkedIn is professional
        if level in ['moderate', 'heavy']:
            adapted['content'] = f"💼 Professional insights on:\n\n{content}"
            adapted['changes'].append("Added professional framing")
        
        # Add hashtags
        if level == 'heavy':
            hashtags = ['#professional', '#business', '#networking', '#careers']
            adapted['content'] += f"\n\n{' '.join(hashtags)}"
            adapted['changes'].append("Added professional hashtags")
        
        # Add engagement elements
        adapted['engagement_elements'] = ['Professional call to action', 'Question', 'Article link']
        
        return adapted
    
    def _adapt_for_tiktok(self, content: str, level: str) -> Dict[str, Any]:
        """Adapt for TikTok"""
        adapted = {'content': content, 'changes': []}
        
        # TikTok is short and engaging
        if len(content) > 150:
            adapted['content'] = content[:147] + "..."
            adapted['changes'].append("Shortened for TikTok")
        
        if level in ['moderate', 'heavy']:
            adapted['content'] = f"🎵 {content}"
            adapted['changes'].append("Added emoji for engagement")
        
        # Add hashtags
        if level in ['moderate', 'heavy']:
            hashtags = ['#tiktok', '#fyp', '#viral']
            adapted['content'] += f" {' '.join(hashtags)}"
            adapted['changes'].append("Added TikTok hashtags")
        
        adapted['engagement_elements'] = ['Call to action', 'Challenge tag', 'Duet option']
        
        return adapted
    
    def _adapt_for_facebook(self, content: str, level: str) -> Dict[str, Any]:
        """Adapt for Facebook"""
        adapted = {'content': content, 'changes': []}
        
        # Facebook allows longer content
        if level == 'heavy':
            adapted['content'] = f"📢 Sharing this important information:\n\n{content}"
            adapted['changes'].added("Added framing")
        
        # Add hashtags
        if level == 'heavy':
            hashtags = ['#facebook', '#socialmedia', '#marketing']
            adapted['content'] += f"\n\n{' '.join(hashtags)}"
            adapted['changes'].append("Added hashtags")
        
        # Add engagement elements
        adapted['engagement_elements'] = ['Call to action', 'Question', 'Share prompt']
        
        return adapted
    
    def _adapt_for_youtube(self, content: str, level: str) -> Dict[str, Any]:
        """Adapt for YouTube"""
        adapted = {'content': content, 'changes': []}
        
        # YouTube is video-focused
        if level in ['moderate', 'heavy']:
            adapted['content'] = f"🎥 Video content:\n\n{content}"
            adapted['changes'].append("Added video framing")
        
        # Add hashtags
        if level == 'heavy':
            hashtags = ['#youtube', '#video', '#tutorial', '#education']
            adapted['content'] += f"\n\n{' '.join(hashtags)}"
            adapted['changes'].append("Added YouTube hashtags")
        
        # Add engagement elements
        adapted['engagement_elements'] = ['Call to action', 'Question', 'Link in description']
        
        return adapted
    
    def _compare_platform_adaptations(self, adaptations: Dict[str, Any]) -> Dict[str, Any]:
        """Compare platform adaptations"""
        comparison = {
            'content_length_comparison': {},
            'engagement_elements_comparison': {},
            'optimization_score': {}
        }
        
        # Compare content lengths
        for platform, adaptation in adaptations.items():
            comparison['content_length_comparison'][platform] = len(adaptation['adapted_content'])
        
        # Compare engagement elements
        for platform, adaptation in adaptations.items():
            comparison['engagement_elements_comparison'][platform] = len(adaptation['engagement_elements'])
        
        # Calculate optimization score
        for platform, adaptation in adaptations.items():
            score = 50  # Base score
            if len(adaptation['changes']) > 0:
                score += 25
            if len(adaptation['engagement_elements']) > 0:
                score += 25
            comparison['optimization_score'][platform] = score
        
        return comparison
    
    def _generate_cross_platform_recommendations(self, adaptations: Dict[str, Any], 
                                                platforms: List[str]) -> List[str]:
        """Generate cross-platform recommendations"""
        recommendations = []
        
        # General recommendations
        recommendations.extend([
            "Maintain consistent brand voice across platforms",
            "Tailor content to each platform's unique audience",
            "Use platform-specific features and formats",
            "Post at optimal times for each platform"
        ])
        
        # Platform-specific recommendations
        for platform in platforms:
            if platform in adaptations:
                adaptation = adaptations[platform]
                if len(adaptation['changes']) == 0:
                    recommendations.append(f"Consider adapting content more for {platform}")
        
        return recommendations


@register_tool(ToolConfig(
    name="Social Proof",
    slug="social-proof",
    category="social",
    description="Generate social proof elements to build trust and credibility",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Social Proof Generator - LamGen',
        'description': 'Generate social proof elements like testimonials, reviews, and trust signals to build credibility.',
        'keywords': 'social proof, trust signals, testimonials, credibility, social proof marketing'
    }
))
class SocialProofTool(BaseTool):
    """Production-ready social proof tool"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'business_type': ValidationRule(
                type=ValidationType.STRING,
                required=True,
                max_length=50
            ),
            'proof_type': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='testimonials',
                allowed_values=['testimonials', 'reviews', 'case_studies', 'statistics', 'awards', 'user_generated']
            ),
            'platform': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='all',
                allowed_values=['all', 'website', 'social_media', 'landing_page']
            ),
            'tone': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='professional',
                allowed_values=['professional', 'casual', 'enthusiastic', 'formal']
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Generate social proof elements"""
        try:
            business_type = input_data.get('business_type', '')
            proof_type = input_data.get('proof_type', 'testimonials')
            platform = input_data.get('platform', 'all')
            tone = input_data.get('tone', 'professional')
            
            if not business_type:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Business type is required"
                )
            
            # Generate social proof
            proof_results = self._generate_social_proof(
                business_type, proof_type, platform, tone
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'social_proof': proof_results['proof_elements'],
                    'implementation_guide': proof_results['implementation'],
                    'best_practices': proof_results['best_practices'],
                    'proof_type': proof_type
                },
                metadata={
                    'proof_type': proof_type,
                    'platform': platform
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "generate_social_proof")
    
    def _generate_social_proof(self, business_type: str, proof_type: str, 
                             platform: str, tone: str) -> Dict[str, Any]:
        """Generate social proof elements"""
        proof_elements = []
        
        # Generate based on proof type
        if proof_type == 'testimonials':
            proof_elements = self._generate_testimonials(business_type, tone)
        elif proof_type == 'reviews':
            proof_elements = self._generate_reviews(business_type, tone)
        elif proof_type == 'case_studies':
            proof_elements = self._generate_case_studies(business_type, tone)
        elif proof_type == 'statistics':
            proof_elements = self._generate_statistics(business_type)
        elif proof_type == 'awards':
            proof_elements = self._generate_awards(business_type)
        elif proof_type == 'user_generated':
            proof_elements = self._generate_user_generated(business_type)
        
        # Generate implementation guide
        implementation = self._generate_implementation_guide(proof_elements, platform)
        
        # Generate best practices
        best_practices = self._generate_best_practices(proof_type, platform)
        
        return {
            'proof_elements': proof_elements,
            'implementation': implementation,
            'best_practices': best_practices
        }
    
    def _generate_testimonials(self, business_type: str, tone: str) -> List[Dict[str, Any]]:
        """Generate testimonials"""
        testimonials = []
        
        # Generate 3 different testimonials
        for i in range(3):
            testimonial = {
                'type': 'testimonial',
                'customer_name': self._generate_name(),
                'customer_title': self._generate_title(),
                'customer_company': business_type,
                'rating': 4 + (i % 2),  # 4 or 5 stars
                'testimonial_text': self._generate_testimonial_text(business_type, tone, i),
                'date': (datetime.now() - timedelta(days=i*30)).strftime('%Y-%m-%d'),
                'verified': True,
                'image': 'customer_photo.jpg'
            }
            testimonials.append(testimonial)
        
        return testimonials
    
    def _generate_reviews(self, business_type: str, tone: str) -> List[Dict[str, Any]]:
        """Generate reviews"""
        reviews = []
        
        # Generate 5 different reviews
        for i in range(5):
            star_rating = 3 + (i % 3)  # 3, 4, 5 stars
            review = {
                'type': 'review',
                'reviewer_name': self._generate_name(),
                'rating': star_rating,
                'review_title': self._generate_review_title(business_type, star_rating),
                'review_text': self._generate_review_text(business_type, star_rating),
                'date': (datetime.now() - timedelta(days=i*7)).strftime('%Y-%m-%d'),
                'verified': star_rating >= 4,
                'helpful_count': 5 + i * 2
            }
            reviews.append(review)
        
        return reviews
    
    def _generate_case_studies(self, business_type: str, tone: str) -> List[Dict[str, Any]]:
        """Generate case studies"""
        case_studies = []
        
        # Generate 2 case studies
        for i in range(2):
            case_study = {
                'type': 'case_study',
                'client_name': self._generate_company_name(),
                'client_industry': self._generate_industry(),
                'challenge': self._generate_challenge(business_type),
                'solution': self._generate_solution(business_type),
                'results': self._generate_results(),
                'duration': f"{3 + i} months",
                'image': 'case_study_image.jpg'
            }
            case_studies.append(case_study)
        
        return case_studies
    
    def _generate_statistics(self, business_type: str) -> List[Dict[str, Any]]:
        """Generate statistics"""
        statistics = [
            {
                'type': 'statistic',
                'metric': 'Customers Served',
                'value': f"{1000 + hash(business_type) % 9000:,}",
                'description': f"Happy customers served by {business_type}",
                'trend': 'increasing'
            },
            {
                'type': 'statistic',
                'metric': 'Satisfaction Rate',
                'value': f"{95 + hash(business_type) % 5}%",
                'description': f"Customer satisfaction rate for {business_type}",
                'trend': 'stable'
            },
            {
                'type': 'statistic',
                'metric': 'Years in Business',
                'value': f"{5 + hash(business_type) % 15}",
                'description': f"Years of experience in {business_type}",
                'trend': 'increasing'
            }
        ]
        
        return statistics
    
    def _generate_awards(self, business_type: str) -> List[Dict[str, Any]]:
        """Generate awards"""
        awards = []
        
        award_types = [
            'Excellence Award',
            'Innovation Prize',
            'Customer Choice Award',
            'Industry Recognition',
            'Best in Business'
        ]
        
        for i, award_type in enumerate(award_types):
            award = {
                'type': 'award',
                'name': f"{business_type} {award_type}",
                'year': 2020 + i,
                'organization': 'Industry Association',
                'description': f"Recognized for excellence in {business_type}",
                'image': 'award_badge.jpg'
            }
            awards.append(award)
        
        return awards
    
    def _generate_user_generated(self, business_type: str) -> List[Dict[str, Any]]:
        """Generate user-generated content"""
        ugc = []
        
        # Generate different types of user content
        content_types = ['photo', 'video', 'review', 'testimonial', 'story']
        
        for content_type in content_types:
            content = {
                'type': 'user_generated',
                'content_type': content_type,
                'user_name': self._generate_name(),
                'content': self._generate_ugc_text(business_type, content_type),
                'date': (datetime.now() - timedelta(days=hash(content_type) % 30)).strftime('%Y-%m-%d'),
                'verified': False,
                'media_url': f'{content_type}_content.jpg'
            }
            ugc.append(content)
        
        return ugc
    
    def _generate_name(self) -> str:
        """Generate random name"""
        first_names = ['John', 'Sarah', 'Mike', 'Emily', 'David', 'Lisa', 'Chris', 'Anna', 'Tom', 'Jessica', 'Robert']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis', 'Rodriguez', 'Martinez']
        return f"{first_names[hash('test') % len(first_names)]} {last_names[hash('test') % len(last_names)]}"
    
    def _generate_title(self) -> str:
        """Generate professional title"""
        titles = ['Manager', 'Director', 'Specialist', 'Consultant', 'Analyst', 'Coordinator', 'Administrator', 'Associate', 'Executive', 'Lead']
        return titles[hash('test') % len(titles)]
    
    def _generate_company_name(self) -> str:
        """Generate company name"""
        company_names = ['Tech Solutions', 'Digital Innovations', 'Creative Agency', 'Global Services', 'Professional Group', 'Enterprise Solutions']
        return company_names[hash('test') % len(company_names)]
    
    def _generate_industry(self) -> str:
        """Generate industry"""
        industries = ['Technology', 'Marketing', 'Finance', 'Healthcare', 'Education', 'Retail', 'Manufacturing', 'Consulting']
        return industries[hash('test') % len(industries)]
    
    def _generate_challenge(self, business_type: str) -> str:
        """Generate challenge description"""
        challenges = [
            f"Needed to improve {business_type.lower()} efficiency",
            f"Faced competition in {business_type.lower()} market",
            f"Required modernization of {business_type.lower()} processes",
            f"Struggled with customer acquisition for {business_type.lower()}"
        ]
        return challenges[hash('test') % len(challenges)]
    
    def _generate_solution(self, business_type: str) -> str:
        """Generate solution description"""
        solutions = [
            f"Implemented innovative {business_type.lower()} solutions",
            f"Developed custom {business_type.lower()} platform",
            f"Created strategic {business_type.lower()} approach",
            f"Built comprehensive {business_type.lower()} system"
        ]
        return solutions[hash('test') % len(solutions)]
    
    def _generate_results(self) -> Dict[str, Any]:
        """Generate results"""
        return {
            'revenue_growth': f"{20 + hash('test') % 30}%",
            'cost_reduction': f"{15 + hash('test') % 25}%",
            'efficiency_improvement': f"{25 + hash('test') % 35}%",
            'customer_satisfaction': f"{95 + hash('test') % 5}%"
        }
    
    def _generate_testimonial_text(self, business_type: str, tone: str, index: int) -> str:
        """Generate testimonial text"""
        testimonials = [
            f"Amazing experience with {business_type}. Highly recommended!",
            f"{business_type} exceeded all expectations. Professional and reliable.",
            f"Great service from {business_type}. Would definitely use again!",
            f"{business_type} delivered exactly what they promised. Excellent results.",
            f"Outstanding {business_type} service. Professional and efficient."
        ]
        
        return testimonials[index % len(testimonials)]
    
    def _generate_review_title(self, business_type: str, rating: int) -> str:
        """Generate review title"""
        if rating >= 5:
            return f"Excellent {business_type} Service"
        elif rating >= 4:
            return f"Great {business_type} Experience"
        else:
            return f"{business_type} Review"
    
    def _generate_review_text(self, business_type: str, rating: int) -> str:
        """Generate review text"""
        if rating >= 5:
            return f"Outstanding service from {business_type}. Highly recommended!"
        elif rating >= 4:
            return f"Great experience with {business_type}. Would use again."
        elif rating >= 3:
            return f"Good service from {business_type}. Met expectations."
        else:
            return f"Average experience with {business_type}. Room for improvement."
    
    def _generate_ugc_text(self, business_type: str, content_type: str) -> str:
        """Generate user-generated content text"""
        ugc_texts = {
            'photo': f"Great experience with {business_type}! #{business_type.lower().replace(' ', '')}",
            'video': f"Check out my experience with {business_type}! #{business_type.lower().replace(' ', '')}",
            'review': f"{business_type} is amazing! #{business_type.lower().replace(' ', '')}",
            'testimonial': f"Love {business_type}! #{business_type.lower().replace(' ', '')}",
            'story': f"My {business_type} story #{business_type.lower().replace(' ', '')}"
        }
        
        return ugc_texts.get(content_type, f"Great {business_type} content!")
    
    def _generate_implementation_guide(self, proof_elements: List[Dict[str, Any]], platform: str) -> Dict[str, Any]:
        """Generate implementation guide"""
        guide = {
            'placement_strategy': {},
            'best_practices': [],
            'technical_requirements': {},
            'timing_recommendations': {}
        }
        
        # Placement strategy
        if platform == 'all':
            guide['placement_strategy'] = {
                'website': 'Place testimonials on homepage and service pages',
                'social_media': 'Share across all relevant platforms',
                'landing_pages': 'Include on high-conversion pages'
            }
        else:
            guide['placement_strategy'][platform] = f"Place {proof_elements[0]['type']}s on {platform} profile and pages"
        
        # Best practices
        guide['best_practices'] = [
            "Always get permission before using customer content",
            "Display authentic and recent testimonials",
            "Include customer photos when possible",
            "Show a variety of customer experiences",
            "Update social proof regularly"
        ]
        
        # Technical requirements
        guide['technical_requirements'] = {
            'image_optimization': 'Use high-quality images and proper sizing',
            'attribution': 'Always credit content creators',
            'compliance': 'Ensure compliance with platform guidelines',
            'accessibility': 'Include alt text for images'
        }
        
        # Timing recommendations
        guide['timing_recommendations'] = {
            'frequency': 'Update social proof monthly',
            'seasonal': 'Refresh during peak seasons',
            'campaign_based': 'Add during marketing campaigns'
        }
        
        return guide
    
    def _generate_best_practices(self, proof_type: str, platform: str) -> List[str]:
        """Generate best practices"""
        practices = []
        
        # Type-specific practices
        if proof_type == 'testimonials':
            practices.extend([
                "Use video testimonials when possible",
                "Include specific results and metrics",
                "Show customer photos and names",
                "Display star ratings prominently"
            ])
        elif proof_type == 'reviews':
            practices.extend([
                "Display both positive and constructive reviews",
                "Respond to all reviews, positive and negative",
                "Show review distribution and averages",
                "Highlight recent and relevant reviews"
            ])
        elif proof_type == 'case_studies':
            practices.extend([
                "Focus on measurable results and outcomes",
                "Include client quotes and testimonials",
                "Show before and after comparisons",
                "Detail the process and methodology"
            ])
        
        # Platform-specific practices
        platform_practices = {
            'website': [
                "Create dedicated testimonial page",
                "Add trust badges and certifications",
                "Use schema markup for search engines"
            ],
            'social_media': [
                "Create visual testimonials for Instagram",
                "Share customer success stories on LinkedIn",
                "Use Twitter threads for detailed testimonials"
            ]
        }
        
        practices.extend(platform_practices.get(platform, []))
        
        return practices
