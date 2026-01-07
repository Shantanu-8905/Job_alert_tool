
import logging
from typing import List, Dict, Any

from .base import BaseScraper

logger = logging.getLogger(__name__)


class JobicyScraper(BaseScraper):
    """Scraper for Jobicy job listings."""
    
    SOURCE_NAME = "Jobicy"
    API_URL = "https://jobicy.com/api/v2/remote-jobs"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape Jobicy for AI/ML jobs."""
        jobs = []
        
        # Search tags for AI/ML jobs
        tags = ['data-science', 'machine-learning', 'artificial-intelligence', 'python', 'data']
        
        for tag in tags:
            if len(jobs) >= max_jobs:
                break
            
            logger.info(f"  {self.SOURCE_NAME}: Searching tag '{tag}'...")
            self._random_delay(1, 2)
            
            url = f"{self.API_URL}?count=50&tag={tag}"
            response = self._safe_request(url)
            
            if not response:
                continue
            
            try:
                data = response.json()
                job_list = data.get('jobs', [])
                
                for item in job_list:
                    if len(jobs) >= max_jobs:
                        break
                    
                    title = item.get('jobTitle', '')
                    description = item.get('jobDescription', '')
                    
                    # Filter for AI/ML jobs
                    if not self._is_ai_ml_job(title, description):
                        continue
                    
                    # Parse date
                    date_posted = item.get('pubDate', '')[:10] if item.get('pubDate') else None
                    
                    # Determine job type
                    job_type = 'remote'
                    geo = item.get('jobGeo', '').lower()
                    if 'hybrid' in geo:
                        job_type = 'hybrid'
                    
                    job = self._standardize_job(
                        title=title,
                        company=item.get('companyName', 'Unknown'),
                        location=item.get('jobGeo', 'Remote') or 'Remote',
                        link=item.get('url', ''),
                        date_posted=date_posted,
                        description=description,
                        salary=item.get('annualSalaryMin', ''),
                        job_type=job_type,
                        experience_level=item.get('jobLevel', ''),
                    )
                    
                    # Avoid duplicates
                    if not any(j['title'] == job['title'] and j['company'] == job['company'] for j in jobs):
                        if self._matches_preferences(job):
                            jobs.append(job)
                
            except Exception as e:
                logger.error(f"  {self.SOURCE_NAME}: Parse error - {e}")
        
        logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
        return jobs
