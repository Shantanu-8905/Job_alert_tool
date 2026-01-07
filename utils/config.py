
import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """
    Application configuration with defaults.
    Values can be overridden via environment variables or config file.
    """
    
    # Data storage
    data_dir: str = field(default_factory=lambda: os.getenv('DATA_DIR', './data'))
    
    # Email settings
    gmail_address: str = field(default_factory=lambda: os.getenv('GMAIL_ADDRESS', ''))
    gmail_app_password: str = field(default_factory=lambda: os.getenv('GMAIL_APP_PASSWORD', ''))
    notification_email: str = field(default_factory=lambda: os.getenv('NOTIFICATION_EMAIL', ''))
    
    # Ollama settings
    ollama_model: str = field(default_factory=lambda: os.getenv('OLLAMA_MODEL', 'llama3'))
    
    # Scoring thresholds
    min_relevance_score: int = field(default_factory=lambda: int(os.getenv('MIN_RELEVANCE_SCORE', '5')))
    min_combined_score: float = field(default_factory=lambda: float(os.getenv('MIN_COMBINED_SCORE', '5.0')))
    
    # Resume file
    resume_file: str = field(default_factory=lambda: os.getenv('RESUME_FILE', './resume.txt'))
    
    # Job preferences
    preferred_locations: List[str] = field(default_factory=lambda: _parse_list_env('PREFERRED_LOCATIONS', ['Remote', 'USA', 'Europe']))
    excluded_companies: List[str] = field(default_factory=lambda: _parse_list_env('EXCLUDED_COMPANIES', []))
    min_salary: int = field(default_factory=lambda: int(os.getenv('MIN_SALARY', '0')))
    experience_level: str = field(default_factory=lambda: os.getenv('EXPERIENCE_LEVEL', 'any'))  # junior, mid, senior, any
    job_type: str = field(default_factory=lambda: os.getenv('JOB_TYPE', 'any'))  # remote, hybrid, onsite, any
    
    # Enabled job sources
    enabled_sources: List[str] = field(default_factory=lambda: _parse_list_env('ENABLED_SOURCES', [
        'remoteok',
        'jobicy',
        'arbeitnow',
        'findwork',
        'himalayas',
        'ycombinator',
        'hackernews',
        'github',
        'stackoverflow',
        'linkedin',
        'indeed',
        'builtin',
    ]))
    
    # Scraping settings
    max_jobs_per_source: int = field(default_factory=lambda: int(os.getenv('MAX_JOBS_PER_SOURCE', '50')))
    request_delay_min: float = field(default_factory=lambda: float(os.getenv('REQUEST_DELAY_MIN', '1.0')))
    request_delay_max: float = field(default_factory=lambda: float(os.getenv('REQUEST_DELAY_MAX', '3.0')))
    
    # Search keywords
    search_keywords: List[str] = field(default_factory=lambda: _parse_list_env('SEARCH_KEYWORDS', [
        'machine learning',
        'AI engineer',
        'data scientist',
        'deep learning',
        'MLOps',
        'NLP',
        'computer vision',
        'LLM',
    ]))
    
    # Skills for matching (will be auto-detected from resume if provided)
    user_skills: List[str] = field(default_factory=lambda: _parse_list_env('USER_SKILLS', []))
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Set notification email to gmail if not specified
        if not self.notification_email:
            self.notification_email = self.gmail_address
        
        # Ensure data directory exists
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        
        # Load config file if exists
        config_file = Path('./config.json')
        if config_file.exists():
            self._load_from_file(config_file)
    
    def _load_from_file(self, config_file: Path):
        """Load additional config from JSON file."""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
            
            # Override defaults with file values
            for key, value in file_config.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            
            logger.info(f"Loaded configuration from {config_file}")
        except Exception as e:
            logger.warning(f"Could not load config file: {e}")
    
    def save_to_file(self, config_file: str = './config.json'):
        """Save current config to JSON file."""
        config_dict = {
            'preferred_locations': self.preferred_locations,
            'excluded_companies': self.excluded_companies,
            'min_salary': self.min_salary,
            'experience_level': self.experience_level,
            'job_type': self.job_type,
            'enabled_sources': self.enabled_sources,
            'search_keywords': self.search_keywords,
            'user_skills': self.user_skills,
            'min_relevance_score': self.min_relevance_score,
            'min_combined_score': self.min_combined_score,
        }
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2)
        
        logger.info(f"Saved configuration to {config_file}")
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []
        
        if not self.gmail_address:
            issues.append("GMAIL_ADDRESS not set")
        
        if not self.gmail_app_password:
            issues.append("GMAIL_APP_PASSWORD not set")
        
        if not self.enabled_sources:
            issues.append("No job sources enabled")
        
        return issues


def _parse_list_env(key: str, default: List[str]) -> List[str]:
    """Parse comma-separated environment variable into list."""
    value = os.getenv(key, '')
    if value:
        return [item.strip() for item in value.split(',') if item.strip()]
    return default


# Skill categories for matching
SKILL_CATEGORIES = {
    'programming_languages': [
        'python', 'r', 'java', 'scala', 'julia', 'c++', 'c', 'javascript',
        'typescript', 'go', 'rust', 'sql', 'bash', 'shell', 'matlab',
    ],
    'ml_frameworks': [
        'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'sklearn', 'xgboost',
        'lightgbm', 'catboost', 'jax', 'mxnet', 'caffe', 'theano', 'paddle',
    ],
    'deep_learning': [
        'neural networks', 'cnn', 'rnn', 'lstm', 'transformer', 'bert', 'gpt',
        'attention mechanism', 'gan', 'vae', 'autoencoder', 'diffusion',
    ],
    'ml_concepts': [
        'machine learning', 'deep learning', 'supervised learning', 'unsupervised learning',
        'reinforcement learning', 'transfer learning', 'federated learning',
        'feature engineering', 'model training', 'hyperparameter tuning',
    ],
    'nlp': [
        'nlp', 'natural language processing', 'text classification', 'ner',
        'named entity recognition', 'sentiment analysis', 'language model',
        'word embeddings', 'word2vec', 'transformers', 'huggingface', 'spacy', 'nltk',
    ],
    'computer_vision': [
        'computer vision', 'image classification', 'object detection', 'yolo',
        'image segmentation', 'opencv', 'facial recognition', 'ocr',
    ],
    'llm': [
        'llm', 'large language model', 'gpt', 'chatgpt', 'claude', 'llama',
        'prompt engineering', 'rag', 'retrieval augmented generation',
        'langchain', 'vector database', 'embeddings', 'fine-tuning',
    ],
    'mlops': [
        'mlops', 'ml pipeline', 'model deployment', 'model serving', 'mlflow',
        'kubeflow', 'airflow', 'dagster', 'prefect', 'dvc', 'model monitoring',
    ],
    'cloud_platforms': [
        'aws', 'azure', 'gcp', 'google cloud', 'sagemaker', 'vertex ai',
        'azure ml', 'databricks', 'snowflake', 'bigquery',
    ],
    'data_tools': [
        'spark', 'pyspark', 'hadoop', 'kafka', 'airflow', 'dbt',
        'pandas', 'numpy', 'dask', 'ray', 'polars',
    ],
    'databases': [
        'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'pinecone', 'weaviate', 'milvus', 'chromadb', 'neo4j',
    ],
    'tools': [
        'docker', 'kubernetes', 'git', 'linux', 'jupyter', 'vscode',
        'wandb', 'tensorboard', 'grafana', 'prometheus',
    ],
}

# Flatten all skills for quick lookup
ALL_SKILLS = set()
for category_skills in SKILL_CATEGORIES.values():
    ALL_SKILLS.update(skill.lower() for skill in category_skills)


# For testing
if __name__ == "__main__":
    config = Config()
    print("Current Configuration:")
    print(f"  Data Dir: {config.data_dir}")
    print(f"  Gmail: {config.gmail_address}")
    print(f"  Ollama Model: {config.ollama_model}")
    print(f"  Enabled Sources: {config.enabled_sources}")
    print(f"  Search Keywords: {config.search_keywords}")
    
    issues = config.validate()
    if issues:
        print("\nConfiguration Issues:")
        for issue in issues:
            print(f"  ⚠ {issue}")
