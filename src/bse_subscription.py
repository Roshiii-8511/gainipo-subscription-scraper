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
        
        session = HTMLSession()
        
        try:
            response = session.get(url, timeout=30)
            
            logger.info("Rendering JavaScript to load subscription table...")
            response.html.render(timeout=20, sleep=3)
            
            html = response.html.html
            return self._parse_subscription_data(html)
            
        except Exception as e:
            logger.error(f"Error fetching subscription data: {e}", exc_info=True)
            return None
        finally:
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
            # Find all tables
            tables = soup.find_all('table')
            
            subscription_table = None
            for table in tables:
                # Check if this table has the subscription data structure
                # Look for specific text in table cells
                table_text = table.get_text()
                
                # The subscription table contains these specific category names
                if all(keyword in table_text for keyword in ['QIBs', 'NII', 'Retail', 'shares offered']):
                    subscription_table = table
                    logger.info("Found subscription table by content matching")
                    break
            
            if not subscription_table:
                logger.error("Could not find subscription table")
                self._save_debug_html(html, "bse_subscription_debug.html")
                return None
            
            logger.info("Parsing subscription table rows...")
            
            # Extract data by finding specific rows
            data = {
                'qib': self._extract_category_data_v2(subscription_table, 'QIB'),
                'nii': self._extract_category_data_v2(subscription_table, 'NII'),
                'retail': self._extract_category_data_v2(subscription_table, 'Retail'),
                'total': self._extract_total_data_v2(subscription_table)
            }
            
            logger.info(f"Extracted subscription data: {data}")
            return data
            
        except Exception as e:
            logger.error(f"Error parsing subscription data: {e}", exc_info=True)
            self._save_debug_html(html, "bse_subscription_error.html")
            return None
    
    def _extract_category_data_v2(self, table, category_name: str) -> Dict:
        """
        Extract subscription data for a specific category (improved version)
        
        Args:
            table: BeautifulSoup table element
            category_name: Category to extract (QIB, NII, Retail)
        
        Returns:
            Dictionary with offered, bid, and times data
        """
        rows = table.find_all('tr')
        
        # Simplified category patterns
        category_keywords = {
            'QIB': 'QIB',
            'NII': 'NIIS',  # Match "NIIS" in "Non Institutional Investors(NIIS)"
            'Retail': 'RIIs'  # Match "RIIs" in "Retail Individual Investors (RIIs)"
        }
        
        keyword = category_keywords.get(category_name, category_name)
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 4:
                continue
            
            # Get first cell text
            first_cell_text = clean_text(cells[0].get_text())
            
            # Check if this row contains our keyword
            if keyword in first_cell_text:
                try:
                    # BSE table structure:
                    # Col 0: Sr.No | Col 1: Category | Col 2: Offered | Col 3: Bid | Col 4: Times
                    # But sometimes Sr.No and Category are in same or separate cells
                    
                    # Try to find the cells with data
                    # Usually: cells[0]=number, cells[1]=category, cells[2]=offered, cells[3]=bid, cells[4]=times
                    # OR: cells[0]=category (with number), cells[1]=offered, cells[2]=bid, cells[3]=times
                    
                    if len(cells) >= 5:
                        # Format 1: Sr.No separate
                        offered_text = clean_text(cells[2].get_text())
                        bid_text = clean_text(cells[3].get_text())
                        times_text = clean_text(cells[4].get_text())
                    else:
                        # Format 2: Sr.No + Category together
                        offered_text = clean_text(cells[1].get_text())
                        bid_text = clean_text(cells[2].get_text())
                        times_text = clean_text(cells[3].get_text())
                    
                    offered = self._parse_number(offered_text)
                    bid = self._parse_number(bid_text)
                    times = self._parse_times(times_text)
                    
                    logger.info(f"{category_name} - Offered: {offered}, Bid: {bid}, Times: {times}")
                    
                    return {
                        'offered': offered,
                        'bid': bid,
                        'times': times
                    }
                except Exception as e:
                    logger.warning(f"Error extracting {category_name} data from row: {e}")
                    continue
        
        logger.warning(f"Could not find {category_name} data in table")
        return {'offered': 0, 'bid': 0, 'times': 0.0}
    
    def _extract_total_data_v2(self, table) -> Dict:
        """Extract total subscription data (improved version)"""
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 4:
                continue
            
            # Look for row containing "Total" (case-insensitive)
            row_text = row.get_text().lower()
            
            if 'total' in row_text and 'institutional' not in row_text:
                try:
                    # Find cells with numbers
                    if len(cells) >= 5:
                        offered = self._parse_number(clean_text(cells[2].get_text()))
                        bid = self._parse_number(clean_text(cells[3].get_text()))
                        times = self._parse_times(clean_text(cells[4].get_text()))
                    else:
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
            # Remove all non-digit characters except decimal point
            cleaned = re.sub(r'[^\d]', '', text)
            if not cleaned or cleaned == '-':
                return 0
            return int(cleaned)
        except:
            return 0
    
    def _parse_times(self, text: str) -> float:
        """Parse subscription times value"""
        try:
            # Remove commas, keep only digits and decimal point
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
