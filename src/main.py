import logging
from nse_subscription import NSEScraper
from firestore_manager import FirestoreManager

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    db = FirestoreManager()
    nse = NSEScraper()

    # 1. Fetch NSE Mainboard Data
    logger.info("Fetching NSE Mainboard subscription...")
    nse_data = nse.fetch_subscription()

    if nse_data:
        # Note: NSE ke consolidated JSON me sabhi current IPOs ka data ho sakta hai
        # Ya fir aapko URL me symbol pass karna padega agar NSE structure badle.
        # Filhal hum ise 'current_ipo' slug me save kar rahe hain test ke liye.
        
        # TODO: Logic to identify 'ipo_slug' from the data
        # Agar JSON me 'symbol' hai to usse slug banayein
        
        db.save_subscription_data(
            ipo_slug="test-ipo-slug", # Isse dynamically update karna hoga
            exchange="NSE",
            board="MAINBOARD",
            data={"categories": nse_data}
        )
    else:
        logger.warning("No data fetched from NSE")

if __name__ == "__main__":
    main()
