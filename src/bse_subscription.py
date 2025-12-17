import logging
from bs4 import BeautifulSoup
from config.config import BSE_SUBSCRIPTION_URL
from utils import get_http_session, clean_number, random_delay

def scrape_bse_subscription(ipo):
    ipo_id = ipo.get("bse_ipo_id")
    if not ipo_id:
        logging.warning("Missing bse_ipo_id, skipping")
        return None

    url = BSE_SUBSCRIPTION_URL.format(ipo_id=ipo_id)
    session = get_http_session()

    logging.info(f"BSE scrape started → {ipo['slug']}")
    res = session.get(url, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "lxml")
    table = soup.find("table")

    categories = {}
    total_bid = 0
    total_offered = 0

    for row in table.find_all("tr"):
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 4:
            continue

        name = cols[1].lower()
        offered = clean_number(cols[2])
        bid = clean_number(cols[3])

        if "qualified institutional" in name:
            categories["QIB"] = {
                "shares_offered": offered,
                "shares_bid": bid,
                "subscription": round(bid / offered, 2) if offered else 0
            }

        elif "retail" in name:
            categories["Retail"] = {
                "shares_offered": offered,
                "shares_bid": bid,
                "subscription": round(bid / offered, 2) if offered else 0
            }

        elif "non institutional" in name and ">" in name:
            categories.setdefault("NII", {})["BHNI"] = bid

        elif "non institutional" in name and "upto" in name:
            categories.setdefault("NII", {})["SHNI"] = bid

        elif "employee" in name:
            categories["Employee"] = {
                "shares_offered": offered,
                "shares_bid": bid,
                "subscription": round(bid / offered, 2) if offered else 0
            }

        total_bid += bid
        total_offered += offered

    if "NII" in categories:
        categories["NII"]["total_bid"] = (
            categories["NII"].get("BHNI", 0) +
            categories["NII"].get("SHNI", 0)
        )

    random_delay()

    return {
        "categories": categories,
        "total": {
            "shares_bid": total_bid,
            "shares_offered": total_offered,
            "subscription": round(total_bid / total_offered, 2) if total_offered else 0
        },
        "source": "BSE"
    }
