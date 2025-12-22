import requests
from bs4 import BeautifulSoup


def fetch_active_bse_sme_ipos():
    url = "https://www.bseindia.com/publicissue.html"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    rows = soup.select("table tr")[1:]
    result = []

    for r in rows:
        cols = [c.get_text(strip=True) for c in r.find_all("td")]
        if len(cols) < 8:
            continue

        exchange, issue_type, status = cols[1], cols[6], cols[7]

        if exchange == "SME" and issue_type == "IPO" and status == "Live":
            link = r.find("a")["href"]
            result.append(link)

    return result
