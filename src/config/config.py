import json
import os


class Config:
    FIRESTORE_COLLECTION = "ipo_subscriptions"

    @staticmethod
    def get_firebase_credentials():
        raw = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
        if not raw:
            raise RuntimeError("FIREBASE_SERVICE_ACCOUNT missing")
        return json.loads(raw)
