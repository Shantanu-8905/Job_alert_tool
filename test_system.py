#!/usr/bin/env python3
"""
Test Script for AI/ML Job Alert System v2.0
===========================================
Tests all components including resume matching.
"""

import os
import sys
import logging
import subprocess
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def print_header(text):
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")


def test_environment():
    """Test environment configuration."""
    print_header("1. Testing Environment Configuration")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    required = ['GMAIL_ADDRESS', 'GMAIL_APP_PASSWORD']
    optional = ['NOTIFICATION_EMAIL', 'OLLAMA_MODEL', 'RESUME_FILE', 'USER_SKILLS']
    
    all_good = True
    
    print("\nRequired variables:")
    for var in required:
        value = os.getenv(var)
        if value:
            display = '*' * 8 if 'PASSWORD' in var else value[:30]
            print(f"  ✓ {var}: {display}")
        else:
            print(f"  ✗ {var}: NOT SET")
            all_good = False
    
    print("\nOptional variables:")
    for var in optional:
        value = os.getenv(var)
        if value:
            print(f"  ✓ {var}: {value[:50]}...")
        else:
            print(f"  - {var}: (using default)")
    
    return all_good


def test_ollama():
    """Test Ollama installation."""
    print_header("2. Testing Ollama (Local LLM)")
    
    try:
        result = subprocess.run(
            ['ollama', '--version'],
            capture_output=True, text=True, timeout=10,
            encoding='utf-8', errors='ignore'
        )
        if result.returncode == 0:
            print(f"  ✓ Ollama installed: {result.stdout.strip()}")
        else:
            print(f"  ✗ Ollama error")
            return False
    except FileNotFoundError:
        print("  ✗ Ollama not found - install from ollama.com/download")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False
    
    # Check models
    try:
        result = subprocess.run(
            ['ollama', 'list'],
            capture_output=True, text=True, timeout=10,
            encoding='utf-8', errors='ignore'
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) > 1:
                print(f"  ✓ Available models:")
                for line in lines[1:]:
                    if line.strip():
                        print(f"      {line.split()[0]}")
            else:
                print("  ⚠ No models found. Run: ollama pull llama3")
                return False
    except Exception as e:
        print(f"  ✗ Error listing models: {e}")
        return False
    
    # Test inference
    model = os.getenv('OLLAMA_MODEL', 'llama3')
    print(f"\n  Testing model '{model}'...")
    
    try:
        result = subprocess.run(
            ['ollama', 'run', model, 'Say OK'],
            capture_output=True, text=True, timeout=60,
            encoding='utf-8', errors='ignore'
        )
        if result.returncode == 0 and result.stdout.strip():
            print(f"  ✓ Model responding")
            return True
    except Exception as e:
        print(f"  ✗ Model test failed: {e}")
    
    return False


def test_storage():
    """Test local storage."""
    print_header("3. Testing Local Storage")
    
    try:
        from storage.local_storage import LocalStorageClient
        
        client = LocalStorageClient('./data')
        
        print(f"  ✓ Storage initialized")
        print(f"  ✓ Data dir: {client.data_dir}")
        print(f"  ✓ CSV file: {client.csv_file}")
        print(f"  ✓ Current jobs: {client.get_job_count()}")
        
        return True
    except Exception as e:
        print(f"  ✗ Storage error: {e}")
        return False


def test_scrapers():
    """Test job scrapers."""
    print_header("4. Testing Job Scrapers")
    
    from utils.config import Config
    config = Config()
    config.enabled_sources = ['remoteok', 'jobicy']  # Test just 2
    
    from scrapers import JobScraperManager
    
    manager = JobScraperManager(config)
    
    print(f"\n  Testing {len(manager.scrapers)} scrapers...")
    
    total_jobs = 0
    results = {}
    
    for name in manager.scrapers:
        print(f"\n  {name}...")
        try:
            jobs = manager.scrape_source(name)
            if jobs:
                print(f"  ✓ {name}: Found {len(jobs)} jobs")
                if jobs:
                    print(f"      Sample: {jobs[0].get('title', 'N/A')[:40]}...")
                results[name] = True
                total_jobs += len(jobs)
            else:
                print(f"  ⚠ {name}: No jobs (may be rate limited)")
                results[name] = False
        except Exception as e:
            print(f"  ✗ {name}: Error - {e}")
            results[name] = False
    
    print(f"\n  Total jobs found: {total_jobs}")
    return any(results.values())


def test_resume_matcher():
    """Test resume matching."""
    print_header("5. Testing Resume Matcher")
    
    try:
        from utils.config import Config
        from llm.resume_matcher import ResumeMatcher
        
        config = Config()
        config.user_skills = ['python', 'pytorch', 'machine learning']
        
        matcher = ResumeMatcher(config)
        
        print(f"  ✓ Matcher initialized")
        print(f"  ✓ Skills detected: {len(matcher.user_skills)}")
        
        if matcher.user_skills:
            print(f"      Sample: {list(matcher.user_skills)[:5]}")
        
        # Test matching
        test_job = {
            'title': 'ML Engineer',
            'company': 'TestCo',
            'description': 'Looking for Python and PyTorch experience with machine learning.'
        }
        
        result = matcher.match_job(test_job)
        print(f"\n  Test match result:")
        print(f"      Score: {result.get('match_score', 0)}/10")
        print(f"      Matching: {result.get('matching_skills', [])}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Matcher error: {e}")
        return False


def test_job_scorer():
    """Test job scorer."""
    print_header("6. Testing Job Scorer")
    
    try:
        from utils.config import Config
        from llm.job_scorer import EnhancedJobScorer
        
        config = Config()
        scorer = EnhancedJobScorer(config)
        
        print(f"  ✓ Scorer initialized with model: {scorer.model}")
        
        test_jobs = [
            {'title': 'ML Engineer', 'company': 'AI Corp', 'description': 'Build ML models'},
            {'title': 'Marketing Manager', 'company': 'AdCo', 'description': 'Run campaigns'},
        ]
        
        print("\n  Scoring test jobs:")
        for job in test_jobs:
            score = scorer.score_relevance(job)
            status = "PASS" if score >= 5 else "REJECT"
            print(f"      {job['title']}: {score}/10 ({status})")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Scorer error: {e}")
        return False


def test_email():
    """Test email configuration."""
    print_header("7. Testing Email Configuration")
    
    from dotenv import load_dotenv
    load_dotenv()
    
    email = os.getenv('GMAIL_ADDRESS')
    password = os.getenv('GMAIL_APP_PASSWORD')
    
    if not email:
        print("  ✗ GMAIL_ADDRESS not set")
        return False
    
    if not password:
        print("  ✗ GMAIL_APP_PASSWORD not set")
        return False
    
    print(f"  ✓ Email: {email}")
    print(f"  ✓ Password: {'*' * 8}")
    
    # Test SMTP
    print("\n  Testing SMTP connection...")
    
    try:
        import smtplib
        import ssl
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context, timeout=10) as server:
            server.login(email, password)
            print("  ✓ SMTP login successful")
            return True
    except Exception as e:
        print(f"  ✗ SMTP error: {e}")
        return False


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print(" AI/ML JOB ALERT SYSTEM v2.0 - Component Tests")
    print("=" * 60)
    print(f" Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {
        'Environment': test_environment(),
        'Ollama': test_ollama(),
        'Storage': test_storage(),
        'Scrapers': test_scrapers(),
        'Resume Matcher': test_resume_matcher(),
        'Job Scorer': test_job_scorer(),
        'Email': test_email(),
    }
    
    print_header("TEST SUMMARY")
    
    passed = sum(1 for r in results.values() if r)
    failed = len(results) - passed
    
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {test}: {status}")
    
    print(f"\nResults: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("\n✓ All tests passed! Run: python main.py")
    else:
        print("\n⚠ Some tests failed. Check configuration.")
        print("\nQuick fixes:")
        print("  1. Copy .env.example to .env")
        print("  2. Add Gmail + App Password")
        print("  3. Install Ollama + run: ollama pull llama3")
        print("  4. Create resume.txt with your skills")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
