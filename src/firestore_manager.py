"""Firestore database manager for IPO subscriptions."""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo
import firebase_admin
from firebase_admin import credentials, firestore

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

class FirestoreManager:
    """Manages Firestore database operations."""
    
    def __init__(self, creds_path: str, project_id: str):
        """Initialize Firestore manager."""
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate(creds_path)
                firebase_admin.initialize_app(cred, {'projectId': project_id})
            self.db = firestore.client()
            logger.info("Firestore initialized successfully")
        except Exception as e:
            logger.error(f"Firestore init failed: {e}")
            self.db = None
    
    def save_ipo_subscription(self, data: Dict[str, Any]) -> bool:
        """Save IPO subscription data to Firestore."""
        if not self.db or not data:
            return False
        
        try:
            ipo_slug = data.get('ipo_slug')
            timestamp = datetime.now(IST)
            doc_id = f"{ipo_slug}__{timestamp.strftime('%Y%m%d_%H%M')}"
            
            # Add metadata
            data['created_at'] = timestamp
            data['updated_at'] = timestamp
            data['status'] = 'active'
            
            self.db.collection('ipo_subscriptions').document(doc_id).set(data)
            logger.info(f"✓ Saved {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Save error: {e}")
            return False
    
    def update_ipo_subscription(self, doc_id: str, data: Dict[str, Any]) -> bool:
        """Update existing IPO subscription."""
        if not self.db:
            return False
        
        try:
            data['updated_at'] = datetime.now(IST)
            self.db.collection('ipo_subscriptions').document(doc_id).update(data)
            logger.info(f"✓ Updated {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Update error: {e}")
            return False
    
    def get_ipo_subscription(self, doc_id: str) -> Optional[Dict]:
        """Retrieve IPO subscription by ID."""
        if not self.db:
            return None
        
        try:
            doc = self.db.collection('ipo_subscriptions').document(doc_id).get()
            return doc.to_dict() if doc.exists else None
        except Exception as e:
            logger.error(f"Retrieve error: {e}")
            return None
    
    def query_active_ipos(self) -> List[Dict]:
        """Query all active IPO subscriptions."""
        if not self.db:
            return []
        
        try:
            docs = self.db.collection('ipo_subscriptions').where(
                'status', '==', 'active'
            ).stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            logger.error(f"Query error: {e}")
            return []
    
    def archive_ipo(self, doc_id: str) -> bool:
        """Move IPO to archive."""
        if not self.db:
            return False
        
        try:
            doc = self.db.collection('ipo_subscriptions').document(doc_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['archived_at'] = datetime.now(IST)
                self.db.collection('ipo_archive').document(doc_id).set(data)
                self.db.collection('ipo_subscriptions').document(doc_id).delete()
                logger.info(f"✓ Archived {doc_id}")
                return True
        except Exception as e:
            logger.error(f"Archive error: {e}")
        return False
    
    def delete_ipo(self, doc_id: str) -> bool:
        """Delete IPO subscription."""
        if not self.db:
            return False
        
        try:
            self.db.collection('ipo_subscriptions').document(doc_id).delete()
            logger.info(f"✓ Deleted {doc_id}")
            return True
        except Exception as e:
            logger.error(f"Delete error: {e}")
            return False
