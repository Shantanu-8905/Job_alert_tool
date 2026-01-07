
import re
import logging
from typing import List, Dict, Any
from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class GitHubJobsScraper(BaseScraper):
    """Scraper for GitHub-related job sources."""
    
    SOURCE_NAME = "GitHub"
    
    # GitHub awesome lists with job postings
    AWESOME_LISTS = [
        "https://raw.githubusercontent.com/poteto/hiring-without-whiteboards/main/README.md",
    ]
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape GitHub sources for AI/ML jobs."""
        jobs = []
        
        # Try to scrape from awesome lists
        jobs.extend(self._scrape_awesome_lists(max_jobs))
        
        logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
        return jobs[:max_jobs]
    
    def _scrape_awesome_lists(self, max_jobs: int) -> List[Dict[str, Any]]:
        """Scrape jobs from GitHub awesome lists."""
        jobs = []
        
        for url in self.AWESOME_LISTS:
            if len(jobs) >= max_jobs:
                break
            
            logger.info(f"  {self.SOURCE_NAME}: Checking awesome list...")
            self._random_delay(1, 2)
            
            response = self._safe_request(url)
            
            if not response:
                continue
            
            try:
                content = response.text
                
                # Parse markdown to find company entries
                # Format typically: | [Company](url) | Location | ...
                lines = content.split('\n')
                
                for line in lines:
                    if len(jobs) >= max_jobs:
                        break
                    
                    # Skip non-table rows
                    if '|' not in line or line.startswith('#'):
                        continue
                    
                    # Parse table row
                    parts = [p.strip() for p in line.split('|')]
                    parts = [p for p in parts if p]  # Remove empty
                    
                    if len(parts) < 2:
                        continue
                    
                    # Extract company name and link
                    company_part = parts[0]
                    link_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', company_part)
                    
                    if link_match:
                        company = link_match.group(1)
                        link = link_match.group(2)
                    else:
                        continue
                    
                    # Location if available
                    location = parts[1] if len(parts) > 1 else 'Unknown'
                    
                    # Check if it's a tech company (basic heuristic)
                    # This list is about "hiring without whiteboards" - tech companies
                    job = self._standardize_job(
                        title="Software Engineer",  # Generic title
                        company=company,
                        location=location,
                        link=link,
                        description="Company from 'Hiring Without Whiteboards' list",
                    )
                    
                    # Only add if it might be ML-related company
                    ml_companies = ['ai', 'ml', 'data', 'learn', 'neural', 'deep']
                    if any(kw in company.lower() for kw in ml_companies):
                        job['title'] = "ML/AI Engineer"
                        if self._matches_preferences(job):
                            jobs.append(job)
                
            except Exception as e:
                logger.debug(f"  {self.SOURCE_NAME}: Parse error - {e}")
        
        return jobs
