import logging
from utils import get_http_session

def scrape_nse_subscription(ipo):
    symbol = ipo.get("nse_symbol")
    if not symbol:
        logging.warning("Missing nse_symbol, skipping")
        return None

    logging.info(f"NSE scrape placeholder → {symbol}")
    session = get_http_session()

    # NSE blocking is aggressive.
    # Implement after BSE flow is stable.
    return None

