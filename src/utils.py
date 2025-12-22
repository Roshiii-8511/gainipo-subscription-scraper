from datetime import datetime
import pytz
import os


def is_market_time():
    """
    Enforce market hours ONLY for GitHub Actions.
    Manual runs are always allowed.
    """

    # If not running in GitHub Actions → allow anytime
    if not os.getenv("GITHUB_ACTIONS"):
        return True

    ist = pytz.timezone("Asia/Kolkata")
    now = datetime.now(ist)

    # Mon–Fri only
    if now.weekday() >= 5:
        return False

    # 09:00–17:00 IST
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
