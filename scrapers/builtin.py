
import re
import logging
from typing import List, Dict, Any
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class BuiltInScraper(BaseScraper):
    """Scraper for BuiltIn job listings."""
    
    SOURCE_NAME = "BuiltIn"
    BASE_URL = "https://builtin.com"
    
    # BuiltIn has city-specific sites
    CITY_SITES = [
        "https://builtin.com/jobs/remote",
        "https://builtin.com/jobs/machine-learning",
        "https://builtin.com/jobs/data-science",
    ]
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape BuiltIn for AI/ML jobs."""
        jobs = []
        seen = set()
        
        for url in self.CITY_SITES:
            if len(jobs) >= max_jobs:
                break
            
            logger.info(f"  {self.SOURCE_NAME}: Checking {url.split('/')[-1]}...")
            self._random_delay(2, 4)
            
            response = self._safe_request(url)
            
            if not response:
                continue
            
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find job cards
                job_cards = soup.find_all('div', class_=re.compile(r'job-card|job-listing'))
                
                if not job_cards:
                    # Try alternative selectors
                    job_cards = soup.find_all('article')
                
                for card in job_cards[:20]:
                    if len(jobs) >= max_jobs:
                        break
                    
                    job = self._parse_job_card(card)
                    
                    if not job:
                        continue
                    
                    # Check for duplicates
                    key = f"{job['title']}|{job['company']}".lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    
                    # Filter for AI/ML
                    if not self._is_ai_ml_job(job['title'], job.get('description', '')):
                        continue
                    
                    if self._matches_preferences(job):
                        jobs.append(job)
                
            except Exception as e:
                logger.debug(f"  {self.SOURCE_NAME}: Parse error - {e}")
        
        logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
        return jobs
    
    def _parse_job_card(self, card) -> Dict[str, Any]:
        """Parse a BuiltIn job card."""
        try:
            # Title
            title_elem = card.find('h2') or card.find('h3') or card.find('a', class_=re.compile(r'title'))
            if not title_elem:
                title_elem = card.find('a')
            title = title_elem.get_text(strip=True) if title_elem else ''
            
            if not title or len(title) < 3:
                return None
            
            # Company
            company_elem = card.find('span', class_=re.compile(r'company')) or \
                          card.find('div', class_=re.compile(r'company'))
            company = company_elem.get_text(strip=True) if company_elem else 'Unknown'
            
            # Location
            location_elem = card.find('span', class_=re.compile(r'location')) or \
                           card.find('div', class_=re.compile(r'location'))
            location = location_elem.get_text(strip=True) if location_elem else 'Remote'
            
            # Link
            link_elem = card.find('a', href=True)
            link = ''
            if link_elem:
                href = link_elem.get('href', '')
                if href.startswith('/'):
                    link = f"{self.BASE_URL}{href}"
                elif href.startswith('http'):
                    link = href
            
            # Description snippet
            desc_elem = card.find('p') or card.find('div', class_=re.compile(r'description'))
            description = desc_elem.get_text(strip=True) if desc_elem else ''
            
            return self._standardize_job(
                title=title,
                company=company,
                location=location,
                link=link,
                description=description,
            )
            
        except Exception as e:
            logger.debug(f"Parse error: {e}")
            return None
