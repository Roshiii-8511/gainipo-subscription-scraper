import os
import json
from typing import Dict, Any

class Config:
    """Configuration manager for the scraper"""
    
    # BSE URLs
    BSE_IPO_LIST_URL = "https://www.bseindia.com/publicissue.html"
    BSE_IPO_DETAILS_BASE = "https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx"
    BSE_SUBSCRIPTION_BASE = "https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx"
    
    # NSE URLs (for future SME support)
    NSE_IPO_LIST_URL = "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
    NSE_ISSUE_BASE = "https://www.nseindia.com/market-data/issue-information"
    
    # Request headers to bypass basic bot detection
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAY = 5  # seconds
    REQUEST_TIMEOUT = 30  # seconds
    
    # Firebase configuration
    FIRESTORE_COLLECTION = "ipo_subscriptions"
    
    @staticmethod
    def get_firebase_credentials() -> Dict[str, Any]:
        """Get Firebase credentials from environment variable"""
        creds_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        if not creds_json:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set")
        
        try:
            return json.loads(creds_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in FIREBASE_SERVICE_ACCOUNT_JSON: {e}")
    
    @staticmethod
    def is_ci_environment() -> bool:
        """Check if running in CI environment"""
        return os.getenv('GITHUB_ACTIONS') == 'true'
