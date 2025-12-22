import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import firebase_admin
from firebase_admin import credentials, firestore

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config

logger = logging.getLogger(__name__)


class FirestoreManager:
    def __init__(self):
        try:
            creds_dict = Config.get_firebase_credentials()
            cred = credentials.Certificate(creds_dict)

            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)

            self.db = firestore.client()
            logger.info("Firebase initialized")

        except Exception as e:
            logger.error(f"Firebase init failed: {e}")
            raise

    def save_subscription_data(
        self,
        ipo_slug: str,
        exchange: str,
        board: str,
        data: Dict[str, Any]
    ) -> bool:
        """
        Saves latest + history snapshot
        """
        try:
            now = datetime.now(timezone.utc)

            base_ref = self.db.collection(Config.FIRESTORE_COLLECTION).document(ipo_slug)

            latest_payload = {
                "exchange": exchange,
                "board": board,
                "data": data,
                "updated_at": firestore.SERVER_TIMESTAMP
            }

            base_ref.set(latest_payload, merge=True)

            history_ref = base_ref.collection("history").document(
                now.strftime("%Y%m%d_%H%M")
            )

            history_ref.set({
                "exchange": exchange,
                "board": board,
                "data": data,
                "timestamp": now
            })

            logger.info(f"Saved subscription for {ipo_slug}")
            return True

        except Exception as e:
            logger.error(f"Firestore save failed for {ipo_slug}: {e}")
            return False
