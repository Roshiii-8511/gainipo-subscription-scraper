from utils import is_market_time, slugify
from firestore_manager import FirestoreManager
from nse_subscription import fetch_nse_subscription
from bse_subscription import fetch_bse_sme_subscription

def main():
    if not is_market_time():
        print("Outside market hours")
        return

    fs = FirestoreManager()

    # EXAMPLE NSE MAINBOARD
    data = fetch_nse_subscription("GKSL", "EQ")
    fs.save_subscription_data(
        ipo_slug=slugify("Gujarat Kidney and Super Speciality Limited"),
        exchange="NSE",
        board="MAINBOARD",
        data=data
    )


if __name__ == "__main__":
    main()
