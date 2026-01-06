#!/usr/bin/env python3
"""
RemoteOK Job Scraper
====================
Scrapes AI/ML jobs from RemoteOK using their public JSON API.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any

from .base import BaseScraper

logger = logging.getLogger(__name__)


class RemoteOKScraper(BaseScraper):
    """Scraper for RemoteOK job listings."""
    
    SOURCE_NAME = "RemoteOK"
    API_URL = "https://remoteok.com/api"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape RemoteOK for AI/ML jobs."""
        jobs = []
        
        logger.info(f"  {self.SOURCE_NAME}: Fetching jobs...")
        self._random_delay(1, 2)
        
        response = self._safe_request(self.API_URL, headers={'Accept': 'application/json'})
        
        if not response:
            return jobs
        
        try:
            data = response.json()
            
            if not isinstance(data, list):
                logger.warning(f"  {self.SOURCE_NAME}: Unexpected response format")
                return jobs
            
            # First item is usually legal info
            job_list = data[1:] if len(data) > 1 else data
            
            for item in job_list:
                if len(jobs) >= max_jobs:
                    break
                
                if not isinstance(item, dict) or 'position' not in item:
                    continue
                
                title = item.get('position', '')
                description = item.get('description', '')
                
                # Filter for AI/ML jobs
                if not self._is_ai_ml_job(title, description):
                    continue
                
                # Parse date
                date_str = item.get('date', '')
                try:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    date_posted = dt.strftime('%Y-%m-%d')
                except:
                    date_posted = datetime.now().strftime('%Y-%m-%d')
                
                # Build link
                slug = item.get('slug', '')
                job_id = item.get('id', '')
                if slug:
                    link = f"https://remoteok.com/remote-jobs/{slug}"
                elif job_id:
                    link = f"https://remoteok.com/remote-jobs/{job_id}"
                else:
                    link = item.get('url', '')
                
                # Extract skills from tags
                skills = item.get('tags', [])
                
                job = self._standardize_job(
                    title=title,
                    company=item.get('company', 'Unknown'),
                    location=item.get('location', 'Remote') or 'Remote',
                    link=link,
                    date_posted=date_posted,
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
