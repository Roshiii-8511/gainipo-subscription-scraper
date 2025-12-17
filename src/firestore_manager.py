import os, json, logging
from datetime import datetime
from google.cloud import firestore
from google.oauth2 import service_account

def get_db():
    info = json.loads(os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON"))
    creds = service_account.Credentials.from_service_account_info(info)
    return firestore.Client(project=info["project_id"], credentials=creds)

db = get_db()

def save_subscription(data):
    doc_id = f"{data['ipo_name']}__{datetime.now().strftime('%Y%m%d_%H%M')}"
    db.collection("ipo_subscriptions").document(doc_id).set(data)
    logging.info(f"Saved → {doc_id}")
