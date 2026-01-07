
import logging
from typing import List, Dict, Any

from .base import BaseScraper

logger = logging.getLogger(__name__)


class YCombinatorScraper(BaseScraper):
    """Scraper for Y Combinator Work at a Startup."""
    
    SOURCE_NAME = "Y Combinator"
    API_URL = "https://www.workatastartup.com/api/companies/search"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape Y Combinator startups for AI/ML jobs."""
        jobs = []
        
        # Search queries
        queries = ['machine learning', 'AI', 'data science', 'deep learning']
        
        for query in queries:
            if len(jobs) >= max_jobs:
                break
            
            logger.info(f"  {self.SOURCE_NAME}: Searching '{query}'...")
            self._random_delay(2, 3)
            
            params = {'query': query, 'page': 1}
            response = self._safe_request(self.API_URL, params=params)
            
            if not response:
                continue
            
            try:
                data = response.json()
                companies = data.get('companies', [])
                
                for company in companies[:30]:
                    if len(jobs) >= max_jobs:
                        break
                    
                    company_name = company.get('name', 'YC Startup')
                    company_slug = company.get('slug', '')
                    company_jobs = company.get('jobs', [])
                    
                    for job_item in company_jobs:
                        if len(jobs) >= max_jobs:
                            break
                        
                        title = job_item.get('title', '')
                        
                        # Filter for AI/ML jobs
                        if not self._is_ai_ml_job(title):
                            continue
                        
                        # Build link
                        job_slug = job_item.get('slug', '')
                        if job_slug:
                            link = f"https://www.workatastartup.com/jobs/{job_slug}"
                        elif company_slug:
                            link = f"https://www.workatastartup.com/companies/{company_slug}"
                        else:
                            link = "https://www.workatastartup.com"
                        
                        # Determine job type
                        job_type = 'remote' if job_item.get('remote', False) else 'onsite'
                        
                        job = self._standardize_job(
                            title=title,
                            company=company_name,
                            location=job_item.get('location', 'San Francisco') or 'Remote',
                            link=link,
                            description=job_item.get('description', ''),
                            salary=job_item.get('salary_range', ''),
                            job_type=job_type,
                            experience_level=job_item.get('experience', ''),
                        )
                        
                        # Avoid duplicates
                        if not any(j['title'] == job['title'] and j['company'] == job['company'] for j in jobs):
                            if self._matches_preferences(job):
                                jobs.append(job)
                
            except Exception as e:
                logger.debug(f"  {self.SOURCE_NAME}: Parse error - {e}")
        
        logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
        return jobs
