# 🤖 AI/ML Job Alert System.

An advanced, locally-powered job alert system with **resume matching**, **AI scoring**, and **10+ job sources**.

## ✨ New Features 

- **🎯 Resume Matching**: Upload your resume and get personalized match scores
- **🧠 AI-Powered Scoring**: Local LLM analyzes job relevance (no paid APIs!)
- **📊 10+ Job Sources**: RemoteOK, Jobicy, Hacker News, Y Combinator, and more
- **💼 Skill Gap Analysis**: See which skills you need to learn
- **📈 Analytics**: Track job market trends and your search progress
- **🔧 Highly Configurable**: Customize everything via .env file

## 🚀 Quick Start

## 🎬 Demo Video

[▶ Watch the Demo](https://github.com/Shantanu-8905/Job_alert_tool/blob/main/Working_Video/Job_tool.mp4)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install Ollama (AI engine)
# Download from: https://ollama.com/download
ollama pull llama3

# 3. Configure
cp .env.example .env
# Edit .env with your Gmail + App Password

# 4. Add your resume (optional but recommended)
# Edit resume.txt with your skills and experience

# 5. Run!
python main.py
```

## 📁 Project Structure

```
job_alert_tool/
├── main.py                 # Main entry point
├── scrapers/               # 10+ job source scrapers
│   ├── remoteok.py
│   ├── jobicy.py
│   ├── hackernews.py
│   ├── ycombinator.py
│   └── ...
├── llm/                    # AI components
│   ├── job_scorer.py       # AI relevance scoring
│   └── resume_matcher.py   # Resume matching
├── storage/                # Local CSV/JSON storage
├── notifier/               # Email notifications
├── utils/                  # Config and helpers
├── data/                   # Your job data (created automatically)
├── resume.txt              # Your resume/skills
├── .env                    # Your configuration
└── test_system.py          # Test all components
```

## 🔧 Configuration

### Required Settings (.env)

```env
# Gmail (for notifications)
GMAIL_ADDRESS=your_email@gmail.com
GMAIL_APP_PASSWORD=abcdefghijklmnop

# Ollama model
OLLAMA_MODEL=llama3
```

### Optional Settings

```env
# Your resume file
RESUME_FILE=./resume.txt

# Your skills (auto-detected from resume if provided)
USER_SKILLS=python,pytorch,tensorflow,machine learning

# Score thresholds
MIN_RELEVANCE_SCORE=5
MIN_COMBINED_SCORE=5.0

# Job preferences
PREFERRED_LOCATIONS=Remote,USA,Europe
EXCLUDED_COMPANIES=
EXPERIENCE_LEVEL=any
JOB_TYPE=remote

# Job sources to use
ENABLED_SOURCES=remoteok,jobicy,arbeitnow,hackernews,ycombinator
```

## 📊 Job Sources

| Source | Type | Rate Limit | Notes |
|--------|------|------------|-------|
| RemoteOK | API | Low | Excellent for remote jobs |
| Jobicy | API | Low | Good AI/ML coverage |
| Arbeitnow | API | Low | European focus |
| Findwork | API | Low | Tech startups |
| Himalayas | API | Low | Remote-first |
| Y Combinator | Web | Medium | YC startups |
| Hacker News | API | Low | Monthly "Who's Hiring" |
| LinkedIn | Web | High | Limited access |
| Indeed | Web | High | May be blocked |
| BuiltIn | Web | Medium | US tech hubs |

## 🎯 How Scoring Works

### 1. Relevance Score (1-10)
AI analyzes if the job is truly AI/ML related:
- **9-10**: Core ML roles (ML Engineer, Data Scientist)
- **7-8**: Adjacent roles (Data Engineer with ML)
- **5-6**: Some ML exposure
- **1-4**: Not ML related

### 2. Match Score (1-10)
How well your skills match the job:
- Compares your resume skills with job requirements
- Identifies matching and missing skills
- Higher score = better fit

### 3. Combined Score
`Combined = (Relevance × 0.4) + (Match × 0.6)`

Only jobs above your threshold are saved and emailed.

## 📧 Email Notifications

You'll receive daily emails with:
- Top matched jobs ranked by score
- Match and relevance scores for each job
- Skills you have vs skills needed
- Links to apply

### Setting Up Gmail App Password

1. Enable 2-Factor Authentication: https://myaccount.google.com/security
2. Create App Password: https://myaccount.google.com/apppasswords
3. Copy the 16-character password to your .env file

## 🔄 Daily Automation

### Linux/Mac (cron)
```bash
# Run at 10 AM daily
0 10 * * * cd /path/to/job_alert_tool && python main.py
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task → Daily at 10:00 AM
3. Action: Start program → `python main.py`
4. Start in: `C:\path\to\job_alert_tool`

## 📈 Viewing Your Data

Jobs are saved locally in the `data/` folder:

- **jobs.csv** - Open in Excel/Google Sheets
- **jobs.json** - Full data with all fields
- **analytics.json** - Trends and statistics

## 🛠️ Command Line Options

```bash
# Normal run
python main.py

# Skip email
python main.py --no-email

# Test mode (limit jobs)
python main.py --test

# Only specific sources
python main.py --sources remoteok jobicy

# Analyze your resume
python main.py --analyze-resume
```

## 🐛 Troubleshooting

### "Ollama not found"
```bash
# Install from https://ollama.com/download
# Then pull a model:
ollama pull llama3
```

### "SMTP Authentication Failed"
- Use App Password, NOT regular Gmail password
- Enable 2FA first: https://myaccount.google.com/security
- Get App Password: https://myaccount.google.com/apppasswords

### "403 Forbidden from Indeed/LinkedIn"
- Normal - these sites block scrapers
- Other sources (RemoteOK, Jobicy) work fine
- Disable blocked sources in .env

### ".env parsing errors"
- No spaces around `=` signs
- Correct: `GMAIL_ADDRESS=test@gmail.com`
- Wrong: `GMAIL_ADDRESS = test@gmail.com`

## 📝 Creating Your Resume File

Create `resume.txt` with your skills and experience:

```
## Skills

Programming: Python, SQL, R
ML Frameworks: PyTorch, TensorFlow, scikit-learn
Cloud: AWS, GCP, Azure
Tools: Docker, Kubernetes, Git

## Experience

- 3 years as Data Scientist
- Built recommendation systems
- Experience with NLP and computer vision
```

The AI will automatically extract your skills and match them against job requirements.

## 🤝 Contributing

Feel free to add new job sources or improve the matching algorithm!
