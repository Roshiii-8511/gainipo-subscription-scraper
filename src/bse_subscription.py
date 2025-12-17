import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger("bse_subscription")


def get_subscription_data(ipo):
    ipo_no = ipo["ipo_no"]

    url = (
        "https://www.bseindia.com/markets/publicIssues/"
        f"CummDemandSchedule.aspx?ID={ipo_no}&status=L"
    )

    logger.info(f"Fetching subscription data from: {url}")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": "Mozilla/5.0",
            "Accept-Language": "en-US,en;q=0.9",
        }
    )

    resp = session.get(url, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.find("table")
    if not table:
        raise RuntimeError("Subscription table not found")

    data = {
        "ipo_name": ipo["ipo_name"],
        "board": ipo["board"],
        "ipo_no": ipo_no,
        "categories": {},
    }

    for row in table.find_all("tr"):
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 4:
            continue

        category = cols[1]
        offered = cols[2].replace(",", "")
        bid = cols[3].replace(",", "")
        times = cols[4] if len(cols) > 4 else ""

        data["categories"][category] = {
            "shares_offered": offered,
            "shares_bid": bid,
            "times": times,
        }

    return data
