import requests
import time

BASE_URL = "https://www.nseindia.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive"
}


def _get_nse_session():
    """
    NSE blocks direct API calls.
    We must hit homepage first to set cookies.
    """
    session = requests.Session()
    session.headers.update(HEADERS)

    # Bootstrap cookies
    session.get(BASE_URL, timeout=10)
    time.sleep(1)

    return session


def fetch_nse_subscription(symbol: str, series: str):
    """
    Fetch NSE IPO subscription
    - EQ  → Consolidated
    - SME → Default NSE bid details
    """

    session = _get_nse_session()

    url = f"{BASE_URL}/api/issue-information-bid"

    params = {
        "symbol": symbol,
        "series": series
    }

    # Mainboard needs consolidated flag
    if series == "EQ":
        params["category"] = "CONSOLIDATED"

    resp = session.get(url, params=params, timeout=10)

    if resp.status_code != 200:
        raise RuntimeError(
            f"NSE API failed {resp.status_code} → {resp.text[:200]}"
        )

    json_data = resp.json()
    rows = json_data.get("data", [])

    parsed = {
        "qib": None,
        "nii": None,
        "rii": None,
        "total": None
    }

    for row in rows:
        category = row.get("category", "").lower()

        if "qualified institutional" in category:
            parsed["qib"] = row.get("noOfTimes")
        elif category.startswith("non institutional"):
            parsed["nii"] = row.get("noOfTimes")
        elif "retail" in category:
            parsed["rii"] = row.get("noOfTimes")
        elif category == "total":
            parsed["total"] = row.get("noOfTimes")

    return parsed
