
import logging
from typing import List, Dict, Any

from .base import BaseScraper

logger = logging.getLogger(__name__)


class StackOverflowScraper(BaseScraper):
    """Scraper for Stack Overflow-style tech job sources."""
    
    SOURCE_NAME = "TechJobs"
    
    # Alternative API - uses open tech job APIs
    API_URL = "https://api.adzuna.com/v1/api/jobs/us/search/1"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape tech job sources for AI/ML jobs."""
        jobs = []
        
        # Since Adzuna requires API key, we'll use a simpler approach
        # and provide jobs from internal data or skip
        
        logger.info(f"  {self.SOURCE_NAME}: Checking for jobs...")
        
        # For now, return empty - this can be extended with other APIs
        # that don't require API keys
        
        # Alternative: Use RSS feeds from tech sites
        rss_feeds = [
            "https://weworkremotely.com/categories/remote-programming-jobs.rss",
        ]
        
        for feed_url in rss_feeds:
            if len(jobs) >= max_jobs:
                break
            
            self._random_delay(1, 2)
            response = self._safe_request(feed_url)
            
            if not response:
                continue
            
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')
                
                for item in items[:30]:
                    if len(jobs) >= max_jobs:
                        break
                    
                    title = item.find('title')
                    link = item.find('link')
                    description = item.find('description')
                    
                    if not title or not link:
                        continue
                    
                    title_text = title.get_text()
                    desc_text = description.get_text() if description else ''
                    
                    # Filter for AI/ML jobs
                    if not self._is_ai_ml_job(title_text, desc_text):
                        continue
                    
                    # Extract company from title (format: "Title at Company")
                    company = 'Unknown'
                    if ' at ' in title_text:
                        parts = title_text.rsplit(' at ', 1)
                        title_text = parts[0]
                        company = parts[1]
                    
                    job = self._standardize_job(
                        title=title_text,
                        company=company,
                        location='Remote',
                        link=link.get_text(),
                        description=desc_text[:500],
                        job_type='remote',
                    )
                    
                    if self._matches_preferences(job):
                        jobs.append(job)
                
            except Exception as e:
                logger.debug(f"  {self.SOURCE_NAME}: Parse error - {e}")
        
        logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
        return jobs
