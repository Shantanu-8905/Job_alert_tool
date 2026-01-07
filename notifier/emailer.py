
import os
import ssl
import logging
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class EmailNotifier:
    """
    Sends email notifications via Gmail SMTP.
    Enhanced with match scores and skill analysis.
    """
    
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 465
    
    def __init__(self):
        """Initialize email notifier."""
        self.sender_email = os.getenv('GMAIL_ADDRESS')
        self.sender_password = os.getenv('GMAIL_APP_PASSWORD')
        self.recipient_email = os.getenv('NOTIFICATION_EMAIL') or self.sender_email
        
        if not self.sender_email:
            raise ValueError("GMAIL_ADDRESS not set")
        if not self.sender_password:
            raise ValueError("GMAIL_APP_PASSWORD not set")
        
        logger.info(f"Email notifier initialized for: {self.recipient_email}")
    
    def _generate_html(self, jobs: List[Dict], stored_count: int, stats: Dict) -> str:
        """Generate enhanced HTML email content."""
        today = datetime.now().strftime('%B %d, %Y')
        sorted_jobs = sorted(jobs, key=lambda x: x.get('combined_score', 0), reverse=True)
        top_jobs = sorted_jobs[:10]
        
        # Calculate stats
        avg_match = sum(j.get('match_score', 0) for j in jobs) / len(jobs) if jobs else 0
        top_score = max((j.get('combined_score', 0) for j in jobs), default=0)
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .container {{
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #1a73e8;
            margin-bottom: 5px;
        }}
        .subtitle {{
            color: #666;
            font-size: 14px;
            margin-bottom: 25px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-box {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 28px;
            font-weight: bold;
        }}
        .stat-label {{
            font-size: 11px;
            opacity: 0.9;
            text-transform: uppercase;
        }}
        .job-card {{
            border: 1px solid #e0e0e0;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            transition: box-shadow 0.2s;
        }}
        .job-card:hover {{
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .job-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }}
        .job-title {{
            font-size: 17px;
            font-weight: 600;
            color: #1a73e8;
            text-decoration: none;
            margin: 0;
        }}
        .score-badges {{
            display: flex;
            gap: 8px;
        }}
        .badge {{
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
        }}
        .badge-match {{
            background: #10b981;
            color: white;
        }}
        .badge-relevance {{
            background: #3b82f6;
            color: white;
        }}
        .job-meta {{
            color: #666;
            font-size: 13px;
            margin-bottom: 10px;
        }}
        .job-meta span {{
            margin-right: 15px;
        }}
        .skills-section {{
            margin-top: 10px;
            font-size: 12px;
        }}
        .skills-match {{
            color: #10b981;
        }}
        .skills-missing {{
            color: #ef4444;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            text-align: center;
            color: #999;
            font-size: 12px;
        }}
        .no-jobs {{
            text-align: center;
            padding: 40px;
            color: #666;
        }}
        a {{ color: #1a73e8; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI/ML Job Alert</h1>
        <p class="subtitle">{today} • Enhanced with Resume Matching</p>
        
        <div class="stats-grid">
            <div class="stat-box">
                <div class="stat-number">{stored_count}</div>
                <div class="stat-label">New Jobs</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{len(jobs)}</div>
                <div class="stat-label">Qualified</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{avg_match:.1f}</div>
                <div class="stat-label">Avg Match</div>
            </div>
            <div class="stat-box">
                <div class="stat-number">{top_score}</div>
                <div class="stat-label">Top Score</div>
            </div>
        </div>
"""
        
        if top_jobs:
            html += '<h2 style="font-size: 18px; margin-bottom: 15px;">🏆 Top Matched Jobs</h2>'
            
            for job in top_jobs:
                match_score = job.get('match_score', 0)
                relevance_score = job.get('relevance_score', 0)
                combined = job.get('combined_score', 0)
                
                matching_skills = job.get('matching_skills', [])[:4]
                missing_skills = job.get('missing_skills', [])[:3]
                
                html += f"""
        <div class="job-card">
            <div class="job-header">
                <a href="{job.get('link', '#')}" class="job-title" target="_blank">
                    {job.get('title', 'Unknown')}
                </a>
                <div class="score-badges">
                    <span class="badge badge-match">Match: {match_score}/10</span>
                    <span class="badge badge-relevance">AI: {relevance_score}/10</span>
                </div>
            </div>
            <div class="job-meta">
                <span>🏢 {job.get('company', 'Unknown')}</span>
                <span>📍 {job.get('location', 'Remote')}</span>
                <span>📊 {job.get('source', 'Unknown')}</span>
                {f"<span>💰 {job.get('salary')}</span>" if job.get('salary') else ""}
            </div>
            <div class="skills-section">
                {f'<span class="skills-match">✓ {", ".join(matching_skills)}</span>' if matching_skills else ''}
                {f' &nbsp;|&nbsp; <span class="skills-missing">Need: {", ".join(missing_skills)}</span>' if missing_skills else ''}
            </div>
        </div>
"""
        else:
            html += """
        <div class="no-jobs">
            <p>No matching jobs found today.</p>
            <p>We'll keep looking! Try expanding your skills in your resume.</p>
        </div>
"""
        
        # Add source breakdown if available
        if stats.get('sources'):
            html += '<h3 style="font-size: 14px; margin-top: 25px;">📊 Jobs by Source</h3><p style="font-size: 13px; color: #666;">'
            for source, count in sorted(stats['sources'].items(), key=lambda x: x[1], reverse=True)[:5]:
                html += f'{source}: {count} • '
            html = html.rstrip(' • ') + '</p>'
        
        html += f"""
        <div class="footer">
            <p>AI/ML Job Alert System v2.0 - Enhanced with Resume Matching</p>
            <p>Total jobs in database: {stats.get('total_jobs', 0)}</p>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def _generate_text(self, jobs: List[Dict], stored_count: int, stats: Dict) -> str:
        """Generate plain text email content."""
        today = datetime.now().strftime('%B %d, %Y')
        sorted_jobs = sorted(jobs, key=lambda x: x.get('combined_score', 0), reverse=True)
        
        text = f"""
AI/ML Job Alert - {today}
{'=' * 50}

SUMMARY
-------
• New Jobs Found: {stored_count}
• Qualified Jobs: {len(jobs)}
• Total in Database: {stats.get('total_jobs', 0)}

"""
        
        if jobs:
            text += "TOP MATCHED JOBS\n"
            text += "-" * 50 + "\n\n"
            
            for i, job in enumerate(sorted_jobs[:10], 1):
                text += f"{i}. {job.get('title', 'Unknown')}\n"
                text += f"   Company: {job.get('company', 'Unknown')}\n"
                text += f"   Location: {job.get('location', 'Remote')}\n"
                text += f"   Match Score: {job.get('match_score', 0)}/10\n"
                text += f"   Relevance: {job.get('relevance_score', 0)}/10\n"
                text += f"   Link: {job.get('link', 'N/A')}\n\n"
        
        text += f"\n{'=' * 50}\n"
        text += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return text
    
    def send_notification(self, jobs: List[Dict], stored_count: int, stats: Dict = None) -> bool:
        """Send email notification."""
        stats = stats or {}
        today = datetime.now().strftime('%Y-%m-%d')
        
        subject = f"🤖 AI/ML Jobs: {len(jobs)} Matches Found ({today})"
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = self.sender_email
        message["To"] = self.recipient_email
        
        text_content = self._generate_text(jobs, stored_count, stats)
        html_content = self._generate_html(jobs, stored_count, stats)
        
        message.attach(MIMEText(text_content, "plain"))
        message.attach(MIMEText(html_content, "html"))
        
        try:
            context = ssl.create_default_context()
            
            with smtplib.SMTP_SSL(self.SMTP_SERVER, self.SMTP_PORT, context=context) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, self.recipient_email, message.as_string())
            
            logger.info(f"Email sent to {self.recipient_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("SMTP authentication failed. Check App Password.")
            return False
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False


# For testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    
    from dotenv import load_dotenv
    load_dotenv()
    
    try:
        notifier = EmailNotifier()
        
        test_jobs = [
            {
                'title': 'ML Engineer',
                'company': 'TestCo',
                'location': 'Remote',
                'link': 'https://example.com',
                'source': 'RemoteOK',
                'match_score': 8,
                'relevance_score': 9,
                'combined_score': 8.5,
                'matching_skills': ['python', 'pytorch'],
                'missing_skills': ['kubernetes'],
            }
        ]
        
        stats = {'total_jobs': 100, 'sources': {'RemoteOK': 50, 'Indeed': 30}}
        
        result = notifier.send_notification(test_jobs, 5, stats)
        print(f"Email sent: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
