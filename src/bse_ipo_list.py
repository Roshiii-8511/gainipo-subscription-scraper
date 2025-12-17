import logging
from urllib.parse import urlparse, parse_qs
from pyppeteer import launch

BSE_PUBLIC_ISSUE_URL = "https://www.bseindia.com/publicissue.html"

logger = logging.getLogger("bse_ipo_list")


async def fetch_live_ipos():
    logger.info("Fetching live IPOs from BSE...")

    browser = await launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
        ],
    )

    page = await browser.newPage()
    await page.goto(BSE_PUBLIC_ISSUE_URL, timeout=60000)
    await page.waitForSelector("table")

    rows = await page.querySelectorAll("table tr")

    ipos = []

    for row in rows:
        cols = await row.querySelectorAll("td")
        if len(cols) < 8:
            continue

        name = (await page.evaluate("(el) => el.innerText", cols[0])).strip()
        board = (await page.evaluate("(el) => el.innerText", cols[1])).strip()
        issue_type = (await page.evaluate("(el) => el.innerText", cols[6])).strip()
        status = (await page.evaluate("(el) => el.innerText", cols[7])).strip()

        if issue_type != "IPO" or status != "Live":
            continue

        link_el = await cols[0].querySelector("a")
        detail_url = await page.evaluate("(el) => el.href", link_el)

        # 🔥 FIX: extract IPONo (REAL subscription ID)
        parsed = urlparse(detail_url)
        qs = parse_qs(parsed.query)
        ipo_no = qs.get("IPONo", [None])[0]

        if not ipo_no:
            logger.warning(f"IPONo not found for {name}")
            continue

        ipos.append(
            {
                "ipo_name": name,
                "board": board,
                "ipo_no": ipo_no,
            }
        )

        logger.info(f"Found live IPO: {name} ({board})")

    await browser.close()
    logger.info(f"Total live IPOs found: {len(ipos)}")
    return ipos
