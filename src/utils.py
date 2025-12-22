from datetime import datetime
import pytz


def is_market_time():
    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    if now.weekday() >= 5:
        return False

    if now.hour < 9 or now.hour >= 17:
        return False

    return True


def slugify(text: str) -> str:
    return (
        text.lower()
        .replace("&", "and")
        .replace(" ", "_")
        .replace("/", "_")
        .replace("-", "_")
    )
