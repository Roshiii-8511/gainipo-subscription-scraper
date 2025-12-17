import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from config.config import BSE_PUBLIC_ISSUE_URL

def fetch_live_ipos():
    logging.info("Fetching LIVE IPO list from BSE using Selenium")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(
        ChromeDriverManager().install(),
        options=options
    )

    driver.get(BSE_PUBLIC_ISSUE_URL)
    driver.implicitly_wait(10)

    rows = driver.find_elements(By.XPATH, "//table//tr")

    ipos = []

    for row in rows:
        cols = row.find_elements(By.TAG_NAME, "td")
        if len(cols) < 8:
            continue

        name = cols[0].text.strip()
        board = cols[1].text.strip()
        issue_type = cols[6].text.strip()
        status = cols[7].text.strip()

        if issue_type != "IPO" or status != "Live":
            continue

        link = cols[0].find_element(By.TAG_NAME, "a").get_attribute("href")

        ipos.append({
            "ipo_name": name,
            "board": board,
            "detail_url": link
        })

    driver.quit()

    logging.info(f"LIVE IPOs detected: {len(ipos)}")
    return ipos
