"""Main orchestrator for IPO subscription scraper - FIXED & DEBUGGED"""
import time
import random
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup
import json
import os
from google.cloud import firestore

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
      logger.error("Missing Firebase credentials in environment")
      return None
    creds = json.loads(creds_json)
    return firestore.Client.from_service_account_info(creds, project=project_id)
  except Exception as e:
    logger.error(f"Firebase initialization failed: {e}")
    return None

db = init_firestore()

def get_session():
  """Create HTTP session with retries."""
  session = requests.Session()
  session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
  })
  return session

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
  """Fetch live IPOs from BSE - DEBUGGED VERSION."""
  try:
    session = get_session()
    url = "https://www.bseindia.com/publicissue.html"
    response = session.get(url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    ipos = []
    
    # Find all tables
    tables = soup.find_all('table')
    logger.info(f"Found {len(tables)} tables on page")
    
    # Find the table containing "Security Name" header
    table = None
    for idx, tbl in enumerate(tables):
      headers = tbl.find_all('th')
      header_text = ' '.join([str(h.get_text(strip=True)) for h in headers])
      if 'Security Name' in header_text:
        logger.info(f"Found target table at index {idx}")
        logger.info(f"Headers: {header_text[:100]}...")
        table = tbl
        break
    
    if not table:
      logger.warning("No IPO table found on BSE")
      return ipos
    
    rows = table.find_all('tr')[1:]  # Skip header row
    logger.info(f"Found {len(rows)} data rows in table")
    
    for row_idx, row in enumerate(rows[:5]):
      try:
        cols = row.find_all('td')
        if len(cols) == 0:
          continue
        
        logger.info(f"\n--- ROW {row_idx} ---")
        logger.info(f"Total columns: {len(cols)}")
        
        # Log all column values
        for col_idx, col in enumerate(cols):
          col_text = col.get_text(strip=True)[:50]
          logger.info(f"Col[{col_idx}]: {col_text}")
        
        # Now try to extract with different column indices
        if len(cols) >= 8:
          security_name = cols[0].get_text(strip=True)
          exchange_platform = cols[1].get_text(strip=True)
          issue_status_col7 = cols[7].get_text(strip=True)
          
          logger.info(f"Security: {security_name}")
          logger.info(f"Platform: {exchange_platform}")
          logger.info(f"Status[7]: {issue_status_col7}")
          
          # Check last column too
          last_col = cols[-1].get_text(strip=True)
          logger.info(f"Last Col: {last_col}")
          
          # Try to find "Live" in any column
          live_found = False
          live_col_idx = -1
          for c_idx, col in enumerate(cols):
            if 'Live' in col.get_text(strip=True) or 'Forthcoming' in col.get_text(strip=True):
              live_found = True
              live_col_idx = c_idx
              logger.info(f"Status column is actually at index {c_idx}: {col.get_text(strip=True)}")
              break
          
          if live_found and "Live" in cols[live_col_idx].get_text(strip=True):
            logger.info(f"✓ FOUND LIVE IPO: {security_name}")
            # Extract IPO ID from the link
            ipo_id = None
            security_link = cols[0].find('a')
            if security_link and 'href' in security_link.attrs:
              href = security_link['href']
              if 'id=' in href:
                ipo_id = href.split('id=')[1].split('&')[0]
            
            ipos.append({
              'security_name': security_name,
              'exchange_platform': exchange_platform,
              'ipo_id': ipo_id,
              'status': 'Live',
              'start_date': cols[2].get_text(strip=True) if len(cols) > 2 else '',
              'end_date': cols[3].get_text(strip=True) if len(cols) > 3 else ''
            })
      except Exception as e:
        logger.error(f"Error parsing row {row_idx}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        continue
    
    logger.info(f"\n\nTotal LIVE IPOs found: {len(ipos)}")
    return ipos
    
  except Exception as e:
    logger.error(f"Error fetching BSE IPOs: {e}")
    import traceback
    logger.error(traceback.format_exc())
    return []

def scrape_bse_subscription(ipo_data):
  """Scrape BSE subscription data."""
  try:
    ipo_id = ipo_data.get('ipo_id')
    if not ipo_id:
      logger.warning(f"No IPO ID for {ipo_data['security_name']}")
      return None
    
    session = get_session()
    url = f"https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID={ipo_id}&status=L"
    logger.info(f"Fetching: {url}")
    response = session.get(url, timeout=30)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    table = soup.find('table')
    if not table:
      logger.warning(f"No subscription data for {ipo_data['security_name']}")
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
        logger.debug(f"Error parsing subscription row: {e}")
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
    logger.error(f"Error scraping: {e}")
    import traceback
    logger.error(traceback.format_exc())
    return None

def save_to_firestore(data):
  """Save subscription data to Firestore."""
  if not db or not data:
    return False
  
  try:
    ipo_slug = data['ipo_slug']
    timestamp = datetime.now(IST)
    doc_id = f"{ipo_slug}__{timestamp.strftime('%Y%m%d_%H%M')}"
    
    db.collection('ipo_subscriptions').document(doc_id).set(data)
    logger.info(f"Saved {doc_id} to Firestore")
    return True
    
  except Exception as e:
    logger.error(f"Error saving: {e}")
    return False

def run_scraper():
  """Main scraper execution."""
  logger.info("=" * 50)
  logger.info("Starting IPO Subscription Scraper - DEBUGGED")
  logger.info("=" * 50)
  
  ipos = fetch_bse_ipos()
  if not ipos:
    logger.warning("No live IPOs found")
    return
  
  success_count = 0
  for ipo in ipos:
    logger.info(f"Processing: {ipo['security_name']}")
    time.sleep(random.uniform(1, 3))
    
    data = scrape_bse_subscription(ipo)
    if data:
      if save_to_firestore(data):
        success_count += 1
        logger.info(f"✓ {ipo['security_name']}")
      else:
        logger.error(f"✗ Failed to save {ipo['security_name']}")
    else:
      logger.warning(f"✗ No data for {ipo['security_name']}")
  
  logger.info("=" * 50)
  logger.info(f"Success: {success_count}/{len(ipos)}")
  logger.info("=" * 50)

if __name__ == "__main__":
  run_scraper()
