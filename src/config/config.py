import os
import json
from typing import Dict


class Config:
    """Configuration settings for the scraper"""
    
    # BSE URLs
    BSE_IPO_LIST_URL = "https://www.bseindia.com/publicissue.html"
    BSE_SUBSCRIPTION_URL = "https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx"
    
    # Request settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 2
    
    # Headers
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    # Firestore settings
    FIRESTORE_COLLECTION = 'ipo_subscriptions'
    
    @staticmethod
    def get_firebase_credentials() -> Dict:
        """
        Get Firebase credentials from environment variable
        
        Returns:
            Dictionary containing Firebase credentials
        """
        creds_json = os.getenv('FIREBASE_SERVICE_ACCOUNT_JSON')
        
        if not creds_json:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON environment variable not set")
        
        try:
            return json.loads(creds_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in Firebase credentials: {e}")
