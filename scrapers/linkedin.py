#!/usr/bin/env python3
"""
LinkedIn Jobs Scraper
=====================
Scrapes AI/ML jobs from LinkedIn via RSS/public feeds.
Note: LinkedIn heavily restricts scraping, so we use alternative methods.
"""

import re
import logging
from typing import List, Dict, Any
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class LinkedInScraper(BaseScraper):
    """Scraper for LinkedIn job listings via public feeds."""
    
    SOURCE_NAME = "LinkedIn"
    
    # LinkedIn job search URL (public, limited)
    SEARCH_URL = "https://www.linkedin.com/jobs/search/"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape LinkedIn for AI/ML jobs."""
        jobs = []
        
        # LinkedIn blocks most scraping, but we can try RSS-style approach
        # or use their limited public API
        
        queries = ['machine learning', 'AI engineer', 'data scientist']
        
        for query in queries:
            if len(jobs) >= max_jobs:
                break
            
            logger.info(f"  {self.SOURCE_NAME}: Searching '{query}'...")
            self._random_delay(3, 5)  # LinkedIn is strict
            
            # Try public job search page
            url = f"{self.SEARCH_URL}?keywords={quote_plus(query)}&f_TPR=r86400"  # Last 24 hours
            
            # Use more browser-like headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Cache-Control': 'max-age=0',
            }
            
            try:
                response = self.session.get(url, headers=headers, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Try to find job cards
                    job_cards = soup.find_all('div', class_=re.compile(r'job-search-card|base-card'))
                    
                    for card in job_cards[:20]:
                        if len(jobs) >= max_jobs:
                            break
                        
                        job = self._parse_job_card(card)
                        if job and self._is_ai_ml_job(job['title'], job.get('description', '')):
                            if self._matches_preferences(job):
                                jobs.append(job)
                else:
                    logger.debug(f"  {self.SOURCE_NAME}: Got status {response.status_code}")
                    
            except Exception as e:
                logger.debug(f"  {self.SOURCE_NAME}: Error - {e}")
        
        # If LinkedIn blocked us, that's expected
        if not jobs:
            logger.info(f"  {self.SOURCE_NAME}: Limited access (normal for LinkedIn)")
        else:
            logger.info(f"  {self.SOURCE_NAME}: Found {len(jobs)} AI/ML jobs")
        
        return jobs
    
    def _parse_job_card(self, card) -> Dict[str, Any]:
        """Parse a LinkedIn job card."""
        try:
            # Title
            title_elem = card.find('h3') or card.find('span', class_=re.compile(r'title'))
            title = title_elem.get_text(strip=True) if title_elem else 'Unknown'
            
            # Company
            company_elem = card.find('h4') or card.find('a', class_=re.compile(r'company'))
            company = company_elem.get_text(strip=True) if company_elem else 'Unknown'
            
            # Location
            location_elem = card.find('span', class_=re.compile(r'location'))
            location = location_elem.get_text(strip=True) if location_elem else 'Unknown'
            
            # Link
            link_elem = card.find('a', href=True)
            link = link_elem.get('href', '') if link_elem else ''
            if link and not link.startswith('http'):
                link = f"https://www.linkedin.com{link}"
            
            return self._standardize_job(
                title=title,
                company=company,
                location=location,
                link=link,
            )
            
        except Exception as e:
            logger.debug(f"  {self.SOURCE_NAME}: Parse error - {e}")
            return None
