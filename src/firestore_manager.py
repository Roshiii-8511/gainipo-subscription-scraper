import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config

logger = logging.getLogger(__name__)


class FirestoreManager:
    """Manages Firestore database operations for IPO subscription data"""
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Get credentials from environment
            creds_dict = Config.get_firebase_credentials()
            cred = credentials.Certificate(creds_dict)
            
            # Initialize Firebase (only once)
            if not firebase_admin._apps:
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            logger.info("Firebase initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {e}")
            raise
    
    def save_subscription_data(
        self,
        ipo_name: str,
        exchange_platform: str,
        ipo_id: str,
        subscription_data: Dict[str, Any]
    ) -> bool:
        """
        Save IPO subscription data to Firestore
        
        Args:
            ipo_name: Name of the IPO
            exchange_platform: Mainboard or SME
            ipo_id: BSE IPO ID
            subscription_data: Dictionary containing subscription details
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create document ID: ipo_name__YYYYMMDD_HHMM
            timestamp = datetime.now()
            doc_id = f"{ipo_name}__{timestamp.strftime('%Y%m%d_%H%M')}"
            doc_id = doc_id.replace(' ', '_').replace('/', '_').replace('\\', '_')
            
            # Prepare document data
            doc_data = {
                'ipo_name': ipo_name,
                'exchange_platform': exchange_platform,
                'ipo_id': ipo_id,
                'subscription_data': subscription_data,
                'timestamp': timestamp,
                'created_at': firestore.SERVER_TIMESTAMP
            }
            
            # Save to Firestore
            doc_ref = self.db.collection(Config.FIRESTORE_COLLECTION).document(doc_id)
            doc_ref.set(doc_data)
            
            logger.info(f"Successfully saved subscription data for {ipo_name} (ID: {doc_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save subscription data for {ipo_name}: {e}")
            return False
    
    def get_latest_subscription(self, ipo_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the latest subscription data for a specific IPO
        
        Args:
            ipo_name: Name of the IPO
        
        Returns:
            Latest subscription data or None
        """
        try:
            query = (
                self.db.collection(Config.FIRESTORE_COLLECTION)
                .where(filter=FieldFilter('ipo_name', '==', ipo_name))
                .order_by('timestamp', direction=firestore.Query.DESCENDING)
                .limit(1)
            )
            
            docs = query.stream()
            for doc in docs:
                return doc.to_dict()
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve subscription data for {ipo_name}: {e}")
            return None
    
    def batch_save(self, records: list) -> int:
        """
        Save multiple IPO records in a batch
        
        Args:
            records: List of dictionaries containing IPO data
        
        Returns:
            Number of successfully saved records
        """
        success_count = 0
        
        for record in records:
            if self.save_subscription_data(
                ipo_name=record['ipo_name'],
                exchange_platform=record['exchange_platform'],
                ipo_id=record['ipo_id'],
                subscription_data=record['subscription_data']
            ):
                success_count += 1
        
        return success_count
