import requests
import time

BASE = "https://www.nseindia.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
    "DNT": "1",
}


def _bootstrap_nse_session(symbol: str, series: str) -> requests.Session:
    """
    Proper NSE browser-like navigation:
    1. IPO list page
    2. IPO detail page
    """
    s = requests.Session()
    s.headers.update(HEADERS)

    # 1️⃣ Hit IPO list page
    s.get(
        f"{BASE}/market-data/all-upcoming-issues-ipo",
        timeout=15
    )
    time.sleep(1)

    # 2️⃣ Hit specific IPO detail page
    s.get(
        f"{BASE}/market-data/issue-information",
        params={
            "symbol": symbol,
            "series": series,
            "type": "Active"
        },
        timeout=15
    )
    time.sleep(1)

    return s


def fetch_nse_subscription(symbol: str, series: str):
    """
    NSE IPO subscription fetcher
    - EQ  → Consolidated Bid Details
    - SME → Default Bid Details
    """

    session = _bootstrap_nse_session(symbol, series)

    api_url = f"{BASE}/api/issue-information-bid"

    params = {
        "symbol": symbol,
        "series": series
    }

    if series == "EQ":
        params["category"] = "CONSOLIDATED"

    resp = session.get(api_url, params=params, timeout=15)

    # NSE bot response = HTML instead of JSON
    if resp.status_code != 200 or "text/html" in resp.headers.get("Content-Type", ""):
        raise RuntimeError(
            f"NSE blocked request ({resp.status_code}). "
            f"Likely bot protection. Response preview:\n{resp.text[:300]}"
        )

    payload = resp.json()
    rows = payload.get("data", [])

    parsed = {
        "qib": None,
        "nii": None,
        "rii": None,
        "total": None
    }

    for row in rows:
        cat = row.get("category", "").lower()

        if "qualified institutional" in cat:
            parsed["qib"] = row.get("noOfTimes")
        elif cat.startswith("non institutional"):
            parsed["nii"] = row.get("noOfTimes")
        elif "retail" in cat:
            parsed["rii"] = row.get("noOfTimes")
        elif cat == "total":
            parsed["total"] = row.get("noOfTimes")

    return parsed
