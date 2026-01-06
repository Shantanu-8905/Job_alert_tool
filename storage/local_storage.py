#!/usr/bin/env python3
"""
Local Storage Client (CSV/JSON)
================================
Enhanced storage with support for skills, scores, and analytics.
"""

import os
import csv
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class LocalStorageClient:
    """
    Client for local file storage using CSV and JSON.
    Stores job data with enhanced fields for matching and analytics.
    """
    
    # CSV Headers (enhanced)
    HEADERS = [
        'Date', 'Job Title', 'Company', 'Location', 'Link', 'Source',
        'Relevance Score', 'Match Score', 'Combined Score', 'Status',
        'Matching Skills', 'Missing Skills', 'Salary', 'Job Type'
    ]
    
    def __init__(self, data_dir: str = None):
        """Initialize local storage client."""
        self.data_dir = Path(data_dir or os.getenv('DATA_DIR', './data'))
        self.csv_file = self.data_dir / 'jobs.csv'
        self.json_file = self.data_dir / 'jobs.json'
        self.index_file = self.data_dir / 'job_index.json'
        self.analytics_file = self.data_dir / 'analytics.json'
        
        # Create data directory
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize files
        self._ensure_files_exist()
        
        logger.info(f"Storage initialized at: {self.data_dir}")
    
    def _ensure_files_exist(self):
        """Create data files if they don't exist."""
        # CSV with headers
        if not self.csv_file.exists():
            with open(self.csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(self.HEADERS)
        
        # JSON file
        if not self.json_file.exists():
            with open(self.json_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'jobs': [],
                    'metadata': {
                        'created': datetime.now().isoformat(),
                        'total_jobs': 0,
                        'version': '2.0'
                    }
                }, f, indent=2)
        
        # Index file
        if not self.index_file.exists():
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump({'index': {}}, f)
        
        # Analytics file
        if not self.analytics_file.exists():
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'daily_stats': {},
                    'source_stats': {},
                    'skill_frequency': {}
                }, f, indent=2)
    
    def _normalize_key(self, title: str, company: str) -> str:
        """Create normalized key for deduplication."""
        title = ''.join(c.lower() for c in title if c.isalnum() or c.isspace())
        company = ''.join(c.lower() for c in company if c.isalnum() or c.isspace())
        return f"{' '.join(title.split())}|{' '.join(company.split())}"
    
    def _load_index(self) -> Dict[str, str]:
        """Load job index."""
        try:
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f).get('index', {})
        except:
            return {}
    
    def _save_index(self, index: Dict[str, str]):
        """Save job index."""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump({'index': index, 'updated': datetime.now().isoformat()}, f, indent=2)
    
    def get_existing_jobs(self) -> List[Tuple[str, str]]:
        """Get existing jobs for deduplication."""
        index = self._load_index()
        existing = []
        
        for key in index.keys():
            if '|' in key:
                parts = key.split('|', 1)
                if len(parts) == 2:
                    existing.append((parts[0], parts[1]))
        
        logger.info(f"Retrieved {len(existing)} existing jobs from index")
        return existing
    
    def job_exists(self, title: str, company: str) -> bool:
        """Check if a job already exists."""
        index = self._load_index()
        key = self._normalize_key(title, company)
        return key in index
    
    def append_job(self, row_data: List[Any], job_dict: Dict[str, Any] = None) -> bool:
        """
        Append a job to storage.
        
        Args:
            row_data: List of values for CSV row.
            job_dict: Full job dictionary for JSON storage.
        """
        try:
            title = str(row_data[1]) if len(row_data) > 1 else ''
            company = str(row_data[2]) if len(row_data) > 2 else ''
            
            # Check for duplicates
            if self.job_exists(title, company):
                return False
            
            # Pad row data if needed
            while len(row_data) < len(self.HEADERS):
                row_data.append('')
            
            # Append to CSV
            with open(self.csv_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(row_data[:len(self.HEADERS)])
            
            # Append to JSON
            if job_dict:
                with open(self.json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                job_dict['added_at'] = datetime.now().isoformat()
                data['jobs'].append(job_dict)
                data['metadata']['total_jobs'] = len(data['jobs'])
                data['metadata']['last_updated'] = datetime.now().isoformat()
                
                with open(self.json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Update index
            index = self._load_index()
            key = self._normalize_key(title, company)
            index[key] = datetime.now().isoformat()
            self._save_index(index)
            
            # Update analytics
            self._update_analytics(job_dict or {})
            
            return True
            
        except Exception as e:
            logger.error(f"Error appending job: {e}")
            return False
    
    def _update_analytics(self, job: Dict[str, Any]):
        """Update analytics data."""
        try:
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                analytics = json.load(f)
            
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Daily stats
            if today not in analytics['daily_stats']:
                analytics['daily_stats'][today] = {'count': 0, 'avg_score': 0}
            analytics['daily_stats'][today]['count'] += 1
            
            # Source stats
            source = job.get('source', 'Unknown')
            analytics['source_stats'][source] = analytics['source_stats'].get(source, 0) + 1
            
            # Skill frequency
            for skill in job.get('matching_skills', []):
                skill_lower = skill.lower()
                analytics['skill_frequency'][skill_lower] = analytics['skill_frequency'].get(skill_lower, 0) + 1
            
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(analytics, f, indent=2)
                
        except Exception as e:
            logger.debug(f"Analytics update failed: {e}")
    
    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Get all jobs from JSON storage."""
        try:
            with open(self.json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('jobs', [])
        except:
            return []
    
    def get_job_count(self) -> int:
        """Get total number of jobs."""
        return len(self.get_all_jobs())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        jobs = self.get_all_jobs()
        
        stats = {
            'total_jobs': len(jobs),
            'csv_file': str(self.csv_file),
            'json_file': str(self.json_file),
            'sources': {},
            'avg_relevance_score': 0,
            'avg_match_score': 0,
            'top_skills': [],
        }
        
        relevance_scores = []
        match_scores = []
        
        for job in jobs:
            # Source counts
            source = job.get('source', 'Unknown')
            stats['sources'][source] = stats['sources'].get(source, 0) + 1
            
            # Scores
            if job.get('relevance_score'):
                relevance_scores.append(job['relevance_score'])
            if job.get('match_score'):
                match_scores.append(job['match_score'])
        
        if relevance_scores:
            stats['avg_relevance_score'] = round(sum(relevance_scores) / len(relevance_scores), 1)
        if match_scores:
            stats['avg_match_score'] = round(sum(match_scores) / len(match_scores), 1)
        
        # Load skill frequency from analytics
        try:
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                analytics = json.load(f)
            skill_freq = analytics.get('skill_frequency', {})
            sorted_skills = sorted(skill_freq.items(), key=lambda x: x[1], reverse=True)
            stats['top_skills'] = [s[0] for s in sorted_skills[:10]]
        except:
            pass
        
        return stats
    
    def export_to_excel_csv(self, output_file: str = None) -> str:
        """Export to Excel-compatible CSV."""
        output_path = Path(output_file) if output_file else self.data_dir / 'jobs_excel.csv'
        
        jobs = self.get_all_jobs()
        
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(self.HEADERS)
            
            for job in jobs:
                row = [
                    job.get('date_posted', ''),
                    job.get('title', ''),
                    job.get('company', ''),
                    job.get('location', ''),
                    job.get('link', ''),
                    job.get('source', ''),
                    job.get('relevance_score', ''),
                    job.get('match_score', ''),
                    job.get('combined_score', ''),
                    job.get('status', 'New'),
                    ', '.join(job.get('matching_skills', [])[:5]),
                    ', '.join(job.get('missing_skills', [])[:5]),
                    job.get('salary', ''),
                    job.get('job_type', ''),
                ]
                writer.writerow(row)
        
        return str(output_path)


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    client = LocalStorageClient('./test_data')
    
    test_job = {
        'title': 'ML Engineer',
        'company': 'TestCo',
        'location': 'Remote',
        'link': 'https://example.com',
        'source': 'Test',
        'relevance_score': 9,
        'match_score': 7,
        'combined_score': 8,
        'matching_skills': ['python', 'pytorch'],
        'missing_skills': ['kubernetes'],
    }
    
    row = [
        '2024-01-15', 'ML Engineer', 'TestCo', 'Remote',
        'https://example.com', 'Test', 9, 7, 8, 'New',
        'python, pytorch', 'kubernetes', '', 'remote'
    ]
    
    result = client.append_job(row, test_job)
    print(f"Added job: {result}")
    print(f"Stats: {client.get_stats()}")
