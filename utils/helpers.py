#!/usr/bin/env python3
"""
Utility Helpers
===============
Common utility functions for the job alert system.
"""

import os
import time
import logging
import functools
from datetime import datetime
from typing import List, Dict, Any, Tuple, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0):
    """Decorator for retrying functions with exponential backoff."""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                        time.sleep(delay)
            
            raise last_exception
        return wrapper
    return decorator


def deduplicate_jobs(
    new_jobs: List[Dict[str, Any]], 
    existing_jobs: List[Tuple[str, str]]
) -> List[Dict[str, Any]]:
    """
    Remove duplicate jobs based on title and company.
    
    Args:
        new_jobs: List of newly scraped job dictionaries.
        existing_jobs: List of (title, company) tuples from storage.
        
    Returns:
        List of unique jobs not in existing_jobs.
    """
    existing_keys = set()
    for title, company in existing_jobs:
        key = _normalize_job_key(title, company)
        existing_keys.add(key)
    
    unique_jobs = []
    seen_in_batch = set()
    
    for job in new_jobs:
        key = _normalize_job_key(
            job.get('title', ''),
            job.get('company', '')
        )
        
        if key not in existing_keys and key not in seen_in_batch:
            seen_in_batch.add(key)
            unique_jobs.append(job)
    
    logger.info(f"Deduplication: {len(new_jobs)} -> {len(unique_jobs)} unique jobs")
    return unique_jobs


def _normalize_job_key(title: str, company: str) -> str:
    """Create a normalized key for job deduplication."""
    title = ''.join(c.lower() for c in title if c.isalnum() or c.isspace())
    company = ''.join(c.lower() for c in company if c.isalnum() or c.isspace())
    return f"{' '.join(title.split())}|{' '.join(company.split())}"


def format_job_for_storage(job: Dict[str, Any]) -> List[Any]:
    """
    Format a job dictionary as a row for storage.
    
    Returns:
        List of values for CSV row.
    """
    return [
        job.get('date_posted', datetime.now().strftime('%Y-%m-%d')),
        job.get('title', 'Unknown'),
        job.get('company', 'Unknown'),
        job.get('location', 'Remote'),
        job.get('link', ''),
        job.get('source', 'Unknown'),
        job.get('relevance_score', 0),
        job.get('match_score', 0),
        job.get('combined_score', 0),
        'New',
        ', '.join(job.get('matching_skills', [])[:5]),
        ', '.join(job.get('missing_skills', [])[:5]),
        job.get('salary', ''),
        job.get('job_type', ''),
    ]


def clean_text(text: str) -> str:
    """Clean text by removing extra whitespace."""
    if not text:
        return ""
    return ' '.join(text.split()).strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to a maximum length."""
    if not text or len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid URL."""
    return bool(url) and url.startswith(('http://', 'https://'))


def parse_salary(salary_str: str) -> Dict[str, Any]:
    """
    Parse salary string to extract min/max values.
    
    Returns:
        Dictionary with 'min', 'max', 'currency'.
    """
    import re
    
    result = {'min': None, 'max': None, 'currency': 'USD', 'raw': salary_str}
    
    if not salary_str:
        return result
    
    # Find currency
    if '£' in salary_str:
        result['currency'] = 'GBP'
    elif '€' in salary_str:
        result['currency'] = 'EUR'
    
    # Find numbers
    numbers = re.findall(r'[\d,]+(?:\.\d+)?', salary_str.replace(',', ''))
    numbers = [float(n) for n in numbers if n]
    
    # Handle 'k' suffix
    if 'k' in salary_str.lower():
        numbers = [n * 1000 if n < 1000 else n for n in numbers]
    
    if len(numbers) >= 2:
        result['min'] = min(numbers[:2])
        result['max'] = max(numbers[:2])
    elif len(numbers) == 1:
        result['min'] = result['max'] = numbers[0]
    
    return result


def get_relative_time(dt: datetime) -> str:
    """Get a human-readable relative time string."""
    now = datetime.now()
    diff = now - dt
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours > 1 else ''} ago"
    elif seconds < 172800:
        return "yesterday"
    else:
        days = int(seconds / 86400)
        return f"{days} days ago"


# For testing
if __name__ == "__main__":
    # Test deduplication
    new = [
        {'title': 'ML Engineer', 'company': 'TechCorp'},
        {'title': 'ML Engineer', 'company': 'TechCorp'},
        {'title': 'Data Scientist', 'company': 'StartupAI'},
    ]
    existing = [('data scientist', 'startupai')]
    
    result = deduplicate_jobs(new, existing)
    print(f"Deduplication: {len(new)} -> {len(result)}")
    
    # Test salary parsing
    salaries = ['$100k - $150k', '£80,000 - £100,000', '150000']
    for s in salaries:
        print(f"Parse '{s}': {parse_salary(s)}")
