"""
LLM Module
==========
Local LLM integration using Ollama for:
- Job relevance scoring
- Resume matching
- Skills extraction
"""

from .job_scorer import EnhancedJobScorer
from .resume_matcher import ResumeMatcher

__all__ = ['EnhancedJobScorer', 'ResumeMatcher']
