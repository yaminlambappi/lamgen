"""
Content Uniqueness Engine
Advanced anti-duplicate system with AI detection avoidance
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count
from django.core.cache import cache
from django.conf import settings
import random
import re
import hashlib
from datetime import datetime
import json


class ContentUniquenessEngine:
    """Advanced content uniqueness engine with AI detection avoidance"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 24  # 24 hours
        
        # Advanced sentence structure patterns
        self.sentence_structures = [
            "Subject-Verb-Object-Adverbial",
            "Adverbial-Subject-Verb-Object",
            "Object-Subject-Verb-Adverbial",
            "Subject-Adverbial-Verb-Object",
            "Verb-Subject-Object-Adverbial",
            "Conditional-Subject-Verb-Object",
            "Relative-Subject-Verb-Object"
        ]
        
        # Human-like transition patterns
        self.human_transitions = [
            "That said,", "Having said that,", "With that in mind,", "On that note,",
            "Moving forward,", "Looking ahead,", "In that context,", "From there,",
            "As it turns out,", "Interestingly enough,", "Notably,", "Specifically,"
        ]
        
        # Industry-specific terminology
        self.industry_terminology = {
            "healthcare": ["HIPAA compliance", "clinical workflows", "patient outcomes", "medical records", "healthcare IT"],
            "finance": ["regulatory compliance", "financial modeling", "risk assessment", "investment strategies", "portfolio management"],
            "technology": ["agile methodologies", "cloud architecture", "DevOps practices", "scalable solutions", "digital transformation"],
            "education": ["pedagogical approaches", "learning outcomes", "curriculum design", "educational technology", "student engagement"],
            "marketing": ["customer acquisition", "brand positioning", "conversion optimization", "content strategy", "market segmentation"]
        }
        
        # AI detection avoidance patterns
        self.avoidance_patterns = {
            "repeated_phrases": [
                "in conclusion", "in summary", "to summarize", "in essence", "ultimately",
                "it's important to note", "it's worth mentioning", "keep in mind", "remember that"
            ],
            "ai_tells": [
                "as an ai", "as a language model", "i'm an ai", "ai generated", "machine generated",
                "artificial intelligence", "neural network", "algorithm", "computationally"
            ],
            "generic_patterns": [
                "unlock the power of", "harness the potential of", "leverage the power of",
                "in today's digital age", "in the modern world", "in this fast-paced world"
            ]
        }
        
        # Content variation matrices
        self.content_matrices = {
            "perspectives": ["professional", "academic", "practical", "strategic", "tactical"],
            "tones": ["formal", "conversational", "technical", "accessible", "authoritative"],
            "complexities": ["simple", "intermediate", "advanced", "expert", "comprehensive"]
        }
    
    def generate_unique_content(self, base_content: str, context: Dict[str, Any], variation_count: int = 5) -> List[str]:
        """Generate multiple unique content variations"""
        
        variations = []
        
        for i in range(variation_count):
            # Apply different uniqueness strategies
            if i == 0:
                variation = self._apply_sentence_restructuring(base_content, context)
            elif i == 1:
                variation = self._apply_terminology_variation(base_content, context)
            elif i == 2:
                variation = self._apply_perspective_shift(base_content, context)
            elif i == 3:
                variation = self._apply_structural_variation(base_content, context)
            else:
                variation = self._apply_comprehensive_variation(base_content, context)
            
            # Validate uniqueness
            if self._validate_uniqueness(variation, variations):
                variations.append(variation)
        
        return variations
    
    def _apply_sentence_restructuring(self, content: str, context: Dict[str, Any]) -> str:
        """Apply sentence restructuring for uniqueness"""
        
        sentences = re.split(r'[.!?]+', content)
        restructured_sentences = []
        
        for sentence in sentences:
            if sentence.strip():
                # Randomly select sentence structure
                structure = random.choice(self.sentence_structures)
                restructured = self._restructure_sentence(sentence.strip(), structure)
                restructured_sentences.append(restructured)
        
        # Add human-like transitions
        return self._add_human_transitions('. '.join(restructured_sentences))
    
    def _restructure_sentence(self, sentence: str, structure: str) -> str:
        """Restructure sentence according to pattern"""
        
        words = sentence.split()
        if len(words) < 3:
            return sentence
        
        # Simple restructuring based on pattern
        if structure == "Subject-Verb-Object-Adverbial":
            # Keep original structure
            return sentence
        elif structure == "Adverbial-Subject-Verb-Object":
            # Move adverbial to beginning
            if len(words) >= 4:
                return f"{words[-1]} {' '.join(words[:-1])}"
        elif structure == "Object-Subject-Verb-Adverbial":
            # Invert structure
            if len(words) >= 3:
                return f"{words[-2]} {' '.join(words[:-2])} {words[-1]}"
        
        return sentence
    
    def _apply_terminology_variation(self, content: str, context: Dict[str, Any]) -> str:
        """Apply industry-specific terminology variation"""
        
        industry = context.get('industry', 'general')
        
        if industry in self.industry_terminology:
            terminology = self.industry_terminology[industry]
            
            # Replace generic terms with industry-specific ones
            replacements = {
                "process": ["workflow", "procedure", "methodology"],
                "system": ["platform", "framework", "ecosystem"],
                "tool": ["solution", "utility", "application"],
                "data": ["information", "insights", "analytics"],
                "users": ["professionals", "practitioners", "specialists"]
            }
            
            varied_content = content
            for generic, specific_options in replacements.items():
                if generic in varied_content:
                    replacement = random.choice(specific_options + [generic])
                    varied_content = varied_content.replace(generic, replacement, 1)
            
            # Add industry-specific terms
            for term in random.sample(terminology, min(2, len(terminology))):
                if term not in varied_content:
                    varied_content += f" This includes {term} considerations."
            
            return varied_content
        
        return content
    
    def _apply_perspective_shift(self, content: str, context: Dict[str, Any]) -> str:
        """Apply perspective shift for uniqueness"""
        
        perspective = random.choice(self.content_matrices["perspectives"])
        
        perspective_modifiers = {
            "professional": ["From a professional standpoint,", "Professionally speaking,", "In professional contexts,"],
            "academic": ["From an academic perspective,", "Academically speaking,", "In academic settings,"],
            "practical": ["From a practical standpoint,", "Practically speaking,", "In practical applications,"],
            "strategic": ["From a strategic perspective,", "Strategically speaking,", "In strategic planning,"],
            "tactical": ["From a tactical viewpoint,", "Tactically speaking,", "In tactical execution,"]
        }
        
        modifiers = perspective_modifiers.get(perspective, ["From a general perspective,"])
        modifier = random.choice(modifiers)
        
        return f"{modifier} {content}"
    
    def _apply_structural_variation(self, content: str, context: Dict[str, Any]) -> str:
        """Apply structural variation"""
        
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        varied_paragraphs = []
        
        for paragraph in paragraphs:
            if paragraph.strip():
                # Randomly reorder sentences within paragraph
                sentences = re.split(r'[.!?]+', paragraph)
                if len(sentences) > 2:
                    # Keep first sentence, shuffle middle ones, keep last
                    first = sentences[0].strip()
                    middle = random.sample(sentences[1:-1], len(sentences[1:-1]))
                    last = sentences[-1].strip() if len(sentences) > 1 else ""
                    
                    varied_paragraph = '. '.join([first] + middle + ([last] if last else []))
                    varied_paragraphs.append(varied_paragraph)
                else:
                    varied_paragraphs.append(paragraph)
        
        return '\n\n'.join(varied_paragraphs)
    
    def _apply_comprehensive_variation(self, content: str, context: Dict[str, Any]) -> str:
        """Apply comprehensive variation combining multiple techniques"""
        
        # Start with terminology variation
        varied = self._apply_terminology_variation(content, context)
        
        # Add perspective shift
        varied = self._apply_perspective_shift(varied, context)
        
        # Apply sentence restructuring to parts of it
        sentences = varied.split('. ')
        if len(sentences) > 3:
            # Restructure middle sentences
            middle_start = 1
            middle_end = len(sentences) - 1
            
            for i in range(middle_start, middle_end):
                if i < len(sentences):
                    structure = random.choice(self.sentence_structures)
                    sentences[i] = self._restructure_sentence(sentences[i], structure)
            
            varied = '. '.join(sentences)
        
        return varied
    
    def _add_human_transitions(self, content: str) -> str:
        """Add human-like transitions"""
        
        sentences = content.split('. ')
        if len(sentences) > 2:
            # Add transition to random middle sentence
            transition_pos = random.randint(1, len(sentences) - 2)
            transition = random.choice(self.human_transitions)
            
            sentences[transition_pos] = f"{transition} {sentences[transition_pos]}"
        
        return '. '.join(sentences)
    
    def _validate_uniqueness(self, new_content: str, existing_contents: List[str]) -> bool:
        """Validate content uniqueness against existing content"""
        
        for existing in existing_contents:
            similarity = self._calculate_similarity(new_content, existing)
            if similarity > 0.85:  # 85% similarity threshold
                return False
        
        return True
    
    def _calculate_similarity(self, content1: str, content2: str) -> float:
        """Calculate content similarity"""
        
        # Simple similarity calculation using word overlap
        words1 = set(content1.lower().split())
        words2 = set(content2.lower().split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        if len(union) == 0:
            return 0.0
        
        return len(intersection) / len(union)
    
    def remove_ai_detection_patterns(self, content: str) -> str:
        """Remove AI detection patterns"""
        
        cleaned = content
        
        # Remove AI tells
        for pattern in self.avoidance_patterns["ai_tells"]:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        # Remove generic patterns
        for pattern in self.avoidance_patterns["generic_patterns"]:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        # Remove repeated phrases
        for pattern in self.avoidance_patterns["repeated_phrases"]:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        
        # Clean up double spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def add_human_like_elements(self, content: str) -> str:
        """Add human-like elements to content"""
        
        humanized = content
        
        # Add occasional contractions
        contractions = {
            "it is": "it's",
            "do not": "don't",
            "will not": "won't",
            "cannot": "can't",
            "are not": "aren't",
            "is not": "isn't"
        }
        
        for formal, contraction in contractions.items():
            if random.random() < 0.3:  # 30% chance to replace
                humanized = humanized.replace(formal, contraction)
        
        # Add occasional rhetorical questions
        if random.random() < 0.2:  # 20% chance
            questions = [
                "So what does this mean for you?",
                "Why does this matter?",
                "How can you apply this?",
                "What's the bottom line?"
            ]
            question = random.choice(questions)
            humanized += f" {question}"
        
        # Add occasional emphasis
        if random.random() < 0.15:  # 15% chance
            emphasis_words = ["absolutely", "definitely", "certainly", "clearly"]
            emphasis = random.choice(emphasis_words)
            # Insert at beginning of random sentence
            sentences = humanized.split('. ')
            if len(sentences) > 1:
                pos = random.randint(0, len(sentences) - 1)
                sentences[pos] = f"{emphasis}, {sentences[pos]}"
                humanized = '. '.join(sentences)
        
        return humanized
    
    def generate_contextual_examples(self, tool_name: str, context: Dict[str, Any]) -> List[str]:
        """Generate contextual examples with uniqueness"""
        
        industry = context.get('industry', 'general')
        experience = context.get('experience', 'professional')
        
        examples = []
        
        # Generate industry-specific examples
        if industry in self.industry_terminology:
            terminology = self.industry_terminology[industry]
            
            for i in range(3):
                example = self._create_industry_example(tool_name, industry, terminology, i)
                examples.append(example)
        
        # Generate experience-specific examples
        experience_examples = self._create_experience_examples(tool_name, experience)
        examples.extend(experience_examples)
        
        # Ensure uniqueness
        unique_examples = []
        for example in examples:
            if self._validate_uniqueness(example, unique_examples):
                unique_examples.append(example)
        
        return unique_examples[:5]
    
    def _create_industry_example(self, tool_name: str, industry: str, terminology: List[str], index: int) -> str:
        """Create industry-specific example"""
        
        if index >= len(terminology):
            term = terminology[0]
        else:
            term = terminology[index]
        
        example_templates = [
            f"Using {tool_name} to streamline {term} workflows in the {industry} sector",
            f"Professional {tool_name} implementation for {term} compliance",
            f"Optimizing {term} processes with advanced {tool_name} features",
            f"Industry-leading {tool_name} solutions for {term} management"
        ]
        
        return random.choice(example_templates)
    
    def _create_experience_examples(self, tool_name: str, experience: str) -> List[str]:
        """Create experience-specific examples"""
        
        experience_mapping = {
            "freshers": [
                f"Entry-level {tool_name} usage for recent graduates",
                f"Beginner-friendly {tool_name} features for newcomers",
                f"Learning {tool_name} from scratch for freshers"
            ],
            "mid-level": [
                f"Advanced {tool_name} techniques for experienced professionals",
                f"Intermediate {tool_name} workflows for mid-level practitioners",
                f"Professional {tool_name} applications for career growth"
            ],
            "senior": [
                f"Expert-level {tool_name} strategies for senior professionals",
                f"Advanced {tool_name} optimization for experienced users",
                f"Strategic {tool_name} implementation for leadership roles"
            ]
        }
        
        return experience_mapping.get(experience, [
            f"Professional {tool_name} usage for all experience levels",
            f"Versatile {tool_name} applications for various users"
        ])
    
    def generate_unique_faq_items(self, tool_name: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate unique FAQ items with anti-duplicate patterns"""
        
        faq_items = []
        
        # Generate contextual FAQs
        contextual_faqs = self._generate_contextual_faqs(tool_name, context)
        faq_items.extend(contextual_faqs)
        
        # Generate technical FAQs
        technical_faqs = self._generate_technical_faqs(tool_name)
        faq_items.extend(technical_faqs)
        
        # Generate practical FAQs
        practical_faqs = self._generate_practical_faqs(tool_name, context)
        faq_items.extend(practical_faqs)
        
        # Ensure uniqueness
        unique_faqs = []
        for faq in faq_items:
            if self._validate_faq_uniqueness(faq, unique_faqs):
                unique_faqs.append(faq)
        
        return unique_faqs[:8]
    
    def _generate_contextual_faqs(self, tool_name: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate contextual FAQ items"""
        
        industry = context.get('industry', 'general')
        experience = context.get('experience', 'professional')
        
        contextual_faqs = [
            {
                "q": f"How does {tool_name} specifically benefit {industry} professionals?",
                "a": f"Our {tool_name.lower()} is tailored for {industry} workflows with industry-specific features and compliance considerations that address unique sector challenges."
            },
            {
                "q": f"Is {tool_name} suitable for {experience} users?",
                "a": f"Yes, {tool_name} offers {experience}-appropriate complexity with guided workflows and adjustable settings that match your skill level and experience requirements."
            },
            {
                "q": f"What makes {tool_name} different from other tools in the {industry} space?",
                "a": f"Unlike generic alternatives, our {tool_name.lower()} incorporates deep {industry} knowledge, sector-specific best practices, and compliance features that professionals truly need."
            }
        ]
        
        return contextual_faqs
    
    def _generate_technical_faqs(self, tool_name: str) -> List[Dict[str, str]]:
        """Generate technical FAQ items"""
        
        technical_faqs = [
            {
                "q": f"What are the technical requirements for using {tool_name}?",
                "a": f"{tool_name} works entirely in your web browser with no software installation required. It supports all modern browsers and automatically adapts to your device specifications."
            },
            {
                "q": f"How does {tool_name} handle data security and privacy?",
                "a": f"All processing happens locally in your browser, ensuring your data never leaves your device. We use industry-standard encryption and follow strict privacy protocols."
            },
            {
                "q": f"Can {tool_name} handle large-scale data processing?",
                "a": f"Yes, {tool_name} is optimized for performance and can efficiently handle substantial data volumes while maintaining accuracy and speed."
            }
        ]
        
        return technical_faqs
    
    def _generate_practical_faqs(self, tool_name: str, context: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate practical FAQ items"""
        
        practical_faqs = [
            {
                "q": f"How quickly can I get results with {tool_name}?",
                "a": f"{tool_name} delivers instant results with most operations completing in seconds. Complex processing may take slightly longer but still provides rapid outcomes."
            },
            {
                "q": f"Can I integrate {tool_name} into my existing workflow?",
                "a": f"Absolutely! {tool_name} is designed for seamless integration with various workflows and offers export options that work with your existing tools and processes."
            },
            {
                "q": f"Is there a learning curve for {tool_name}?",
                "a": f"{tool_name} features an intuitive interface that's easy to master. We provide comprehensive guidance and the tool includes helpful prompts throughout your workflow."
            }
        ]
        
        return practical_faqs
    
    def _validate_faq_uniqueness(self, faq: Dict[str, str], existing_faqs: List[Dict[str, str]]) -> bool:
        """Validate FAQ uniqueness"""
        
        for existing in existing_faqs:
            question_similarity = self._calculate_similarity(faq['q'], existing['q'])
            answer_similarity = self._calculate_similarity(faq['a'], existing['a'])
            
            if question_similarity > 0.8 or answer_similarity > 0.8:
                return False
        
        return True
    
    def calculate_content_uniqueness_score(self, content: str) -> float:
        """Calculate overall uniqueness score"""
        
        # Factors that affect uniqueness
        factors = {
            "sentence_variation": self._calculate_sentence_variation(content),
            "vocabulary_diversity": self._calculate_vocabulary_diversity(content),
            "structure_complexity": self._calculate_structure_complexity(content),
            "pattern_avoidance": self._calculate_pattern_avoidance(content)
        }
        
        # Weighted average
        weights = {
            "sentence_variation": 0.3,
            "vocabulary_diversity": 0.25,
            "structure_complexity": 0.25,
            "pattern_avoidance": 0.2
        }
        
        score = sum(factors[factor] * weights[factor] for factor in factors)
        
        return round(score, 2)
    
    def _calculate_sentence_variation(self, content: str) -> float:
        """Calculate sentence variation score"""
        
        sentences = re.split(r'[.!?]+', content)
        if len(sentences) < 2:
            return 0.5
        
        # Calculate sentence length variation
        lengths = [len(s.split()) for s in sentences if s.strip()]
        if not lengths:
            return 0.5
        
        avg_length = sum(lengths) / len(lengths)
        variance = sum((length - avg_length) ** 2 for length in lengths) / len(lengths)
        
        # Normalize to 0-1 scale
        variation_score = min(variance / 100, 1.0)  # Variance of 100 = max variation
        
        return variation_score
    
    def _calculate_vocabulary_diversity(self, content: str) -> float:
        """Calculate vocabulary diversity score"""
        
        words = content.lower().split()
        if len(words) < 10:
            return 0.5
        
        unique_words = set(words)
        diversity_ratio = len(unique_words) / len(words)
        
        # Adjust for content length
        if len(words) > 100:
            diversity_ratio = min(diversity_ratio * 1.2, 1.0)
        
        return diversity_ratio
    
    def _calculate_structure_complexity(self, content: str) -> float:
        """Calculate structure complexity score"""
        
        # Check for various structural elements
        complexity_indicators = {
            "has_paragraphs": '\n\n' in content,
            "has_lists": any(marker in content for marker in ['•', '-', '*', '1.', '2.']),
            "has_questions": '?' in content,
            "has_colons": ':' in content,
            "has_semicolons": ';' in content,
            "has_quotes': '"' in content or "'" in content
        }
        
        complexity_score = sum(complexity_indicators.values()) / len(complexity_indicators)
        
        return complexity_score
    
    def _calculate_pattern_avoidance(self, content: str) -> float:
        """Calculate pattern avoidance score"""
        
        content_lower = content.lower()
        
        # Check for avoided patterns
        avoided_patterns = []
        for category, patterns in self.avoidance_patterns.items():
            for pattern in patterns:
                if pattern in content_lower:
                    avoided_patterns.append(pattern)
        
        # Score based on how many patterns were avoided
        total_patterns = sum(len(patterns) for patterns in self.avoidance_patterns.values())
        if total_patterns == 0:
            avoidance_score = 1.0
        else:
            avoidance_score = 1.0 - (len(avoided_patterns) / total_patterns)
        
        return max(avoidance_score, 0.0)
    
    def get_uniqueness_report(self, content: str) -> Dict[str, Any]:
        """Generate comprehensive uniqueness report"""
        
        report = {
            "overall_score": self.calculate_content_uniqueness_score(content),
            "factors": {
                "sentence_variation": self._calculate_sentence_variation(content),
                "vocabulary_diversity": self._calculate_vocabulary_diversity(content),
                "structure_complexity": self._calculate_structure_complexity(content),
                "pattern_avoidance": self._calculate_pattern_avoidance(content)
            },
            "detected_patterns": self._detect_problematic_patterns(content),
            "recommendations": self._generate_uniqueness_recommendations(content),
            "word_count": len(content.split()),
            "character_count": len(content)
        }
        
        return report
    
    def _detect_problematic_patterns(self, content: str) -> List[str]:
        """Detect problematic patterns in content"""
        
        detected = []
        content_lower = content.lower()
        
        # Check for AI tells
        for pattern in self.avoidance_patterns["ai_tells"]:
            if pattern in content_lower:
                detected.append(f"AI tell detected: {pattern}")
        
        # Check for generic patterns
        for pattern in self.avoidance_patterns["generic_patterns"]:
            if pattern in content_lower:
                detected.append(f"Generic pattern detected: {pattern}")
        
        # Check for repeated phrases
        for pattern in self.avoidance_patterns["repeated_phrases"]:
            if pattern in content_lower:
                detected.append(f"Repeated phrase detected: {pattern}")
        
        return detected
    
    def _generate_uniqueness_recommendations(self, content: str) -> List[str]:
        """Generate recommendations for improving uniqueness"""
        
        recommendations = []
        report = self.get_uniqueness_report(content)
        
        if report["factors"]["sentence_variation"] < 0.5:
            recommendations.append("Vary sentence lengths and structures for better flow")
        
        if report["factors"]["vocabulary_diversity"] < 0.6:
            recommendations.append("Use more diverse vocabulary and avoid repetition")
        
        if report["factors"]["structure_complexity"] < 0.4:
            recommendations.append("Add more structural elements like lists, questions, or quotes")
        
        if report["factors"]["pattern_avoidance"] < 0.8:
            recommendations.append("Remove AI-like patterns and generic phrases")
        
        if len(report["detected_patterns"]) > 2:
            recommendations.append("Consider comprehensive content rewriting for higher uniqueness")
        
        return recommendations


# Singleton instance
content_uniqueness_engine = ContentUniquenessEngine()
