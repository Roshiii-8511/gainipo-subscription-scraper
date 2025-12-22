from datetime import datetime
import pytz
import os


def is_market_time():
    """
    Rules:
    1. FORCE_RUN=true  → always allow
    2. Local run       → allow
    3. GitHub Actions  → only 9–5 IST (Mon–Fri)
    """

    # 1️⃣ Explicit override (highest priority)
    if os.getenv("FORCE_RUN", "").lower() == "true":
        return True

    # 2️⃣ Local run (not GitHub Actions)
    if not os.getenv("GITHUB_ACTIONS"):
        return True

    # 3️⃣ GitHub Actions auto mode → enforce market hours
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
