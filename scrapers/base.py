
import time
import random
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for job scrapers.
    Provides common functionality for all scrapers.
    """
    
    # Source name - override in subclass
    SOURCE_NAME = "Base"
    
    # User agents for rotation
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    ]
    
    # AI/ML related keywords for filtering
    AI_ML_KEYWORDS = [
        'machine learning', 'ml engineer', 'ml ', ' ml',
        'artificial intelligence', 'ai engineer', 'ai ', ' ai',
        'deep learning', 'neural network', 'nlp', 'natural language',
        'computer vision', 'data scientist', 'data science',
        'tensorflow', 'pytorch', 'llm', 'large language model',
        'generative ai', 'gen ai', 'mlops', 'research scientist',
        'research engineer', 'applied scientist', 'ml platform',
    ]
    
    def __init__(self, config):
        """
        Initialize base scraper.
        
        Args:
            config: Configuration object.
        """
        self.config = config
        self.session = requests.Session()
        self._rotate_headers()
    
    def _rotate_headers(self):
        """Set random user agent and common headers."""
        self.session.headers.update({
            'User-Agent': random.choice(self.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _random_delay(self, min_sec: float = None, max_sec: float = None):
        """Add random delay between requests."""
        min_sec = min_sec or self.config.request_delay_min
        max_sec = max_sec or self.config.request_delay_max
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _is_ai_ml_job(self, title: str, description: str = "") -> bool:
        """
        Check if a job is AI/ML related based on title and description.
        
        Args:
            title: Job title.
            description: Job description (optional).
            
        Returns:
            True if AI/ML related.
        """
        combined = f"{title} {description}".lower()
        return any(kw in combined for kw in self.AI_ML_KEYWORDS)
    
    def _matches_preferences(self, job: Dict[str, Any]) -> bool:
        """
        Check if job matches user preferences.
        
        Args:
            job: Job dictionary.
            
        Returns:
            True if matches preferences.
        """
        # Check excluded companies
        company = job.get('company', '').lower()
        for excluded in self.config.excluded_companies:
            if excluded.lower() in company:
                return False
        
        # Check location preferences (if strict matching enabled)
        # For now, we're lenient - let the AI scorer handle location preferences
        
        return True
    
    def _standardize_job(
        self,
        title: str,
        company: str,
        location: str,
        link: str,
        date_posted: str = None,
        description: str = "",
        salary: str = "",
        job_type: str = "",
        experience_level: str = "",
        skills: List[str] = None,
        **extra
    ) -> Dict[str, Any]:
        """
        Create standardized job dictionary.
        
        Returns:
            Standardized job dictionary.
        """
        return {
            'title': title.strip() if title else 'Unknown',
            'company': company.strip() if company else 'Unknown',
            'location': location.strip() if location else 'Remote',
            'link': link.strip() if link else '',
            'date_posted': date_posted or datetime.now().strftime('%Y-%m-%d'),
            'source': self.SOURCE_NAME,
            'description': description[:1000] if description else '',  # Truncate
            'salary': salary,
            'job_type': job_type,  # remote, hybrid, onsite
            'experience_level': experience_level,  # junior, mid, senior
            'skills': skills or [],
            'scraped_at': datetime.now().isoformat(),
            **extra
        }
    
    def _safe_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        Make a safe HTTP request with error handling.
        
        Args:
            url: URL to request.
            method: HTTP method.
            **kwargs: Additional arguments for requests.
            
        Returns:
            Response object or None if failed.
        """
        try:
            kwargs.setdefault('timeout', 30)
            
            if method.upper() == 'GET':
                response = self.session.get(url, **kwargs)
            elif method.upper() == 'POST':
                response = self.session.post(url, **kwargs)
            else:
                response = self.session.request(method, url, **kwargs)
            
            response.raise_for_status()
            return response
            
        except requests.exceptions.HTTPError as e:
            logger.warning(f"{self.SOURCE_NAME}: HTTP error for {url}: {e}")
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"{self.SOURCE_NAME}: Connection error for {url}")
        except requests.exceptions.Timeout as e:
            logger.warning(f"{self.SOURCE_NAME}: Timeout for {url}")
        except Exception as e:
            logger.error(f"{self.SOURCE_NAME}: Request error for {url}: {e}")
        
        return None
    
    @abstractmethod
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """
        Scrape jobs from the source.
        
        Args:
            max_jobs: Maximum number of jobs to return.
            
        Returns:
            List of standardized job dictionaries.
        """
        pass
