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
        url = "https://www.bseindia.com/publicissue.html"
        logger.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for page to fully load
        logger.info("Waiting for IPO table to render...")
        time.sleep(10)  # Give page time to render JavaScript
        
        # Try multiple selectors to find IPO data
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        ipos = []
        
        # Try finding all tables and extract data
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables on page")
        
        if tables:
            # Usually the first or second table contains IPOs
            for table_idx, table in enumerate(tables[:3]):
                logger.info(f"Processing table {table_idx}")
                rows = table.find_all('tr')
                logger.info(f"Table {table_idx} has {len(rows)} rows")
                
                for row_idx, row in enumerate(rows[1:]):  # Skip header
                    cols = row.find_all('td')
                    
                    if len(cols) >= 2:
                        # Extract text from cells
                        company_name = cols[0].get_text(strip=True)
                        
                        # Filter out empty rows and headers
                        if company_name and len(company_name) > 3:
                            logger.info(f"Found IPO: {company_name}")
                            ipos.append({
                                'security_name': company_name,
                                'issue_type': cols[1].get_text(strip=True) if len(cols) > 1 else 'N/A',
                            })
        
        logger.info(f"Found {len(ipos)} active IPOs")
        return ipos
    
    except Exception as e:
        logger.error(f"Fetch error: {e}", exc_info=True)
        return []
    finally:
        if driver:
            driver.quit()

def scrape_bse_subscription(ipo):
    """Scrape subscription data for IPO."""
    driver = get_driver()
    if not driver:
        return None
    
    try:
        # Navigate to IPO subscription page
        security_name = ipo.get('security_name')
        logger.info(f"Scraping: {security_name}")
        
        url = "https://www.bseindia.com/publicissue.html"
        driver.get(url)
        time.sleep(random.uniform(2, 4))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        data = {
            'ipo_slug': security_name.lower().replace(' ', '-')[:50],
            'security_name': security_name,
            'subscription_data': {
                'retail': 'N/A',
                'hni': 'N/A',
                'institutional': 'N/A',
            },
            'scraped_at': datetime.now(IST).isoformat(),
        }
        
        return data
    
    except Exception as e:
        logger.error(f"Scrape error: {e}", exc_info=True)
        return None
    finally:
        if driver:
            driver.quit()

def save_to_firestore(data):
    """Save subscription data to Firestore."""
    if not db or not data:
        return False
    
    try:
        ipo_slug = data['ipo_slug']
        timestamp = datetime.now(IST)
        doc_id = f"{ipo_slug}__{timestamp.strftime('%Y%m%d_%H%M')}"
        
        db.collection('ipo_subscriptions').document(doc_id).set(data)
        logger.info(f"✓ Saved {doc_id}")
        return True
    except Exception as e:
        logger.error(f"Save error: {e}")
        return False

def run_scraper():
    """Main scraper execution."""
    logger.info("="*60)
    logger.info("IPO Subscription Scraper - SELENIUM (JavaScript Rendering)")
    logger.info("="*60)
    
    ipos = fetch_bse_ipos()
    
    if not ipos:
        logger.warning("No live IPOs found")
        logger.warning("This may be due to: market hours, data not loaded, or page structure change")
        return
    
    success_count = 0
    for ipo in ipos:
        logger.info(f"Processing: {ipo['security_name']}")
        time.sleep(random.uniform(2, 4))
        
        data = scrape_bse_subscription(ipo)
        if data:
            if save_to_firestore(data):
                success_count += 1
            else:
                logger.error(f"Failed to save {ipo['security_name']}")
        else:
            logger.warning(f"No subscription data for {ipo['security_name']}")
    
    logger.info("="*60)
    logger.info(f"Scraper completed. Success: {success_count}/{len(ipos)}")
    logger.info("="*60)

if __name__ == "__main__":
    run_scraper()
