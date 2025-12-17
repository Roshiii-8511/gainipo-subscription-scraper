#!/usr/bin/env python3
"""
GainIPO Subscription Scraper
Scrapes live IPO subscription data from BSE and saves to Firestore
"""

import logging
import sys
from bse_ipo_list import BSEIPOListScraper
from bse_subscription import BSESubscriptionScraper
from firestore_manager import FirestoreManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('scraper.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main scraper execution flow"""
    logger.info("=" * 60)
    logger.info("GainIPO Subscription Scraper - Starting")
    logger.info("=" * 60)
    
    try:
        # Initialize components
        ipo_list_scraper = BSEIPOListScraper()
        subscription_scraper = BSESubscriptionScraper()
        firestore_manager = FirestoreManager()
        
        # Step 1: Get list of live IPOs
        live_ipos = ipo_list_scraper.get_live_ipos()
        
        if not live_ipos:
            logger.warning("No live IPOs found")
            return
        
        logger.info(f"Processing {len(live_ipos)} live IPO(s)")
        
        # Step 2-4: For each IPO, get ID, scrape subscription, save to Firestore
        success_count = 0
        
        for ipo in live_ipos:
            logger.info("-" * 60)
            logger.info(f"Processing: {ipo['security_name']} ({ipo['exchange_platform']})")
            
            try:
                # Step 2: Get IPO ID from details page
                ipo_id = ipo_list_scraper.get_ipo_id(ipo['details_url'])
                
                if not ipo_id:
                    logger.error(f"Could not extract IPO ID for {ipo['security_name']}")
                    continue
                
                # Step 3: Scrape subscription data
                subscription_data = subscription_scraper.get_subscription_data(ipo_id)
                
                if not subscription_data:
                    logger.error(f"Could not fetch subscription data for {ipo['security_name']}")
                    continue
                
                # Step 4: Save to Firestore
                saved = firestore_manager.save_subscription_data(
                    ipo_name=ipo['security_name'],
                    exchange_platform=ipo['exchange_platform'],
                    ipo_id=ipo_id,
                    subscription_data=subscription_data
                )
                
                if saved:
                    success_count += 1
                    logger.info(f"✓ Successfully processed {ipo['security_name']}")
                else:
                    logger.error(f"✗ Failed to save data for {ipo['security_name']}")
                
            except Exception as e:
                logger.error(f"Error processing {ipo['security_name']}: {e}")
                continue
        
        # Summary
        logger.info("=" * 60)
        logger.info(f"Scraper completed: {success_count}/{len(live_ipos)} IPOs processed successfully")
        logger.info("=" * 60)
        
        # Exit with error code if no IPOs were processed successfully
        if success_count == 0:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Fatal error in main execution: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
