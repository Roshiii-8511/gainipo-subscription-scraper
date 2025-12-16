"""IPO Subscription Scraper - REAL-TIME BSE/NSE DATA EXTRACTION"""
import time
import random
import logging
import re
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

db = None

CHROME_OPTIONS = [
    '--disable-blink-features=AutomationControlled',
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--headless',
    '--disable-extensions',
    '--disable-plugins',
    '--incognito',
]

def init_firestore():
    global db
    try:
        creds_json = os.getenv('FIREBASE_CREDENTIALS')
        project_id = os.getenv('FIRESTORE_PROJECT_ID')
        if not creds_json or not project_id:
            logger.error("Missing Firebase credentials")
            return None
        creds = json.loads(creds_json)
        db = firestore.Client.from_service_account_info(
            creds, project=project_id
        )
        logger.info("✓ Firestore initialized")
        return db
    except Exception as e:
        logger.error(f"Firestore init failed: {e}")
        return None

db = init_firestore()

def get_driver():
    try:
        options = webdriver.ChromeOptions()
        for opt in CHROME_OPTIONS:
            options.add_argument(opt)
        chromedriver_path = os.getenv('CHROMEDRIVER_PATH', 'chromedriver')
        service = Service(chromedriver_path)
        driver = webdriver.Chrome(service=service, options=options)
        logger.info("✓ Chrome WebDriver initialized")
        return driver
    except Exception as e:
        logger.error(f"Cannot get WebDriver: {e}")
        return None

def fetch_bse_ipo_list(driver):
    """Fetch IPO list from BSE"""
    try:
        url = "https://www.bseindia.com/markets/PublicIssues/IPOIssues_new.aspx?id=1&Type=p"
        logger.info(f"Fetching IPO list from: {url}")
        driver.get(url)
        time.sleep(3)
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        ipos = []
        rows = soup.find_all('tr')
        logger.info(f"Found {len(rows)} rows in table")
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 2:
                ipo_name = cells[0].get_text(strip=True)
                
                link_tag = cells[0].find('a')
                if link_tag and link_tag.get('href'):
                    ipo_id = extract_ipo_id_from_url(link_tag['href'])
                    if ipo_name and ipo_id:
                        ipos.append({
                            'security_name': ipo_name,
                            'ipo_id': ipo_id,
                            'url': link_tag['href']
                        })
                        logger.info(f"Found IPO: {ipo_name} (ID: {ipo_id})")
        
        logger.info(f"Total IPOs found: {len(ipos)}")
        return ipos
    except Exception as e:
        logger.error(f"Error fetching BSE IPO list: {e}")
        return []

def extract_ipo_id_from_url(url):
    """Extract IPO ID from URL"""
    match = re.search(r'id=(\d+)', url)
    return match.group(1) if match else None

def fetch_subscription_data_bse(driver, ipo):
    """Fetch real-time subscription data from BSE detail page"""
    try:
        ipo_id = ipo['ipo_id']
        detail_url = f"https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx?id={ipo_id}&type=IPO&idtype=1&status=L"
        
        logger.info(f"Fetching subscription data from: {detail_url}")
        driver.get(detail_url)
        time.sleep(2)
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.TAG_NAME, "table"))
        )
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        subscription_data = {
            'retail': {},
            'hni': {},
            'institutional': {},
            'timestamp': datetime.now(IST).isoformat()
        }
        
        # Extract subscription data from BSE Bid Details tab
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables on detail page")
        
        for table in tables:
            rows = table.find_all('tr')
            for i, row in enumerate(rows):
                cells = row.find_all('td')
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    
                    # Extract Retail data
                    if 'retail' in label or 'rii' in label:
                        if 'bid' in label or 'quantity' in label:
                            try:
                                value = cells[1].get_text(strip=True).replace(',', '')
                                if value.isdigit():
                                    subscription_data['retail']['quantity'] = int(value)
                            except:
                                pass
                        if 'ratio' in label or 'times' in label:
                            try:
                                value = cells[1].get_text(strip=True)
                                subscription_data['retail']['ratio'] = float(value)
                            except:
                                pass
                    
                    # Extract HNI data
                    if 'hni' in label or 'high net worth' in label:
                        if 'bid' in label or 'quantity' in label:
                            try:
                                value = cells[1].get_text(strip=True).replace(',', '')
                                if value.isdigit():
                                    subscription_data['hni']['quantity'] = int(value)
                            except:
                                pass
                        if 'ratio' in label or 'times' in label:
                            try:
                                value = cells[1].get_text(strip=True)
                                subscription_data['hni']['ratio'] = float(value)
                            except:
                                pass
                    
                    # Extract Institutional data
                    if 'institutional' in label or 'qib' in label:
                        if 'bid' in label or 'quantity' in label:
                            try:
                                value = cells[1].get_text(strip=True).replace(',', '')
                                if value.isdigit():
                                    subscription_data['institutional']['quantity'] = int(value)
                            except:
                                pass
                        if 'ratio' in label or 'times' in label:
                            try:
                                value = cells[1].get_text(strip=True)
                                subscription_data['institutional']['ratio'] = float(value)
                            except:
                                pass
        
        logger.info(f"Extracted subscription data: {subscription_data}")
        return subscription_data
    except Exception as e:
        logger.error(f"Error fetching subscription data for {ipo['security_name']}: {e}")
        return None

def save_to_firestore(ipo, subscription_data):
    """Save IPO data to Firestore"""
    if not db:
        logger.error("Firestore not initialized")
        return False
    
    try:
        ipo_slug = ipo['security_name'].lower().replace(' ', '_')
        doc_data = {
            'ipo_slug': ipo_slug,
            'security_name': ipo['security_name'],
            'ipo_id': ipo['ipo_id'],
            'subscription_data': subscription_data,
            'updated_at': datetime.now(IST).isoformat(),
            'bse_url': ipo.get('url', '')
        }
        
        db.collection('ipo_subscriptions').document(ipo_slug).set(
            doc_data,
            merge=True
        )
        logger.info(f"✓ Saved to Firestore: {ipo['security_name']}")
        return True
    except Exception as e:
        logger.error(f"Error saving to Firestore: {e}")
        return False

def run_scraper():
    driver = get_driver()
    if not driver:
        logger.error("Cannot get WebDriver")
        return
    
    success_count = 0
    try:
        for ipo in ipos:
            logger.info(f"\nProcessing: {ipo['security_name']}")
            
            # Fetch subscription data
            subscription_data = fetch_subscription_data_bse(driver, ipo)
            
            # Save to Firestore
            if save_to_firestore(ipo, subscription_data):
                success_count += 1
            
            time.sleep(random.uniform(2, 4))
        
        finally:
            if driver:
                driver.quit()
        
        logger.info("═"*70)
        logger.info(f"RESULTS: Saved {success_count}/{len(ipos)} IPOs with subscription data")
        logger.info("═"*70)
    
    except Exception as e:
        logger.error(f"Error in scraper: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    ipos = []
    driver = get_driver()
    if driver:
        ipos = fetch_bse_ipo_list(driver)
        driver.quit()
    
    if ipos:
        run_scraper()
    else:
        logger.error("No IPOs found")
