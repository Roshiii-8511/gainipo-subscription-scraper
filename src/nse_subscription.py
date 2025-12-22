import requests
import logging

logger = logging.getLogger(__name__)

class NSEScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.nseindia.com/market-data/new-stock-issue-ipo',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _get_cookies(self):
        """NSE requires visiting the home page first to get valid cookies"""
        try:
            self.session.get("https://www.nseindia.com", timeout=10)
        except Exception as e:
            logger.error(f"Error fetching cookies: {e}")

    def fetch_subscription(self):
        self._get_cookies() # Get fresh session
        url = "https://www.nseindia.com/json/liveMarket/issue-information-bid-consolidated-eq.json"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code == 200:
                raw_data = response.json()
                return self._parse_data(raw_data)
            else:
                logger.error(f"NSE API failed with status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"NSE Fetch Error: {e}")
            return None

    def _parse_data(self, json_data):
        # Yahan hum wo table wala data nikalenge jo tu Firestore me chahta hai
        # NSE response me 'data' field ke andar actual numbers hote hain
        parsed = []
        if 'data' in json_data:
            for item in json_data['data']:
                parsed.append({
                    'category': item.get('category'),
                    'shares_offered': item.get('noOfShareOffered'),
                    'shares_bid': item.get('noOfSharesBid'),
                    'subscription_times': item.get('noOfTotalMeant')
                })
        return parsed
