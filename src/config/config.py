from datetime import time

# Market hours (IST)
MARKET_START = time(10, 0)
MARKET_END = time(17, 30)

# BSE subscription URL
BSE_SUBSCRIPTION_URL = (
    "https://www.bseindia.com/markets/publicIssues/"
    "CummDemandSchedule.aspx?ID={ipo_id}&status=L"
)

# NSE subscription URL (SME only)
NSE_SUBSCRIPTION_URL = (
    "https://www.nseindia.com/market-data/"
    "issue-information?symbol={symbol}&series=EQ&type=Active"
)
