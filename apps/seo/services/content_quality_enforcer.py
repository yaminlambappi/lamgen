"""
Content Quality Enforcement System
Validates content quality before publishing any generated page
"""

from typing import List, Dict, Any, Optional, Tuple
from django.db.models import Q, Count, F, Avg
from django.core.cache import cache
from django.conf import settings
from django.utils.text import slugify
from apps.tools.models import Tool, ToolCategory
from apps.seo.models import SEOPage, LongTailVariant
from apps.seo.services.content_uniqueness_engine import content_uniqueness_engine
import hashlib
import json
import time
from datetime import datetime, timedelta
import re


class ContentQualityEnforcer:
    """Content quality enforcement system"""
    
    def __init__(self):
        self.cache_timeout = 60 * 60 * 24  # 24 hours
        
        # Quality thresholds
        self.quality_thresholds = {
            "min_uniqueness_score": 0.80,      # 80% uniqueness required
            "min_word_count": 300,            # 300 words minimum
            "min_faq_count": 3,                # Minimum 3 FAQ items
            "min_examples_count": 2,           # Minimum 2 examples
            "min_internal_links": 8,           # Minimum 8 internal links
            "max_duplicate_intent": 0.1,       # 10% duplicate intent threshold
            "min_semantic_relevance": 0.7,      # 70% semantic relevance
            "min_content_depth": 0.6,          # 60% content depth score
            "max_readability_issues": 5         # Maximum readability issues
        }
        
        # Content quality factors
        self.quality_factors = {
            "uniqueness": {"weight": 0.25, "threshold": 0.80},
            "word_count": {"weight": 0.15, "threshold": 300},
            "content_structure": {"weight": 0.15, "threshold": 0.6},
            "semantic_relevance": {"weight": 0.20, "threshold": 0.7},
            "internal_linking": {"weight": 0.10, "threshold": 8},
            "readability": {"weight": 0.10, "threshold": 0.7},
            "completeness": {"weight": 0.05, "threshold": 0.8}
        }
    
    def validate_content_for_publishing(self, content_data: Dict[str, Any], page_type: str = "tool") -> Dict[str, Any]:
        """Validate content quality before publishing"""
        
        validation_result = {
            "passed": False,
            "overall_score": 0.0,
            "factor_scores": {},
            "critical_issues": [],
            "warnings": [],
            "recommendations": [],
            "validation_timestamp": datetime.now().isoformat(),
            "page_type": page_type
        }
        
        # Run all quality checks
        factor_scores = {}
        
        # Uniqueness check
        uniqueness_score = self._check_uniqueness(content_data)
        factor_scores["uniqueness"] = uniqueness_score
        
        # Word count check
        word_count_score = self._check_word_count(content_data)
        factor_scores["word_count"] = word_count_score
        
        # Content structure check
        structure_score = self._check_content_structure(content_data)
        factor_scores["content_structure"] = structure_score
        
        # Semantic relevance check
        semantic_score = self._check_semantic_relevance(content_data)
        factor_scores["semantic_relevance"] = semantic_score
        
        # Internal linking check
        linking_score = self._check_internal_linking(content_data)
        factor_scores["internal_linking"] = linking_score
        
        # Readability check
        readability_score = self._check_readability(content_data)
        factor_scores["readability"] = readability_score
        
        # Completeness check
        completeness_score = self._check_completeness(content_data)
        factor_scores["completeness"] = completeness_score
        
        # Calculate overall score
        overall_score = self._calculate_overall_quality_score(factor_scores)
        validation_result["overall_score"] = overall_score
        validation_result["factor_scores"] = factor_scores
        
        # Determine if content passes
        validation_result["passed"] = self._determine_pass_status(factor_scores, overall_score)
        
        # Generate issues and recommendations
        validation_result["critical_issues"] = self._identify_critical_issues(factor_scores)
        validation_result["warnings"] = self._identify_warnings(factor_scores)
        validation_result["recommendations"] = self._generate_quality_recommendations(factor_scores)
        
        return validation_result
    
    def _check_uniqueness(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check content uniqueness"""
        
        result = {
            "score": 0.0,
            "passed": False,
            "issues": []
        }
        
        # Get content text
        content_text = self._extract_content_text(content_data)
        
        if not content_text:
            result["issues"].append("No content found for uniqueness check")
            return result
        
        # Calculate uniqueness score
        uniqueness_report = content_uniqueness_engine.get_uniqueness_report(content_text)
        uniqueness_score = uniqueness_report["overall_score"]
        result["score"] = uniqueness_score
        
        # Check against threshold
        if uniqueness_score < self.quality_thresholds["min_uniqueness_score"]:
            result["issues"].append(f"Uniqueness score {uniqueness_score:.2f} below threshold {self.quality_thresholds['min_uniqueness_score']}")
        else:
            result["passed"] = True
        
        # Check for detected patterns
        detected_patterns = uniqueness_report.get("detected_patterns", [])
        if detected_patterns:
            result["issues"].extend([f"Pattern detected: {pattern}" for pattern in detected_patterns])
        
        return result
    
    def _check_word_count(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check word count"""
        
        result = {
            "score": 0.0,
            "passed": False,
            "word_count": 0,
            "issues": []
        }
        
        # Count words
        content_text = self._extract_content_text(content_data)
        word_count = len(content_text.split()) if content_text else 0
        result["word_count"] = word_count
        
        # Calculate score based on word count
        min_words = self.quality_thresholds["min_word_count"]
        
        if word_count >= min_words:
            # Bonus points for longer content
            if word_count >= 1000:
                result["score"] = 1.0
            elif word_count >= 500:
                result["score"] = 0.9
            elif word_count >= min_words:
                result["score"] = 0.8
            
            result["passed"] = True
        else:
            # Partial score for short content
            result["score"] = max(word_count / min_words, 0.1)
            result["issues"].append(f"Word count {word_count} below minimum {min_words}")
        
        return result
    
    def _check_content_structure(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check content structure"""
        
        result = {
            "score": 0.0,
            "passed": False,
            "structure_elements": {},
            "issues": []
        }
        
        # Check for structural elements
        structure_elements = {
            "has_intro": bool(content_data.get("content_intro")),
            "has_examples": bool(content_data.get("examples")),
            "has_faq": bool(content_data.get("faq_items")),
            "has_use_cases": bool(content_data.get("use_cases")),
            "has_benefits": bool(content_data.get("benefits")),
            "has_steps": bool(content_data.get("steps"))
        }
        
        result["structure_elements"] = structure_elements
        
        # Calculate structure score
        structure_score = 0.0
        
        # Essential elements
        if structure_elements["has_intro"]:
            structure_score += 0.3
        
        if structure_elements["has_examples"]:
            structure_score += 0.2
        
        if structure_elements["has_faq"]:
            structure_score += 0.2
        
        # Bonus elements
        if structure_elements["has_use_cases"]:
            structure_score += 0.1
        
        if structure_elements["has_benefits"]:
            structure_score += 0.1
        
        if structure_elements["has_steps"]:
            structure_score += 0.1
        
        result["score"] = structure_score
        
        # Check minimum requirements
        if structure_elements["has_intro"] and structure_elements["has_examples"]:
            result["passed"] = True
        else:
            result["issues"].append("Missing essential structure elements (intro or examples)")
        
        return result
    
    def _check_semantic_relevance(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check semantic relevance"""
        
        result = {
            "score": 0.0,
            "passed": False,
            "relevance_metrics": {},
            "issues": []
        }
        
        # Extract keywords from content
        content_keywords = self._extract_keywords(content_data)
        
        # Get target keywords from context
        target_keywords = self._get_target_keywords(content_data)
        
        if not target_keywords:
            result["issues"].append("No target keywords defined")
            result["score"] = 0.5  # Default score
            return result
        
        # Calculate keyword overlap
        content_kw_set = set(content_keywords)
        target_kw_set = set(target_keywords)
        
        intersection = content_kw_set.intersection(target_kw_set)
        union = content_kw_set.union(target_kw_set)
        
        if union:
            keyword_overlap = len(intersection) / len(union)
        else:
            keyword_overlap = 0.0
        
        # Calculate semantic similarity (simplified)
        semantic_similarity = self._calculate_semantic_similarity(content_data, target_keywords)
        
        # Combine scores
        relevance_score = (keyword_overlap * 0.6) + (semantic_similarity * 0.4)
        result["score"] = relevance_score
        
        result["relevance_metrics"] = {
            "keyword_overlap": keyword_overlap,
            "semantic_similarity": semantic_similarity,
            "content_keywords": len(content_keywords),
            "target_keywords": len(target_keywords)
        }
        
        # Check threshold
        if relevance_score >= self.quality_thresholds["min_semantic_relevance"]:
            result["passed"] = True
        else:
            result["issues"].append(f"Semantic relevance {relevance_score:.2f} below threshold {self.quality_thresholds['min_semantic_relevance']}")
        
        return result
    
    def _check_internal_linking(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check internal linking"""
        
        result = {
            "score": 0.0,
            "passed": False,
            "link_count": 0,
            "link_types": {},
            "issues": []
        }
        
        # Count internal links
        internal_links = content_data.get("internal_links", [])
        link_count = len(internal_links)
        result["link_count"] = link_count
        
        # Analyze link types
        link_types = {
            "contextual": 0,
            "navigational": 0,
            "related": 0,
            "authority": 0
        }
        
        for link in internal_links:
            link_type = link.get("type", "contextual")
            if link_type in link_types:
                link_types[link_type] += 1
        
        result["link_types"] = link_types
        
        # Calculate linking score
        min_links = self.quality_thresholds["min_internal_links"]
        
        if link_count >= min_links:
            # Bonus for diverse link types
            type_diversity = len([t for t in link_types.values() if t > 0])
            diversity_bonus = min(type_diversity / 4, 0.2)  # Max 20% bonus
            
            result["score"] = 0.8 + diversity_bonus
            result["passed"] = True
        else:
            # Partial score based on link count
            result["score"] = max(link_count / min_links, 0.1)
            result["issues"].append(f"Internal links {link_count} below minimum {min_links}")
        
        return result
    
    def _check_readability(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check content readability"""
        
        result = {
            "score": 0.0,
            "passed": False,
            "readability_metrics": {},
            "issues": []
        }
        
        # Get content text
        content_text = self._extract_content_text(content_data)
        
        if not content_text:
            result["issues"].append("No content found for readability check")
            return result
        
        # Calculate readability metrics
        readability_metrics = self._calculate_readability_metrics(content_text)
        result["readability_metrics"] = readability_metrics
        
        # Calculate readability score
        readability_score = 0.0
        
        # Sentence length score (shorter is better)
        avg_sentence_length = readability_metrics["avg_sentence_length"]
        if avg_sentence_length <= 15:
            readability_score += 0.3
        elif avg_sentence_length <= 20:
            readability_score += 0.2
        elif avg_sentence_length <= 25:
            readability_score += 0.1
        
        # Paragraph length score
        avg_paragraph_length = readability_metrics["avg_paragraph_length"]
        if avg_paragraph_length <= 50:
            readability_score += 0.2
        elif avg_paragraph_length <= 100:
            readability_score += 0.15
        elif avg_paragraph_length <= 150:
            readability_score += 0.1
        
        # Vocabulary complexity score
        vocabulary_complexity = readability_metrics["vocabulary_complexity"]
        if vocabulary_complexity <= 0.7:
            readability_score += 0.2
        elif vocabulary_complexity <= 0.8:
            readability_score += 0.15
        elif vocabulary_complexity <= 0.9:
            readability_score += 0.1
        
        # Structure score
        has_headings = readability_metrics["has_headings"]
        has_lists = readability_metrics["has_lists"]
        
        if has_headings:
            readability_score += 0.1
        if has_lists:
            readability_score += 0.1
        
        result["score"] = min(readability_score, 1.0)
        
        # Check readability issues
        readability_issues = readability_metrics.get("issues", [])
        max_issues = self.quality_thresholds["max_readability_issues"]
        
        if len(readability_issues) > max_issues:
            result["issues"].append(f"Too many readability issues: {len(readability_issues)}")
        else:
            result["passed"] = True
        
        return result
    
    def _check_completeness(self, content_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check content completeness"""
        
        result = {
            "score": 0.0,
            "passed": False,
            "completeness_items": {},
            "issues": []
        }
        
        # Check completeness items
        completeness_items = {
            "has_title": bool(content_data.get("title")),
            "has_meta_description": bool(content_data.get("meta_description")),
            "has_h1": bool(content_data.get("h1")),
            "has_canonical": bool(content_data.get("canonical_url")),
            "has_schema": bool(content_data.get("schema_type")),
            "has_examples": bool(content_data.get("examples")),
            "has_faq": bool(content_data.get("faq_items")),
            "has_benefits": bool(content_data.get("benefits"))
        }
        
        result["completeness_items"] = completeness_items
        
        # Calculate completeness score
        completed_items = sum(completeness_items.values())
        total_items = len(completeness_items)
        completeness_score = completed_items / total_items
        
        result["score"] = completeness_score
        
        # Essential items for publishing
        essential_items = ["has_title", "has_meta_description", "has_h1", "has_examples"]
        essential_completed = sum(completeness_items.get(item, False) for item in essential_items)
        
        if essential_completed >= 3:  # At least 3 essential items
            result["passed"] = True
        else:
            result["issues"].append(f"Missing essential items: {4 - essential_completed}")
        
        return result
    
    def _extract_content_text(self, content_data: Dict[str, Any]) -> str:
        """Extract text content from content data"""
        
        text_parts = []
        
        # Add various content fields
        if content_data.get("content_intro"):
            text_parts.append(content_data["content_intro"])
        
        if content_data.get("use_cases"):
            if isinstance(content_data["use_cases"], list):
                text_parts.extend(content_data["use_cases"])
            else:
                text_parts.append(str(content_data["use_cases"]))
        
        if content_data.get("faq_items"):
            if isinstance(content_data["faq_items"], list):
                for faq in content_data["faq_items"]:
                    if isinstance(faq, dict):
                        text_parts.append(faq.get("q", ""))
                        text_parts.append(faq.get("a", ""))
                    else:
                        text_parts.append(str(faq))
        
        if content_data.get("examples"):
            if isinstance(content_data["examples"], list):
                text_parts.extend([str(ex) for ex in content_data["examples"]])
            else:
                text_parts.append(str(content_data["examples"]))
        
        if content_data.get("benefits"):
            if isinstance(content_data["benefits"], list):
                text_parts.extend(content_data["benefits"])
            else:
                text_parts.append(str(content_data["benefits"]))
        
        if content_data.get("steps"):
            if isinstance(content_data["steps"], list):
                for step in content_data["steps"]:
                    if isinstance(step, dict):
                        text_parts.append(step.get("title", ""))
                        text_parts.append(step.get("content", ""))
                    else:
                        text_parts.append(str(step))
        
        return " ".join(text_parts)
    
    def _extract_keywords(self, content_data: Dict[str, Any]) -> List[str]:
        """Extract keywords from content data"""
        
        keywords = set()
        
        # Add keywords from various sources
        if content_data.get("keywords"):
            if isinstance(content_data["keywords"], list):
                keywords.update(content_data["keywords"])
            else:
                keywords.update(content_data["keywords"].split(","))
        
        if content_data.get("tags"):
            if isinstance(content_data["tags"], list):
                keywords.update(content_data["tags"])
            else:
                keywords.update(content_data["tags"].split(","))
        
        # Extract from title
        if content_data.get("title"):
            title_words = content_data["title"].lower().split()
            keywords.update([word for word in title_words if len(word) > 3])
        
        # Extract from content text
        content_text = self._extract_content_text(content_data)
        content_words = content_text.lower().split()
        keywords.update([word for word in content_words if len(word) > 4])
        
        return list(keywords)
    
    def _get_target_keywords(self, content_data: Dict[str, Any]) -> List[str]:
        """Get target keywords for content"""
        
        target_keywords = []
        
        # Get from category or context
        if content_data.get("category"):
            target_keywords.extend(content_data["category"].lower().split())
        
        if content_data.get("topic"):
            target_keywords.extend(content_data["topic"].lower().split())
        
        if content_data.get("tool_name"):
            target_keywords.extend(content_data["tool_name"].lower().split())
        
        # Add common SEO keywords
        if content_data.get("page_type") == "tool":
            target_keywords.extend(["tool", "generator", "maker", "creator", "online", "free"])
        
        return [kw for kw in target_keywords if len(kw) > 2]
    
    def _calculate_semantic_similarity(self, content_data: Dict[str, Any], target_keywords: List[str]) -> float:
        """Calculate semantic similarity (simplified)"""
        
        # Get content keywords
        content_keywords = self._extract_keywords(content_data)
        
        # Calculate semantic similarity based on keyword overlap and context
        content_kw_set = set(content_keywords)
        target_kw_set = set(target_keywords)
        
        if not target_kw_set:
            return 0.5  # Default score
        
        # Jaccard similarity
        intersection = content_kw_set.intersection(target_kw_set)
        union = content_kw_set.union(target_kw_set)
        
        if union:
            jaccard_similarity = len(intersection) / len(union)
        else:
            jaccard_similarity = 0.0
        
        # Add context-based similarity
        context_similarity = self._calculate_context_similarity(content_data)
        
        # Combine scores
        semantic_similarity = (jaccard_similarity * 0.7) + (context_similarity * 0.3)
        
        return semantic_similarity
    
    def _calculate_context_similarity(self, content_data: Dict[str, Any]) -> float:
        """Calculate context similarity"""
        
        # Simplified context similarity based on content structure
        context_score = 0.0
        
        # Check for structured content
        if content_data.get("content_intro"):
            context_score += 0.2
        
        if content_data.get("examples"):
            context_score += 0.2
        
        if content_data.get("faq_items"):
            context_score += 0.2
        
        if content_data.get("benefits"):
            context_score += 0.2
        
        if content_data.get("steps"):
            context_score += 0.2
        
        return context_score
    
    def _calculate_readability_metrics(self, content_text: str) -> Dict[str, Any]:
        """Calculate readability metrics"""
        
        metrics = {
            "avg_sentence_length": 0,
            "avg_paragraph_length": 0,
            "vocabulary_complexity": 0,
            "has_headings": False,
            "has_lists": False,
            "issues": []
        }
        
        if not content_text:
            return metrics
        
        # Calculate average sentence length
        sentences = re.split(r'[.!?]+', content_text)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if sentences:
            sentence_lengths = [len(s.split()) for s in sentences]
            metrics["avg_sentence_length"] = sum(sentence_lengths) / len(sentence_lengths)
            
            # Check for long sentences
            long_sentences = [s for s in sentences if len(s.split()) > 25]
            if len(long_sentences) > len(sentences) * 0.2:
                metrics["issues"].append(f"Too many long sentences: {len(long_sentences)}")
        
        # Calculate average paragraph length
        paragraphs = content_text.split('\n\n')
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if paragraphs:
            paragraph_lengths = [len(p.split()) for p in paragraphs]
            metrics["avg_paragraph_length"] = sum(paragraph_lengths) / len(paragraph_lengths)
            
            # Check for long paragraphs
            long_paragraphs = [p for p in paragraphs if len(p.split()) > 100]
            if len(long_paragraphs) > len(paragraphs) * 0.3:
                metrics["issues"].append(f"Too many long paragraphs: {len(long_paragraphs)}")
        
        # Calculate vocabulary complexity (simplified)
        words = content_text.lower().split()
        unique_words = set(words)
        
        if words:
            metrics["vocabulary_complexity"] = len(unique_words) / len(words)
        
        # Check for structural elements
        metrics["has_headings"] = bool(re.search(r'<h[1-6]', content_text, re.IGNORECASE))
        metrics["has_lists"] = bool(re.search(r'[-*•]\s|^\d+\.', content_text, re.MULTILINE))
        
        return metrics
    
    def _calculate_overall_quality_score(self, factor_scores: Dict[str, Dict[str, Any]]) -> float:
        """Calculate overall quality score"""
        
        overall_score = 0.0
        
        for factor_name, factor_data in factor_scores.items():
            if factor_name in self.quality_factors:
                weight = self.quality_factors[factor_name]["weight"]
                score = factor_data.get("score", 0.0)
                overall_score += score * weight
        
        return min(overall_score, 1.0)
    
    def _determine_pass_status(self, factor_scores: Dict[str, Dict[str, Any]], overall_score: float) -> bool:
        """Determine if content passes quality check"""
        
        # Critical factors that must pass
        critical_factors = ["uniqueness", "word_count", "content_structure"]
        
        for factor in critical_factors:
            if factor in factor_scores:
                factor_data = factor_scores[factor]
                if not factor_data.get("passed", False):
                    return False
        
        # Overall score threshold
        if overall_score < 0.7:  # 70% minimum overall score
            return False
        
        return True
    
    def _identify_critical_issues(self, factor_scores: Dict[str, Dict[str, Any]]) -> List[str]:
        """Identify critical quality issues"""
        
        critical_issues = []
        
        for factor_name, factor_data in factor_scores.items():
            if factor_data.get("issues"):
                for issue in factor_data["issues"]:
                    # Mark as critical if it's a core factor
                    if factor_name in ["uniqueness", "word_count", "content_structure"]:
                        critical_issues.append(f"Critical: {factor_name} - {issue}")
                    else:
                        critical_issues.append(f"Issue: {factor_name} - {issue}")
        
        return critical_issues
    
    def _identify_warnings(self, factor_scores: Dict[str, Dict[str, Any]]) -> List[str]:
        """Identify non-critical warnings"""
        
        warnings = []
        
        for factor_name, factor_data in factor_scores.items():
            if factor_data.get("score", 0) < 0.8 and factor_data.get("passed", False):
                warnings.append(f"Low {factor_name} score: {factor_data['score']:.2f}")
        
        return warnings
    
    def _generate_quality_recommendations(self, factor_scores: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate quality improvement recommendations"""
        
        recommendations = []
        
        for factor_name, factor_data in factor_scores.items():
            if not factor_data.get("passed", False):
                if factor_name == "uniqueness":
                    recommendations.append("Improve content uniqueness by rewriting passages and avoiding AI patterns")
                elif factor_name == "word_count":
                    recommendations.append("Add more content to meet minimum word count requirements")
                elif factor_name == "content_structure":
                    recommendations.append("Add missing structure elements like intro, examples, or FAQ")
                elif factor_name == "semantic_relevance":
                    recommendations.append("Improve semantic relevance by using target keywords naturally")
                elif factor_name == "internal_linking":
                    recommendations.append("Add more internal links to improve content connectivity")
                elif factor_name == "readability":
                    recommendations.append("Improve readability by using shorter sentences and paragraphs")
                elif factor_name == "completeness":
                    recommendations.append("Complete missing essential elements like meta description or canonical URL")
        
        return recommendations
    
    def batch_validate_content(self, content_batch: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate multiple content items in batch"""
        
        batch_result = {
            "total_items": len(content_batch),
            "passed_items": 0,
            "failed_items": 0,
            "average_score": 0.0,
            "quality_distribution": {},
            "common_issues": {},
            "processing_time": 0
        }
        
        start_time = time.time()
        
        scores = []
        all_issues = []
        
        for content_data in content_batch:
            validation_result = self.validate_content_for_publishing(content_data)
            
            if validation_result["passed"]:
                batch_result["passed_items"] += 1
            else:
                batch_result["failed_items"] += 1
            
            scores.append(validation_result["overall_score"])
            all_issues.extend(validation_result["critical_issues"])
        
        # Calculate average score
        if scores:
            batch_result["average_score"] = sum(scores) / len(scores)
        
        # Quality distribution
        batch_result["quality_distribution"] = {
            "excellent": len([s for s in scores if s >= 0.9]),
            "good": len([s for s in scores if 0.8 <= s < 0.9]),
            "acceptable": len([s for s in scores if 0.7 <= s < 0.8]),
            "poor": len([s for s in scores if s < 0.7])
        }
        
        # Common issues
        issue_counts = {}
        for issue in all_issues:
            issue_type = issue.split(":")[0] if ":" in issue else issue
            issue_counts[issue_type] = issue_counts.get(issue_type, 0) + 1
        
        batch_result["common_issues"] = issue_counts
        
        end_time = time.time()
        batch_result["processing_time"] = end_time - start_time
        
        return batch_result
    
    def get_quality_enforcement_report(self) -> Dict[str, Any]:
        """Get comprehensive quality enforcement report"""
        
        report = {
            "summary": {},
            "thresholds": self.quality_thresholds,
            "quality_factors": self.quality_factors,
            "recent_validations": {},
            "quality_trends": {},
            "recommendations": []
        }
        
        # Get recent validation data from cache
        recent_validations = cache.get("recent_quality_validations", [])
        
        if recent_validations:
            # Calculate summary metrics
            total_validations = len(recent_validations)
            passed_validations = sum(1 for v in recent_validations if v.get("passed", False))
            avg_score = sum(v.get("overall_score", 0) for v in recent_validations) / total_validations
            
            report["summary"] = {
                "total_validations": total_validations,
                "passed_validations": passed_validations,
                "pass_rate": (passed_validations / total_validations) * 100,
                "average_score": avg_score
            }
            
            report["recent_validations"] = recent_validations[-10:]  # Last 10 validations
        
        # Quality trends
        report["quality_trends"] = self._calculate_quality_trends()
        
        # Recommendations
        report["recommendations"] = self._generate_enforcement_recommendations()
        
        return report
    
    def _calculate_quality_trends(self) -> Dict[str, Any]:
        """Calculate quality trends over time"""
        
        trends = {
            "daily_scores": [],
            "pass_rates": [],
            "common_issues_trend": {}
        }
        
        # Get cached validation data
        validation_history = cache.get("validation_history", [])
        
        # Group by date
        daily_data = {}
        
        for validation in validation_history:
            date = validation.get("timestamp", "").split("T")[0]  # Extract date
            if date not in daily_data:
                daily_data[date] = {"scores": [], "passed": 0, "total": 0}
            
            daily_data[date]["scores"].append(validation.get("overall_score", 0))
            if validation.get("passed", False):
                daily_data[date]["passed"] += 1
            daily_data[date]["total"] += 1
        
        # Calculate daily averages
        for date, data in daily_data.items():
            avg_score = sum(data["scores"]) / len(data["scores"]) if data["scores"] else 0
            pass_rate = (data["passed"] / data["total"]) * 100 if data["total"] > 0 else 0
            
            trends["daily_scores"].append({
                "date": date,
                "average_score": avg_score
            })
            
            trends["pass_rates"].append({
                "date": date,
                "pass_rate": pass_rate
            })
        
        return trends
    
    def _generate_enforcement_recommendations(self) -> List[str]:
        """Generate enforcement system recommendations"""
        
        recommendations = [
            "Set up automated quality checks in the content generation pipeline",
            "Implement content improvement workflows for failed validations",
            "Monitor quality trends and adjust thresholds as needed",
            "Create quality guidelines for content creators",
            "Set up alerts for quality score drops below 80%"
        ]
        
        return recommendations


# Singleton instance
content_quality_enforcer = ContentQualityEnforcer()
