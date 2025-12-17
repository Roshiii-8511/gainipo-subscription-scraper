import logging
import os
import sys
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from utils import clean_text

logger = logging.getLogger(__name__)


class BSEIPOListScraper:
    """Scraper for BSE IPO list page using Selenium"""
    
    def __init__(self):
        self.driver = None
    
    def _init_driver(self):
        """Initialize Chrome driver with headless options"""
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument(f'user-agent={Config.HEADERS["User-Agent"]}')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome driver initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Chrome driver: {e}")
            raise
    
    def get_live_ipos(self) -> List[Dict[str, str]]:
        """
        Fetch list of LIVE IPOs from BSE using Selenium
        
        Returns:
            List of dictionaries containing IPO details
        """
        logger.info("Fetching live IPOs from BSE...")
        
        try:
            if not self.driver:
                self._init_driver()
            
            # Load the page
            self.driver.get(Config.BSE_IPO_LIST_URL)
            
            # Wait for the table to load (wait for ng-repeat elements)
            wait = WebDriverWait(self.driver, 20)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'tr[ng-repeat]')))
            
            # Give Angular a bit more time to render
            time.sleep(2)
            
            # Get the page source after JavaScript has run
            html = self.driver.page_source
            
            return self._parse_ipo_list(html)
            
        except Exception as e:
            logger.error(f"Error fetching IPO list: {e}", exc_info=True)
            return []
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def _parse_ipo_list(self, html: str) -> List[Dict[str, str]]:
        """
        Parse IPO list HTML and extract live IPOs
        
        Args:
            html: HTML content from BSE IPO list page
        
        Returns:
            List of IPO dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        ipos = []
        
        try:
            # Find all links to DisplayIPO.aspx
            ipo_links = soup.find_all('a', href=lambda x: x and 'DisplayIPO.aspx' in x)
            
            if not ipo_links:
                logger.error("No IPO links found in the page")
                self._save_debug_html(html, "bse_ipo_list_debug.html")
                return []
            
            logger.info(f"Found {len(ipo_links)} IPO links")
            
            for link in ipo_links:
                try:
                    # Get the parent row
                    row = link.find_parent('tr')
                    if not row:
                        continue
                    
                    cols = row.find_all('td')
                    
                    if len(cols) < 8:
                        continue
                    
                    # Extract security name from link
                    security_name = clean_text(link.get_text())
                    details_url = link.get('href', '')
                    
                    # Extract other fields from columns
                    exchange_platform = clean_text(cols[1].get_text())
                    issue_type = clean_text(cols[6].get_text())
                    issue_status = clean_text(cols[7].get_text())
                    
                    # Filter: Only IPO/FPO type and Live status
                    if issue_type.upper() not in ['IPO', 'FPO']:
                        continue
                    
                    if issue_status.upper() != 'LIVE':
                        continue
                    
                    # Make absolute URL
                    if details_url and not details_url.startswith('http'):
                        if details_url.startswith('markets'):
                            details_url = f"https://www.bseindia.com/{details_url}"
                        else:
                            details_url = f"https://www.bseindia.com/markets/publicIssues/{details_url}"
                    
                    if not details_url:
                        logger.warning(f"No details URL found for {security_name}")
                        continue
                    
                    ipo_info = {
                        'security_name': security_name,
                        'exchange_platform': exchange_platform,
                        'details_url': details_url
                    }
                    
                    ipos.append(ipo_info)
                    logger.info(f"Found live IPO: {security_name} ({exchange_platform})")
                    
                except Exception as e:
                    logger.warning(f"Error parsing IPO link: {e}")
                    continue
            
            logger.info(f"Total live IPOs found: {len(ipos)}")
            
        except Exception as e:
            logger.error(f"Error parsing IPO list: {e}", exc_info=True)
            self._save_debug_html(html, "bse_ipo_list_error.html")
        
        return ipos
    
    def get_ipo_id(self, details_url: str) -> Optional[str]:
        """
        Extract IPO ID from URL parameters
        
        Args:
            details_url: URL of the IPO details page
        
        Returns:
            IPO ID or None
        """
        logger.info(f"Extracting IPO ID from: {details_url}")
        
        # Extract ID from URL
        # URL format: DisplayIPO.aspx?id=4362&type=IPO&idtype=1&status=L&IPONo=7504&startdt=16Dec2025
        if 'id=' in details_url:
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(details_url)
                params = urllib.parse.parse_qs(parsed.query)
                if 'id' in params:
                    ipo_id = params['id'][0]
                    logger.info(f"Extracted IPO ID from URL: {ipo_id}")
                    return ipo_id
            except Exception as e:
                logger.error(f"Could not extract ID from URL: {e}")
        
        return None
    
    def _save_debug_html(self, html: str, filename: str):
        """Save HTML for debugging purposes"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Saved debug HTML to {filename}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML: {e}")
