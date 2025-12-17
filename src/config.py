import os
from datetime import time

# ========= SCRAPER TIMING =========
MARKET_START = time(10, 0)
MARKET_END = time(17, 30)

SCRAPE_INTERVAL_MINUTES = 5

# ========= BASE URLS =========
BSE_SUBSCRIPTION_URL = (
    "https://www.bseindia.com/markets/publicIssues/"
    "CummDemandSchedule.aspx?ID={ipo_id}&status=L"
)

NSE_SUBSCRIPTION_URL = (
    "https://www.nseindia.com/market-data/"
    "issue-information?symbol={symbol}&series=EQ&type=Active"
)

# ========= FIREBASE =========
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID")
FIREBASE_CLIENT_EMAIL = os.getenv("FIREBASE_CLIENT_EMAIL")
FIREBASE_PRIVATE_KEY = os.getenv("FIREBASE_PRIVATE_KEY")
