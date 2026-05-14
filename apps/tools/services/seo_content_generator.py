"""
AI Content Generation Engine for SEO
Generates humanized, unique SEO content for tools, categories, and programmatic pages
"""

import random
import json
from typing import List, Dict, Any, Optional
from django.conf import settings
from django.utils.text import slugify


class SEOContentGenerator:
    """Advanced AI content generation with humanization and uniqueness"""
    
    def __init__(self):
        # Humanization patterns to avoid repetitive AI content
        self.sentence_starters = [
            "Discover how", "Learn to", "Master the art of", "Explore our", 
            "Transform your", "Elevate your", "Streamline your", "Optimize",
            "Unlock the power of", "Harness the potential of", "Dive into",
            "Get started with", "Take control of", "Simplify your", "Enhance"
        ]
        
        self.transition_phrases = [
            "Moreover", "Furthermore", "In addition", "What's more", 
            "Not only that", "Beyond this", "Additionally", "Plus",
            "On top of that", "As well as", "Coupled with", "Along with"
        ]
        
        self.benefit_words = [
            "effortlessly", "instantly", "quickly", "easily", "seamlessly",
            "efficiently", "professionally", "accurately", "reliably", "securely"
        ]
        
        self.use_case_verbs = [
            "create", "generate", "convert", "transform", "optimize", "analyze",
            "validate", "format", "compress", "extract", "calculate", "measure"
        ]
    
    def generate_tool_intro(self, tool_name: str, tool_desc: str, category_name: str, word_count: int = 250) -> str:
        """Generate unique, humanized tool introduction"""
        
        # Extract key concepts
        keywords = self._extract_keywords(tool_name, tool_desc, category_name)
        
        # Build introduction structure
        intro_parts = []
        
        # Opening hook
        hook = self._generate_hook(tool_name, keywords)
        intro_parts.append(hook)
        
        # Value proposition
        value_prop = self._generate_value_proposition(tool_name, tool_desc, keywords)
        intro_parts.append(value_prop)
        
        # Key benefits
        benefits = self._generate_benefits(tool_name, keywords)
        intro_parts.append(benefits)
        
        # Use case preview
        use_case_preview = self._generate_use_case_preview(tool_name, keywords)
        intro_parts.append(use_case_preview)
        
        # Combine and refine
        intro = " ".join(intro_parts)
        
        # Ensure word count target
        current_words = len(intro.split())
        if current_words < word_count:
            intro = self._expand_content(intro, word_count - current_words, keywords)
        elif current_words > word_count + 50:
            intro = self._trim_content(intro, word_count)
        
        return intro
    
    def generate_use_cases(self, tool_name: str, tags: str = "", count: int = 5) -> List[str]:
        """Generate diverse use cases for the tool"""
        
        keywords = self._extract_keywords(tool_name, tags, "")
        base_verb = self._get_primary_verb(tool_name, keywords)
        
        use_cases = []
        
        # Professional use cases
        professional = self._generate_professional_use_cases(tool_name, base_verb, keywords)
        use_cases.extend(professional[:2])
        
        # Personal use cases
        personal = self._generate_personal_use_cases(tool_name, base_verb, keywords)
        use_cases.extend(personal[:2])
        
        # Educational use cases
        educational = self._generate_educational_use_cases(tool_name, base_verb, keywords)
        use_cases.extend(educational[:1])
        
        # Ensure we have enough unique use cases
        while len(use_cases) < count:
            additional = self._generate_additional_use_cases(tool_name, base_verb, keywords)
            for case in additional:
                if case not in use_cases and len(use_cases) < count:
                    use_cases.append(case)
        
        return use_cases[:count]
    
    def generate_faq_items(self, tool_name: str, tool_desc: str, category_name: str, count: int = 5) -> List[Dict[str, str]]:
        """Generate relevant FAQ items with natural questions"""
        
        keywords = self._extract_keywords(tool_name, tool_desc, category_name)
        
        faq_items = []
        
        # Core functionality questions
        core_questions = self._generate_core_questions(tool_name, keywords)
        faq_items.extend(core_questions[:2])
        
        # Technical questions
        technical_questions = self._generate_technical_questions(tool_name, keywords)
        faq_items.extend(technical_questions[:1])
        
        # Comparison questions
        comparison_questions = self._generate_comparison_questions(tool_name, keywords)
        faq_items.extend(comparison_questions[:1])
        
        # Usage questions
        usage_questions = self._generate_usage_questions(tool_name, keywords)
        faq_items.extend(usage_questions[:1])
        
        # Ensure we have enough unique FAQs
        while len(faq_items) < count:
            additional = self._generate_additional_faqs(tool_name, keywords)
            for faq in additional:
                if not any(faq['q'] == existing['q'] for existing in faq_items) and len(faq_items) < count:
                    faq_items.append(faq)
        
        return faq_items[:count]
    
    def generate_examples(self, tool_name: str, tool_desc: str, count: int = 3) -> List[Dict[str, Any]]:
        """Generate practical usage examples"""
        
        keywords = self._extract_keywords(tool_name, tool_desc, "")
        examples = []
        
        for i in range(count):
            example = {
                "title": f"Example {i + 1}: {self._generate_example_title(tool_name, keywords)}",
                "description": self._generate_example_description(tool_name, keywords),
                "input": self._generate_example_input(tool_name, keywords),
                "output": self._generate_example_output(tool_name, keywords),
                "steps": self._generate_example_steps(tool_name, keywords)
            }
            examples.append(example)
        
        return examples
    
    def generate_content_blocks(self, tool_name: str, tool_desc: str, category_name: str) -> List[Dict[str, Any]]:
        """Generate dynamic content blocks for tool pages"""
        
        keywords = self._extract_keywords(tool_name, tool_desc, category_name)
        blocks = []
        
        # How-to section
        how_to_block = {
            "type": "steps",
            "title": f"How to Use {tool_name}",
            "subtitle": f"Step-by-step guide to {self._get_primary_verb(tool_name, keywords)} with our tool",
            "steps": self._generate_how_to_steps(tool_name, keywords)
        }
        blocks.append(how_to_block)
        
        # Features section
        features_block = {
            "type": "list",
            "title": "Key Features",
            "subtitle": "What makes our tool stand out",
            "items": self._generate_features_list(tool_name, keywords)
        }
        blocks.append(features_block)
        
        # Benefits section
        benefits_block = {
            "type": "text",
            "title": "Why Choose Our Tool",
            "content": self._generate_benefits_content(tool_name, keywords)
        }
        blocks.append(benefits_block)
        
        # Tips section
        tips_block = {
            "type": "list",
            "title": "Pro Tips",
            "subtitle": "Get the most out of our tool",
            "items": self._generate_pro_tips(tool_name, keywords)
        }
        blocks.append(tips_block)
        
        return blocks
    
    def _extract_keywords(self, tool_name: str, tool_desc: str, category_name: str) -> List[str]:
        """Extract relevant keywords from input text"""
        
        text = f"{tool_name} {tool_desc} {category_name}".lower()
        
        # Common technical keywords
        tech_keywords = [
            "json", "xml", "html", "css", "javascript", "python", "java", "sql",
            "api", "csv", "pdf", "image", "text", "data", "format", "convert",
            "validate", "parse", "generate", "compress", "optimize", "encrypt",
            "decode", "hash", "url", "base64", "regex", "markdown", "yaml"
        ]
        
        # Extract keywords that appear in text
        extracted = []
        for keyword in tech_keywords:
            if keyword in text:
                extracted.append(keyword)
        
        # Extract words from tool name
        name_words = [word for word in tool_name.lower().split() if len(word) > 2]
        extracted.extend(name_words)
        
        return list(set(extracted))
    
    def _generate_hook(self, tool_name: str, keywords: List[str]) -> str:
        """Generate compelling opening hook"""
        
        starter = random.choice(self.sentence_starters)
        benefit = random.choice(self.benefit_words)
        
        if keywords:
            primary_keyword = keywords[0]
            return f"{starter} {benefit} {primary_keyword} with our powerful {tool_name}."
        else:
            return f"{starter} {benefit} transform your workflow with {tool_name}."
    
    def _generate_value_proposition(self, tool_name: str, tool_desc: str, keywords: List[str]) -> str:
        """Generate value proposition"""
        
        if tool_desc:
            desc_part = tool_desc[:100] + "..." if len(tool_desc) > 100 else tool_desc
            return f"Whether you're {self._generate_user_persona(keywords)} or {self._generate_user_persona(keywords, alt=True)}, our {tool_name} {desc_part}"
        else:
            return f"Our {tool_name} is designed to {self._get_primary_verb(tool_name, keywords)} with precision and efficiency."
    
    def _generate_benefits(self, tool_name: str, keywords: List[str]) -> str:
        """Generate benefits statement"""
        
        benefits = []
        
        # Speed benefit
        benefits.append(f"Process your data {random.choice(['instantly', 'quickly', 'in seconds'])}")
        
        # Accuracy benefit
        benefits.append(f"Get {random.choice(['accurate', 'precise', 'reliable'])} results every time")
        
        # Convenience benefit
        benefits.append(f"No {random.choice(['installation', 'download', 'signup'])} required")
        
        # Security benefit
        benefits.append(f"Your data stays {random.choice(['private', 'secure', 'confidential'])}")
        
        return f"{random.choice(self.transition_phrases)}, you can {', '.join(benefits[:3])}."
    
    def _generate_use_case_preview(self, tool_name: str, keywords: List[str]) -> str:
        """Generate use case preview"""
        
        verb = self._get_primary_verb(tool_name, keywords)
        return f"Perfect for {self._generate_target_audience(keywords)} who need to {verb} {random.choice(['efficiently', 'professionally', 'regularly'])}."
    
    def _get_primary_verb(self, tool_name: str, keywords: List[str]) -> str:
        """Determine primary verb based on tool name and keywords"""
        
        name_lower = tool_name.lower()
        
        for verb in self.use_case_verbs:
            if verb in name_lower:
                return verb
        
        # Fallback based on keywords
        if any(kw in keywords for kw in ["json", "xml", "html", "css"]):
            return "format"
        elif any(kw in keywords for kw in ["convert", "transform"]):
            return "convert"
        elif any(kw in keywords for kw in ["generate", "create"]):
            return "generate"
        elif any(kw in keywords for kw in ["compress", "optimize"]):
            return "optimize"
        else:
            return "process"
    
    def _generate_user_persona(self, keywords: List[str], alt: bool = False) -> str:
        """Generate user persona based on keywords"""
        
        personas = [
            "developers", "designers", "content creators", "students", 
            "researchers", "analysts", "marketers", "business owners"
        ]
        
        if keywords:
            if any(kw in keywords for kw in ["json", "api", "code"]):
                return "developers" if not alt else "software engineers"
            elif any(kw in keywords for kw in ["image", "design"]):
                return "designers" if not alt else "creative professionals"
            elif any(kw in keywords for kw in ["text", "content", "writing"]):
                return "content creators" if not alt else "writers"
            elif any(kw in keywords for kw in ["data", "analysis"]):
                return "analysts" if not alt else "data scientists"
        
        return random.choice(personas)
    
    def _generate_target_audience(self, keywords: List[str]) -> str:
        """Generate target audience description"""
        
        persona = self._generate_user_persona(keywords)
        qualifiers = ["professional", "busy", "modern", "tech-savvy"]
        
        return f"{random.choice(qualifiers)} {persona}"
    
    def _expand_content(self, content: str, target_words: int, keywords: List[str]) -> str:
        """Expand content to meet word count target"""
        
        sentences = content.split('. ')
        expanded_sentences = []
        
        for sentence in sentences:
            if sentence:
                expanded_sentences.append(sentence)
                
                # Add related details if we need more words
                if target_words > 0 and random.random() < 0.3:
                    detail = self._generate_related_detail(keywords)
                    expanded_sentences.append(detail)
                    target_words -= len(detail.split())
        
        return '. '.join(expanded_sentences)
    
    def _trim_content(self, content: str, target_words: int) -> str:
        """Trim content to meet word count target"""
        
        words = content.split()
        if len(words) <= target_words:
            return content
        
        trimmed = ' '.join(words[:target_words])
        
        # Ensure we don't cut off mid-sentence
        if '.' in trimmed:
            last_period = trimmed.rfind('.')
            trimmed = trimmed[:last_period + 1]
        
        return trimmed
    
    def _generate_related_detail(self, keywords: List[str]) -> str:
        """Generate related detail for content expansion"""
        
        if keywords:
            keyword = random.choice(keywords)
            templates = [
                f"This means you can work with {keyword} files seamlessly.",
                f"The tool handles {keyword} processing with high accuracy.",
                f"You'll get professional results for {keyword} tasks.",
                f"Perfect for {keyword} workflows and projects."
            ]
            return random.choice(templates)
        else:
            return "The interface is intuitive and user-friendly."
    
    def _generate_professional_use_cases(self, tool_name: str, verb: str, keywords: List[str]) -> List[str]:
        """Generate professional use cases"""
        
        use_cases = [
            f"{verb.capitalize()} business documents and reports",
            f"Process client data with professional accuracy",
            f"Streamline team workflows and collaboration",
            f"Generate deliverables for client projects",
            f"Maintain consistent formatting across documents"
        ]
        
        return random.sample(use_cases, min(3, len(use_cases)))
    
    def _generate_personal_use_cases(self, tool_name: str, verb: str, keywords: List[str]) -> List[str]:
        """Generate personal use cases"""
        
        use_cases = [
            f"{verb.capitalize()} personal projects and hobbies",
            f"Organize personal data and files",
            f"Create content for social media or blogs",
            f"Manage personal documentation",
            f"Quick format conversions for everyday use"
        ]
        
        return random.sample(use_cases, min(3, len(use_cases)))
    
    def _generate_educational_use_cases(self, tool_name: str, verb: str, keywords: List[str]) -> List[str]:
        """Generate educational use cases"""
        
        use_cases = [
            f"{verb.capitalize()} learning materials and assignments",
            f"Teach students about data formats and structures",
            f"Create examples for classroom demonstrations",
            f"Validate student work and submissions",
            f"Generate practice problems and exercises"
        ]
        
        return random.sample(use_cases, min(3, len(use_cases)))
    
    def _generate_additional_use_cases(self, tool_name: str, verb: str, keywords: List[str]) -> List[str]:
        """Generate additional use cases"""
        
        use_cases = [
            f"{verb.capitalize()} content for marketing campaigns",
            f"Process data for research and analysis",
            f"Create assets for web development",
            f"Handle batch processing operations",
            f"Integrate with existing workflows"
        ]
        
        return random.sample(use_cases, min(2, len(use_cases)))
    
    def _generate_core_questions(self, tool_name: str, keywords: List[str]) -> List[Dict[str, str]]:
        """Generate core functionality questions"""
        
        questions = [
            {
                "q": f"What is {tool_name} and how does it work?",
                "a": f"{tool_name} is a professional online tool designed to {self._get_primary_verb(tool_name, keywords)} {random.choice(['efficiently', 'accurately', 'quickly'])}. Simply {self._generate_simple_instruction(keywords)} and get instant results."
            },
            {
                "q": f"Is {tool_name} free to use?",
                "a": f"Yes, {tool_name} is completely free to use with no hidden charges, registration requirements, or usage limits. You can use it as many times as you need."
            },
            {
                "q": f"Do I need to download or install anything?",
                "a": f"No downloads or installations required. {tool_name} is a web-based tool that works directly in your browser on any device with an internet connection."
            }
        ]
        
        return random.sample(questions, min(2, len(questions)))
    
    def _generate_technical_questions(self, tool_name: str, keywords: List[str]) -> List[Dict[str, str]]:
        """Generate technical questions"""
        
        questions = [
            {
                "q": f"What file formats does {tool_name} support?",
                "a": f"{tool_name} supports a wide range of formats including {self._generate_supported_formats(keywords)}. All processing is done securely in your browser."
            },
            {
                "q": f"Is my data secure when using {tool_name}?",
                "a": f"Absolutely. All processing happens locally in your browser, and your data never leaves your device. We don't store or access any of your files."
            }
        ]
        
        return random.sample(questions, min(2, len(questions)))
    
    def _generate_comparison_questions(self, tool_name: str, keywords: List[str]) -> List[Dict[str, str]]:
        """Generate comparison questions"""
        
        questions = [
            {
                "q": f"How is {tool_name} different from other tools?",
                "a": f"{tool_name} stands out with its {random.choice(['intuitive interface', 'professional results', 'fast processing'])}, {random.choice(['no registration requirement', 'cross-platform compatibility', 'advanced features'])}, and {random.choice(['completely free usage', 'privacy-first approach', 'regular updates'])}."
            }
        ]
        
        return questions
    
    def _generate_usage_questions(self, tool_name: str, keywords: List[str]) -> List[Dict[str, str]]:
        """Generate usage questions"""
        
        questions = [
            {
                "q": f"Can I use {tool_name} on mobile devices?",
                "a": f"Yes, {tool_name} is fully responsive and works perfectly on smartphones, tablets, and desktop computers. The interface automatically adapts to your screen size."
            }
        ]
        
        return questions
    
    def _generate_additional_faqs(self, tool_name: str, keywords: List[str]) -> List[Dict[str, str]]:
        """Generate additional FAQ items"""
        
        questions = [
            {
                "q": f"Are there any usage limits or restrictions?",
                "a": f"No, there are no usage limits. You can use {tool_name} as many times as you need, whenever you need it, without any restrictions."
            },
            {
                "q": f"Can I integrate {tool_name} into my workflow?",
                "a": f"While {tool_name} is designed as a standalone web tool, you can easily incorporate it into your workflow by bookmarking the page and using it whenever needed."
            }
        ]
        
        return random.sample(questions, min(2, len(questions)))
    
    def _generate_simple_instruction(self, keywords: List[str]) -> str:
        """Generate simple instruction for FAQ answers"""
        
        if keywords:
            if "upload" in keywords or "file" in keywords:
                return "upload your file"
            elif "input" in keywords or "text" in keywords:
                return "enter your text"
            elif "paste" in keywords:
                return "paste your content"
            else:
                return "provide your input"
        else:
            return "provide your data"
    
    def _generate_supported_formats(self, keywords: List[str]) -> str:
        """Generate list of supported formats"""
        
        if keywords:
            format_keywords = [kw for kw in keywords if kw in ["json", "xml", "html", "css", "csv", "pdf", "txt", "md"]]
            if format_keywords:
                return ", ".join(format_keywords[:3]) + " and more"
        
        return "common text and data formats"
    
    def _generate_example_title(self, tool_name: str, keywords: List[str]) -> str:
        """Generate example title"""
        
        if keywords:
            primary_keyword = keywords[0]
            return f"{primary_keyword.title()} Processing"
        else:
            return "Basic Usage"
    
    def _generate_example_description(self, tool_name: str, keywords: List[str]) -> str:
        """Generate example description"""
        
        return f"This example demonstrates how to {self._get_primary_verb(tool_name, keywords)} using our {tool_name}."
    
    def _generate_example_input(self, tool_name: str, keywords: List[str]) -> str:
        """Generate example input"""
        
        if keywords:
            if "json" in keywords:
                return '{"name": "example", "value": 123}'
            elif "url" in keywords:
                return "https://example.com/page"
            elif "text" in keywords:
                return "Sample text content for processing"
            elif "number" in keywords or "calculate" in keywords:
                return "42"
        
        return "Sample input data"
    
    def _generate_example_output(self, tool_name: str, keywords: List[str]) -> str:
        """Generate example output"""
        
        return "Processed output will appear here"
    
    def _generate_example_steps(self, tool_name: str, keywords: List[str]) -> List[str]:
        """Generate example steps"""
        
        steps = [
            f"Enter your {random.choice(['data', 'text', 'content'])} in the input field",
            f"Click the {random.choice(['Process', 'Convert', 'Generate', 'Format'])} button",
            f"View and {random.choice(['download', 'copy', 'use'])} your results"
        ]
        
        return steps
    
    def _generate_how_to_steps(self, tool_name: str, keywords: List[str]) -> List[Dict[str, str]]:
        """Generate step-by-step instructions"""
        
        steps = [
            {
                "title": "Step 1: Prepare Your Data",
                "content": f"Gather the {random.choice(['files', 'text', 'data'])} you want to process with {tool_name}."
            },
            {
                "title": "Step 2: Input Your Content",
                "content": f"{self._generate_simple_instruction(keywords).title()} using the provided interface."
            },
            {
                "title": "Step 3: Process and Review",
                "content": f"Click the process button and review the {random.choice(['formatted', 'converted', 'generated'])} results."
            },
            {
                "title": "Step 4: Use Your Results",
                "content": f"{random.choice(['Download', 'Copy', 'Save'])} your processed content for immediate use."
            }
        ]
        
        return steps
    
    def _generate_features_list(self, tool_name: str, keywords: List[str]) -> List[str]:
        """Generate features list"""
        
        features = [
            f"Lightning-fast {self._get_primary_verb(tool_name, keywords)}",
            "Professional-grade accuracy and reliability",
            "Intuitive, user-friendly interface",
            "No registration or software installation required",
            "Cross-platform compatibility (desktop, mobile, tablet)",
            "Secure local processing (data never leaves your device)",
            "Unlimited free usage with no restrictions",
            "Regular updates and feature improvements"
        ]
        
        return random.sample(features, 5)
    
    def _generate_benefits_content(self, tool_name: str, keywords: List[str]) -> str:
        """Generate benefits content"""
        
        return f"Our {tool_name} offers numerous advantages over traditional methods. You'll save time with instant processing, ensure accuracy with professional-grade algorithms, and maintain privacy with local-only processing. The tool is designed to handle {self._get_primary_verb(tool_name, keywords)} tasks efficiently, making it the perfect choice for both personal and professional use."
    
    def _generate_pro_tips(self, tool_name: str, keywords: List[str]) -> List[str]:
        """Generate pro tips"""
        
        tips = [
            f"Use keyboard shortcuts to speed up your {tool_name} workflow",
            f"Bookmark the tool for quick access during projects",
            f"Try different input formats to see how {tool_name} handles various data types",
            f"Use the results directly in your applications for seamless integration",
            f"Share the tool with team members to standardize your workflow"
        ]
        
        return random.sample(tips, 3)


# Singleton instance for easy import
seo_content_generator = SEOContentGenerator()
