#!/usr/bin/env python3
"""
Hacker News Job Scraper
=======================
Scrapes AI/ML jobs from Hacker News "Who's Hiring" threads.
"""

import re
import logging
from datetime import datetime
from typing import List, Dict, Any

from .base import BaseScraper

logger = logging.getLogger(__name__)


class HackerNewsScraper(BaseScraper):
    """Scraper for Hacker News Who's Hiring threads."""
    
    SOURCE_NAME = "HackerNews"
    API_BASE = "https://hacker-news.firebaseio.com/v0"
    HN_USER = "whoishiring"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape Hacker News for AI/ML jobs."""
        jobs = []
        
        logger.info(f"  {self.SOURCE_NAME}: Finding latest Who's Hiring thread...")
        self._random_delay(1, 2)
        
        # Get whoishiring user's submissions to find the latest thread
        user_url = f"{self.API_BASE}/user/{self.HN_USER}.json"
        response = self._safe_request(user_url)
        
        if not response:
            return jobs
        
        try:
            user_data = response.json()
            submissions = user_data.get('submitted', [])[:10]  # Check recent submissions
            
            # Find the "Who is hiring?" thread
            hiring_thread_id = None
            current_month = datetime.now().strftime("%B %Y")
            
            for submission_id in submissions:
                self._random_delay(0.5, 1)
                item_url = f"{self.API_BASE}/item/{submission_id}.json"
                item_response = self._safe_request(item_url)
                
                if item_response:
                    item = item_response.json()
                    title = item.get('title', '')
                    if 'who is hiring' in title.lower():
                        hiring_thread_id = submission_id
                        logger.info(f"  {self.SOURCE_NAME}: Found thread: {title}")
                        break
            
            if not hiring_thread_id:
                logger.warning(f"  {self.SOURCE_NAME}: No hiring thread found")
                return jobs
            
            # Get the thread and its comments
            thread_url = f"{self.API_BASE}/item/{hiring_thread_id}.json"
            thread_response = self._safe_request(thread_url)
            
            if not thread_response:
                return jobs
            
            thread = thread_response.json()
            comment_ids = thread.get('kids', [])[:200]  # Limit to first 200 comments
            
            logger.info(f"  {self.SOURCE_NAME}: Processing {len(comment_ids)} job posts...")
            
            for comment_id in comment_ids:
                if len(jobs) >= max_jobs:
                    break
                
                self._random_delay(0.3, 0.6)
                comment_url = f"{self.API_BASE}/item/{comment_id}.json"
                comment_response = self._safe_request(comment_url)
                
                if not comment_response:
                    continue
                
                comment = comment_response.json()
                text = comment.get('text', '')
                
                if not text:
                    continue
                
                # Parse the job posting
                job = self._parse_hn_job(text, comment_id)
                
                if job and self._is_ai_ml_job(job.get('title', ''), text):
                    if self._matches_preferences(job):
                        jobs.append(job)
            
            logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
            
        except Exception as e:
            logger.error(f"  {self.SOURCE_NAME}: Error - {e}")
        
        return jobs
    
    def _parse_hn_job(self, text: str, comment_id: int) -> Dict[str, Any]:
        """
        Parse a Hacker News job comment.
        
        HN job posts typically follow the format:
        Company Name | Position | Location | Remote/Onsite | ...
        """
        # Clean HTML
        text = re.sub(r'<[^>]+>', ' ', text)
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        text = text.replace('&#x27;', "'").replace('&quot;', '"')
        
        # Try to extract info from the first line (usually has the format)
        lines = text.strip().split('\n')
        first_line = lines[0] if lines else text[:200]
        
        # Parse pipe-separated format
        parts = [p.strip() for p in first_line.split('|')]
        
        company = parts[0] if len(parts) > 0 else 'Unknown'
        title = parts[1] if len(parts) > 1 else 'Unknown Position'
        location = parts[2] if len(parts) > 2 else 'Unknown'
        
        # Clean up
        company = company[:100]  # Limit length
        title = title[:200]
        
        # If company looks like a URL, try to extract company name
        if 'http' in company.lower() or len(company) > 50:
            # Try to find a shorter identifier
            words = company.split()
            company = words[0] if words else 'Startup'
        
        # Determine job type
        job_type = 'unknown'
        text_lower = text.lower()
        if 'remote' in text_lower:
            job_type = 'remote'
        elif 'onsite' in text_lower or 'on-site' in text_lower:
            job_type = 'onsite'
        elif 'hybrid' in text_lower:
            job_type = 'hybrid'
        
        # Try to extract salary
        salary = ''
        salary_patterns = [
            r'\$[\d,]+k?\s*-\s*\$[\d,]+k?',
            r'\$[\d,]+k?\s*(?:to|–)\s*\$[\d,]+k?',
            r'[\d,]+k\s*-\s*[\d,]+k',
        ]
        for pattern in salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                salary = match.group(0)
                break
        
        return self._standardize_job(
            title=title,
            company=company,
            location=location,
            link=f"https://news.ycombinator.com/item?id={comment_id}",
            description=text[:1000],
            salary=salary,
            job_type=job_type,
        )
