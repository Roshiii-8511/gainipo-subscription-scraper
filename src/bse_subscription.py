import logging
import re
from typing import Optional, Dict
from bs4 import BeautifulSoup
from requests_html import HTMLSession

from config.config import Config
from utils import clean_text

logger = logging.getLogger(__name__)


class BSESubscriptionScraper:
    """Scraper for BSE subscription data"""
    
    def __init__(self):
        # Don't initialize session here, create fresh one for each request
        pass
    
    def get_subscription_data(self, ipo_id: str) -> Optional[Dict]:
        """
        Fetch subscription data for an IPO
        
        Args:
            ipo_id: BSE IPO Number (IPONo)
        
        Returns:
            Dictionary containing subscription data or None
        """
        url = f"{Config.BSE_SUBSCRIPTION_URL}?ID={ipo_id}&status=L"
        logger.info(f"Fetching subscription data from: {url}")
        
        # Create fresh session for each request
        session = HTMLSession()
        
        try:
            # Fetch and render the page
            response = session.get(url, timeout=30)
            
            # Render JavaScript to load the table
            logger.info("Rendering JavaScript to load subscription table...")
            response.html.render(timeout=20, sleep=3)
            
            html = response.html.html
            return self._parse_subscription_data(html)
            
        except Exception as e:
            logger.error(f"Error fetching subscription data: {e}", exc_info=True)
            return None
        finally:
            # Always close session
            try:
                session.close()
            except:
                pass
    
    def _parse_subscription_data(self, html: str) -> Optional[Dict]:
        """
        Parse subscription data from HTML
        
        Args:
            html: HTML content from subscription page
        
        Returns:
            Dictionary with subscription data or None
        """
        soup = BeautifulSoup(html, 'lxml')
        
        try:
            # Find the main subscription table
            tables = soup.find_all('table')
            
            subscription_table = None
            for table in tables:
                headers = table.find_all('th')
                header_text = ' '.join([h.get_text(strip=True) for h in headers])
                
                if 'Category' in header_text and 'shares' in header_text:
                    subscription_table = table
                    break
            
            if not subscription_table:
                logger.error("Could not find subscription table")
                self._save_debug_html(html, "bse_subscription_debug.html")
                return None
            
            logger.info("Found subscription table")
            
            # Extract subscription data
            data = {
                'qib': self._extract_category_data(subscription_table, 'QIB'),
                'nii': self._extract_category_data(subscription_table, 'NII'),
                'retail': self._extract_category_data(subscription_table, 'Retail'),
                'total': self._extract_total_data(subscription_table)
            }
            
            logger.info(f"Extracted subscription data: {data}")
            return data
            
        except Exception as e:
            logger.error(f"Error parsing subscription data: {e}", exc_info=True)
            self._save_debug_html(html, "bse_subscription_error.html")
            return None
    
    def _extract_category_data(self, table, category_name: str) -> Dict:
        """
        Extract subscription data for a specific category
        
        Args:
            table: BeautifulSoup table element
            category_name: Category to extract (QIB, NII, Retail)
        
        Returns:
            Dictionary with offered, bid, and times data
        """
        rows = table.find_all('tr')
        
        # Map category names to variations in the table
        category_patterns = {
            'QIB': ['Qualified Institutional Buyers', 'QIB', 'Institutional'],
            'NII': ['Non Institutional Investors', 'NII', 'Non-Institutional'],
            'Retail': ['Retail Individual Investors', 'Retail', 'Individual']
        }
        
        patterns = category_patterns.get(category_name, [category_name])
        
        for row in rows:
            cells = row.find_all('td')
            if not cells or len(cells) < 3:
                continue
            
            first_cell_text = clean_text(cells[0].get_text())
            
            # Check if this row matches the category
            if any(pattern.lower() in first_cell_text.lower() for pattern in patterns):
                try:
                    # Column indices: 0=Category, 1=Offered, 2=Bid, 3=Times
                    offered = clean_text(cells[1].get_text()) if len(cells) > 1 else '0'
                    bid = clean_text(cells[2].get_text()) if len(cells) > 2 else '0'
                    times = clean_text(cells[3].get_text()) if len(cells) > 3 else '0'
                    
                    # Parse numbers
                    offered = self._parse_number(offered)
                    bid = self._parse_number(bid)
                    times = self._parse_times(times)
                    
                    logger.info(f"{category_name} - Offered: {offered}, Bid: {bid}, Times: {times}")
                    
                    return {
                        'offered': offered,
                        'bid': bid,
                        'times': times
                    }
                except Exception as e:
                    logger.warning(f"Error extracting {category_name} data: {e}")
        
        logger.warning(f"Could not find {category_name} data in table")
        return {'offered': 0, 'bid': 0, 'times': 0.0}
    
    def _extract_total_data(self, table) -> Dict:
        """Extract total subscription data"""
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if not cells:
                continue
            
            first_cell = clean_text(cells[0].get_text())
            
            # Look for "Total" row
            if 'total' in first_cell.lower() and len(cells) >= 4:
                try:
                    offered = self._parse_number(clean_text(cells[1].get_text()))
                    bid = self._parse_number(clean_text(cells[2].get_text()))
                    times = self._parse_times(clean_text(cells[3].get_text()))
                    
                    logger.info(f"Total - Offered: {offered}, Bid: {bid}, Times: {times}")
                    
                    return {
                        'offered': offered,
                        'bid': bid,
                        'times': times
                    }
                except Exception as e:
                    logger.warning(f"Error extracting total data: {e}")
        
        logger.warning("Could not find total subscription data")
        return {'offered': 0, 'bid': 0, 'times': 0.0}
    
    def _parse_number(self, text: str) -> int:
        """Parse a number string, removing commas and converting to int"""
        try:
            # Remove commas and any non-digit characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', text)
            if not cleaned or cleaned == '-':
                return 0
            return int(float(cleaned))
        except:
            return 0
    
    def _parse_times(self, text: str) -> float:
        """Parse subscription times value"""
        try:
            # Remove any non-numeric characters except decimal point
            cleaned = re.sub(r'[^\d.]', '', text)
            if not cleaned or cleaned == '-':
                return 0.0
            return round(float(cleaned), 2)
        except:
            return 0.0
    
    def _save_debug_html(self, html: str, filename: str):
        """Save HTML for debugging"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Saved debug HTML to {filename}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML: {e}")
