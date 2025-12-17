from datetime import time

# ============================
# MARKET HOURS (IST)
# ============================
MARKET_START = time(10, 0)
MARKET_END = time(17, 30)

# ============================
# BSE URLs
# ============================

# 1️⃣ BSE IPO LIST PAGE (JS rendered – Selenium use hoga)
BSE_PUBLIC_ISSUE_URL = "https://www.bseindia.com/publicissue.html"

# 2️⃣ BSE LIVE SUBSCRIPTION PAGE (static HTML)
BSE_SUBSCRIPTION_URL = (
    "https://www.bseindia.com/markets/publicIssues/"
    "CummDemandSchedule.aspx?ID={ipo_id}&status=L"
)

# ============================
# NSE URL (FOR SME – FUTURE USE)
# ============================

# NSE subscription page (JS + heavy protection)
# Abhi implement nahi kiya, but config me rehna chahiye
NSE_SUBSCRIPTION_URL = (
    "https://www.nseindia.com/market-data/"
    "issue-information?symbol={symbol}&series=EQ&type=Active"
)
