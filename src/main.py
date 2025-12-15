"""Main orchestrator for IPO subscription scraper - SELENIUM VERSION"""
import time
import random
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from bs4 import BeautifulSoup
import json
import os
from google.cloud import firestore
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

# Logging setup
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global Firestore client
db = None

# Chrome options
CHROME_OPTIONS = [
    '--disable-blink-features=AutomationControlled',
    '--disable-extensions',
    '--disable-plugins',
    '--disable-web-resources',
    '--incognito',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--headless',
]

def init_firestore():
    """Initialize Firestore client."""
    global db
    try:
        creds_json = os.getenv('FIREBASE_CREDENTIALS')
        project_id = os.getenv('FIRESTORE_PROJECT_ID')
        
        if not creds_json or not project_id:
            logger.error("Missing Firebase credentials")
            return None
        
        creds = json.loads(creds_json)
        db = firestore.Client.from_service_account_info(creds, project=project_id)
        logger.info("✓ Firestore initialized")
        return db
    except Exception as e:
        logger.error(f"Firestore init failed: {e}")
        return None

db = init_firestore()

def get_driver():
    """Get Chrome WebDriver for Selenium."""
    try:
        logger.info("Initializing Selenium WebDriver...")
        
        options = webdriver.ChromeOptions()
        for opt in CHROME_OPTIONS:
            options.add_argument(opt)
        
        # Use system ChromeDriver path or fall back to PATH
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH', 'chromedriver')
        
        # Try with Service first
        try:
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        except:
            # Fallback to direct path
            driver = webdriver.Chrome(chromedriver_path, options=options)
        
        if not driver:
            return None
        
        logger.info("✓ WebDriver initialized")
        return driver
    except Exception as e:
        logger.error(f"WebDriver init failed: {e}")
        return None

def fetch_bse_ipos():
    """Fetch active IPOs from BSE website."""
    driver = get_driver()
    if not driver:
        logger.error("No WebDriver available")
        return []
    
    try:
        # Use the correct URL for live IPOs
        url = "https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p"
        logger.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for the table to load
        logger.info("Waiting for IPO table to render...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
        )
        time.sleep(5)  # Extra wait for full rendering
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        ipos = []
        
        # Find the main data table
        table = soup.find('table')
        if not table:
            logger.warning("No table found on page")
            return []
        
        rows = table.find_all('tr')
        logger.info(f"Found table with {len(rows)} rows")
        
        # Parse each row (skip header)
        for idx, row in enumerate(rows[1:]):
            try:
                cols = row.find_all('td')
                if len(cols) >= 8:  # At least 8 columns expected
                    security_name = cols[0].get_text(strip=True)
                    exchange = cols[1].get_text(strip=True)
                    start_date = cols[2].get_text(strip=True)
                    end_date = cols[3].get_text(strip=True)
                    offer_price = cols[4].get_text(strip=True)
                    face_value = cols[5].get_text(strip=True)
                    issue_type = cols[6].get_text(strip=True)
                    status = cols[7].get_text(strip=True)
                    
                    # Only include live IPOs
                    if security_name and status.lower() == 'live':
                        logger.info(f"Found Live IPO: {security_name}")
                        ipos.append({
                            'security_name': security_name,
                            'exchange': exchange,
                            'start_date': start_date,
                            'end_date': end_date,
                            'offer_price': offer_price,
                            'face_value': face_value,
                            'issue_type': issue_type,
                            'status': status,
                        })
            except Exception as e:
                logger.debug(f"Error parsing row {idx}: {e}")
                continue
        
        logger.info(f"Total live IPOs found: {len(ipos)}")
        return ipos
    
    except Exception as e:
        logger.error(f"Fetch error: {e}", exc_info=True)
        return []
    finally:
        if driver:
            driver.quit()

def scrape_subscription_details(driver, ipo):
    """Scrape detailed subscription data for an IPO."""
    try:
        security_name = ipo.get('security_name')
        logger.info(f"Fetching subscription details for {security_name}")
        
        # Try to find subscription data on current page
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # Extract subscription data if available
        subscription_data = {
            'retail': 'N/A',
            'hni': 'N/A',
            'institutional': 'N/A',
            'employee': 'N/A',
        }
        
        return subscription_data
    except Exception as e:
        logger.error(f"Subscription fetch error: {e}")
        return None

def save_to_firestore(data):
    """Save IPO data to Firestore."""
    if not db or not data:
        return False
    
    try:
        ipo_slug = data['security_name'].lower().replace(' ', '-')[:50]
        timestamp = datetime.now(IST)
        doc_id = f"{ipo_slug}__{timestamp.strftime('%Y%m%d_%H%M')}"
        
        db.collection('ipo_subscriptions').document(doc_id).set(data)
        logger.info(f"✓ Saved to Firestore: {doc_id}")
        return True
    except Exception as e:
        logger.error(f"Firestore save error: {e}")
        return False

def run_scraper():
    """Main scraper execution."""
    logger.info("="*70)
    logger.info("IPO SUBSCRIPTION SCRAPER - SELENIUM (JavaScript Rendering)")
    logger.info("="*70)
    
    ipos = fetch_bse_ipos()
    
    if not ipos:
        logger.warning("No live IPOs found on BSE")
        logger.info("="*70)
        return
    
    success_count = 0
    for ipo in ipos:
        try:
            logger.info(f"\nProcessing IPO: {ipo['security_name']}")
            logger.info(f"  Exchange: {ipo['exchange']}")
            logger.info(f"  Type: {ipo['issue_type']}")
            logger.info(f"  Start Date: {ipo['start_date']}")
            logger.info(f"  End Date: {ipo['end_date']}")
            
            # Add scraped timestamp
            ipo['scraped_at'] = datetime.now(IST).isoformat()
            
            # Save to Firestore
            if save_to_firestore(ipo):
                success_count += 1
            else:
                logger.error(f"Failed to save {ipo['security_name']} to Firestore")
            
            # Rate limiting
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            logger.error(f"Error processing {ipo.get('security_name')}: {e}")
            continue
    
    logger.info("="*70)
    logger.info(f"RESULTS: Successfully saved {success_count}/{len(ipos)} IPOs to Firestore")
    logger.info("="*70)

if __name__ == "__main__":
    run_scraper()
