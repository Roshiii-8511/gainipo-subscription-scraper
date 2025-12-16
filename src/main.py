"""IPO Subscription Scraper - Live Subscription Data from BSE/NSE"""
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
        url = "https://www.bseindia.com/publicissue.html"
        logger.info(f"Fetching IPO list from: {url}")
        driver.get(url)
        time.sleep(4)
        
        html_content = driver.page_source
        soup = BeautifulSoup(html_content, 'html.parser')
        
        ipos = []
        rows = soup.find_all('tr')
        logger.info(f"Found {len(rows)} rows in table")
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                try:
                    ipo_name = cells[0].get_text(strip=True)
                    link_tag = cells[0].find('a')
                    if link_tag and link_tag.get('href'):
                        ipo_id = extract_ipo_id(link_tag['href'])
                        if ipo_name and ipo_id:
                            ipos.append({
                                'security_name': ipo_name,
                                'ipo_id': ipo_id,
                                'url': link_tag['href']
                            })
                            logger.info(f"Found IPO: {ipo_name} (ID: {ipo_id})")
                except Exception as e:
                    logger.debug(f"Error parsing row: {e}")
                    continue
        
        logger.info(f"Total IPOs found: {len(ipos)}")
        return ipos
    except Exception as e:
        logger.error(f"Error fetching BSE IPO list: {e}")
        return []

def extract_ipo_id(url_or_text):
    """Extract IPO ID from URL or onclick text"""
    match = re.search(r'id=(\d+)', str(url_or_text))
    if match:
        return match.group(1)
    match = re.search(r'\((\d+)[\,\)]", str(url_or_text))
    return match.group(1) if match else None

def fetch_bse_subscription_data(driver, ipo):
    """Fetch subscription data from BSE Cumulative Demand Schedule"""
    try:
        ipo_id = ipo['ipo_id']
        detail_url = f"https://www.bseindia.com/markets/publicIssues/DisplayIPO.aspx?id={ipo_id}"
        
        logger.info(f"Fetching BSE data from: {detail_url}")
        driver.get(detail_url)
        time.sleep(3)
        
        subscription_data = {
            'retail': {},
            'hni': {},
            'institutional': {},
            'timestamp': datetime.now(IST).isoformat(),
            'source': 'BSE'
        }
        
        try:
            cumulative_button = driver.find_element(By.XPATH, "//a[contains(text(), 'Cumulative Demand Schedule')]")
            logger.info("Found Cumulative Demand Schedule button")
            driver.execute_script("arguments[0].click();", cumulative_button)
            time.sleep(2)
        except Exception as e:
            logger.debug(f"Could not click Cumulative button: {e}")
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables")
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    try:
                        label_text = cells[0].get_text(strip=True).lower()
                        value_text = cells[1].get_text(strip=True)
                        
                        if 'retail' in label_text or 'rii' in label_text:
                            if 'ratio' in label_text or 'times' in label_text:
                                try:
                                    subscription_data['retail']['ratio'] = float(value_text)
                                except:
                                    pass
                            elif 'qty' in label_text or 'shares' in label_text:
                                try:
                                    val = value_text.replace(',', '').replace('x', '')
                                    subscription_data['retail']['quantity'] = int(float(val))
                                except:
                                    pass
                        
                        elif 'hni' in label_text or 'high net worth' in label_text:
                            if 'ratio' in label_text or 'times' in label_text:
                                try:
                                    subscription_data['hni']['ratio'] = float(value_text)
                                except:
                                    pass
                            elif 'qty' in label_text or 'shares' in label_text:
                                try:
                                    val = value_text.replace(',', '').replace('x', '')
                                    subscription_data['hni']['quantity'] = int(float(val))
                                except:
                                    pass
                        
                        elif 'institutional' in label_text or 'qib' in label_text:
                            if 'ratio' in label_text or 'times' in label_text:
                                try:
                                    subscription_data['institutional']['ratio'] = float(value_text)
                                except:
                                    pass
                            elif 'qty' in label_text or 'shares' in label_text:
                                try:
                                    val = value_text.replace(',', '').replace('x', '')
                                    subscription_data['institutional']['quantity'] = int(float(val))
                                except:
                                    pass
                    except Exception as e:
                        logger.debug(f"Error processing cell: {e}")
                        continue
        
        logger.info(f"BSE data extracted: {subscription_data}")
        return subscription_data
    except Exception as e:
        logger.error(f"Error fetching BSE subscription data: {e}")
        return None

def save_to_firestore(ipo, subscription_data):
    """Save IPO data to Firestore"""
    if not db:
        logger.error("Firestore not initialized")
        return False
    
    try:
        ipo_slug = ipo['security_name'].lower().replace(' ', '_').replace('&', 'and')
        doc_data = {
            'ipo_slug': ipo_slug,
            'security_name': ipo['security_name'],
            'ipo_id': ipo['ipo_id'],
            'subscription_data': subscription_data,
            'updated_at': datetime.now(IST).isoformat(),
        }
        
        db.collection('ipo_subscriptions').document(ipo_slug).set(doc_data, merge=True)
        logger.info(f"✓ Saved to Firestore: {ipo['security_name']}")
        return True
    except Exception as e:
        logger.error(f"Error saving to Firestore: {e}")
        return False

def main():
    driver = None
    try:
        driver = get_driver()
        if not driver:
            logger.error("Cannot initialize WebDriver")
            return
        
        ipos = fetch_bse_ipo_list(driver)
        if not ipos:
            logger.warning("No IPOs found")
            return
        
        logger.info(f"Processing {len(ipos)} IPOs...")
        success_count = 0
        
        for ipo in ipos[:3]:  
            try:
                logger.info(f"\nProcessing: {ipo['security_name']}")
                subscription_data = fetch_bse_subscription_data(driver, ipo)
                
                if subscription_data:
                    if save_to_firestore(ipo, subscription_data):
                        success_count += 1
                
                time.sleep(random.uniform(2, 4))
            except Exception as e:
                logger.error(f"Error processing {ipo['security_name']}: {e}")
                continue
        
        logger.info(f"\n" + "═"*70)
        logger.info(f"Completed: {success_count} IPOs saved to Firestore")
        logger.info("═"*70)
    
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if driver:
            driver.quit()
            logger.info("WebDriver closed")

if __name__ == "__main__":
    main()
