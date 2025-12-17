import logging
from bs4 import BeautifulSoup
from utils import get_http_session, clean_number
from config.config import BSE_SUBSCRIPTION_URL

def extract_ipo_id(detail_url):
    session = get_http_session()
    res = session.get(detail_url, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "lxml")

    for a in soup.find_all("a"):
        href = a.get("href", "")
        if "CummDemandSchedule.aspx" in href and "ID=" in href:
            return href.split("ID=")[1].split("&")[0]

    raise RuntimeError("IPO ID not found")

def scrape_bse_subscription(ipo):
    ipo_id = extract_ipo_id(ipo["detail_url"])
    url = BSE_SUBSCRIPTION_URL.format(ipo_id=ipo_id)

    logging.info(f"Scraping LIVE subs → {ipo['ipo_name']} (ID {ipo_id})")

    session = get_http_session()
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

        cat = cols[1].lower()
        offered = clean_number(cols[2])
        bid = clean_number(cols[3])

        if "qualified institutional" in cat:
            categories["QIB"] = {"shares_offered": offered, "shares_bid": bid}
        elif "retail" in cat:
            categories["Retail"] = {"shares_offered": offered, "shares_bid": bid}
        elif "more than ten lakh" in cat:
            categories.setdefault("NII", {})["BHNI"] = bid
        elif "upto 10 lakh" in cat:
            categories.setdefault("NII", {})["SHNI"] = bid

        total_bid += bid
        total_offered += offered

    if "NII" in categories:
        categories["NII"]["total_bid"] = (
            categories["NII"].get("BHNI", 0) +
            categories["NII"].get("SHNI", 0)
        )

    return {
        "ipo_name": ipo["ipo_name"],
        "board": ipo["board"],
        "categories": categories,
        "total": {
            "shares_bid": total_bid,
            "shares_offered": total_offered,
            "subscription": round(total_bid / total_offered, 2) if total_offered else 0
        },
        "source": "BSE"
    }
