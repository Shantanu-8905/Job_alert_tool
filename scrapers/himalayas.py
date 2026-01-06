#!/usr/bin/env python3
"""
Himalayas Job Scraper
=====================
Scrapes AI/ML jobs from Himalayas.app.
"""

import logging
from typing import List, Dict, Any

from .base import BaseScraper

logger = logging.getLogger(__name__)


class HimalayasScraper(BaseScraper):
    """Scraper for Himalayas.app job listings."""
    
    SOURCE_NAME = "Himalayas"
    API_URL = "https://himalayas.app/jobs/api"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape Himalayas for AI/ML jobs."""
        jobs = []
        
        logger.info(f"  {self.SOURCE_NAME}: Fetching jobs...")
        self._random_delay(1, 2)
        
        response = self._safe_request(self.API_URL)
        
        if not response:
            return jobs
        
        try:
            data = response.json()
            job_list = data if isinstance(data, list) else data.get('jobs', [])
            
            for item in job_list[:100]:  # Limit to first 100
                if len(jobs) >= max_jobs:
                    break
                
                title = item.get('title', '') or item.get('name', '')
                description = item.get('description', '')
                
                # Filter for AI/ML jobs
                if not self._is_ai_ml_job(title, description):
                    continue
                
                # Get company info
                company_info = item.get('company', {})
                if isinstance(company_info, dict):
                    company_name = company_info.get('name', 'Unknown')
                else:
                    company_name = item.get('companyName', 'Unknown')
                
                # Build link
                link = item.get('applicationLink', '') or item.get('url', '')
                if not link and item.get('slug'):
                    link = f"https://himalayas.app/jobs/{item.get('slug')}"
                
                # Extract skills/categories
                skills = item.get('categories', []) or item.get('skills', [])
                
                job = self._standardize_job(
                    title=title,
                    company=company_name,
                    location=item.get('location', 'Remote') or 'Remote',
                    link=link,
                    description=description,
                    salary=item.get('salary', ''),
                    job_type='remote',
                    skills=skills,
                )
                
                if self._matches_preferences(job):
                    jobs.append(job)
            
            logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
            
        except Exception as e:
            logger.error(f"  {self.SOURCE_NAME}: Parse error - {e}")
        
        return jobs
