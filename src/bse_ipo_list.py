import logging
import os
import sys
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from requests_html import HTMLSession

# Add src directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from utils import clean_text

logger = logging.getLogger(__name__)


class BSEIPOListScraper:
    """Scraper for BSE IPO list page using requests-html"""
    
    def __init__(self):
        self.session = HTMLSession()
    
    def get_live_ipos(self) -> List[Dict[str, str]]:
        """
        Fetch list of LIVE IPOs from BSE
        
        Returns:
            List of dictionaries containing IPO details
        """
        logger.info("Fetching live IPOs from BSE...")
        
        try:
            # Fetch the page
            response = self.session.get(Config.BSE_IPO_LIST_URL, timeout=30)
            
            # Render JavaScript (this executes Angular and waits for it)
            logger.info("Rendering JavaScript...")
            response.html.render(timeout=20, sleep=3)
            
            # Get the rendered HTML
            html = response.html.html
            
            return self._parse_ipo_list(html)
            
        except Exception as e:
            logger.error(f"Error fetching IPO list: {e}", exc_info=True)
            return []
        finally:
            self.session.close()
    
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
        Extract IPO Number (IPONo) from URL parameters for subscription data
        
        Args:
            details_url: URL of the IPO details page
        
        Returns:
            IPO Number or None
        """
        logger.info(f"Extracting IPO Number from: {details_url}")
        
        # Extract IPONo from URL (this is the correct ID for subscription page)
        # URL format: DisplayIPO.aspx?id=4362&type=IPO&idtype=1&status=L&IPONo=7504&startdt=16/Dec/2025
        if 'IPONo=' in details_url:
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(details_url)
                params = urllib.parse.parse_qs(parsed.query)
                
                # Use IPONo instead of id
                if 'IPONo' in params:
                    ipo_id = params['IPONo'][0]
                    logger.info(f"Extracted IPO Number from URL: {ipo_id}")
                    return ipo_id
                    
            except Exception as e:
                logger.error(f"Could not extract IPONo from URL: {e}")
        
        # Fallback: try to get 'id' if IPONo not found
        if 'id=' in details_url:
            try:
                import urllib.parse
                parsed = urllib.parse.urlparse(details_url)
                params = urllib.parse.parse_qs(parsed.query)
                if 'id' in params:
                    ipo_id = params['id'][0]
                    logger.warning(f"Using fallback 'id' parameter: {ipo_id}")
                    return ipo_id
            except Exception as e:
                logger.error(f"Could not extract id from URL: {e}")
        
        return None
    
    def _save_debug_html(self, html: str, filename: str):
        """Save HTML for debugging purposes"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Saved debug HTML to {filename}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML: {e}")
