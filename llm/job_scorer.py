#!/usr/bin/env python3
"""
Enhanced Job Scorer
===================
Uses local LLM (Ollama) for advanced job relevance scoring.
Analyzes job titles, descriptions, and requirements.
"""

import os
import re
import json
import logging
import subprocess
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class EnhancedJobScorer:
    """
    Enhanced job scorer using Ollama for AI-powered analysis.
    Provides detailed relevance scoring for AI/ML positions.
    """
    
    # High relevance keywords (score 9-10)
    HIGH_RELEVANCE = [
        'machine learning engineer', 'ml engineer', 'ai engineer',
        'deep learning engineer', 'data scientist', 'research scientist',
        'applied scientist', 'nlp engineer', 'computer vision engineer',
        'mlops engineer', 'ml platform', 'ai researcher', 'llm engineer',
    ]
    
    # Medium relevance keywords (score 7-8)
    MEDIUM_RELEVANCE = [
        'data engineer', 'ml ', ' ml', ' ai ', 'ai ', 'analytics engineer',
        'research engineer', 'quantitative', 'machine learning',
        'artificial intelligence', 'neural network', 'deep learning',
    ]
    
    # Low relevance keywords (score 5-6)
    LOW_RELEVANCE = [
        'data analyst', 'business intelligence', 'python developer',
        'backend engineer', 'software engineer', 'full stack',
    ]
    
    SCORING_PROMPT = """You are an AI/ML job relevance scorer. Analyze this job posting and score its relevance for AI/Machine Learning roles.

Job Details:
- Title: {title}
- Company: {company}
- Description: {description}

Scoring Criteria (1-10 scale):
- 9-10: Core AI/ML role (ML Engineer, Data Scientist, AI Researcher, Deep Learning, NLP, Computer Vision, MLOps, LLM Engineer)
- 7-8: AI/ML adjacent role (Data Engineer with ML, Backend with ML systems, Research roles)
- 5-6: Roles with some AI/ML exposure (Data Analyst, Full Stack with AI features)
- 1-4: Not AI/ML related (Generic software, unrelated positions)

Respond with ONLY a JSON object:
{{"score": <number 1-10>, "reason": "<brief 10-word explanation>", "is_ml_role": <true/false>}}
"""
    
    def __init__(self, config):
        """Initialize the enhanced job scorer."""
        self.config = config
        self.model = config.ollama_model
        self._verify_ollama()
        logger.info(f"Enhanced job scorer initialized with model: {self.model}")
    
    def _verify_ollama(self):
        """Verify Ollama is available."""
        try:
            result = subprocess.run(
                ['ollama', 'list'],
                capture_output=True,
                text=True,
                timeout=10,
                encoding='utf-8',
                errors='ignore'
            )
            if result.returncode != 0:
                logger.warning("Ollama may not be running. Using fallback scoring.")
        except Exception as e:
            logger.warning(f"Ollama not available: {e}. Using fallback scoring.")
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama with a prompt."""
        try:
            result = subprocess.run(
                ['ollama', 'run', self.model, prompt],
                capture_output=True,
                text=True,
                timeout=60,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
            
        except subprocess.TimeoutExpired:
            logger.warning("Ollama request timed out")
            return None
        except Exception as e:
            logger.debug(f"Ollama call failed: {e}")
            return None
    
    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """Parse LLM JSON response."""
        if not response:
            return None
        
        # Try direct JSON parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from response
        json_match = re.search(r'\{[^{}]*"score"\s*:\s*(\d+)[^{}]*\}', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except:
                pass
        
        # Try to extract just the score
        score_match = re.search(r'"score"\s*:\s*(\d+)', response)
        if score_match:
            return {'score': int(score_match.group(1)), 'reason': 'Extracted from response'}
        
        # Try to find any number 1-10
        numbers = re.findall(r'\b([1-9]|10)\b', response)
        if numbers:
            return {'score': int(numbers[0]), 'reason': 'Number extracted'}
        
        return None
    
    def _fallback_score(self, job: Dict[str, Any]) -> int:
        """Fallback scoring using keyword matching."""
        title = job.get('title', '').lower()
        description = job.get('description', '').lower()
        combined = f"{title} {description}"
        
        # Check high relevance
        for keyword in self.HIGH_RELEVANCE:
            if keyword in combined:
                return 9
        
        # Check medium relevance
        for keyword in self.MEDIUM_RELEVANCE:
            if keyword in combined:
                return 7
        
        # Check low relevance
        for keyword in self.LOW_RELEVANCE:
            if keyword in combined:
                return 5
        
        return 3
    
    def score_relevance(self, job: Dict[str, Any]) -> int:
        """
        Score a job's relevance for AI/ML positions.
        
        Args:
            job: Job dictionary with title, company, description.
            
        Returns:
            Integer score from 1-10.
        """
        title = job.get('title', 'Unknown')
        company = job.get('company', 'Unknown')
        description = job.get('description', '')[:500]  # Truncate
        
        # Build prompt
        prompt = self.SCORING_PROMPT.format(
            title=title,
            company=company,
            description=description or 'No description available'
        )
        
        # Try LLM scoring
        response = self._call_ollama(prompt)
        
        if response:
            result = self._parse_llm_response(response)
            if result and 'score' in result:
                score = max(1, min(10, int(result['score'])))
                logger.debug(f"LLM score for '{title}': {score}")
                return score
        
        # Fallback to keyword scoring
        score = self._fallback_score(job)
        logger.debug(f"Fallback score for '{title}': {score}")
        return score
    
    def analyze_job_details(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform detailed analysis of a job posting.
        
        Returns:
            Dictionary with detailed analysis.
        """
        analysis_prompt = f"""Analyze this AI/ML job posting in detail:

Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Description: {job.get('description', 'No description')[:800]}

Extract and respond with JSON only:
{{
    "required_skills": ["skill1", "skill2", ...],
    "experience_years": <number or null>,
    "experience_level": "junior|mid|senior|lead",
    "job_type": "remote|hybrid|onsite",
    "ml_areas": ["nlp", "cv", "mlops", ...],
    "key_responsibilities": ["resp1", "resp2", ...]
}}
"""
        
        response = self._call_ollama(analysis_prompt)
        
        if response:
            try:
                # Find JSON in response
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    return json.loads(json_match.group(0))
            except:
                pass
        
        # Return basic analysis
        return {
            'required_skills': job.get('skills', []),
            'experience_level': job.get('experience_level', 'unknown'),
            'job_type': job.get('job_type', 'unknown'),
        }


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    from utils.config import Config
    config = Config()
    
    scorer = EnhancedJobScorer(config)
    
    test_jobs = [
        {
            'title': 'Senior Machine Learning Engineer',
            'company': 'AI Startup',
            'description': 'Build and deploy ML models using PyTorch and TensorFlow.'
        },
        {
            'title': 'Marketing Manager',
            'company': 'AdCorp',
            'description': 'Manage marketing campaigns and brand strategy.'
        },
        {
            'title': 'Data Scientist - NLP',
            'company': 'TechCo',
            'description': 'Work on natural language processing and LLM applications.'
        },
    ]
    
    print("\nScoring test jobs:")
    for job in test_jobs:
        score = scorer.score_relevance(job)
        print(f"  {job['title']}: {score}/10")
