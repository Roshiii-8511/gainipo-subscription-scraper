import logging
from datetime import datetime
from firestore_manager import get_live_ipos, save_subscription_snapshot
from bse_subscription import scrape_bse_subscription
from nse_subscription import scrape_nse_subscription

logging.basicConfig(level=logging.INFO)

def run():
    logging.info("===== GAINIPO SUBSCRIPTION SCRAPER START =====")

    ipos = get_live_ipos()
    logging.info(f"Active IPOs found: {len(ipos)}")

    for ipo in ipos:
        try:
            if ipo["board"] == "MAINBOARD":
                data = scrape_bse_subscription(ipo)
            else:
                if ipo["listing_exchange"] == "BSE":
                    data = scrape_bse_subscription(ipo)
                else:
                    data = scrape_nse_subscription(ipo)

            if not data:
                continue

            snapshot = {
                "ipo_slug": ipo["slug"],
                "exchange": ipo["listing_exchange"],
                "board": ipo["board"],
                "captured_at": datetime.utcnow().isoformat(),
                "is_live": True,
                **data
            }

            save_subscription_snapshot(ipo["slug"], snapshot)

        except Exception:
            logging.exception(f"Error processing IPO → {ipo.get('slug')}")

    logging.info("===== SCRAPER RUN COMPLETE =====")

if __name__ == "__main__":
    run()
