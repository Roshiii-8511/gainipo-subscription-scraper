import requests
from bs4 import BeautifulSoup


def fetch_bse_sme_subscription(ipo_no: str):
    url = f"https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID={ipo_no}&status=L"
    soup = BeautifulSoup(requests.get(url).text, "html.parser")

    table = soup.find("table")
    rows = table.find_all("tr")[1:]

    data = {}

    for r in rows:
        cols = [c.get_text(strip=True) for c in r.find_all("td")]
        if not cols:
            continue

        name = cols[0].lower()
        if "qualified" in name:
            data["qib"] = cols[-1]
        elif "non institutional" in name:
            data["nii"] = cols[-1]
        elif "individual" in name:
            data["rii"] = cols[-1]
        elif name == "total":
            data["total"] = cols[-1]

    return data
