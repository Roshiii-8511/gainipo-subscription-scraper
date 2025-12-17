import logging
from bse_ipo_list import fetch_live_ipos
from bse_subscription import scrape_bse_subscription
from firestore_manager import save_subscription

logging.basicConfig(level=logging.INFO)

def run():
    logging.info("===== GAINIPO BSE LIVE SUBS SCRAPER START =====")

    ipos = fetch_live_ipos()

    for ipo in ipos:
        try:
            data = scrape_bse_subscription(ipo)
            save_subscription(data)
        except Exception:
            logging.exception(f"Failed for {ipo['ipo_name']}")

    logging.info("===== SCRAPER RUN COMPLETE =====")

if __name__ == "__main__":
    run()
