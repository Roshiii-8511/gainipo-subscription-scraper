import logging
import os
import sys
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
        Parse IPO list HTML and extract live IPOs
        
        Args:
            html: HTML content from BSE IPO list page
        
        Returns:
            List of IPO dictionaries
        """
        soup = BeautifulSoup(html, 'lxml')
        ipos = []
        
        try:
            # Find the main table containing IPO data
            # BSE uses a table with id='ContentPlaceHolder1_gvData'
            table = soup.find('table', {'id': 'ContentPlaceHolder1_gvData'})
            
            if not table:
                logger.error("Could not find IPO table on BSE page")
                self._save_debug_html(html, "bse_ipo_list_debug.html")
                return []
            
            rows = table.find_all('tr')[1:]  # Skip header row
            
            for row in rows:
                cols = row.find_all('td')
                
                if len(cols) < 6:
                    continue
                
                # Extract data from columns
                # Columns: Security Name | Issue Type | Issue Status | Open Date | Close Date | Exchange Platform
                security_name = clean_text(cols[0].get_text())
                issue_type = clean_text(cols[1].get_text())
                issue_status = clean_text(cols[2].get_text())
                exchange_platform = clean_text(cols[5].get_text()) if len(cols) > 5 else ""
                
                # Filter: Only IPO type and Live status
                if issue_type.upper() != 'IPO' or issue_status.upper() != 'LIVE':
                    continue
                
                # Extract link to IPO details page
                link_tag = cols[0].find('a')
                if not link_tag or 'href' not in link_tag.attrs:
                    logger.warning(f"No details link found for {security_name}")
                    continue
                
                details_url = link_tag['href']
                
                # Make absolute URL
                if details_url.startswith('DisplayIPO.aspx'):
                    details_url = f"https://www.bseindia.com/markets/publicIssues/{details_url}"
                elif not details_url.startswith('http'):
                    details_url = f"https://www.bseindia.com{details_url}"
                
                ipo_info = {
                    'security_name': security_name,
                    'exchange_platform': exchange_platform,
                    'details_url': details_url
                }
                
                ipos.append(ipo_info)
                logger.info(f"Found live IPO: {security_name} ({exchange_platform})")
            
            logger.info(f"Total live IPOs found: {len(ipos)}")
            
        except Exception as e:
            logger.error(f"Error parsing IPO list: {e}")
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
