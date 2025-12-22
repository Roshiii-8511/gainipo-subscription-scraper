import requests
from utils import slugify

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json"
}


def fetch_nse_subscription(symbol: str, series: str):
    url = (
        "https://www.nseindia.com/api/issue-information-bid-consolidated"
        if series == "EQ"
        else "https://www.nseindia.com/api/issue-information-bid"
    )

    params = {"symbol": symbol, "series": series}

    r = requests.get(url, headers=HEADERS, params=params, timeout=10)
    r.raise_for_status()

    rows = r.json().get("data", [])

    parsed = {}

    for row in rows:
        cat = row.get("category", "").lower()
        if "qualified" in cat:
            parsed["qib"] = row["noOfTimes"]
        elif "non institutional" in cat:
            parsed["nii"] = row["noOfTimes"]
        elif "retail" in cat:
            parsed["rii"] = row["noOfTimes"]
        elif cat == "total":
            parsed["total"] = row["noOfTimes"]

    return parsed
