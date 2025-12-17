import requests
import logging
import time
import random

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

def get_http_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9"
    })
    return session

def clean_number(val):
    if not val or val == "-":
        return 0
    return int(val.replace(",", "").strip())

def small_delay():
    time.sleep(random.uniform(0.5, 1.2))
