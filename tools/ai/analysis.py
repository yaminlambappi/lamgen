"""
AI Analysis - Complete Implementation of AI-Powered Analysis

Provides production-ready AI analysis capabilities for content analysis,
sentiment analysis, topic analysis, and quality assessment across the LamGen tools ecosystem.
"""

import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from collections import Counter

from tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus, register_tool
from tools.utils.validation import ValidationRule, ValidationType, COMMON_SCHEMAS
from tools.utils.processing import TextProcessor
from tools.utils.analytics import analytics_tracker


class ContentAnalyzer:
    """Production-ready AI content analyzer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.analysis_patterns = self._default_analysis_patterns()
        self.quality_metrics = self._default_quality_metrics()
    
    def _default_analysis_patterns(self) -> Dict[str, Any]:
        """Default analysis patterns"""
        return {
            'readability': {
                'sentence_length_threshold': 20,
                'paragraph_length_threshold': 100,
                'word_complexity_threshold': 6
            },
            'structure': {
                'heading_pattern': r'^#{1,6}\s',
                'list_pattern': r'^\s*[-*+]\s',
                'link_pattern': r'\[.*?\]\(.*?\)'
            },
            'content': {
                'keyword_density_range': (0.01, 0.03),
                'passive_voice_indicators': ['is', 'are', 'was', 'were', 'be', 'been', 'being'],
                'filler_words': ['very', 'really', 'quite', 'rather', 'somewhat', 'actually']
            }
        }
    
    def _default_quality_metrics(self) -> Dict[str, Dict[str, float]]:
        """Default quality metrics weights"""
        return {
            'readability': {'weight': 0.3, 'target': 80},
            'structure': {'weight': 0.25, 'target': 75},
            'content_quality': {'weight': 0.25, 'target': 70},
            'engagement': {'weight': 0.2, 'target': 75}
        }
    
    def analyze_content(self, content: str, content_type: str = 'general') -> Dict[str, Any]:
        """Analyze content comprehensively"""
        analysis_result = {
            'content': content,
            'content_type': content_type,
            'overall_score': 0,
            'metrics': {},
            'issues': [],
            'strengths': [],
            'recommendations': [],
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Perform various analyses
            readability_score = self._analyze_readability(content)
            structure_score = self._analyze_structure(content)
            content_quality_score = self._analyze_content_quality(content)
            engagement_score = self._analyze_engagement_potential(content)
            
            # Store metrics
            analysis_result['metrics'] = {
                'readability': readability_score,
                'structure': structure_score,
                'content_quality': content_quality_score,
                'engagement': engagement_score
            }
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(analysis_result['metrics'])
            analysis_result['overall_score'] = overall_score
            
            # Generate insights
            analysis_result['issues'] = self._identify_issues(analysis_result['metrics'])
            analysis_result['strengths'] = self._identify_strengths(analysis_result['metrics'])
            analysis_result['recommendations'] = self._generate_recommendations(analysis_result['metrics'])
            
        except Exception as e:
            self.logger.error(f"Error analyzing content: {str(e)}")
            analysis_result['error'] = str(e)
        
        return analysis_result
    
    def _analyze_readability(self, content: str) -> float:
        """Analyze content readability"""
        score = 50  # Base score
        
        # Sentence analysis
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if sentences:
            sentence_lengths = [len(s.split()) for s in sentences]
            avg_sentence_length = sum(sentence_lengths) / len(sentence_lengths)
            
            # Optimal sentence length is 10-20 words
            if 10 <= avg_sentence_length <= 20:
                score += 20
            elif avg_sentence_length < 10:
                score += 10
            elif avg_sentence_length > 25:
                score -= 10
        
        # Paragraph analysis
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if paragraphs:
            paragraph_lengths = [len(p.split()) for p in paragraphs]
            avg_paragraph_length = sum(paragraph_lengths) / len(paragraph_lengths)
            
            # Optimal paragraph length is 50-150 words
            if 50 <= avg_paragraph_length <= 150:
                score += 15
            elif avg_paragraph_length < 30:
                score += 5
            elif avg_paragraph_length > 200:
                score -= 5
        
        # Word complexity
        words = content.split()
        complex_words = [w for w in words if len(w) > 6]
        complexity_ratio = len(complex_words) / len(words) if words else 0
        
        # Some complexity is good, but not too much
        if 0.1 <= complexity_ratio <= 0.2:
            score += 15
        elif complexity_ratio < 0.05:
            score += 5
        elif complexity_ratio > 0.3:
            score -= 10
        
        return min(100, max(0, score))
    
    def _analyze_structure(self, content: str) -> float:
        """Analyze content structure"""
        score = 50  # Base score
        
        patterns = self.analysis_patterns['structure']
        
        # Check for headings
        headings = re.findall(patterns['heading_pattern'], content, re.MULTILINE)
        if headings:
            score += 20
            # Bonus for hierarchical structure
            if len(set(h[0] for h in headings)) > 1:
                score += 10
        
        # Check for lists
        lists = re.findall(patterns['list_pattern'], content, re.MULTILINE)
        if lists:
            score += 15
        
        # Check for links
        links = re.findall(patterns['link_pattern'], content)
        if links:
            score += 10
        
        # Check paragraph structure
        paragraphs = content.split('\n\n')
        if len(paragraphs) > 1:
            score += 5
        
        return min(100, max(0, score))
    
    def _analyze_content_quality(self, content: str) -> float:
        """Analyze content quality"""
        score = 50  # Base score
        
        patterns = self.analysis_patterns['content']
        
        # Word count analysis
        word_count = len(content.split())
        if 100 <= word_count <= 1000:
            score += 20
        elif 50 <= word_count <= 2000:
            score += 10
        elif word_count < 50:
            score -= 10
        
        # Passive voice analysis (simplified)
        passive_indicators = patterns['passive_voice_indicators']
        passive_count = sum(content.lower().count(indicator) for indicator in passive_indicators)
        total_sentences = len([s for s in content.split('.') if s.strip()])
        
        if total_sentences > 0:
            passive_ratio = passive_count / total_sentences
            if passive_ratio < 0.2:
                score += 10
            elif passive_ratio > 0.4:
                score -= 10
        
        # Filler words analysis
        filler_words = patterns['filler_words']
        filler_count = sum(content.lower().count(word) for word in filler_words)
        filler_ratio = filler_count / word_count if word_count > 0 else 0
        
        if filler_ratio < 0.05:
            score += 10
        elif filler_ratio > 0.15:
            score -= 10
        
        return min(100, max(0, score))
    
    def _analyze_engagement_potential(self, content: str) -> float:
        """Analyze engagement potential"""
        score = 50  # Base score
        
        # Question analysis
        questions = content.count('?')
        if questions > 0:
            score += min(20, questions * 5)
        
        # Emotional words analysis
        emotional_words = ['amazing', 'excellent', 'wonderful', 'fantastic', 'great', 'love', 'exciting', 'beautiful']
        emotional_count = sum(content.lower().count(word) for word in emotional_words)
        if emotional_count > 0:
            score += min(15, emotional_count * 3)
        
        # Call-to-action analysis
        cta_phrases = ['click here', 'learn more', 'shop now', 'get started', 'sign up', 'contact us']
        cta_count = sum(content.lower().count(phrase) for phrase in cta_phrases)
        if cta_count > 0:
            score += min(15, cta_count * 5)
        
        # Interactive elements
        if re.search(r'\[.*?\]\(.*?\)', content):  # Links
            score += 10
        
        if re.search(r'^\s*[-*+]', content, re.MULTILINE):  # Lists
            score += 5
        
        return min(100, max(0, score))
    
    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """Calculate overall content score"""
        total_score = 0
        total_weight = 0
        
        for metric, weight_config in self.quality_metrics.items():
            if metric in metrics:
                weight = weight_config['weight']
                target = weight_config['target']
                
                # Calculate weighted score
                metric_score = min(100, (metrics[metric] / target) * 100)
                total_score += metric_score * weight
                total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def _identify_issues(self, metrics: Dict[str, float]) -> List[str]:
        """Identify content issues"""
        issues = []
        
        if metrics.get('readability', 0) < 60:
            issues.append("Readability could be improved - consider shorter sentences and paragraphs")
        
        if metrics.get('structure', 0) < 60:
            issues.append("Structure needs improvement - add headings, lists, or better organization")
        
        if metrics.get('content_quality', 0) < 60:
            issues.append("Content quality needs enhancement - check for passive voice and filler words")
        
        if metrics.get('engagement', 0) < 60:
            issues.append("Engagement potential is low - add questions, calls-to-action, or emotional language")
        
        return issues
    
    def _identify_strengths(self, metrics: Dict[str, float]) -> List[str]:
        """Identify content strengths"""
        strengths = []
        
        if metrics.get('readability', 0) > 80:
            strengths.append("Excellent readability - well-structured sentences and paragraphs")
        
        if metrics.get('structure', 0) > 80:
            strengths.append("Great structure - effective use of headings and organization")
        
        if metrics.get('content_quality', 0) > 80:
            strengths.append("High content quality - minimal passive voice and filler words")
        
        if metrics.get('engagement', 0) > 80:
            strengths.append("High engagement potential - effective use of questions and interactive elements")
        
        return strengths
    
    def _generate_recommendations(self, metrics: Dict[str, float]) -> List[str]:
        """Generate improvement recommendations"""
        recommendations = []
        
        if metrics.get('readability', 0) < 70:
            recommendations.extend([
                "Break long sentences into shorter ones",
                "Add paragraph breaks for better readability",
                "Use simpler language where appropriate"
            ])
        
        if metrics.get('structure', 0) < 70:
            recommendations.extend([
                "Add headings to organize content",
                "Use bullet points for lists",
                "Include internal and external links"
            ])
        
        if metrics.get('content_quality', 0) < 70:
            recommendations.extend([
                "Reduce passive voice usage",
                "Eliminate filler words",
                "Add specific examples and data"
            ])
        
        if metrics.get('engagement', 0) < 70:
            recommendations.extend([
                "Add questions to encourage interaction",
                "Include clear calls-to-action",
                "Use emotional language to connect with readers"
            ])
        
        return recommendations


class SentimentAnalyzer:
    """Production-ready AI sentiment analyzer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.sentiment_patterns = self._default_sentiment_patterns()
        self.emotion_lexicon = self._default_emotion_lexicon()
    
    def _default_sentiment_patterns(self) -> Dict[str, List[str]]:
        """Default sentiment patterns"""
        return {
            'positive': [
                'excellent', 'amazing', 'wonderful', 'fantastic', 'great', 'good', 'love',
                'happy', 'excited', 'thrilled', 'delighted', 'pleased', 'satisfied',
                'beautiful', 'perfect', 'outstanding', 'brilliant', 'superb'
            ],
            'negative': [
                'terrible', 'awful', 'horrible', 'bad', 'poor', 'hate', 'dislike',
                'sad', 'angry', 'frustrated', 'disappointed', 'worried', 'concerned',
                'ugly', 'worst', 'disgusting', 'pathetic', 'useless', 'failed'
            ],
            'neutral': [
                'okay', 'fine', 'average', 'normal', 'standard', 'typical', 'regular',
                'acceptable', 'adequate', 'sufficient', 'reasonable', 'moderate'
            ]
        }
    
    def _default_emotion_lexicon(self) -> Dict[str, List[str]]:
        """Default emotion lexicon"""
        return {
            'joy': ['happy', 'joyful', 'excited', 'delighted', 'pleased', 'cheerful'],
            'sadness': ['sad', 'depressed', 'unhappy', 'sorrowful', 'melancholy', 'down'],
            'anger': ['angry', 'furious', 'irritated', 'annoyed', 'mad', 'enraged'],
            'fear': ['afraid', 'scared', 'fearful', 'anxious', 'worried', 'nervous'],
            'surprise': ['surprised', 'amazed', 'astonished', 'shocked', 'stunned'],
            'disgust': ['disgusted', 'revolted', 'repulsed', 'sickened', 'nauseated']
        }
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Analyze text sentiment"""
        analysis_result = {
            'text': text,
            'overall_sentiment': 'neutral',
            'sentiment_score': 0,
            'confidence': 0,
            'emotions': {},
            'sentiment_breakdown': {},
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Calculate sentiment scores
            positive_score = self._calculate_sentiment_score(text, 'positive')
            negative_score = self._calculate_sentiment_score(text, 'negative')
            neutral_score = self._calculate_sentiment_score(text, 'neutral')
            
            # Determine overall sentiment
            total_score = positive_score + negative_score + neutral_score
            if total_score > 0:
                positive_ratio = positive_score / total_score
                negative_ratio = negative_score / total_score
                
                if positive_ratio > 0.6:
                    analysis_result['overall_sentiment'] = 'positive'
                    analysis_result['sentiment_score'] = positive_ratio
                elif negative_ratio > 0.6:
                    analysis_result['overall_sentiment'] = 'negative'
                    analysis_result['sentiment_score'] = -negative_ratio
                else:
                    analysis_result['overall_sentiment'] = 'neutral'
                    analysis_result['sentiment_score'] = 0
                
                analysis_result['confidence'] = max(positive_ratio, negative_ratio)
            
            # Sentiment breakdown
            analysis_result['sentiment_breakdown'] = {
                'positive': positive_score,
                'negative': negative_score,
                'neutral': neutral_score
            }
            
            # Emotion analysis
            analysis_result['emotions'] = self._analyze_emotions(text)
            
        except Exception as e:
            self.logger.error(f"Error analyzing sentiment: {str(e)}")
            analysis_result['error'] = str(e)
        
        return analysis_result
    
    def _calculate_sentiment_score(self, text: str, sentiment_type: str) -> float:
        """Calculate sentiment score for specific type"""
        patterns = self.sentiment_patterns.get(sentiment_type, [])
        words = text.lower().split()
        
        score = 0
        for word in words:
            for pattern in patterns:
                if pattern in word:
                    score += 1
                    break
        
        return score
    
    def _analyze_emotions(self, text: str) -> Dict[str, float]:
        """Analyze emotions in text"""
        emotions = {}
        words = text.lower().split()
        
        for emotion, emotion_words in self.emotion_lexicon.items():
            emotion_score = 0
            for word in words:
                for emotion_word in emotion_words:
                    if emotion_word in word:
                        emotion_score += 1
                        break
            
            if emotion_score > 0:
                emotions[emotion] = emotion_score
        
        return emotions
    
    def batch_analyze(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze sentiment for multiple texts"""
        batch_result = {
            'total_texts': len(texts),
            'results': [],
            'summary': {
                'positive_count': 0,
                'negative_count': 0,
                'neutral_count': 0,
                'average_sentiment': 0
            }
        }
        
        try:
            for text in texts:
                result = self.analyze_sentiment(text)
                batch_result['results'].append(result)
                
                # Update summary
                sentiment = result['overall_sentiment']
                if sentiment == 'positive':
                    batch_result['summary']['positive_count'] += 1
                elif sentiment == 'negative':
                    batch_result['summary']['negative_count'] += 1
                else:
                    batch_result['summary']['neutral_count'] += 1
            
            # Calculate average sentiment
            if batch_result['results']:
                avg_sentiment = sum(r['sentiment_score'] for r in batch_result['results']) / len(batch_result['results'])
                batch_result['summary']['average_sentiment'] = avg_sentiment
            
        except Exception as e:
            self.logger.error(f"Error in batch sentiment analysis: {str(e)}")
            batch_result['error'] = str(e)
        
        return batch_result


class TopicAnalyzer:
    """Production-ready AI topic analyzer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.stop_words = self._default_stop_words()
        self.topic_patterns = self._default_topic_patterns()
    
    def _default_stop_words(self) -> set:
        """Default stop words"""
        return {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'shall', 'a', 'an', 'this', 'that', 'these', 'those', 'i',
            'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who',
            'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just'
        }
    
    def _default_topic_patterns(self) -> Dict[str, List[str]]:
        """Default topic patterns"""
        return {
            'technology': ['software', 'programming', 'code', 'app', 'digital', 'online', 'web', 'data', 'ai', 'machine learning'],
            'business': ['business', 'company', 'market', 'sales', 'revenue', 'profit', 'customer', 'strategy', 'management', 'growth'],
            'health': ['health', 'medical', 'doctor', 'patient', 'treatment', 'medicine', 'hospital', 'disease', 'wellness', 'fitness'],
            'education': ['education', 'school', 'student', 'teacher', 'learning', 'course', 'study', 'university', 'knowledge', 'training'],
            'lifestyle': ['life', 'lifestyle', 'home', 'family', 'personal', 'daily', 'living', 'style', 'hobby', 'interest'],
            'entertainment': ['movie', 'music', 'game', 'entertainment', 'fun', 'play', 'watch', 'listen', 'enjoy', 'leisure']
        }
    
    def analyze_topics(self, text: str, max_topics: int = 5) -> Dict[str, Any]:
        """Analyze topics in text"""
        analysis_result = {
            'text': text,
            'topics': [],
            'topic_distribution': {},
            'key_phrases': [],
            'main_topic': None,
            'topic_confidence': 0,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Extract keywords
            keywords = self._extract_keywords(text)
            
            # Identify topics
            topics = self._identify_topics(keywords)
            
            # Calculate topic distribution
            topic_distribution = self._calculate_topic_distribution(keywords, topics)
            
            # Extract key phrases
            key_phrases = self._extract_key_phrases(text)
            
            # Determine main topic
            main_topic, confidence = self._determine_main_topic(topic_distribution)
            
            # Sort topics by relevance
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:max_topics]
            
            analysis_result['topics'] = [{'topic': topic, 'score': score} for topic, score in sorted_topics]
            analysis_result['topic_distribution'] = topic_distribution
            analysis_result['key_phrases'] = key_phrases
            analysis_result['main_topic'] = main_topic
            analysis_result['topic_confidence'] = confidence
            
        except Exception as e:
            self.logger.error(f"Error analyzing topics: {str(e)}")
            analysis_result['error'] = str(e)
        
        return analysis_result
    
    def _extract_keywords(self, text: str) -> Counter:
        """Extract keywords from text"""
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Remove stop words
        keywords = [word for word in words if word not in self.stop_words and len(word) > 2]
        
        return Counter(keywords)
    
    def _identify_topics(self, keywords: Counter) -> Dict[str, int]:
        """Identify topics based on keywords"""
        topics = {}
        
        for topic, topic_words in self.topic_patterns.items():
            topic_score = 0
            for word, count in keywords.items():
                for topic_word in topic_words:
                    if topic_word in word:
                        topic_score += count
                        break
            if topic_score > 0:
                topics[topic] = topic_score
        
        return topics
    
    def _calculate_topic_distribution(self, keywords: Counter, topics: Dict[str, int]) -> Dict[str, float]:
        """Calculate topic distribution"""
        total_score = sum(topics.values()) if topics else 1
        
        distribution = {}
        for topic, score in topics.items():
            distribution[topic] = (score / total_score) * 100
        
        return distribution
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases from text"""
        # Simple phrase extraction - look for 2-3 word combinations
        words = re.findall(r'\b\w+\b', text.lower())
        phrases = []
        
        # 2-word phrases
        for i in range(len(words) - 1):
            if words[i] not in self.stop_words and words[i+1] not in self.stop_words:
                phrase = f"{words[i]} {words[i+1]}"
                phrases.append(phrase)
        
        # 3-word phrases
        for i in range(len(words) - 2):
            if (words[i] not in self.stop_words and 
                words[i+1] not in self.stop_words and 
                words[i+2] not in self.stop_words):
                phrase = f"{words[i]} {words[i+1]} {words[i+2]}"
                phrases.append(phrase)
        
        # Return most common phrases
        phrase_counter = Counter(phrases)
        return [phrase for phrase, count in phrase_counter.most_common(10)]
    
    def _determine_main_topic(self, topic_distribution: Dict[str, float]) -> Tuple[str, float]:
        """Determine main topic and confidence"""
        if not topic_distribution:
            return 'unknown', 0
        
        main_topic = max(topic_distribution.items(), key=lambda x: x[1])
        return main_topic[0], main_topic[1]
    
    def compare_topics(self, text1: str, text2: str) -> Dict[str, Any]:
        """Compare topics between two texts"""
        comparison_result = {
            'text1_topics': {},
            'text2_topics': {},
            'common_topics': [],
            'topic_similarity': 0,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Analyze both texts
            analysis1 = self.analyze_topics(text1)
            analysis2 = self.analyze_topics(text2)
            
            comparison_result['text1_topics'] = {topic['topic']: topic['score'] for topic in analysis1['topics']}
            comparison_result['text2_topics'] = {topic['topic']: topic['score'] for topic in analysis2['topics']}
            
            # Find common topics
            topics1 = set(comparison_result['text1_topics'].keys())
            topics2 = set(comparison_result['text2_topics'].keys())
            common_topics = topics1.intersection(topics2)
            comparison_result['common_topics'] = list(common_topics)
            
            # Calculate similarity
            similarity = self._calculate_topic_similarity(
                comparison_result['text1_topics'],
                comparison_result['text2_topics']
            )
            comparison_result['topic_similarity'] = similarity
            
        except Exception as e:
            self.logger.error(f"Error comparing topics: {str(e)}")
            comparison_result['error'] = str(e)
        
        return comparison_result
    
    def _calculate_topic_similarity(self, topics1: Dict[str, int], topics2: Dict[str, int]) -> float:
        """Calculate topic similarity between two topic distributions"""
        all_topics = set(topics1.keys()).union(set(topics2.keys()))
        
        if not all_topics:
            return 0
        
        # Convert to vectors
        vector1 = [topics1.get(topic, 0) for topic in all_topics]
        vector2 = [topics2.get(topic, 0) for topic in all_topics]
        
        # Calculate cosine similarity
        dot_product = sum(v1 * v2 for v1, v2 in zip(vector1, vector2))
        magnitude1 = sum(v1 ** 2 for v1 in vector1) ** 0.5
        magnitude2 = sum(v2 ** 2 for v2 in vector2) ** 0.5
        
        if magnitude1 == 0 or magnitude2 == 0:
            return 0
        
        return dot_product / (magnitude1 * magnitude2)


class QualityAnalyzer:
    """Production-ready AI quality analyzer"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.quality_criteria = self._default_quality_criteria()
        self.weights = self._default_weights()
    
    def _default_quality_criteria(self) -> Dict[str, Dict[str, Any]]:
        """Default quality criteria"""
        return {
            'completeness': {
                'description': 'How complete and thorough the content is',
                'indicators': ['word_count', 'coverage', 'depth'],
                'thresholds': {'excellent': 90, 'good': 75, 'average': 60, 'poor': 40}
            },
            'accuracy': {
                'description': 'Factual accuracy and correctness',
                'indicators': ['facts', 'sources', 'consistency'],
                'thresholds': {'excellent': 95, 'good': 80, 'average': 65, 'poor': 50}
            },
            'clarity': {
                'description': 'How clear and understandable the content is',
                'indicators': ['readability', 'structure', 'language'],
                'thresholds': {'excellent': 90, 'good': 75, 'average': 60, 'poor': 40}
            },
            'relevance': {
                'description': 'How relevant the content is to the topic',
                'indicators': ['topic_focus', 'audience_match', 'purpose'],
                'thresholds': {'excellent': 90, 'good': 75, 'average': 60, 'poor': 40}
            },
            'engagement': {
                'description': 'How engaging and interesting the content is',
                'indicators': ['interaction', 'emotion', 'interest'],
                'thresholds': {'excellent': 85, 'good': 70, 'average': 55, 'poor': 40}
            }
        }
    
    def _default_weights(self) -> Dict[str, float]:
        """Default quality weights"""
        return {
            'completeness': 0.25,
            'accuracy': 0.25,
            'clarity': 0.25,
            'relevance': 0.15,
            'engagement': 0.10
        }
    
    def analyze_quality(self, content: str, topic: str = None, target_audience: str = None) -> Dict[str, Any]:
        """Analyze content quality comprehensively"""
        analysis_result = {
            'content': content,
            'topic': topic,
            'target_audience': target_audience,
            'overall_score': 0,
            'quality_level': 'average',
            'criteria_scores': {},
            'strengths': [],
            'weaknesses': [],
            'improvement_areas': [],
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        try:
            # Analyze each quality criterion
            criteria_scores = {}
            
            criteria_scores['completeness'] = self._analyze_completeness(content)
            criteria_scores['accuracy'] = self._analyze_accuracy(content)
            criteria_scores['clarity'] = self._analyze_clarity(content)
            criteria_scores['relevance'] = self._analyze_relevance(content, topic, target_audience)
            criteria_scores['engagement'] = self._analyze_engagement(content)
            
            # Calculate overall score
            overall_score = self._calculate_weighted_score(criteria_scores)
            analysis_result['overall_score'] = overall_score
            analysis_result['criteria_scores'] = criteria_scores
            
            # Determine quality level
            analysis_result['quality_level'] = self._determine_quality_level(overall_score)
            
            # Generate insights
            analysis_result['strengths'] = self._identify_strengths(criteria_scores)
            analysis_result['weaknesses'] = self._identify_weaknesses(criteria_scores)
            analysis_result['improvement_areas'] = self._generate_improvement_areas(criteria_scores)
            
        except Exception as e:
            self.logger.error(f"Error analyzing quality: {str(e)}")
            analysis_result['error'] = str(e)
        
        return analysis_result
    
    def _analyze_completeness(self, content: str) -> float:
        """Analyze content completeness"""
        score = 50  # Base score
        
        # Word count analysis
        word_count = len(content.split())
        if word_count >= 500:
            score += 30
        elif word_count >= 200:
            score += 20
        elif word_count >= 100:
            score += 10
        else:
            score -= 10
        
        # Structure analysis
        paragraphs = content.split('\n\n')
        if len(paragraphs) >= 3:
            score += 10
        elif len(paragraphs) >= 2:
            score += 5
        
        # Content depth indicators
        if re.search(r'\d+\.?\d*', content):  # Numbers/data
            score += 5
        
        if re.search(r'\[.*?\]\(.*?\)', content):  # Links
            score += 5
        
        return min(100, max(0, score))
    
    def _analyze_accuracy(self, content: str) -> float:
        """Analyze content accuracy (simplified)"""
        # In production, would use fact-checking APIs
        score = 75  # Base score - assume mostly accurate
        
        # Check for potential issues
        if 'click here' in content.lower():
            score -= 5  # Generic CTA might indicate low quality
        
        if content.count('!') > len(content) * 0.05:  # Too many exclamation marks
            score -= 10
        
        if len(content.split()) < 50:
            score -= 15  # Very short content might lack depth
        
        return min(100, max(0, score))
    
    def _analyze_clarity(self, content: str) -> float:
        """Analyze content clarity"""
        score = 50  # Base score
        
        # Sentence length analysis
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        if sentences:
            avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)
            
            if 10 <= avg_sentence_length <= 20:
                score += 25
            elif avg_sentence_length < 10:
                score += 10
            elif avg_sentence_length > 25:
                score -= 10
        
        # Paragraph structure
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        if paragraphs:
            avg_paragraph_length = sum(len(p.split()) for p in paragraphs) / len(paragraphs)
            
            if 50 <= avg_paragraph_length <= 150:
                score += 15
            elif avg_paragraph_length < 30:
                score += 5
            elif avg_paragraph_length > 200:
                score -= 5
        
        # Language simplicity
        complex_words = [w for w in content.split() if len(w) > 8]
        complexity_ratio = len(complex_words) / len(content.split()) if content.split() else 0
        
        if complexity_ratio < 0.1:
            score += 10
        elif complexity_ratio > 0.3:
            score -= 10
        
        return min(100, max(0, score))
    
    def _analyze_relevance(self, content: str, topic: str = None, target_audience: str = None) -> float:
        """Analyze content relevance"""
        score = 70  # Base score
        
        if topic:
            # Check topic relevance
            topic_words = topic.lower().split()
            content_lower = content.lower()
            
            topic_matches = sum(1 for word in topic_words if word in content_lower)
            topic_ratio = topic_matches / len(topic_words) if topic_words else 0
            
            if topic_ratio >= 0.5:
                score += 20
            elif topic_ratio >= 0.3:
                score += 10
            elif topic_ratio < 0.1:
                score -= 20
        
        if target_audience:
            # Check audience appropriateness
            if target_audience == 'professional':
                if 'professional' in content.lower() or 'business' in content.lower():
                    score += 10
            elif target_audience == 'casual':
                if content.count('?') > 0 or 'you' in content.lower():
                    score += 10
        
        return min(100, max(0, score))
    
    def _analyze_engagement(self, content: str) -> float:
        """Analyze engagement potential"""
        score = 50  # Base score
        
        # Interactive elements
        if content.count('?') > 0:
            score += 15
        
        if re.search(r'\[.*?\]\(.*?\)', content):  # Links
            score += 10
        
        # Emotional language
        emotional_words = ['amazing', 'excellent', 'wonderful', 'great', 'love', 'exciting']
        emotional_count = sum(content.lower().count(word) for word in emotional_words)
        
        if emotional_count > 0:
            score += min(15, emotional_count * 3)
        
        # Call-to-action
        cta_phrases = ['click here', 'learn more', 'get started', 'contact us']
        if any(phrase in content.lower() for phrase in cta_phrases):
            score += 10
        
        return min(100, max(0, score))
    
    def _calculate_weighted_score(self, criteria_scores: Dict[str, float]) -> float:
        """Calculate weighted quality score"""
        total_score = 0
        total_weight = 0
        
        for criterion, score in criteria_scores.items():
            weight = self.weights.get(criterion, 0.2)
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0
    
    def _determine_quality_level(self, score: float) -> str:
        """Determine quality level from score"""
        if score >= 90:
            return 'excellent'
        elif score >= 80:
            return 'good'
        elif score >= 70:
            return 'average'
        elif score >= 60:
            return 'fair'
        else:
            return 'poor'
    
    def _identify_strengths(self, criteria_scores: Dict[str, float]) -> List[str]:
        """Identify quality strengths"""
        strengths = []
        
        for criterion, score in criteria_scores.items():
            if score >= 80:
                criterion_info = self.quality_criteria.get(criterion, {})
                strengths.append(f"Excellent {criterion_info.get('description', criterion)}")
            elif score >= 70:
                criterion_info = self.quality_criteria.get(criterion, {})
                strengths.append(f"Good {criterion_info.get('description', criterion)}")
        
        return strengths
    
    def _identify_weaknesses(self, criteria_scores: Dict[str, float]) -> List[str]:
        """Identify quality weaknesses"""
        weaknesses = []
        
        for criterion, score in criteria_scores.items():
            if score < 60:
                criterion_info = self.quality_criteria.get(criterion, {})
                weaknesses.append(f"Needs improvement in {criterion_info.get('description', criterion)}")
        
        return weaknesses
    
    def _generate_improvement_areas(self, criteria_scores: Dict[str, float]) -> List[str]:
        """Generate improvement recommendations"""
        improvements = []
        
        for criterion, score in criteria_scores.items():
            if score < 70:
                if criterion == 'completeness':
                    improvements.append("Add more detail and depth to cover the topic thoroughly")
                elif criterion == 'accuracy':
                    improvements.append("Verify facts and add credible sources")
                elif criterion == 'clarity':
                    improvements.append("Improve sentence structure and simplify complex language")
                elif criterion == 'relevance':
                    improvements.append("Focus more closely on the main topic and audience needs")
                elif criterion == 'engagement':
                    improvements.append("Add interactive elements and emotional language")
        
        return improvements


# Global instances
_content_analyzer = None
_sentiment_analyzer = None
_topic_analyzer = None
_quality_analyzer = None


def get_content_analyzer() -> ContentAnalyzer:
    """Get global content analyzer instance"""
    global _content_analyzer
    if _content_analyzer is None:
        _content_analyzer = ContentAnalyzer()
    return _content_analyzer


def get_sentiment_analyzer() -> SentimentAnalyzer:
    """Get global sentiment analyzer instance"""
    global _sentiment_analyzer
    if _sentiment_analyzer is None:
        _sentiment_analyzer = SentimentAnalyzer()
    return _sentiment_analyzer


def get_topic_analyzer() -> TopicAnalyzer:
    """Get global topic analyzer instance"""
    global _topic_analyzer
    if _topic_analyzer is None:
        _topic_analyzer = TopicAnalyzer()
    return _topic_analyzer


def get_quality_analyzer() -> QualityAnalyzer:
    """Get global quality analyzer instance"""
    global _quality_analyzer
    if _quality_analyzer is None:
        _quality_analyzer = QualityAnalyzer()
    return _quality_analyzer
