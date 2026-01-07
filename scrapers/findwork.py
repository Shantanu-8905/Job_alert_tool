
import logging
from typing import List, Dict, Any

from .base import BaseScraper

logger = logging.getLogger(__name__)


class FindworkScraper(BaseScraper):
    """Scraper for Findwork.dev job listings."""
    
    SOURCE_NAME = "Findwork"
    API_URL = "https://findwork.dev/api/jobs/"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape Findwork for AI/ML jobs."""
        jobs = []
        
        # Search queries
        queries = ['machine learning', 'data scientist', 'AI engineer', 'deep learning']
        
        for query in queries:
            if len(jobs) >= max_jobs:
                break
            
            logger.info(f"  {self.SOURCE_NAME}: Searching '{query}'...")
            self._random_delay(1, 2)
            
            url = f"{self.API_URL}?search={query.replace(' ', '+')}&sort_by=relevance"
            response = self._safe_request(url)
            
            if not response:
                continue
            
            try:
                data = response.json()
                job_list = data.get('results', [])
                
                for item in job_list:
                    if len(jobs) >= max_jobs:
                        break
                    
                    title = item.get('role', '')
                    description = item.get('text', '')
                    
                    # Filter for AI/ML jobs
                    if not self._is_ai_ml_job(title, description):
                        continue
                    
                    # Parse date
                    date_posted = item.get('date_posted', '')[:10] if item.get('date_posted') else None
                    
                    # Determine job type
                    job_type = 'remote' if item.get('remote', False) else 'onsite'
                    
                    # Extract keywords as skills
                    skills = item.get('keywords', [])
                    
                    job = self._standardize_job(
                        title=title,
                        company=item.get('company_name', 'Unknown'),
                        location=item.get('location', 'Remote') or 'Remote',
                        link=item.get('url', ''),
                        date_posted=date_posted,
                        description=description,
                        job_type=job_type,
                        skills=skills,
                        employment_type=item.get('employment_type', ''),
                    )
                    
                    # Avoid duplicates
                    if not any(j['title'] == job['title'] and j['company'] == job['company'] for j in jobs):
                        if self._matches_preferences(job):
                            jobs.append(job)
                
            except Exception as e:
                logger.error(f"  {self.SOURCE_NAME}: Parse error - {e}")
        
        logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
        return jobs
