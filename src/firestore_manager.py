import os
import json
import logging
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

def get_firestore_client():
    sa_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    if not sa_json:
        raise RuntimeError("FIREBASE_SERVICE_ACCOUNT_JSON not found")

    info = json.loads(sa_json)
    credentials = service_account.Credentials.from_service_account_info(info)

    return firestore.Client(
        project=info["project_id"],
        credentials=credentials
    )

db = get_firestore_client()

def get_live_ipos():
    logging.info("Fetching OPEN IPOs with live updates enabled")
    docs = (
        db.collection("ipos")
        .where("status", "==", "OPEN")
        .where("accept_live_updates", "==", True)
        .stream()
    )
    return [doc.to_dict() for doc in docs]

def save_subscription_snapshot(ipo_slug, data):
    doc_id = f"{ipo_slug}__{datetime.now().strftime('%Y%m%d_%H%M')}"
    db.collection("ipo_subscriptions").document(doc_id).set(data)
    logging.info(f"Saved snapshot → {doc_id}")
