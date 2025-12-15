"""Configuration management for IPO subscription scraper."""
import os
from typing import Dict, Any, Optional

class Config:
    """Application configuration."""
    
    # Browser settings
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    CHROME_OPTIONS = [
        '--disable-blink-features=AutomationControlled',
        '--disable-extensions',
        '--disable-plugins',
        '--disable-web-resources',
        '--incognito',
    ]
    
    # Firestore settings
    FIRESTORE_CREDENTIALS = os.getenv('FIRESTORE_CREDENTIALS', 'serviceAccountKey.json')
    FIRESTORE_PROJECT_ID = os.getenv('FIRESTORE_PROJECT_ID')
    
    # Scraping URLs
    BSE_IPO_URL = 'https://www.bseindia.com/publicissue.html'
    NSE_IPO_URL = 'https://www.nseindia.com/market-data/issue-information'
    GAINIPO_BASE_URL = 'https://www.gainipo.com'
    
    # Scraping settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    RATE_LIMIT_DELAY = (2, 4)  # seconds
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # Database
    DB_COLLECTION_IPOS = 'ipo_subscriptions'
    DB_COLLECTION_ARCHIVE = 'ipo_archive'
    
    # Selenium wait times
    IMPLICIT_WAIT = 10
    EXPLICIT_WAIT = 20
    PAGE_LOAD_TIMEOUT = 30

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    HEADLESS = False

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    HEADLESS = True

def get_config(env: Optional[str] = None) -> Dict[str, Any]:
    """Get configuration based on environment."""
    if env is None:
        env = os.getenv('ENVIRONMENT', 'production')
    
    if env.lower() == 'development':
        return vars(DevelopmentConfig())
    else:
        return vars(ProductionConfig())
