import requests
import logging
import time

logger = logging.getLogger(__name__)

class NSEScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.nseindia.com"
        # Professional Headers
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }

    def _init_session(self):
        """NSE requires a landing page visit to set cookies before API calls work"""
        try:
            # Step 1: Visit main page
            self.session.get(self.base_url, headers=self.headers, timeout=15)
            time.sleep(1) # Chota sa delay human behavior dikhane ke liye
            
            # Step 2: Visit IPO market page specifically to strengthen the session
            ipo_page = "https://www.nseindia.com/market-data/new-stock-issue-ipo"
            self.session.get(ipo_page, headers=self.headers, timeout=15)
            time.sleep(1)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize NSE session: {e}")
            return False

    def fetch_subscription(self):
        if not self._init_session():
            return None

        # Actual API URL for consolidated bid details
        api_url = "https://www.nseindia.com/json/liveMarket/issue-information-bid-consolidated-eq.json"
        
        # Add referer to headers for the specific API call
        api_headers = self.headers.copy()
        api_headers['Referer'] = 'https://www.nseindia.com/market-data/new-stock-issue-ipo'

        try:
            response = self.session.get(api_url, headers=api_headers, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                # Debug log to see what we actually got
                logger.info(f"Successfully fetched data from NSE. Keys: {data.keys()}")
                
                # Check if data exists or IPO is closed
                if 'data' not in data or not data['data']:
                    logger.warning("NSE returned 200 but 'data' array is empty. (Maybe market is closed?)")
                    return None
                    
                return self._parse_data(data)
            else:
                logger.error(f"NSE API Failed. Status: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error during NSE API call: {e}")
            return None

    def _parse_data(self, json_data):
        parsed_results = []
        # JSON structure usually has a 'data' list
        for item in json_data.get('data', []):
            parsed_results.append({
                'category': item.get('category', 'N/A'),
                'shares_offered': item.get('noOfShareOffered', 0),
                'shares_bid': item.get('noOfSharesBid', 0),
                'subscription_times': item.get('noOfTotalMeant', 0)
            })
        return parsed_results
