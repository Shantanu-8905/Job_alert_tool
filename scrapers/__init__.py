

import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from .remoteok import RemoteOKScraper
from .jobicy import JobicyScraper
from .arbeitnow import ArbeitnowScraper
from .findwork import FindworkScraper
from .himalayas import HimalayasScraper
from .ycombinator import YCombinatorScraper
from .hackernews import HackerNewsScraper
from .github import GitHubJobsScraper
from .stackoverflow import StackOverflowScraper
from .linkedin import LinkedInScraper
from .indeed import IndeedScraper
from .builtin import BuiltInScraper

logger = logging.getLogger(__name__)


class JobScraperManager:
    """
    Manages all job scrapers and coordinates scraping across multiple sources.
    """
    
    # Map of source names to scraper classes
    SCRAPER_CLASSES = {
        'remoteok': RemoteOKScraper,
        'jobicy': JobicyScraper,
        'arbeitnow': ArbeitnowScraper,
        'findwork': FindworkScraper,
        'himalayas': HimalayasScraper,
        'ycombinator': YCombinatorScraper,
        'hackernews': HackerNewsScraper,
        'github': GitHubJobsScraper,
        'stackoverflow': StackOverflowScraper,
        'linkedin': LinkedInScraper,
        'indeed': IndeedScraper,
        'builtin': BuiltInScraper,
    }
    
    def __init__(self, config):
        """
        Initialize scraper manager.
        
        Args:
            config: Configuration object with enabled_sources and other settings.
        """
        self.config = config
        self.scrapers = {}
        
        # Initialize enabled scrapers
        for source_name in config.enabled_sources:
            source_name = source_name.lower()
            if source_name in self.SCRAPER_CLASSES:
                try:
                    self.scrapers[source_name] = self.SCRAPER_CLASSES[source_name](config)
                    logger.debug(f"Initialized scraper: {source_name}")
                except Exception as e:
                    logger.warning(f"Failed to initialize {source_name} scraper: {e}")
        
        logger.info(f"Initialized {len(self.scrapers)} job scrapers")
    
    def scrape_source(self, source_name: str) -> List[Dict[str, Any]]:
        """
        Scrape jobs from a single source.
        
        Args:
            source_name: Name of the source to scrape.
            
        Returns:
            List of job dictionaries.
        """
        if source_name not in self.scrapers:
            logger.warning(f"Unknown source: {source_name}")
            return []
        
        try:
            scraper = self.scrapers[source_name]
            jobs = scraper.scrape(max_jobs=self.config.max_jobs_per_source)
            logger.info(f"  {source_name}: Found {len(jobs)} jobs")
            return jobs
        except Exception as e:
            logger.error(f"  {source_name}: Error - {e}")
            return []
    
    def scrape_all(self, parallel: bool = False) -> List[Dict[str, Any]]:
        """
        Scrape jobs from all enabled sources.
        
        Args:
            parallel: If True, scrape sources in parallel.
            
        Returns:
            Aggregated list of jobs from all sources.
        """
        all_jobs = []
        seen_keys = set()
        
        logger.info(f"Scraping {len(self.scrapers)} sources...")
        
        if parallel and len(self.scrapers) > 1:
            # Parallel scraping
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_source = {
                    executor.submit(self.scrape_source, source): source
                    for source in self.scrapers.keys()
                }
                
                for future in as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        jobs = future.result()
                        for job in jobs:
                            key = self._job_key(job)
                            if key not in seen_keys:
                                seen_keys.add(key)
                                all_jobs.append(job)
                    except Exception as e:
                        logger.error(f"  {source}: Failed - {e}")
        else:
            # Sequential scraping
            for source_name in self.scrapers.keys():
                jobs = self.scrape_source(source_name)
                for job in jobs:
                    key = self._job_key(job)
                    if key not in seen_keys:
                        seen_keys.add(key)
                        all_jobs.append(job)
        
        logger.info(f"Total unique jobs collected: {len(all_jobs)}")
        return all_jobs
    
    def _job_key(self, job: Dict[str, Any]) -> str:
        """Generate unique key for job deduplication."""
        title = job.get('title', '').lower().strip()
        company = job.get('company', '').lower().strip()
        # Normalize
        title = ''.join(c for c in title if c.isalnum() or c.isspace())
        company = ''.join(c for c in company if c.isalnum() or c.isspace())
        return f"{title}|{company}"
    
    def get_available_sources(self) -> List[str]:
        """Get list of all available scraper sources."""
        return list(self.SCRAPER_CLASSES.keys())
    
    def get_enabled_sources(self) -> List[str]:
        """Get list of currently enabled sources."""
        return list(self.scrapers.keys())


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    from utils.config import Config
    config = Config()
    config.enabled_sources = ['remoteok', 'jobicy']  # Test with just 2 sources
    
    manager = JobScraperManager(config)
    print(f"Available sources: {manager.get_available_sources()}")
    print(f"Enabled sources: {manager.get_enabled_sources()}")
    
    jobs = manager.scrape_all()
    print(f"\nTotal jobs: {len(jobs)}")
