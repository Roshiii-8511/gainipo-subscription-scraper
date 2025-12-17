import logging
from bs4 import BeautifulSoup
from utils import get_http_session

BSE_IPO_LIST_URL = "https://www.bseindia.com/publicissue.html"

def fetch_live_ipos():
    """
    Fetch LIVE IPOs (Type = IPO, Status = Live) from BSE
    Returns list of dicts with:
    - name
    - board
    - detail_url
    """
    session = get_http_session()
    logging.info("Fetching LIVE IPO list from BSE")

    res = session.get(BSE_IPO_LIST_URL, timeout=20)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "lxml")
    table = soup.find("table")

    ipos = []

    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) < 8:
            continue

        security = cols[0].get_text(strip=True)
        board = cols[1].get_text(strip=True)
        issue_type = cols[6].get_text(strip=True)
        status = cols[7].get_text(strip=True)

        if issue_type != "IPO" or status != "Live":
            continue

        link_tag = cols[0].find("a")
        if not link_tag:
            continue

        detail_url = "https://www.bseindia.com" + link_tag["href"]

        ipos.append({
            "name": security,
            "board": board,
            "detail_url": detail_url
        })

    logging.info(f"LIVE IPOs found on BSE: {len(ipos)}")
    return ipos
