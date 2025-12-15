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
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

# Timezone
IST = ZoneInfo("Asia/Kolkata")

# Logging setup
logging.basicConfig(
  level=logging.INFO,
  format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Firebase initialization
def init_firestore():
  try:
    creds_json = os.getenv("FIREBASE_CREDENTIALS")
    project_id = os.getenv("FIRESTORE_PROJECT_ID")
    if not creds_json or not project_id:
      logger.error("Missing Firebase credentials")
      return None
    creds = json.loads(creds_json)
    return firestore.Client.from_service_account_info(creds, project=project_id)
  except Exception as e:
    logger.error(f"Firebase init failed: {e}")
    return None

db = init_firestore()

def get_driver():
  """Get Chrome WebDriver for Selenium."""
  try:
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver
  except Exception as e:
    logger.error(f"WebDriver init failed: {e}")
    return None

def parse_number(text):
  """Parse numbers from strings."""
  if not text or text == '-' or text == '--':
    return 0
  import re
  cleaned = re.sub(r'[,\\s]', '', str(text))
  try:
    return int(cleaned)
  except:
    try:
      return int(float(cleaned))
    except:
      return 0

def fetch_bse_ipos():
  """Fetch live IPOs from BSE using Selenium."""
  driver = None
  try:
    logger.info("Initializing Selenium WebDriver...")
    driver = get_driver()
    if not driver:
      return []
    
    url = "https://www.bseindia.com/publicissue.html"
    logger.info(f"Navigating to {url}")
    driver.get(url)
    
    # Wait for table to load
    logger.info("Waiting for IPO table to render...")
    WebDriverWait(driver, 10).until(
      EC.presence_of_all_elements_located((By.TAG_NAME, "tr"))
    )
    
    # Give JS time to finish rendering
    time.sleep(2)
    
    # Get rendered HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    ipos = []
    table = None
    for tbl in soup.find_all('table'):
      headers = tbl.find_all('th')
      if headers and any('Security Name' in str(h) for h in headers):
        table = tbl
        break
    
    if not table:
      logger.warning("No IPO table found")
      return ipos
    
    rows = table.find_all('tr')[1:]
    logger.info(f"Found {len(rows)} rows")
    
    for row in rows:
      try:
        cols = row.find_all('td')
        if len(cols) < 8:
          continue
        
        security_link = cols[0].find('a')
        security_name = security_link.get_text(strip=True) if security_link else cols[0].get_text(strip=True)
        exchange_platform = cols[1].get_text(strip=True)
        issue_status = cols[7].get_text(strip=True)
        
        if issue_status.upper() == "LIVE":
          ipo_id = None
          if security_link and 'href' in security_link.attrs:
            href = security_link['href']
            if 'id=' in href:
              ipo_id = href.split('id=')[1].split('&')[0]
          
          logger.info(f"✓ Found LIVE: {security_name}")
          ipos.append({
            'security_name': security_name,
            'exchange_platform': exchange_platform,
            'ipo_id': ipo_id,
            'status': 'Live',
            'start_date': cols[2].get_text(strip=True) if len(cols) > 2 else '',
            'end_date': cols[3].get_text(strip=True) if len(cols) > 3 else ''
          })
      except Exception as e:
        logger.debug(f"Row parse error: {e}")
        continue
    
    logger.info(f"Total LIVE IPOs: {len(ipos)}")
    return ipos
    
  except Exception as e:
    logger.error(f"Error fetching IPOs: {e}")
    import traceback
    logger.error(traceback.format_exc())
    return []
  finally:
    if driver:
      driver.quit()
      logger.info("WebDriver closed")

def scrape_bse_subscription(ipo_data):
  """Scrape BSE subscription data."""
  driver = None
  try:
    ipo_id = ipo_data.get('ipo_id')
    if not ipo_id:
      return None
    
    driver = get_driver()
    if not driver:
      return None
    
    url = f"https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID={ipo_id}&status=L"
    logger.info(f"Fetching subscription data: {security_name}")
    driver.get(url)
    time.sleep(2)
    
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    table = soup.find('table')
    if not table:
      return None
    
    categories = {}
    rows = table.find_all('tr')[1:]
    
    for row in rows:
      cols = row.find_all('td')
      if len(cols) < 4:
        continue
      
      try:
        category = cols[1].get_text(strip=True).upper()
        shares_offered = parse_number(cols[2].get_text(strip=True))
        shares_bid = parse_number(cols[3].get_text(strip=True))
        
        if shares_offered > 0:
          subscription = round(shares_bid / shares_offered, 2)
        else:
          subscription = 0
        
        if 'QIB' in category:
          categories['QIB'] = {'offered': shares_offered, 'bid': shares_bid, 'subscription': subscription}
        elif 'RETAIL' in category:
          categories['Retail'] = {'offered': shares_offered, 'bid': shares_bid, 'subscription': subscription}
        elif 'NII' in category or 'NON' in category:
          categories['NII'] = {'offered': shares_offered, 'bid': shares_bid, 'subscription': subscription}
      except Exception as e:
        logger.debug(f"Subscription parse error: {e}")
        continue
    
    if not categories:
      return None
    
    total_offered = sum(c['offered'] for c in categories.values())
    total_bid = sum(c['bid'] for c in categories.values())
    total_subscription = round(total_bid / total_offered, 2) if total_offered > 0 else 0
    
    result = {
      'ipo_slug': ipo_data['security_name'].lower().replace(' ', '-'),
      'exchange': 'BSE',
      'board': ipo_data.get('exchange_platform', 'MAINBOARD'),
      'captured_at': datetime.now(IST).isoformat(),
      'categories': categories,
      'total': {'offered': total_offered, 'bid': total_bid, 'subscription': total_subscription},
      'source': 'BSE'
    }
    return result
    
  except Exception as e:
    logger.error(f"Scraping error: {e}")
    import traceback
    logger.error(traceback.format_exc())
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
  logger.info("=" * 60)
  logger.info("IPO Subscription Scraper - SELENIUM (JavaScript Rendering)")
  logger.info("=" * 60)
  
  ipos = fetch_bse_ipos()
  if not ipos:
    logger.warning("No live IPOs found")
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
  
  logger.info("=" * 60)
  logger.info(f"Scraper completed. Success: {success_count}/{len(ipos)}")
  logger.info("=" * 60)

if __name__ == "__main__":
  run_scraper()
