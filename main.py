
import os
import sys
import logging
import argparse
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging with UTF-8 encoding
log_level = os.getenv('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('job_alert.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Import project modules
from scrapers import JobScraperManager
from storage.local_storage import LocalStorageClient
from llm.job_scorer import EnhancedJobScorer
from llm.resume_matcher import ResumeMatcher
from notifier.emailer import EmailNotifier
from utils.helpers import deduplicate_jobs, format_job_for_storage
from utils.config import Config


def print_banner():
    """Print application banner."""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║        🤖 AI/ML JOB ALERT SYSTEM - Enhanced Edition          ║
    ║                                                               ║
    ║   Features:                                                   ║
    ║   • 10+ Job Sources (RemoteOK, LinkedIn, HN, etc.)           ║
    ║   • AI-Powered Job Scoring                                    ║
    ║   • Resume Matching & Skill Analysis                          ║
    ║   • Smart Deduplication                                       ║
    ║   • Email Notifications                                       ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def scrape_all_sources(config: Config) -> List[Dict[str, Any]]:
    """
    Scrape jobs from all configured sources.
    
    Returns:
        List of job dictionaries with standardized fields.
    """
    scraper_manager = JobScraperManager(config)
    return scraper_manager.scrape_all()


def process_jobs_with_ai(
    jobs: List[Dict[str, Any]], 
    scorer: EnhancedJobScorer,
    resume_matcher: ResumeMatcher,
    config: Config
) -> List[Dict[str, Any]]:
    """
    Process jobs with AI scoring and resume matching.
    
    Args:
        jobs: List of job dictionaries
        scorer: EnhancedJobScorer instance
        resume_matcher: ResumeMatcher instance
        config: Configuration object
        
    Returns:
        List of scored and matched jobs
    """
    processed_jobs = []
    total = len(jobs)
    
    for i, job in enumerate(jobs):
        try:
            logger.info(f"Processing job {i+1}/{total}: {job.get('title', 'Unknown')[:50]}...")
            
            # Step 1: AI Relevance Score (is this an AI/ML job?)
            relevance_score = scorer.score_relevance(job)
            
            if relevance_score < config.min_relevance_score:
                logger.debug(f"  → Relevance: {relevance_score}/10 (SKIP - below threshold)")
                continue
            
            # Step 2: Resume Match Score (how well does it match your profile?)
            match_result = resume_matcher.match_job(job)
            match_score = match_result.get('match_score', 0)
            matching_skills = match_result.get('matching_skills', [])
            missing_skills = match_result.get('missing_skills', [])
            
            # Step 3: Calculate combined score
            combined_score = (relevance_score * 0.4) + (match_score * 0.6)
            
            # Add scores to job
            job['relevance_score'] = relevance_score
            job['match_score'] = match_score
            job['combined_score'] = round(combined_score, 1)
            job['matching_skills'] = matching_skills
            job['missing_skills'] = missing_skills
            job['ai_score'] = round(combined_score)  # For backward compatibility
            
            logger.info(f"  → Relevance: {relevance_score}/10, Match: {match_score}/10, Combined: {combined_score:.1f}/10")
            
            if combined_score >= config.min_combined_score:
                processed_jobs.append(job)
                logger.info(f"  → ACCEPTED ✓")
            else:
                logger.info(f"  → REJECTED (combined score below {config.min_combined_score})")
                
        except Exception as e:
            logger.error(f"Error processing job: {e}")
            # Fallback: use keyword-based scoring
            if any(kw in job.get('title', '').lower() for kw in ['machine learning', 'ai ', 'ml ', 'data scientist']):
                job['relevance_score'] = 7
                job['match_score'] = 5
                job['combined_score'] = 6
                job['ai_score'] = 6
                job['matching_skills'] = []
                job['missing_skills'] = []
                processed_jobs.append(job)
    
    # Sort by combined score
    processed_jobs.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
    
    logger.info(f"Jobs passing AI filter: {len(processed_jobs)}/{total}")
    return processed_jobs


def main(args=None):
    """
    Main execution flow.
    """
    parser = argparse.ArgumentParser(description='AI/ML Job Alert System')
    parser.add_argument('--no-email', action='store_true', help='Skip sending email')
    parser.add_argument('--test', action='store_true', help='Run in test mode (limit jobs)')
    parser.add_argument('--sources', nargs='+', help='Specific sources to scrape')
    parser.add_argument('--analyze-resume', action='store_true', help='Only analyze resume')
    args = parser.parse_args(args)
    
    print_banner()
    
    logger.info("=" * 60)
    logger.info("Starting AI/ML Job Alert System - Enhanced Edition")
    logger.info(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)
    
    # Load configuration
    config = Config()
    
    # Initialize components
    try:
        storage_client = LocalStorageClient(config.data_dir)
        scorer = EnhancedJobScorer(config)
        resume_matcher = ResumeMatcher(config)
        emailer = EmailNotifier() if not args.no_email else None
    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        sys.exit(1)
    
    # If only analyzing resume
    if args.analyze_resume:
        logger.info("\n[RESUME ANALYSIS MODE]")
        analysis = resume_matcher.analyze_resume()
        print("\n" + "=" * 60)
        print("RESUME ANALYSIS RESULTS")
        print("=" * 60)
        print(f"\nDetected Skills ({len(analysis.get('skills', []))}):")
        for skill in analysis.get('skills', [])[:20]:
            print(f"  • {skill}")
        print(f"\nExperience Level: {analysis.get('experience_level', 'Unknown')}")
        print(f"Primary Domain: {analysis.get('domain', 'Unknown')}")
        return
    
    # Step 1: Scrape all job sources
    logger.info("\n[STEP 1] Scraping job sources...")
    if args.sources:
        config.enabled_sources = args.sources
    
    scraped_jobs = scrape_all_sources(config)
    
    if args.test:
        scraped_jobs = scraped_jobs[:10]  # Limit for testing
    
    if not scraped_jobs:
        logger.warning("No jobs scraped. Exiting.")
        return
    
    logger.info(f"Total jobs scraped: {len(scraped_jobs)}")
    
    # Step 2: Deduplicate against existing data
    logger.info("\n[STEP 2] Deduplicating jobs...")
    try:
        existing_jobs = storage_client.get_existing_jobs()
        new_jobs = deduplicate_jobs(scraped_jobs, existing_jobs)
        logger.info(f"New unique jobs after deduplication: {len(new_jobs)}")
    except Exception as e:
        logger.error(f"Error during deduplication: {e}")
        new_jobs = scraped_jobs
    
    if not new_jobs:
        logger.info("No new jobs to process.")
        if emailer:
            try:
                emailer.send_notification([], 0, storage_client.get_stats())
            except:
                pass
        return
    
    # Step 3: AI Processing (Scoring + Resume Matching)
    logger.info("\n[STEP 3] AI Processing (Scoring + Resume Matching)...")
    qualified_jobs = process_jobs_with_ai(new_jobs, scorer, resume_matcher, config)
    
    if not qualified_jobs:
        logger.info("No jobs passed AI filter.")
        if emailer:
            try:
                emailer.send_notification([], 0, storage_client.get_stats())
            except:
                pass
        return
    
    # Step 4: Store in local storage
    logger.info("\n[STEP 4] Storing qualified jobs...")
    stored_count = 0
    for job in qualified_jobs:
        try:
            row_data = format_job_for_storage(job)
            if storage_client.append_job(row_data, job):
                stored_count += 1
                logger.info(f"Stored: {job.get('title')[:40]}... (Score: {job.get('combined_score', 0)})")
        except Exception as e:
            logger.error(f"Error storing job: {e}")
    
    logger.info(f"Successfully stored {stored_count} jobs")
    
    # Get stats
    stats = storage_client.get_stats()
    logger.info(f"Data saved to: {storage_client.csv_file}")
    
    # Step 5: Send email notification
    if emailer:
        logger.info("\n[STEP 5] Sending email notification...")
        try:
            emailer.send_notification(qualified_jobs, stored_count, stats)
            logger.info("Email notification sent successfully")
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("JOB ALERT RUN COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total scraped: {len(scraped_jobs)}")
    logger.info(f"New unique jobs: {len(new_jobs)}")
    logger.info(f"Passed AI filter: {len(qualified_jobs)}")
    logger.info(f"Stored: {stored_count}")
    logger.info(f"Total in database: {stats.get('total_jobs', 0)}")
    logger.info("=" * 60)
    
    # Print top jobs
    if qualified_jobs:
        print("\n🏆 TOP 5 MATCHED JOBS:")
        print("-" * 60)
        for i, job in enumerate(qualified_jobs[:5], 1):
            print(f"\n{i}. {job.get('title', 'Unknown')}")
            print(f"   Company: {job.get('company', 'Unknown')}")
            print(f"   Location: {job.get('location', 'Remote')}")
            print(f"   Combined Score: {job.get('combined_score', 0)}/10")
            print(f"   Matching Skills: {', '.join(job.get('matching_skills', [])[:5]) or 'N/A'}")
            if job.get('salary'):
                print(f"   Salary: {job.get('salary')}")


if __name__ == "__main__":
    main()
