from playwright.sync_api import sync_playwright
import time

NSE_LIST_URL = "https://www.nseindia.com/market-data/all-upcoming-issues-ipo"
NSE_DETAIL_URL = "https://www.nseindia.com/market-data/issue-information"
NSE_API_PART = "/api/issue-information-bid"


def fetch_nse_subscription(symbol: str, series: str):
    """
    NSE subscription fetcher
    - GitHub Actions safe
    - HTTP/2 disabled
    - Retry enabled
    """

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--disable-http2",
                "--disable-quic",
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True
        )

        page = context.new_page()

        def safe_goto(url):
            for attempt in range(2):
                try:
                    page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    return
                except Exception:
                    if attempt == 1:
                        raise
                    time.sleep(2)

        # 1️⃣ NSE IPO list page
        safe_goto(NSE_LIST_URL)
        time.sleep(2)

        # 2️⃣ NSE IPO detail page
        safe_goto(
            f"{NSE_DETAIL_URL}?symbol={symbol}&series={series}&type=Active"
        )
        time.sleep(2)

        # 3️⃣ Capture API response
        with page.expect_response(
            lambda r: NSE_API_PART in r.url,
            timeout=30000
        ) as resp_info:
            page.reload(wait_until="domcontentloaded")

        response = resp_info.value
        payload = response.json()

        browser.close()

    rows = payload.get("data", [])

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
