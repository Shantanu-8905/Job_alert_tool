#!/usr/bin/env python3
"""
Indeed Job Scraper
==================
Scrapes AI/ML jobs from Indeed using multiple strategies.
"""

import re
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from urllib.parse import quote_plus
from bs4 import BeautifulSoup

from .base import BaseScraper

logger = logging.getLogger(__name__)


class IndeedScraper(BaseScraper):
    """Scraper for Indeed job listings."""
    
    SOURCE_NAME = "Indeed"
    BASE_URL = "https://www.indeed.com"
    
    def scrape(self, max_jobs: int = 50) -> List[Dict[str, Any]]:
        """Scrape Indeed for AI/ML jobs."""
        jobs = []
        
        # Try RSS feed first (less likely to be blocked)
        jobs.extend(self._scrape_rss(max_jobs))
        
        # If RSS didn't work well, try main site
        if len(jobs) < 5:
            jobs.extend(self._scrape_search(max_jobs - len(jobs)))
        
        # Deduplicate
        seen = set()
        unique_jobs = []
        for job in jobs:
            key = f"{job['title']}|{job['company']}".lower()
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)
        
        logger.info(f"  {self.SOURCE_NAME}: Found {len(unique_jobs)} AI/ML jobs")
        return unique_jobs[:max_jobs]
    
    def _scrape_rss(self, max_jobs: int) -> List[Dict[str, Any]]:
        """Try to scrape via Indeed RSS feed."""
        jobs = []
        
        queries = ['machine+learning+engineer', 'data+scientist', 'AI+engineer']
        
        for query in queries:
            if len(jobs) >= max_jobs:
                break
            
            logger.info(f"  {self.SOURCE_NAME}: Trying RSS for '{query}'...")
            self._random_delay(1, 2)
            
            rss_url = f"https://www.indeed.com/rss?q={query}&l=Remote"
            response = self._safe_request(rss_url)
            
            if not response:
                continue
            
            if 'xml' not in response.headers.get('content-type', ''):
                continue
            
            try:
                soup = BeautifulSoup(response.text, 'xml')
                items = soup.find_all('item')
                
                for item in items[:15]:
                    if len(jobs) >= max_jobs:
                        break
                    
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title_text = title_elem.get_text()
                    
                    # Filter for AI/ML
                    if not self._is_ai_ml_job(title_text):
                        continue
                    
                    # Parse "Title - Company" format
                    parts = title_text.rsplit(' - ', 1)
                    title = parts[0].strip()
                    company = parts[1].strip() if len(parts) > 1 else 'Unknown'
                    
                    job = self._standardize_job(
                        title=title,
                        company=company,
                        location='Remote',
                        link=link_elem.get_text().strip(),
                    )
                    
                    if self._matches_preferences(job):
                        jobs.append(job)
                
            except Exception as e:
                logger.debug(f"  {self.SOURCE_NAME}: RSS parse error - {e}")
        
        return jobs
    
    def _scrape_search(self, max_jobs: int) -> List[Dict[str, Any]]:
        """Scrape via search page (may be blocked)."""
        jobs = []
        
        queries = self.config.search_keywords[:3]  # Limit queries
        
        for query in queries:
            if len(jobs) >= max_jobs:
                break
            
            logger.info(f"  {self.SOURCE_NAME}: Searching '{query}'...")
            self._random_delay(3, 5)
            
            url = f"{self.BASE_URL}/jobs?q={quote_plus(query)}&l=Remote&sort=date"
            response = self._safe_request(url)
            
            if not response:
                continue
            
            if response.status_code == 403:
                logger.warning(f"  {self.SOURCE_NAME}: Blocked (403)")
                break
            
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find job cards
                job_cards = soup.find_all('div', class_=re.compile(r'job_seen_beacon|cardOutline'))
                
                if not job_cards:
                    job_cards = soup.find_all('td', class_='resultContent')
                
                for card in job_cards[:15]:
                    if len(jobs) >= max_jobs:
                        break
                    
                    job = self._parse_job_card(card)
                    if job and self._is_ai_ml_job(job['title']):
                        if self._matches_preferences(job):
                            jobs.append(job)
                
            except Exception as e:
                logger.debug(f"  {self.SOURCE_NAME}: Parse error - {e}")
        
        return jobs
    
    def _parse_job_card(self, card) -> Dict[str, Any]:
        """Parse an Indeed job card."""
        try:
            # Title
            title_elem = card.find('h2') or card.find('a', class_=re.compile(r'title'))
            title = title_elem.get_text(strip=True) if title_elem else 'Unknown'
            
            # Company
            company_elem = card.find('span', class_=re.compile(r'company'))
            company = company_elem.get_text(strip=True) if company_elem else 'Unknown'
            
            # Location
            location_elem = card.find('div', class_=re.compile(r'location'))
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
            
            return self._standardize_job(
                title=title,
                company=company,
                location=location,
                link=link,
            )
            
        except Exception as e:
            return None
