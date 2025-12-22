import logging
from nse_subscription import NSEScraper
from firestore_manager import FirestoreManager

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# src/main.py (Update this part)

def main():
    db = FirestoreManager()
    nse = NSEScraper()

    logger.info("Fetching NSE Mainboard subscription...")
    nse_data = nse.fetch_subscription()

    if nse_data:
        # NSE data ek list hai, usme har category ke liye company name ya symbol ho sakta hai
        # Hum pehli category se naam nikal sakte hain (Example logic)
        for item in nse_data:
            # Maan lo hume 'ZOMATO' ka data mila
            # Aapko yahan decide karna hai ki kis IPO ka data save karna hai
            print(f"Found data for: {item['category']}") 

        # Filhal testing ke liye:
        db.save_subscription_data(
            ipo_slug="ongoing-ipo-test", 
            exchange="NSE",
            board="MAINBOARD",
            data={"categories": nse_data}
        )
    else:
        logger.warning("No data fetched from NSE")

if __name__ == "__main__":
    main()
