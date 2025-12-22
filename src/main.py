from utils import is_market_time, slugify
from firestore_manager import FirestoreManager
from nse_subscription import fetch_nse_subscription


def main():
    if not is_market_time():
        print("⏰ Outside market hours (auto mode) — skipping run")
        return

    print("🚀 IPO Subscription scraper running")

    fs = FirestoreManager()

    data = fetch_nse_subscription("GKSL", "EQ")

    fs.save_subscription_data(
        ipo_slug=slugify("Gujarat Kidney and Super Speciality Limited"),
        exchange="NSE",
        board="MAINBOARD",
        data=data
    )

    print("✅ Run completed")


if __name__ == "__main__":
    main()
