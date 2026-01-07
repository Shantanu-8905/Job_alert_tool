
import logging
from typing import List, Dict, Any

from .base import BaseScraper

logger = logging.getLogger(__name__)


class ArbeitnowScraper(BaseScraper):
    """Scraper for Arbeitnow job listings."""
    
    SOURCE_NAME = "Arbeitnow"
    API_URL = "https://www.arbeitnow.com/api/job-board-api"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape Arbeitnow for AI/ML jobs."""
        jobs = []
        
        logger.info(f"  {self.SOURCE_NAME}: Fetching jobs...")
        self._random_delay(1, 2)
        
        response = self._safe_request(self.API_URL)
        
        if not response:
            return jobs
        
        try:
            data = response.json()
            job_list = data.get('data', [])
            
            for item in job_list:
                if len(jobs) >= max_jobs:
                    break
                
                title = item.get('title', '')
                description = item.get('description', '')
                
                # Filter for AI/ML jobs
                if not self._is_ai_ml_job(title, description):
                    continue
                
                # Parse date
                date_posted = item.get('created_at', '')[:10] if item.get('created_at') else None
                
                # Determine job type
                job_type = 'remote' if item.get('remote', False) else 'onsite'
                
                # Extract tags as skills
                skills = item.get('tags', [])
                
                job = self._standardize_job(
                    title=title,
                    company=item.get('company_name', 'Unknown'),
                    location=item.get('location', 'Remote') or 'Remote',
                    link=item.get('url', ''),
                    date_posted=date_posted,
                    description=description,
                    job_type=job_type,
                    skills=skills,
                )
                
                if self._matches_preferences(job):
                    jobs.append(job)
            
            logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
            
        except Exception as e:
            logger.error(f"  {self.SOURCE_NAME}: Parse error - {e}")
        
        return jobs
