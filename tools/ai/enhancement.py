"""
AI Enhancement - Complete Implementation of AI-Powered Enhancement

Provides production-ready AI enhancement capabilities for content optimization,
quality improvement, and intelligent suggestions across the LamGen tools ecosystem.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus, register_tool
from tools.utils.validation import ValidationRule, ValidationType, COMMON_SCHEMAS
from tools.utils.processing import TextProcessor
from tools.utils.analytics import analytics_tracker


class AIEnhancer:
    """Production-ready AI enhancer for content optimization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.enhancement_rules = self._default_enhancement_rules()
        self.quality_metrics = self._default_quality_metrics()
    
    def _default_enhancement_rules(self) -> Dict[str, Any]:
        """Default enhancement rules"""
        return {
            'readability': {
                'target_score': 70,
                'max_sentence_length': 25,
                'min_paragraph_length': 20,
                'max_paragraph_length': 150
            },
            'seo': {
                'keyword_density_min': 1.0,
                'keyword_density_max': 3.0,
                'min_title_length': 30,
                'max_title_length': 60,
                'min_description_length': 50,
                'max_description_length': 160
            },
            'engagement': {
                'min_h2_count': 2,
                'max_h2_count': 10,
                'min_image_count': 1,
                'max_image_count': 10,
                'min_link_count': 2,
                'max_link_count': 20
            }
        }
    
    def _default_quality_metrics(self) -> Dict[str, Any]:
        """Default quality metrics"""
        return {
            'readability': {'weight': 0.3, 'target': 80},
            'seo': {'weight': 0.25, 'target': 75},
            'engagement': {'weight': 0.25, 'target': 70},
            'completeness': {'weight': 0.2, 'target': 85}
        }
    
    def enhance_content(self, content: str, content_type: str = 'general', 
                        target_keywords: List[str] = None) -> Dict[str, Any]:
        """Enhance content with AI-powered improvements"""
        enhancement_result = {
            'original_content': content,
            'enhanced_content': content,
            'improvements': [],
            'quality_scores': {},
            'suggestions': [],
            'enhancement_level': 'minimal'
        }
        
        try:
            # Analyze current content
            analysis = self._analyze_content(content, content_type, target_keywords)
            enhancement_result['quality_scores'] = analysis['scores']
            
            # Generate improvements
            improvements = self._generate_improvements(analysis, content_type)
            enhancement_result['improvements'] = improvements
            
            # Apply improvements
            if improvements:
                enhanced_content = self._apply_improvements(content, improvements)
                enhancement_result['enhanced_content'] = enhanced_content
                enhancement_result['enhancement_level'] = self._determine_enhancement_level(improvements)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(analysis, improvements)
            enhancement_result['suggestions'] = suggestions
            
        except Exception as e:
            self.logger.error(f"Error enhancing content: {str(e)}")
            enhancement_result['error'] = str(e)
        
        return enhancement_result
    
    def _analyze_content(self, content: str, content_type: str, 
                         target_keywords: List[str] = None) -> Dict[str, Any]:
        """Analyze content quality"""
        analysis = {
            'scores': {},
            'issues': [],
            'strengths': [],
            'metrics': {}
        }
        
        # Readability analysis
        readability_score = self._analyze_readability(content)
        analysis['scores']['readability'] = readability_score
        analysis['metrics']['readability'] = readability_score
        
        # SEO analysis
        seo_score = self._analyze_seo(content, target_keywords)
        analysis['scores']['seo'] = seo_score
        analysis['metrics']['seo'] = seo_score
        
        # Engagement analysis
        engagement_score = self._analyze_engagement(content)
        analysis['scores']['engagement'] = engagement_score
        analysis['metrics']['engagement'] = engagement_score
        
        # Completeness analysis
        completeness_score = self._analyze_completeness(content, content_type)
        analysis['scores']['completeness'] = completeness_score
        analysis['metrics']['completeness'] = completeness_score
        
        # Calculate overall score
        overall_score = self._calculate_overall_score(analysis['scores'])
        analysis['scores']['overall'] = overall_score
        
        return analysis
    
    def _analyze_readability(self, content: str) -> float:
        """Analyze content readability"""
        processor = TextProcessor()
        
        # Calculate readability metrics
        sentences = processor.count_sentences(content)
        words = processor.count_words(content)
        avg_sentence_length = words / sentences if sentences > 0 else 0
        
        # Score based on sentence length and structure
        score = 50  # Base score
        
        if 10 <= avg_sentence_length <= 20:
            score += 30
        elif avg_sentence_length < 10:
            score += 10
        elif avg_sentence_length > 25:
            score -= 10
        
        # Check for paragraph structure
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 1:
            score += 10
        
        # Check for variety in sentence length
        sentence_lengths = [len(s.split()) for s in content.split('.') if s.strip()]
        if len(set(sentence_lengths)) > len(sentence_lengths) / 2:
            score += 10
        
        return min(100, max(0, score))
    
    def _analyze_seo(self, content: str, target_keywords: List[str] = None) -> float:
        """Analyze SEO optimization"""
        score = 50  # Base score
        
        if target_keywords:
            # Keyword density
            words = content.lower().split()
            total_words = len(words)
            keyword_count = sum(words.count(kw.lower()) for kw in target_keywords)
            density = (keyword_count / total_words) * 100 if total_words > 0 else 0
            
            if 1.0 <= density <= 3.0:
                score += 30
            elif density < 1.0:
                score += 10
            else:
                score -= 10
        
        # Check for headings
        h2_count = len(re.findall(r'<h2>', content, re.IGNORECASE))
        if 2 <= h2_count <= 6:
            score += 10
        
        # Check for images
        img_count = len(re.findall(r'<img', content, re.IGNORECASE))
        if img_count >= 1:
            score += 5
        
        # Check for links
        link_count = len(re.findall(r'<a\s+href', content, re.IGNORECASE))
        if link_count >= 2:
            score += 5
        
        return min(100, max(0, score))
    
    def _analyze_engagement(self, content: str) -> float:
        """Analyze engagement potential"""
        score = 50  # Base score
        
        # Check for interactive elements
        if '?' in content:
            score += 10
        
        # Check for emotional words
        emotional_words = ['amazing', 'excellent', 'wonderful', 'fantastic', 'great', 'love', 'exciting']
        emotional_count = sum(1 for word in emotional_words if word.lower() in content.lower())
        if emotional_count > 0:
            score += min(20, emotional_count * 5)
        
        # Check for call-to-action
        cta_phrases = ['click here', 'learn more', 'shop now', 'get started', 'sign up']
        if any(phrase in content.lower() for phrase in cta_phrases):
            score += 10
        
        # Check for lists
        if re.search(r'^\s*[-*+]', content, re.MULTILINE):
            score += 5
        
        return min(100, max(0, score))
    
    def _analyze_completeness(self, content: str, content_type: str) -> float:
        """Analyze content completeness"""
        score = 50  # Base score
        
        # Length check
        word_count = len(content.split())
        if word_count >= 300:
            score += 20
        elif word_count >= 150:
            score += 10
        else:
            score -= 10
        
        # Structure check
        if content_type == 'blog_post':
            has_intro = len(content.split('\n\n')) > 0
            has_body = word_count > 100
            has_conclusion = content.strip().endswith('.')
            
            if has_intro and has_body and has_conclusion:
                score += 20
            elif has_intro and has_body:
                score += 10
        
        return min(100, max(0, score))
    
    def _calculate_overall_score(self, scores: Dict[str, float]) -> float:
        """Calculate overall quality score"""
        total_score = 0
        total_weight = 0
        
        for metric, weight_config in self.quality_metrics.items():
            if metric in scores:
                weight = weight_config['weight']
                target = weight_config['target']
                
                # Calculate score based on target
                metric_score = min(100, (scores[metric] / target) * 100)
                total_score += metric_score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def _generate_improvements(self, analysis: Dict[str, Any], content_type: str) -> List[Dict[str, Any]]:
        """Generate improvement suggestions"""
        improvements = []
        
        scores = analysis['scores']
        
        # Readability improvements
        if scores.get('readability', 0) < 70:
            improvements.append({
                'type': 'readability',
                'priority': 'high',
                'description': 'Improve readability by breaking long sentences and adding paragraphs',
                'actions': ['Break long sentences into shorter ones', 'Add paragraph breaks', 'Use simpler language']
            })
        
        # SEO improvements
        if scores.get('seo', 0) < 70:
            improvements.append({
                'type': 'seo',
                'priority': 'high',
                'description': 'Improve SEO optimization with better keywords and structure',
                'actions': ['Add relevant keywords', 'Include proper headings', 'Add meta description']
            })
        
        # Engagement improvements
        if scores.get('engagement', 0) < 70:
            improvements.append({
                'type': 'engagement',
                'priority': 'medium',
                'description': 'Increase engagement potential with interactive elements',
                'actions': ['Add questions', 'Include call-to-action', 'Use emotional language']
            })
        
        # Completeness improvements
        if scores.get('completeness', 0) < 70:
            improvements.append({
                'type': 'completeness',
                'priority': 'medium',
                'description': 'Add more content to improve completeness',
                'actions': ['Add introduction', 'Expand body content', 'Add conclusion']
            })
        
        return improvements
    
    def _apply_improvements(self, content: str, improvements: List[Dict[str, Any]]) -> str:
        """Apply improvements to content"""
        enhanced_content = content
        
        for improvement in improvements:
            if improvement['type'] == 'readability':
                enhanced_content = self._improve_readability(enhanced_content)
            elif improvement['type'] == 'seo':
                enhanced_content = self._improve_seo(enhanced_content)
            elif improvement['type'] == 'engagement':
                enhanced_content = self._improve_engagement(enhanced_content)
            elif improvement['type'] == 'completeness':
                enhanced_content = self._improve_completeness(enhanced_content)
        
        return enhanced_content
    
    def _improve_readability(self, content: str) -> str:
        """Improve content readability"""
        # Break long sentences
        sentences = content.split('. ')
        improved_sentences = []
        
        for sentence in sentences:
            if len(sentence.split()) > 20:
                # Break long sentence
                words = sentence.split()
                mid_point = len(words) // 2
                improved_sentences.append(' '.join(words[:mid_point]) + '.')
                improved_sentences.append(' '.join(words[mid_point:]) + '.')
            else:
                improved_sentences.append(sentence + '.')
        
        # Add paragraph breaks
        improved_content = '. '.join(improved_sentences)
        paragraphs = improved_content.split('\n\n')
        
        # Add paragraph breaks if needed
        if len(paragraphs) == 1 and len(improved_content) > 300:
            # Split into paragraphs
            words = improved_content.split()
            mid_point = len(words) // 2
            first_half = ' '.join(words[:mid_point])
            second_half = ' '.join(words[mid_point:])
            improved_content = f"{first_half}\n\n{second_half}"
        
        return improved_content
    
    def _improve_seo(self, content: str) -> str:
        """Improve SEO optimization"""
        # Add headings (simplified)
        if '<h2>' not in content and len(content) > 200:
            # Find logical break points
            sentences = content.split('. ')
            if len(sentences) > 3:
                mid_point = len(sentences) // 2
                content = '. '.join(sentences[:mid_point]) + '.'
                content += f"\n\n<h2>Key Points</h2>\n\n"
                content += '. '.join(sentences[mid_point:]) + '.'
        
        return content
    
    def _improve_engagement(self, content: str) -> str:
        """Improve engagement potential"""
        # Add question if missing
        if '?' not in content:
            content += "\n\nWhat are your thoughts on this?"
        
        # Add call-to-action if missing
        cta_phrases = ['click here', 'learn more', 'shop now', 'get started']
        if not any(phrase in content.lower() for phrase in cta_phrases):
            content += "\n\nLearn more about how we can help you!"
        
        return content
    
    def _improve_completeness(self, content: str) -> str:
        """Improve content completeness"""
        # Add introduction if missing
        if len(content.split()) < 50:
            content = f"Welcome to our comprehensive guide.\n\n{content}"
        
        # Add conclusion if missing
        if not content.strip().endswith('.'):
            content += "\n\nThank you for reading. We hope this information was helpful!"
        
        return content
    
    def _determine_enhancement_level(self, improvements: List[Dict[str, Any]]) -> str:
        """Determine enhancement level"""
        if not improvements:
            return 'minimal'
        
        high_priority_count = sum(1 for imp in improvements if imp['priority'] == 'high')
        
        if high_priority_count >= 2:
            return 'extensive'
        elif high_priority_count >= 1:
            return 'moderate'
        else:
            return 'minimal'
    
    def _generate_suggestions(self, analysis: Dict[str, Any], 
                           improvements: List[Dict[str, Any]]) -> List[str]:
        """Generate improvement suggestions"""
        suggestions = []
        
        # Based on analysis
        scores = analysis['scores']
        
        if scores.get('readability', 0) < 70:
            suggestions.append("Consider breaking up long sentences and adding more paragraphs")
        
        if scores.get('seo', 0) < 70:
            suggestions.append("Add relevant keywords and proper heading structure")
        
        if scores.get('engagement', 0) < 70:
            suggestions.append("Include questions and calls-to-action to increase engagement")
        
        if scores.get('completeness', 0) < 70:
            suggestions.append("Expand content with introduction and conclusion")
        
        # Based on improvements
        for improvement in improvements:
            suggestions.extend(improvement['actions'])
        
        return list(set(suggestions))


class ContentOptimizer:
    """Production-ready content optimizer with AI enhancement"""
    
    def __init__(self):
        self.enhancer = AIEnhancer()
        self.logger = logging.getLogger(__name__)
    
    def optimize_for_platform(self, content: str, platform: str, 
                            target_keywords: List[str] = None) -> Dict[str, Any]:
        """Optimize content for specific platform"""
        optimization_result = {
            'original_content': content,
            'optimized_content': content,
            'platform': platform,
            'optimizations': [],
            'platform_specific_tips': [],
            'improvement_score': 0
        }
        
        try:
            # Platform-specific optimization rules
            platform_rules = self._get_platform_rules(platform)
            
            # Apply AI enhancement
            enhanced_result = self.enhancer.enhance_content(
                content, platform, target_keywords
            )
            
            # Apply platform-specific optimizations
            platform_optimized = self._apply_platform_optimizations(
                enhanced_result['enhanced_content'], platform_rules
            )
            
            optimization_result['optimized_content'] = platform_optimized['content']
            optimization_result['optimizations'] = enhanced_result['improvements']
            optimization_result['optimizations'].extend(platform_optimized['optimizations'])
            optimization_result['platform_specific_tips'] = platform_optimized['tips']
            optimization_result['improvement_score'] = self._calculate_improvement_score(
                content, platform_optimized['content']
            )
            
        except Exception as e:
            self.logger.error(f"Error optimizing content for {platform}: {str(e)}")
            optimization_result['error'] = str(e)
        
        return optimization_result
    
    def _get_platform_rules(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific optimization rules"""
        rules = {
            'blog': {
                'title_length': [50, 60],
                'meta_description_length': [150, 160],
                'content_length': [300, 2000],
                'heading_structure': True,
                'image_count': [1, 5],
                'link_count': [2, 10]
            },
            'social_media': {
                'title_length': [20, 100],
                'content_length': [50, 500],
                'hashtag_count': [3, 10],
                'emoji_usage': True,
                'mention_usage': True
            },
            'email': {
                'subject_length': [20, 50],
                'content_length': [100, 1000],
                'personalization': True,
                'call_to_action': True,
                'single_column': True
            },
            'landing_page': {
                'title_length': [30, 60],
                'content_length': [200, 1500],
                'form_present': True,
                'social_proof': True,
                'urgency_elements': True
            }
        }
        
        return rules.get(platform.lower(), rules['blog'])
    
    def _apply_platform_optimizations(self, content: str, rules: Dict[str, Any]) -> Dict[str, Any]:
        """Apply platform-specific optimizations"""
        optimized_content = content
        optimizations = []
        tips = []
        
        # Length optimization
        if 'content_length' in rules:
            min_len, max_len = rules['content_length']
            current_len = len(content.split())
            
            if current_len < min_len:
                tips.append(f"Content is too short for {rules.get('platform', 'platform')}. Target: {min_len}-{max_len} words")
            elif current_len > max_len:
                tips.append(f"Content is too long for {rules.get('platform', 'platform')}. Target: {min_len}-{max_len} words")
                # Truncate content
                words = content.split()
                optimized_content = ' '.join(words[:max_len])
        
        # Hashtag optimization for social media
        if rules.get('hashtag_count') and 'social_media' in str(rules):
            min_tags, max_tags = rules['hashtag_count']
            current_hashtags = len(re.findall(r'#\w+', optimized_content))
            
            if current_hashtags < min_tags:
                # Add relevant hashtags
                words = optimized_content.split()
                relevant_words = [w for w in words if len(w) > 3][:min_tags - current_hashtags]
                hashtags = ' '.join([f"#{w}" for w in relevant_words])
                optimized_content += f"\n\n{hashtags}"
                optimizations.append(f"Added {len(relevant_words)} hashtags")
        
        # Emoji optimization for social media
        if rules.get('emoji_usage') and 'social_media' in str(rules):
            if not any(char in optimized_content for char in '😀😊😎🔥💯'):
                optimized_content += " 😊"
                optimizations.append("Added emoji for engagement")
        
        return {
            'content': optimized_content,
            'optimizations': optimizations,
            'tips': tips
        }
    
    def _calculate_improvement_score(self, original: str, optimized: str) -> float:
        """Calculate improvement score"""
        # Simplified improvement calculation
        original_metrics = self._calculate_content_metrics(original)
        optimized_metrics = self._calculate_content_metrics(optimized)
        
        improvement = 0
        for metric in original_metrics:
            if metric in optimized_metrics:
                improvement += (optimized_metrics[metric] - original_metrics[metric]) / original_metrics[metric] * 100
        
        return min(100, max(0, improvement / len(original_metrics)))
    
    def _calculate_content_metrics(self, content: str) -> Dict[str, float]:
        """Calculate content metrics"""
        return {
            'word_count': len(content.split()),
            'sentence_count': len(content.split('.')),
            'paragraph_count': len(content.split('\n\n')),
            'hashtag_count': len(re.findall(r'#\w+', content)),
            'emoji_count': len([char for char in content if char in '😀😊😎🔥💯'])
        }


class QualityImprover:
    """Production-ready quality improver with AI enhancement"""
    
    def __init__(self):
        self.enhancer = AIEnhancer()
        self.logger = logging.getLogger(__name__)
        self.quality_thresholds = self._default_quality_thresholds()
    
    def _default_quality_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Default quality thresholds"""
        return {
            'excellent': {'min_score': 90, 'issues_max': 2},
            'good': {'min_score': 75, 'issues_max': 5},
            'average': {'min_score': 60, 'issues_max': 10},
            'poor': {'min_score': 40, 'issues_max': 15}
        }
    
    def improve_quality(self, content: str, target_quality: str = 'good', 
                        max_iterations: int = 3) -> Dict[str, Any]:
        """Improve content quality to target level"""
        improvement_result = {
            'original_content': content,
            'final_content': content,
            'target_quality': target_quality,
            'iterations': [],
            'final_score': 0,
            'quality_achieved': False,
            'improvements_applied': []
        }
        
        try:
            current_content = content
            current_score = 0
            
            for iteration in range(max_iterations):
                # Analyze current content
                analysis = self.enhancer._analyze_content(current_content)
                current_score = analysis['scores'].get('overall', 0)
                
                # Check if target quality achieved
                if self._is_quality_achieved(current_score, target_quality):
                    improvement_result['quality_achieved'] = True
                    break
                
                # Apply improvements
                enhanced_result = self.enhancer.enhance_content(current_content)
                current_content = enhanced_result['enhanced_content']
                
                # Record iteration
                improvement_result['iterations'].append({
                    'iteration': iteration + 1,
                    'score': current_score,
                    'improvements': enhanced_result['improvements']
                })
            
            improvement_result['final_content'] = current_content
            improvement_result['final_score'] = current_score
            improvement_result['quality_achieved'] = self._is_quality_achieved(current_score, target_quality)
            
            # Collect all improvements applied
            for iteration in improvement_result['iterations']:
                improvement_result['improvements_applied'].extend(iteration['improvements'])
            
        except Exception as e:
            self.logger.error(f"Error improving content quality: {str(e)}")
            improvement_result['error'] = str(e)
        
        return improvement_result
    
    def _is_quality_achieved(self, score: float, target_quality: str) -> bool:
        """Check if quality target is achieved"""
        threshold = self.quality_thresholds.get(target_quality, {})
        return score >= threshold.get('min_score', 60)
    
    def get_quality_report(self, content: str) -> Dict[str, Any]:
        """Get comprehensive quality report"""
        try:
            analysis = self.enhancer._analyze_content(content)
            
            report = {
                'overall_score': analysis['scores'].get('overall', 0),
                'quality_level': self._determine_quality_level(analysis['scores'].get('overall', 0)),
                'individual_scores': analysis['scores'],
                'strengths': analysis.get('strengths', []),
                'issues': analysis.get('issues', []),
                'recommendations': self._generate_quality_recommendations(analysis),
                'timestamp': datetime.now().isoformat()
            }
            
            return report
            
        except Exception as e:
            self.logger.error(f"Error generating quality report: {str(e)}")
            return {'error': str(e)}
    
    def _determine_quality_level(self, score: float) -> str:
        """Determine quality level from score"""
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 60:
            return 'average'
        elif score >= 40:
            return 'poor'
        else:
            return 'very_poor'
    
    def _generate_quality_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate quality improvement recommendations"""
        recommendations = []
        
        scores = analysis.get('scores', {})
        
        if scores.get('readability', 0) < 70:
            recommendations.append("Improve readability by breaking long sentences and adding paragraphs")
        
        if scores.get('seo', 0) < 70:
            recommendations.append("Enhance SEO with better keywords and structure")
        
        if scores.get('engagement', 0) < 70:
            recommendations.append("Increase engagement with interactive elements and calls-to-action")
        
        if scores.get('completeness', 0) < 70:
            recommendations.append("Add more content to improve completeness")
        
        return recommendations


class SmartSuggester:
    """Production-ready smart suggester with AI enhancement"""
    
    def __init__(self):
        self.enhancer = AIEnhancer()
        self.logger = logging.getLogger(__name__)
        self.suggestion_categories = self._default_suggestion_categories()
    
    def _default_suggestion_categories(self) -> Dict[str, List[str]]:
        """Default suggestion categories"""
        return {
            'content': [
                'Add more examples and case studies',
                'Include statistics and data',
                'Add personal anecdotes',
                'Include step-by-step instructions',
                'Add visual elements descriptions'
            ],
            'seo': [
                'Optimize title for search engines',
                'Add meta description',
                'Include relevant keywords naturally',
                'Add internal links',
                'Optimize for featured snippets'
            ],
            'engagement': [
                'Add questions to encourage comments',
                'Include social sharing buttons',
                'Add related content suggestions',
                'Include user-generated content',
                'Add interactive elements'
            ],
            'structure': [
                'Add table of contents',
                'Improve heading hierarchy',
                'Add summary section',
                'Include FAQ section',
                'Add conclusion with call-to-action'
            ]
        }
    
    def get_suggestions(self, content: str, category: str = 'all', 
                        count: int = 5) -> Dict[str, Any]:
        """Get smart suggestions for content improvement"""
        suggestion_result = {
            'content': content,
            'suggestions': [],
            'category': category,
            'count': count,
            'priority_suggestions': [],
            'implementation_tips': []
        }
        
        try:
            # Analyze content
            analysis = self.enhancer._analyze_content(content)
            
            # Generate suggestions based on category
            if category == 'all':
                all_suggestions = []
                for cat, suggestions in self.suggestion_categories.items():
                    all_suggestions.extend(suggestions)
                suggestions_list = all_suggestions
            else:
                suggestions_list = self.suggestion_categories.get(category, [])
            
            # Prioritize suggestions based on analysis
            prioritized = self._prioritize_suggestions(suggestions_list, analysis)
            
            # Select top suggestions
            top_suggestions = prioritized[:count]
            
            suggestion_result['suggestions'] = top_suggestions
            suggestion_result['priority_suggestions'] = top_suggestions[:3]
            suggestion_result['implementation_tips'] = self._generate_implementation_tips(top_suggestions)
            
        except Exception as e:
            self.logger.error(f"Error generating suggestions: {str(e)}")
            suggestion_result['error'] = str(e)
        
        return suggestion_result
    
    def _prioritize_suggestions(self, suggestions: List[str], analysis: Dict[str, Any]) -> List[str]:
        """Prioritize suggestions based on analysis"""
        prioritized = []
        scores = analysis.get('scores', {})
        
        for suggestion in suggestions:
            priority_score = 50  # Base priority
            
            # Adjust priority based on content weaknesses
            if 'seo' in suggestion.lower() and scores.get('seo', 0) < 70:
                priority_score += 20
            
            if 'engagement' in suggestion.lower() and scores.get('engagement', 0) < 70:
                priority_score += 20
            
            if 'structure' in suggestion.lower() and scores.get('completeness', 0) < 70:
                priority_score += 15
            
            prioritized.append((suggestion, priority_score))
        
        # Sort by priority score
        prioritized.sort(key=lambda x: x[1], reverse=True)
        
        return [suggestion for suggestion, _ in prioritized]
    
    def _generate_implementation_tips(self, suggestions: List[str]) -> List[str]:
        """Generate implementation tips for suggestions"""
        tips = []
        
        for suggestion in suggestions:
            if 'examples' in suggestion.lower():
                tips.append("Use real-world examples and case studies to illustrate points")
            elif 'statistics' in suggestion.lower():
                tips.append("Include credible data sources and cite your statistics")
            elif 'keywords' in suggestion.lower():
                tips.append("Use keywords naturally and avoid keyword stuffing")
            elif 'questions' in suggestion.lower():
                tips.append("Ask open-ended questions to encourage discussion")
            elif 'headings' in suggestion.lower():
                tips.append("Use a logical heading hierarchy (H1, H2, H3)")
            else:
                tips.append("Implement the suggestion gradually and measure its impact")
        
        return tips


# Global instances
_ai_enhancer = None
_content_optimizer = None
_quality_improver = None
_smart_suggester = None


def get_ai_enhancer() -> AIEnhancer:
    """Get global AI enhancer instance"""
    global _ai_enhancer
    if _ai_enhancer is None:
        _ai_enhancer = AIEnhancer()
    return _ai_enhancer


def get_content_optimizer() -> ContentOptimizer:
    """Get global content optimizer instance"""
    global _content_optimizer
    if _content_optimizer is None:
        _content_optimizer = ContentOptimizer()
    return _content_optimizer


def get_quality_improver() -> QualityImprover:
    """Get global quality improver instance"""
    global _quality_improver
    if _quality_improver is None:
        _quality_improver = QualityImprover()
    return _quality_improver


def get_smart_suggester() -> SmartSuggester:
    """Get global smart suggester instance"""
    global _smart_suggester
    if _smart_suggester is None:
        _smart_suggester = SmartSuggester()
    return _smart_suggester
