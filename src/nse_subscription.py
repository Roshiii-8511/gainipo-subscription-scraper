from playwright.sync_api import sync_playwright
import json
import time

NSE_BASE = "https://www.nseindia.com"


def fetch_nse_subscription(symbol: str, series: str):
    """
    NSE-safe subscription fetcher using real browser.
    Works on GitHub Actions.
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        )

        page = context.new_page()

        # Step 1: IPO list page
        page.goto(
            "https://www.nseindia.com/market-data/all-upcoming-issues-ipo",
            wait_until="networkidle"
        )

        # Step 2: IPO detail page
        page.goto(
            f"https://www.nseindia.com/market-data/issue-information"
            f"?symbol={symbol}&series={series}&type=Active",
            wait_until="networkidle"
        )

        # Capture XHR response
        api_url = "/api/issue-information-bid"

        with page.expect_response(lambda r: api_url in r.url) as resp_info:
            page.reload(wait_until="networkidle")

        response = resp_info.value
        data = response.json()

        browser.close()

    rows = data.get("data", [])

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
