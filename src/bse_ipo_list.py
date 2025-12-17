import logging
import os
import sys
import re
import json
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
import requests

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from utils import create_session, retry_on_failure, clean_text

logger = logging.getLogger(__name__)


class BSEIPOListScraper:
    """Scraper for BSE IPO list page"""
    
    def __init__(self):
        self.session = create_session()
        self.session.headers.update(Config.HEADERS)
    
    def get_live_ipos(self) -> List[Dict[str, str]]:
        """
        Fetch list of LIVE IPOs from BSE
        
        Returns:
            List of dictionaries containing IPO details
        """
        logger.info("Fetching live IPOs from BSE...")
        
        def fetch():
            response = self.session.get(
                Config.BSE_IPO_LIST_URL,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response
        
        response = retry_on_failure(fetch, max_retries=Config.MAX_RETRIES)
        
        if not response:
            logger.error("Failed to fetch BSE IPO list page")
            return []
        
        return self._parse_ipo_list(response.text)
    
    def _parse_ipo_list(self, html: str) -> List[Dict[str, str]]:
        """
        Parse IPO list HTML (Angular-rendered) and extract live IPOs
        
        Args:
            html: HTML content from BSE IPO list page
        
        Returns:
            List of IPO dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        ipos = []
        
        try:
            # BSE now uses Angular.js with ng-repeat
            # Find all rows with ng-repeat="pi in GetData.Table"
            table_rows = soup.find_all('tr', {'ng-repeat': re.compile(r'pi in GetData\.Table')})
            
            if not table_rows:
                logger.warning("No ng-repeat table rows found. Trying alternative parsing...")
                # Try to find the table by structure
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    if len(rows) > 1:
                        # Check if this looks like the IPO table
                        header_row = rows[0]
                        headers = [th.get_text(strip=True) for th in header_row.find_all('th')]
                        
                        if 'Security Name' in headers and 'Exchange Platform' in headers:
                            logger.info("Found IPO table by structure matching")
                            table_rows = rows[1:]  # Skip header
                            break
            
            if not table_rows:
                logger.error("Could not find IPO table rows")
                self._save_debug_html(html, "bse_ipo_list_debug.html")
                return []
            
            for row in table_rows:
                cols = row.find_all('td')
                
                if len(cols) < 8:
                    continue
                
                # Extract data from columns
                # Structure: Security Name | Exchange Platform | Start Date | End Date | Offer Price | Face Value | Type Of Issue | Issue Status
                security_name_col = cols[0]
                exchange_platform = clean_text(cols[1].get_text())
                issue_type = clean_text(cols[6].get_text())
                issue_status = clean_text(cols[7].get_text())
                
                # Filter: Only IPO/FPO type and Live status
                if issue_type.upper() not in ['IPO', 'FPO'] or issue_status.upper() != 'LIVE':
                    continue
                
                # Extract security name and link
                link_tag = security_name_col.find('a')
                if not link_tag:
                    logger.warning(f"No link found in row: {security_name_col.get_text()}")
                    continue
                
                security_name = clean_text(link_tag.get_text())
                details_url = link_tag.get('href', '')
                
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
            
            logger.info(f"Total live IPOs found: {len(ipos)}")
            
        except Exception as e:
            logger.error(f"Error parsing IPO list: {e}", exc_info=True)
            self._save_debug_html(html, "bse_ipo_list_error.html")
        
        return ipos
    
    def get_ipo_id(self, details_url: str) -> Optional[str]:
        """
        Extract IPO ID from IPO details page
        
        Args:
            details_url: URL of the IPO details page
        
        Returns:
            IPO ID or None
        """
        logger.info(f"Fetching IPO ID from: {details_url}")
        
        # Try to extract ID from URL first
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
                logger.warning(f"Could not extract ID from URL: {e}")
        
        # Fallback: Fetch the page
        def fetch():
            response = self.session.get(details_url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response
        
        response = retry_on_failure(fetch, max_retries=Config.MAX_RETRIES)
        
        if not response:
            logger.error(f"Failed to fetch IPO details page: {details_url}")
            return None
        
        return self._extract_ipo_id(response.text)
    
    def _extract_ipo_id(self, html: str) -> Optional[str]:
        """
        Extract IPO ID from Cumulative Demand Schedule link
        
        Args:
            html: HTML content from IPO details page
        
        Returns:
            IPO ID or None
        """
        soup = BeautifulSoup(html, 'lxml')
        
        try:
            # Find link containing "CummDemandSchedule.aspx"
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link['href']
                
                # Check if this is the cumulative demand schedule link
                if 'CummDemandSchedule.aspx' in href and 'ID=' in href:
                    # Extract ID parameter
                    id_part = href.split('ID=')[1]
                    ipo_id = id_part.split('&')[0] if '&' in id_part else id_part
                    
                    logger.info(f"Extracted IPO ID: {ipo_id}")
                    return ipo_id
            
            logger.error("Could not find Cumulative Demand Schedule link")
            self._save_debug_html(html, "bse_ipo_details_debug.html")
            
        except Exception as e:
            logger.error(f"Error extracting IPO ID: {e}")
        
        return None
    
    def _save_debug_html(self, html: str, filename: str):
        """Save HTML for debugging purposes"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Saved debug HTML to {filename}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML: {e}")
