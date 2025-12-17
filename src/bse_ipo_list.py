import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from config.config import BSE_PUBLIC_ISSUE_URL


def fetch_live_ipos():
    logging.info("Fetching LIVE IPO list from BSE using Selenium (safe mode)")

    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-notifications")
    chrome_options.add_argument("--disable-extensions")
    chrome_options.add_argument("--blink-settings=imagesEnabled=false")

    # 🔥 CRITICAL FIX
    chrome_options.page_load_strategy = "eager"

    service = Service(ChromeDriverManager().install())

    driver = webdriver.Chrome(
        service=service,
        options=chrome_options
    )

    try:
        driver.set_page_load_timeout(30)
        driver.get(BSE_PUBLIC_ISSUE_URL)

        wait = WebDriverWait(driver, 20)

        # wait only till table rows appear, NOT full page
        wait.until(
            EC.presence_of_element_located((By.XPATH, "//table//tr"))
        )

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

        logging.info(f"LIVE IPOs detected: {len(ipos)}")
        return ipos

    finally:
        driver.quit()
