#!/usr/bin/env python3
"""
Resume Matcher
==============
Matches job requirements against user's resume/skills profile.
Uses AI to extract skills and calculate match scores.
"""

import os
import re
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Set

logger = logging.getLogger(__name__)


class ResumeMatcher:
    """
    Matches jobs against user's resume and skills profile.
    Provides match scores and identifies skill gaps.
    """
    
    # Common skill patterns to extract
    SKILL_PATTERNS = {
        'programming': [
            'python', 'r', 'java', 'scala', 'julia', 'c\\+\\+', 'c#', 'javascript',
            'typescript', 'go', 'golang', 'rust', 'sql', 'bash', 'shell', 'matlab',
            'kotlin', 'swift', 'ruby', 'php', 'perl',
        ],
        'ml_frameworks': [
            'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'xgboost',
            'lightgbm', 'catboost', 'jax', 'mxnet', 'paddle', 'huggingface',
            'transformers', 'spacy', 'nltk', 'gensim', 'fastai',
        ],
        'ml_concepts': [
            'machine learning', 'deep learning', 'neural network', 'cnn', 'rnn',
            'lstm', 'transformer', 'attention', 'bert', 'gpt', 'llm',
            'reinforcement learning', 'supervised learning', 'unsupervised',
            'computer vision', 'nlp', 'natural language', 'speech recognition',
            'recommendation system', 'time series', 'anomaly detection',
        ],
        'data_tools': [
            'pandas', 'numpy', 'scipy', 'dask', 'ray', 'polars', 'spark',
            'pyspark', 'hadoop', 'hive', 'presto', 'airflow', 'dagster',
            'prefect', 'dbt', 'great expectations',
        ],
        'cloud': [
            'aws', 'amazon web services', 'azure', 'gcp', 'google cloud',
            'sagemaker', 'vertex ai', 'azure ml', 'databricks', 'snowflake',
            'bigquery', 'redshift', 's3', 'ec2', 'lambda',
        ],
        'mlops': [
            'mlflow', 'kubeflow', 'mlops', 'model deployment', 'model serving',
            'docker', 'kubernetes', 'k8s', 'ci/cd', 'github actions', 'jenkins',
            'terraform', 'ansible', 'model monitoring', 'feature store',
        ],
        'databases': [
            'postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'cassandra',
            'elasticsearch', 'neo4j', 'pinecone', 'weaviate', 'milvus',
            'chromadb', 'qdrant', 'faiss',
        ],
        'tools': [
            'git', 'linux', 'unix', 'jupyter', 'notebook', 'vscode',
            'wandb', 'weights & biases', 'tensorboard', 'grafana', 'prometheus',
            'api', 'rest', 'graphql', 'fastapi', 'flask', 'django',
        ],
    }
    
    MATCH_PROMPT = """You are a resume-job matcher. Compare the candidate's skills with the job requirements.

Candidate Profile:
{resume_summary}

Job Details:
- Title: {title}
- Company: {company}  
- Description: {description}

Analyze the match and respond with JSON only:
{{
    "match_score": <1-10>,
    "matching_skills": ["skill1", "skill2", ...],
    "missing_skills": ["skill1", "skill2", ...],
    "match_summary": "<brief explanation>"
}}
"""

    def __init__(self, config):
        """Initialize the resume matcher."""
        self.config = config
        self.model = config.ollama_model
        self.user_skills: Set[str] = set()
        self.resume_text: str = ""
        self.experience_level: str = "unknown"
        
        # Load resume and extract skills
        self._load_resume()
        self._load_user_skills()
        
        logger.info(f"Resume matcher initialized with {len(self.user_skills)} skills")
    
    def _load_resume(self):
        """Load resume from file if available."""
        resume_path = Path(self.config.resume_file)
        
        if resume_path.exists():
            try:
                with open(resume_path, 'r', encoding='utf-8') as f:
                    self.resume_text = f.read()
                logger.info(f"Loaded resume from {resume_path}")
                
                # Extract skills from resume
                extracted = self._extract_skills_from_text(self.resume_text)
                self.user_skills.update(extracted)
                
            except Exception as e:
                logger.warning(f"Could not load resume: {e}")
        else:
            logger.info("No resume file found. Using configured skills only.")
    
    def _load_user_skills(self):
        """Load user skills from configuration."""
        if self.config.user_skills:
            self.user_skills.update(skill.lower() for skill in self.config.user_skills)
    
    def _extract_skills_from_text(self, text: str) -> Set[str]:
        """Extract skills from text using pattern matching."""
        skills = set()
        text_lower = text.lower()
        
        for category, patterns in self.SKILL_PATTERNS.items():
            for pattern in patterns:
                # Use word boundaries for better matching
                if re.search(rf'\b{pattern}\b', text_lower):
                    # Normalize skill name
                    skill = pattern.replace('\\+\\+', '++').replace('\\', '')
                    skills.add(skill)
        
        return skills
    
    def _call_ollama(self, prompt: str) -> Optional[str]:
        """Call Ollama with a prompt."""
        try:
            result = subprocess.run(
                ['ollama', 'run', self.model, prompt],
                capture_output=True,
                text=True,
                timeout=90,
                encoding='utf-8',
                errors='ignore'
            )
            
            if result.returncode == 0:
                return result.stdout.strip()
            return None
            
        except Exception as e:
            logger.debug(f"Ollama call failed: {e}")
            return None
    
    def _keyword_match(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback keyword-based matching."""
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        job_skills = self._extract_skills_from_text(job_text)
        
        # Also check any skills listed in the job
        if job.get('skills'):
            for skill in job.get('skills', []):
                job_skills.add(skill.lower())
        
        # Find matches
        matching = self.user_skills.intersection(job_skills)
        missing = job_skills - self.user_skills
        
        # Calculate score based on match percentage
        if not job_skills:
            match_score = 5  # No skills to match
        else:
            match_percentage = len(matching) / len(job_skills)
            match_score = min(10, max(1, int(match_percentage * 10) + 2))
        
        return {
            'match_score': match_score,
            'matching_skills': list(matching)[:10],
            'missing_skills': list(missing)[:10],
            'match_summary': f"Matched {len(matching)}/{len(job_skills)} required skills",
        }
    
    def match_job(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """
        Match a job against user's profile.
        
        Args:
            job: Job dictionary.
            
        Returns:
            Dictionary with match_score, matching_skills, missing_skills.
        """
        title = job.get('title', 'Unknown')
        company = job.get('company', 'Unknown')
        description = job.get('description', '')[:600]
        
        # If we have resume text and LLM, use AI matching
        if self.resume_text and len(self.resume_text) > 100:
            resume_summary = self.resume_text[:1000]  # Truncate for prompt
            
            prompt = self.MATCH_PROMPT.format(
                resume_summary=resume_summary,
                title=title,
                company=company,
                description=description or 'No description available'
            )
            
            response = self._call_ollama(prompt)
            
            if response:
                try:
                    # Find JSON in response
                    json_match = re.search(r'\{[\s\S]*\}', response)
                    if json_match:
                        result = json.loads(json_match.group(0))
                        # Ensure score is in range
                        result['match_score'] = max(1, min(10, int(result.get('match_score', 5))))
                        return result
                except Exception as e:
                    logger.debug(f"Failed to parse LLM response: {e}")
        
        # Fallback to keyword matching
        return self._keyword_match(job)
    
    def analyze_resume(self) -> Dict[str, Any]:
        """
        Analyze the loaded resume and return a summary.
        
        Returns:
            Dictionary with skills, experience level, and domain.
        """
        if not self.resume_text:
            return {
                'skills': list(self.user_skills),
                'experience_level': 'unknown',
                'domain': 'unknown',
                'summary': 'No resume loaded. Add skills via USER_SKILLS in .env or create resume.txt'
            }
        
        # Use LLM for analysis if available
        analysis_prompt = f"""Analyze this resume/profile and extract key information:

{self.resume_text[:2000]}

Respond with JSON only:
{{
    "skills": ["skill1", "skill2", ...],
    "experience_years": <number>,
    "experience_level": "junior|mid|senior|lead",
    "domain": "ML/AI|Data Science|Backend|Full Stack|etc",
    "summary": "<2 sentence summary>"
}}
"""
        
        response = self._call_ollama(analysis_prompt)
        
        if response:
            try:
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    result = json.loads(json_match.group(0))
                    # Merge with extracted skills
                    all_skills = set(result.get('skills', []))
                    all_skills.update(self.user_skills)
                    result['skills'] = list(all_skills)
                    return result
            except Exception as e:
                logger.debug(f"Failed to parse analysis: {e}")
        
        # Return keyword-based analysis
        return {
            'skills': list(self.user_skills),
            'experience_level': self.experience_level,
            'domain': 'AI/ML' if any('ml' in s or 'ai' in s or 'machine' in s for s in self.user_skills) else 'Tech',
            'summary': f'Profile with {len(self.user_skills)} identified skills.'
        }
    
    def get_skill_gaps(self, jobs: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Analyze multiple jobs to find common skill gaps.
        
        Args:
            jobs: List of job dictionaries.
            
        Returns:
            Dictionary of missing skills with frequency counts.
        """
        skill_gaps = {}
        
        for job in jobs:
            result = self.match_job(job)
            for skill in result.get('missing_skills', []):
                skill_lower = skill.lower()
                skill_gaps[skill_lower] = skill_gaps.get(skill_lower, 0) + 1
        
        # Sort by frequency
        sorted_gaps = dict(sorted(skill_gaps.items(), key=lambda x: x[1], reverse=True))
        return sorted_gaps
    
    def add_skill(self, skill: str):
        """Add a skill to user's profile."""
        self.user_skills.add(skill.lower())
    
    def remove_skill(self, skill: str):
        """Remove a skill from user's profile."""
        self.user_skills.discard(skill.lower())


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    from utils.config import Config
    config = Config()
    config.user_skills = ['python', 'pytorch', 'tensorflow', 'machine learning', 'nlp']
    
    matcher = ResumeMatcher(config)
    
    print(f"\nUser skills: {matcher.user_skills}")
    
    test_job = {
        'title': 'Senior ML Engineer',
        'company': 'AI Startup',
        'description': 'Looking for ML engineer with Python, PyTorch, transformers experience. Must know AWS and MLOps.'
    }
    
    result = matcher.match_job(test_job)
    print(f"\nMatch result:")
    print(f"  Score: {result['match_score']}/10")
    print(f"  Matching: {result['matching_skills']}")
    print(f"  Missing: {result['missing_skills']}")
