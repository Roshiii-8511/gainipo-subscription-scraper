import requests
import time

API_URL = "https://www.nseindia.com/api/issue-information-bid"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://www.nseindia.com/",
    "Connection": "keep-alive",
}


def fetch_nse_subscription(symbol: str, series: str):
    """
    GitHub-safe NSE scraper using mobile headers
    (used by real production bots)
    """

    s = requests.Session()
    s.headers.update(HEADERS)

    # STEP 1: hit lightweight page to set cookies
    s.get("https://www.nseindia.com", timeout=10)
    time.sleep(0.5)

    # STEP 2: call API directly
    params = {
        "symbol": symbol,
        "series": series
    }

    # Mainboard only
    if series == "EQ":
        params["category"] = "CONSOLIDATED"

    r = s.get(API_URL, params=params, timeout=10)

    if r.status_code != 200 or "application/json" not in r.headers.get("content-type", ""):
        raise RuntimeError(
            f"NSE blocked request ({r.status_code}) → {r.text[:200]}"
        )

    data = r.json().get("data", [])

    parsed = {
        "qib": None,
        "nii": None,
        "rii": None,
        "total": None
    }

    for row in data:
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
