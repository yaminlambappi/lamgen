"""
Job Tools - Complete Implementation of Job Application Utilities

Provides production-ready job description analyzer, keyword matcher, resume keyword,
and ATS resume checker tools with comprehensive job application support.
"""

import re
from typing import Dict, Any, List, Tuple
from datetime import datetime

from apps.tools.framework.base_tool import BaseTool, ToolConfig, ToolResult, ToolStatus, register_tool
from apps.tools.utils.validation import ValidationRule, ValidationType, COMMON_SCHEMAS
from apps.tools.utils.processing import TextProcessor
from apps.tools.utils.analytics import analytics_tracker


@register_tool(ToolConfig(
    name="Job Description Analyzer",
    slug="job-description-analyzer",
    category="resume",
    description="Analyze job descriptions to extract key requirements and insights",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Job Description Analyzer - LamGen',
        'description': 'Analyze job descriptions to extract requirements, skills, and get application insights.',
        'keywords': 'job description analyzer, job requirements, skills extraction, job analysis'
    }
))
class JobDescriptionAnalyzerTool(BaseTool):
    """Production-ready job description analyzer"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'job_description': COMMON_SCHEMAS['text_field'],
            'analysis_type': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='comprehensive',
                allowed_values=['basic', 'comprehensive', 'skills', 'requirements']
            ),
            'target_role': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                max_length=50
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Analyze job description"""
        try:
            job_description = input_data.get('job_description', '')
            analysis_type = input_data.get('analysis_type', 'comprehensive')
            target_role = input_data.get('target_role', '').strip()
            
            if not job_description:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Job description is required"
                )
            
            # Analyze job description
            analysis = self._analyze_job_description(job_description, analysis_type, target_role)
            
            # Generate insights
            insights = self._generate_job_insights(analysis)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'job_analysis': analysis,
                    'insights': insights,
                    'analysis_type': analysis_type,
                    'target_role': target_role
                },
                metadata={
                    'analysis_type': analysis_type,
                    'description_length': len(job_description)
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "analyze_job_description")
    
    def _analyze_job_description(self, description: str, analysis_type: str, target_role: str) -> Dict[str, Any]:
        """Analyze job description"""
        analysis = {
            'basic_info': self._extract_basic_info(description),
            'requirements': self._extract_requirements(description) if analysis_type in ['comprehensive', 'requirements'] else {},
            'skills': self._extract_skills(description) if analysis_type in ['comprehensive', 'skills'] else {},
            'responsibilities': self._extract_responsibilities(description) if analysis_type == 'comprehensive' else [],
            'qualifications': self._extract_qualifications(description) if analysis_type == 'comprehensive' else [],
            'company_info': self._extract_company_info(description) if analysis_type == 'comprehensive' else {},
            'job_level': self._determine_job_level(description),
            'keywords': self._extract_keywords(description)
        }
        
        return analysis
    
    def _extract_basic_info(self, description: str) -> Dict[str, Any]:
        """Extract basic job information"""
        info = {
            'title': '',
            'location': '',
            'salary': '',
            'employment_type': '',
            'remote_status': ''
        }
        
        lines = description.split('\n')
        
        # Extract title (usually in first few lines)
        for line in lines[:5]:
            if line.strip() and len(line.strip().split()) <= 5:
                info['title'] = line.strip()
                break
        
        # Extract location
        location_patterns = [
            r'Location:\s*(.+)',
            r'located in\s+(.+)',
            r'(.+)\s+(?:office|location)'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                info['location'] = match.group(1).strip()
                break
        
        # Extract salary
        salary_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:-\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:-\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)?)\s*k'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                info['salary'] = match.group(0)
                break
        
        # Extract employment type
        employment_types = ['full-time', 'part-time', 'contract', 'temporary', 'internship']
        for emp_type in employment_types:
            if emp_type in description.lower():
                info['employment_type'] = emp_type
                break
        
        # Extract remote status
        remote_keywords = ['remote', 'work from home', 'wfh', 'hybrid', 'on-site']
        for keyword in remote_keywords:
            if keyword in description.lower():
                info['remote_status'] = keyword
                break
        
        return info
    
    def _extract_requirements(self, description: str) -> Dict[str, Any]:
        """Extract job requirements"""
        requirements = {
            'education': [],
            'experience': [],
            'certifications': [],
            'technical_requirements': []
        }
        
        # Education requirements
        education_keywords = ['bachelor', 'master', 'phd', 'degree', 'diploma']
        for keyword in education_keywords:
            if keyword in description.lower():
                requirements['education'].append(keyword)
        
        # Experience requirements
        exp_pattern = r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp\.)'
        matches = re.findall(exp_pattern, description, re.IGNORECASE)
        requirements['experience'] = [f"{match} years" for match in matches]
        
        # Certifications
        cert_keywords = ['certification', 'certificate', 'certified', 'license']
        for keyword in cert_keywords:
            if keyword in description.lower():
                requirements['certifications'].append(keyword)
        
        # Technical requirements
        tech_keywords = ['programming', 'coding', 'software', 'tools', 'platforms', 'frameworks']
        for keyword in tech_keywords:
            if keyword in description.lower():
                requirements['technical_requirements'].append(keyword)
        
        return requirements
    
    def _extract_skills(self, description: str) -> Dict[str, List[str]]:
        """Extract skills from job description"""
        skills = {
            'technical': [],
            'soft': [],
            'tools': [],
            'languages': []
        }
        
        # Common technical skills
        technical_skills = [
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker',
            'git', 'linux', 'html', 'css', 'angular', 'vue', 'mongodb', 'postgresql'
        ]
        
        # Common soft skills
        soft_skills = [
            'communication', 'leadership', 'teamwork', 'problem-solving', 'analytical',
            'creativity', 'adaptability', 'time management', 'collaboration'
        ]
        
        # Common tools
        tools = [
            'jira', 'slack', 'github', 'gitlab', 'vs code', 'intellij', 'eclipse',
            'figma', 'sketch', 'photoshop', 'excel', 'powerpoint', 'word'
        ]
        
        # Extract skills
        description_lower = description.lower()
        
        for skill in technical_skills:
            if skill in description_lower:
                skills['technical'].append(skill)
        
        for skill in soft_skills:
            if skill in description_lower:
                skills['soft'].append(skill)
        
        for tool in tools:
            if tool in description_lower:
                skills['tools'].append(tool)
        
        # Remove duplicates
        for category in skills:
            skills[category] = list(set(skills[category]))
        
        return skills
    
    def _extract_responsibilities(self, description: str) -> List[str]:
        """Extract job responsibilities"""
        responsibilities = []
        
        lines = description.split('\n')
        in_responsibilities = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if we're in responsibilities section
            if any(keyword in line_lower for keyword in ['responsibilities', 'duties', 'what you\'ll do']):
                in_responsibilities = True
                continue
            
            # Check if we've left responsibilities section
            if in_responsibilities and any(keyword in line_lower for keyword in ['requirements', 'qualifications', 'skills']):
                break
            
            # Extract responsibility
            if in_responsibilities and line.strip():
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    responsibilities.append(line.strip())
                elif line.strip() and len(line.strip()) > 20:
                    responsibilities.append(line.strip())
        
        return responsibilities
    
    def _extract_qualifications(self, description: str) -> List[str]:
        """Extract job qualifications"""
        qualifications = []
        
        lines = description.split('\n')
        in_qualifications = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Check if we're in qualifications section
            if any(keyword in line_lower for keyword in ['qualifications', 'requirements', 'what you need']):
                in_qualifications = True
                continue
            
            # Check if we've left qualifications section
            if in_qualifications and any(keyword in line_lower for keyword in ['responsibilities', 'benefits', 'about']):
                break
            
            # Extract qualification
            if in_qualifications and line.strip():
                if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                    qualifications.append(line.strip())
                elif line.strip() and len(line.strip()) > 20:
                    qualifications.append(line.strip())
        
        return qualifications
    
    def _extract_company_info(self, description: str) -> Dict[str, Any]:
        """Extract company information"""
        company_info = {
            'name': '',
            'size': '',
            'industry': '',
            'culture': []
        }
        
        # Extract company name (simplified)
        company_patterns = [
            r'at\s+([A-Z][a-zA-Z\s&]+)',
            r'([A-Z][a-zA-Z\s&]+)\s+is\s+looking',
            r'join\s+([A-Z][a-zA-Z\s&]+)'
        ]
        
        for pattern in company_patterns:
            match = re.search(pattern, description)
            if match:
                company_info['name'] = match.group(1).strip()
                break
        
        # Extract company size
        size_patterns = [
            r'(\d+)\s*[-–]\s*(\d+)\s*employees',
            r'(\d+)\s*\+\s*employees',
            r'(small|medium|large|enterprise)\s+(?:company|organization)'
        ]
        
        for pattern in size_patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                company_info['size'] = match.group(0)
                break
        
        # Extract culture keywords
        culture_keywords = [
            'fast-paced', 'innovative', 'collaborative', 'diverse', 'inclusive',
            'work-life balance', 'flexible', 'growth', 'learning'
        ]
        
        for keyword in culture_keywords:
            if keyword in description.lower():
                company_info['culture'].append(keyword)
        
        return company_info
    
    def _determine_job_level(self, description: str) -> str:
        """Determine job level"""
        level_keywords = {
            'entry': ['entry level', 'junior', 'associate', 'intern'],
            'mid': ['mid level', 'intermediate', 'experienced'],
            'senior': ['senior', 'lead', 'principal', 'head'],
            'executive': ['manager', 'director', 'vp', 'executive', 'c-level']
        }
        
        description_lower = description.lower()
        
        for level, keywords in level_keywords.items():
            if any(keyword in description_lower for keyword in keywords):
                return level
        
        return 'unspecified'
    
    def _extract_keywords(self, description: str) -> List[str]:
        """Extract important keywords"""
        # Remove common words and extract keywords
        common_words = {
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
        
        words = re.findall(r'\b\w+\b', description.lower())
        keywords = [word for word in words if word not in common_words and len(word) > 3]
        
        # Return most common keywords
        word_freq = {}
        for word in keywords:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, count in sorted_words[:20]]
    
    def _generate_job_insights(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate job insights"""
        insights = []
        
        # Basic info insights
        basic_info = analysis.get('basic_info', {})
        if basic_info.get('remote_status'):
            insights.append(f"Job offers {basic_info['remote_status']} work option")
        
        if basic_info.get('salary'):
            insights.append(f"Salary range: {basic_info['salary']}")
        
        # Requirements insights
        requirements = analysis.get('requirements', {})
        if requirements.get('experience'):
            insights.append(f"Experience requirement: {requirements['experience'][0] if requirements['experience'] else 'Not specified'}")
        
        # Skills insights
        skills = analysis.get('skills', {})
        total_skills = sum(len(skill_list) for skill_list in skills.values())
        if total_skills > 0:
            insights.append(f"Job requires {total_skills} key skills")
        
        # Job level insights
        job_level = analysis.get('job_level', '')
        if job_level != 'unspecified':
            insights.append(f"Position level: {job_level}")
        
        # Application tips
        insights.extend([
            "Tailor your resume to match the key skills and requirements",
            "Highlight relevant experience in your cover letter",
            "Prepare examples for each key responsibility"
        ])
        
        return insights


@register_tool(ToolConfig(
    name="Keyword Matcher",
    slug="keyword-matcher",
    category="resume",
    description="Match keywords between resume and job description",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Keyword Matcher - LamGen',
        'description': 'Match keywords between resume and job description to optimize your application.',
        'keywords': 'keyword matcher, resume matching, job matching, ats optimization'
    }
))
class KeywordMatcherTool(BaseTool):
    """Production-ready keyword matcher"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'resume_text': COMMON_SCHEMAS['text_field'],
            'job_description': COMMON_SCHEMAS['text_field'],
            'match_type': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='comprehensive',
                allowed_values=['basic', 'comprehensive', 'skills', 'experience']
            ),
            'custom_keywords': ValidationRule(
                type=ValidationType.ARRAY,
                required=False,
                max_length=20
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Match keywords between resume and job description"""
        try:
            resume_text = input_data.get('resume_text', '')
            job_description = input_data.get('job_description', '')
            match_type = input_data.get('match_type', 'comprehensive')
            custom_keywords = input_data.get('custom_keywords', [])
            
            if not resume_text or not job_description:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Resume text and job description are required"
                )
            
            # Perform keyword matching
            match_results = self._match_keywords(
                resume_text, job_description, match_type, custom_keywords
            )
            
            # Generate recommendations
            recommendations = self._generate_keyword_recommendations(match_results)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'match_results': match_results,
                    'recommendations': recommendations,
                    'match_type': match_type
                },
                metadata={
                    'match_type': match_type,
                    'overall_score': match_results.get('overall_score', 0)
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "match_keywords")
    
    def _match_keywords(self, resume: str, job_desc: str, match_type: str, custom_keywords: List[str]) -> Dict[str, Any]:
        """Match keywords between resume and job description"""
        # Extract keywords from job description
        job_keywords = self._extract_job_keywords(job_desc)
        
        # Add custom keywords
        job_keywords.extend(custom_keywords)
        
        # Extract keywords from resume
        resume_keywords = self._extract_resume_keywords(resume)
        
        # Perform matching
        matching_results = {
            'job_keywords': job_keywords,
            'resume_keywords': resume_keywords,
            'matched_keywords': [],
            'missing_keywords': [],
            'keyword_density': {},
            'match_score': 0,
            'overall_score': 0
        }
        
        # Find matches
        for job_keyword in job_keywords:
            job_keyword_lower = job_keyword.lower()
            matched = False
            
            for resume_keyword in resume_keywords:
                if job_keyword_lower in resume_keyword.lower() or resume_keyword.lower() in job_keyword_lower:
                    matching_results['matched_keywords'].append({
                        'job_keyword': job_keyword,
                        'resume_keyword': resume_keyword,
                        'match_type': 'exact' if job_keyword_lower == resume_keyword.lower() else 'partial'
                    })
                    matched = True
                    break
            
            if not matched:
                matching_results['missing_keywords'].append(job_keyword)
        
        # Calculate scores
        if job_keywords:
            matching_results['match_score'] = (len(matching_results['matched_keywords']) / len(job_keywords)) * 100
        
        # Calculate overall score (including other factors)
        matching_results['overall_score'] = self._calculate_overall_score(matching_results, resume, job_desc, match_type)
        
        return matching_results
    
    def _extract_job_keywords(self, job_description: str) -> List[str]:
        """Extract keywords from job description"""
        # Common job-related keywords
        job_keywords = [
            'experience', 'skills', 'development', 'management', 'project',
            'team', 'leadership', 'communication', 'analytical', 'technical',
            'software', 'programming', 'coding', 'design', 'marketing', 'sales',
            'customer', 'service', 'support', 'operations', 'strategy', 'planning'
        ]
        
        # Extract specific keywords from job description
        words = re.findall(r'\b\w+\b', job_description.lower())
        
        # Filter for relevant keywords
        extracted_keywords = []
        for word in words:
            if len(word) > 3 and word not in extracted_keywords:
                if any(keyword in word for keyword in job_keywords):
                    extracted_keywords.append(word)
        
        return extracted_keywords[:30]  # Limit to top 30
    
    def _extract_resume_keywords(self, resume_text: str) -> List[str]:
        """Extract keywords from resume"""
        words = re.findall(r'\b\w+\b', resume_text.lower())
        
        # Filter for relevant keywords
        resume_keywords = []
        for word in words:
            if len(word) > 3 and word not in resume_keywords:
                resume_keywords.append(word)
        
        return resume_keywords[:50]  # Limit to top 50
    
    def _calculate_overall_score(self, results: Dict[str, Any], resume: str, job_desc: str, match_type: str) -> float:
        """Calculate overall match score"""
        score = results['match_score'] * 0.6  # 60% weight for keyword matching
        
        # Add other factors
        if match_type in ['comprehensive', 'experience']:
            # Experience matching
            exp_score = self._calculate_experience_match(resume, job_desc)
            score += exp_score * 0.2
        
        if match_type in ['comprehensive', 'skills']:
            # Skills matching
            skills_score = self._calculate_skills_match(resume, job_desc)
            score += skills_score * 0.2
        
        return min(100, score)
    
    def _calculate_experience_match(self, resume: str, job_desc: str) -> float:
        """Calculate experience match score"""
        # Extract years from job description
        job_exp_pattern = r'(\d+)\s*(?:years?|yrs?)'
        job_matches = re.findall(job_exp_pattern, job_desc)
        
        if not job_matches:
            return 50  # Neutral score
        
        required_years = int(job_matches[0])
        
        # Extract years from resume
        resume_matches = re.findall(job_exp_pattern, resume)
        resume_years = max([int(year) for year in resume_matches]) if resume_matches else 0
        
        # Calculate match
        if resume_years >= required_years:
            return 100
        elif resume_years >= required_years * 0.8:
            return 80
        elif resume_years >= required_years * 0.5:
            return 60
        else:
            return 40
    
    def _calculate_skills_match(self, resume: str, job_desc: str) -> float:
        """Calculate skills match score"""
        # Technical skills
        tech_skills = ['python', 'java', 'javascript', 'react', 'node', 'sql', 'aws', 'docker']
        
        job_tech_skills = [skill for skill in tech_skills if skill in job_desc.lower()]
        resume_tech_skills = [skill for skill in tech_skills if skill in resume.lower()]
        
        if not job_tech_skills:
            return 50  # Neutral score
        
        matched_skills = len(set(job_tech_skills) & set(resume_tech_skills))
        return (matched_skills / len(job_tech_skills)) * 100
    
    def _generate_keyword_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate keyword optimization recommendations"""
        recommendations = []
        
        # Missing keywords
        missing_count = len(results['missing_keywords'])
        if missing_count > 0:
            recommendations.append(f"Add {missing_count} missing keywords: {', '.join(results['missing_keywords'][:5])}")
        
        # Match score
        if results['match_score'] < 70:
            recommendations.append("Improve keyword match rate by including more job-specific terms")
        
        # Overall score
        if results['overall_score'] < 60:
            recommendations.append("Significant optimization needed - consider rewriting sections")
        elif results['overall_score'] < 80:
            recommendations.append("Good foundation - focus on adding missing keywords")
        else:
            recommendations.append("Excellent keyword matching - minor tweaks may help")
        
        # General recommendations
        recommendations.extend([
            "Use exact keywords from job description",
            "Include keywords in different sections (summary, experience, skills)",
            "Maintain natural language while including keywords"
        ])
        
        return recommendations


@register_tool(ToolConfig(
    name="Resume Keyword",
    slug="resume-keyword",
    category="resume",
    description="Optimize resume keywords for better job matching",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online Resume Keyword Optimizer - LamGen',
        'description': 'Optimize resume keywords for better job matching and ATS system performance.',
        'keywords': 'resume keywords, keyword optimization, ats resume, resume optimization'
    }
))
class ResumeKeywordTool(BaseTool):
    """Production-ready resume keyword optimizer"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'resume_text': COMMON_SCHEMAS['text_field'],
            'target_keywords': ValidationRule(
                type=ValidationType.ARRAY,
                required=False,
                max_length=30
            ),
            'job_title': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                max_length=50
            ),
            'optimization_level': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='moderate',
                allowed_values=['light', 'moderate', 'aggressive']
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Optimize resume keywords"""
        try:
            resume_text = input_data.get('resume_text', '')
            target_keywords = input_data.get('target_keywords', [])
            job_title = input_data.get('job_title', '').strip()
            optimization_level = input_data.get('optimization_level', 'moderate')
            
            if not resume_text:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Resume text is required"
                )
            
            # Optimize keywords
            optimization_results = self._optimize_resume_keywords(
                resume_text, target_keywords, job_title, optimization_level
            )
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'optimization_results': optimization_results,
                    'optimization_level': optimization_level
                },
                metadata={
                    'optimization_level': optimization_level,
                    'original_length': len(resume_text),
                    'optimized_length': len(optimization_results.get('optimized_resume', ''))
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "optimize_keywords")
    
    def _optimize_resume_keywords(self, resume: str, target_keywords: List[str], 
                                 job_title: str, level: str) -> Dict[str, Any]:
        """Optimize resume keywords"""
        results = {
            'current_keywords': self._extract_current_keywords(resume),
            'keyword_density': self._calculate_keyword_density(resume, target_keywords),
            'optimization_suggestions': [],
            'optimized_resume': '',
            'improvement_score': 0
        }
        
        # Generate optimization suggestions
        suggestions = self._generate_optimization_suggestions(
            resume, target_keywords, job_title, level
        )
        results['optimization_suggestions'] = suggestions
        
        # Generate optimized resume (simplified)
        if level in ['moderate', 'aggressive']:
            results['optimized_resume'] = self._generate_optimized_resume(
                resume, target_keywords, suggestions
            )
        
        # Calculate improvement score
        results['improvement_score'] = self._calculate_improvement_score(results)
        
        return results
    
    def _extract_current_keywords(self, resume: str) -> List[str]:
        """Extract current keywords from resume"""
        words = re.findall(r'\b\w+\b', resume.lower())
        
        # Filter for relevant keywords
        keywords = []
        for word in words:
            if len(word) > 3 and word not in keywords:
                keywords.append(word)
        
        return keywords[:50]
    
    def _calculate_keyword_density(self, resume: str, target_keywords: List[str]) -> Dict[str, float]:
        """Calculate keyword density"""
        density = {}
        total_words = len(re.findall(r'\b\w+\b', resume))
        
        for keyword in target_keywords:
            keyword_count = resume.lower().count(keyword.lower())
            density[keyword] = (keyword_count / total_words) * 100 if total_words > 0 else 0
        
        return density
    
    def _generate_optimization_suggestions(self, resume: str, target_keywords: List[str], 
                                         job_title: str, level: str) -> List[Dict[str, Any]]:
        """Generate optimization suggestions"""
        suggestions = []
        
        # Check for missing keywords
        current_keywords = self._extract_current_keywords(resume)
        missing_keywords = [kw for kw in target_keywords if kw.lower() not in [ck.lower() for ck in current_keywords]]
        
        if missing_keywords:
            suggestions.append({
                'type': 'missing_keywords',
                'keywords': missing_keywords,
                'suggestion': f"Add these keywords: {', '.join(missing_keywords[:5])}",
                'priority': 'high'
            })
        
        # Check keyword density
        density = self._calculate_keyword_density(resume, target_keywords)
        low_density_keywords = [kw for kw, d in density.items() if d < 1]
        
        if low_density_keywords:
            suggestions.append({
                'type': 'low_density',
                'keywords': low_density_keywords,
                'suggestion': f"Increase density for: {', '.join(low_density_keywords[:3])}",
                'priority': 'medium'
            })
        
        # Check section placement
        suggestions.append({
            'type': 'section_placement',
            'suggestion': 'Place keywords in summary, experience, and skills sections',
            'priority': 'medium'
        })
        
        # Level-specific suggestions
        if level == 'aggressive':
            suggestions.append({
                'type': 'aggressive_optimization',
                'suggestion': 'Rewrite sections to naturally include more keywords',
                'priority': 'high'
            })
        
        return suggestions
    
    def _generate_optimized_resume(self, resume: str, target_keywords: List[str], 
                                 suggestions: List[Dict[str, Any]]) -> str:
        """Generate optimized resume (simplified)"""
        optimized = resume
        
        # Add missing keywords to summary section
        missing_keywords = []
        for suggestion in suggestions:
            if suggestion['type'] == 'missing_keywords':
                missing_keywords.extend(suggestion['keywords'])
        
        if missing_keywords:
            # Find summary section and add keywords
            lines = resume.split('\n')
            for i, line in enumerate(lines):
                if 'summary' in line.lower() or 'objective' in line.lower():
                    # Add keywords to next line
                    if i + 1 < len(lines):
                        lines[i + 1] = f"{lines[i + 1]} with expertise in {', '.join(missing_keywords[:3])}"
                    break
            
            optimized = '\n'.join(lines)
        
        return optimized
    
    def _calculate_improvement_score(self, results: Dict[str, Any]) -> float:
        """Calculate improvement score"""
        score = 50  # Base score
        
        # Add points for suggestions
        for suggestion in results['optimization_suggestions']:
            if suggestion['priority'] == 'high':
                score += 15
            elif suggestion['priority'] == 'medium':
                score += 10
            else:
                score += 5
        
        return min(100, score)


@register_tool(ToolConfig(
    name="ATS Resume Checker",
    slug="ats-resume-checker",
    category="resume",
    description="Check resume compatibility with ATS systems",
    version="2.0.0",
    requires_auth=False,
    rate_limit_per_minute=30,
    cache_ttl_seconds=600,
    ai_enhanced=True,
    seo_metadata={
        'title': 'Free Online ATS Resume Checker - LamGen',
        'description': 'Check resume compatibility with ATS systems and get optimization recommendations.',
        'keywords': 'ats resume checker, ats compatibility, resume parsing, applicant tracking'
    }
))
class ATSResumeCheckerTool(BaseTool):
    """Production-ready ATS resume checker"""
    
    def get_schema(self) -> Dict[str, ValidationRule]:
        return {
            'resume_text': COMMON_SCHEMAS['text_field'],
            'check_type': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                default='comprehensive',
                allowed_values=['basic', 'comprehensive', 'formatting', 'content']
            ),
            'target_job': ValidationRule(
                type=ValidationType.STRING,
                required=False,
                max_length=50
            )
        }
    
    def process(self, input_data: Dict[str, Any]) -> ToolResult:
        """Check ATS compatibility"""
        try:
            resume_text = input_data.get('resume_text', '')
            check_type = input_data.get('check_type', 'comprehensive')
            target_job = input_data.get('target_job', '').strip()
            
            if not resume_text:
                return ToolResult(
                    status=ToolStatus.VALIDATION_ERROR,
                    error_message="Resume text is required"
                )
            
            # Perform ATS check
            ats_results = self._check_ats_compatibility(resume_text, check_type, target_job)
            
            # Generate recommendations
            recommendations = self._generate_ats_recommendations(ats_results)
            
            return ToolResult(
                status=ToolStatus.SUCCESS,
                data={
                    'ats_results': ats_results,
                    'recommendations': recommendations,
                    'check_type': check_type,
                    'target_job': target_job
                },
                metadata={
                    'check_type': check_type,
                    'ats_score': ats_results.get('overall_score', 0)
                }
            )
            
        except Exception as e:
            return self.handle_error(e, "check_ats")
    
    def _check_ats_compatibility(self, resume: str, check_type: str, target_job: str) -> Dict[str, Any]:
        """Check ATS compatibility"""
        results = {
            'formatting_score': 0,
            'content_score': 0,
            'structure_score': 0,
            'keyword_score': 0,
            'overall_score': 0,
            'issues': [],
            'recommendations': []
        }
        
        # Check formatting
        if check_type in ['comprehensive', 'formatting']:
            results['formatting_score'] = self._check_formatting(resume)
            results['issues'].extend(self._get_formatting_issues(resume))
        
        # Check content
        if check_type in ['comprehensive', 'content']:
            results['content_score'] = self._check_content(resume, target_job)
        
        # Check structure
        if check_type == 'comprehensive':
            results['structure_score'] = self._check_structure(resume)
        
        # Check keywords
        if target_job:
            results['keyword_score'] = self._check_keywords(resume, target_job)
        
        # Calculate overall score
        scores = [results['formatting_score'], results['content_score'], results['structure_score'], results['keyword_score']]
        scores = [score for score in scores if score > 0]
        results['overall_score'] = sum(scores) / len(scores) if scores else 0
        
        return results
    
    def _check_formatting(self, resume: str) -> float:
        """Check formatting compatibility"""
        score = 100
        
        # Check for problematic formatting
        if '|' in resume and resume.count('|') > 10:
            score -= 20  # Tables
        
        if any(char in resume for char in ['•', '○', '■', '★']):
            score -= 15  # Special characters
        
        if resume.count('\t') > 5:
            score -= 10  # Multiple columns
        
        if len(resume) > 50000:
            score -= 10  # Too long
        
        return max(0, score)
    
    def _get_formatting_issues(self, resume: str) -> List[str]:
        """Get formatting issues"""
        issues = []
        
        if '|' in resume and resume.count('|') > 10:
            issues.append("Contains tables (ATS may have trouble parsing)")
        
        if any(char in resume for char in ['•', '○', '■', '★']):
            issues.append("Contains special characters")
        
        if resume.count('\t') > 5:
            issues.append("Multiple column format detected")
        
        return issues
    
    def _check_content(self, resume: str, target_job: str) -> float:
        """Check content quality"""
        score = 50  # Base score
        
        # Check for contact info
        if re.search(r'\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', resume):
            score += 20
        
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume):
            score += 20
        
        # Check for sections
        sections = ['experience', 'education', 'skills']
        for section in sections:
            if section in resume.lower():
                score += 10
        
        return min(100, score)
    
    def _check_structure(self, resume: str) -> float:
        """Check resume structure"""
        score = 50
        
        # Check for clear sections
        section_headers = ['experience', 'education', 'skills', 'summary']
        found_sections = 0
        
        for header in section_headers:
            if header in resume.lower():
                found_sections += 1
        
        score += (found_sections / len(section_headers)) * 50
        
        return min(100, score)
    
    def _check_keywords(self, resume: str, target_job: str) -> float:
        """Check keyword relevance"""
        # Extract keywords from job title
        job_keywords = target_job.lower().split()
        
        # Count matches
        matches = 0
        for keyword in job_keywords:
            if keyword in resume.lower():
                matches += 1
        
        return (matches / len(job_keywords)) * 100 if job_keywords else 0
    
    def _generate_ats_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate ATS recommendations"""
        recommendations = []
        
        # Format recommendations
        if results['formatting_score'] < 80:
            recommendations.append("Remove special characters and complex formatting")
        
        # Content recommendations
        if results['content_score'] < 70:
            recommendations.append("Add contact information and clear sections")
        
        # Structure recommendations
        if results['structure_score'] < 70:
            recommendations.append("Use standard section headers (Experience, Education, Skills)")
        
        # Keyword recommendations
        if results['keyword_score'] < 60:
            recommendations.append("Include relevant keywords from job description")
        
        # General recommendations
        recommendations.extend([
            "Save as .docx or .pdf (not .doc)",
            "Use standard fonts (Arial, Calibri, Times New Roman)",
            "Keep formatting simple and consistent",
            "Test with different ATS systems if possible"
        ])
        
        return recommendations
