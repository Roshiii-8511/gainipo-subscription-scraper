import logging
from bs4 import BeautifulSoup
from utils import get_http_session

BSE_LIVE_ISSUES_URL = "https://www.bseindia.com/markets/PublicIssues/PublicIssues.aspx"

def fetch_live_ipos():
    session = get_http_session()

    payload = {
        "ddlType": "IPO",
        "ddlStatus": "Live"
    }

    headers = {
        "Referer": "https://www.bseindia.com/publicissue.html",
        "X-Requested-With": "XMLHttpRequest"
    }

    logging.info("Fetching LIVE IPO list from BSE (server-side endpoint)")

    res = session.post(
        BSE_LIVE_ISSUES_URL,
        data=payload,
        headers=headers,
        timeout=20
    )
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "lxml")
    table = soup.find("table")

    if not table:
        logging.warning("BSE IPO table not found in response")
        return []

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

        link = cols[0].find("a")
        if not link:
            continue

        detail_url = "https://www.bseindia.com" + link["href"]

        ipos.append({
            "name": security,
            "board": board,
            "detail_url": detail_url
        })

    logging.info(f"LIVE IPOs detected: {len(ipos)}")
    return ipos
