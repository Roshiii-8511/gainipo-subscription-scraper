import logging
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from config.config import Config
from utils import create_session, retry_on_failure, safe_float, safe_int, clean_text

logger = logging.getLogger(__name__)


class BSESubscriptionScraper:
    """Scraper for BSE IPO subscription data"""
    
    def __init__(self):
        self.session = create_session()
        self.session.headers.update(Config.HEADERS)
    
    def get_subscription_data(self, ipo_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch subscription data for a specific IPO
        
        Args:
            ipo_id: BSE IPO ID
        
        Returns:
            Dictionary containing subscription data or None
        """
        url = f"{Config.BSE_SUBSCRIPTION_BASE}?ID={ipo_id}&status=L"
        logger.info(f"Fetching subscription data from: {url}")
        
        def fetch():
            response = self.session.get(url, timeout=Config.REQUEST_TIMEOUT)
            response.raise_for_status()
            return response
        
        response = retry_on_failure(fetch, max_retries=Config.MAX_RETRIES)
        
        if not response:
            logger.error(f"Failed to fetch subscription data for IPO ID: {ipo_id}")
            return None
        
        return self._parse_subscription_data(response.text)
    
    def _parse_subscription_data(self, html: str) -> Optional[Dict[str, Any]]:
        """
        Parse subscription data from HTML
        
        Args:
            html: HTML content from subscription page
        
        Returns:
            Dictionary containing parsed subscription data
        """
        soup = BeautifulSoup(html, 'lxml')
        
        try:
            # Find the subscription table
            # Table ID: ContentPlaceHolder1_gvData
            table = soup.find('table', {'id': 'ContentPlaceHolder1_gvData'})
            
            if not table:
                logger.error("Could not find subscription table")
                self._save_debug_html(html, "bse_subscription_debug.html")
                return None
            
            rows = table.find_all('tr')
            
            if len(rows) < 2:
                logger.error("Subscription table has insufficient rows")
                return None
            
            # Initialize category data
            categories = {
                'QIB': {'shares_offered': 0, 'shares_bid': 0, 'times': 0.0, 'applications': 0},
                'NII': {'shares_offered': 0, 'shares_bid': 0, 'times': 0.0, 'applications': 0},
                'bNII': {'shares_offered': 0, 'shares_bid': 0, 'times': 0.0, 'applications': 0},
                'sNII': {'shares_offered': 0, 'shares_bid': 0, 'times': 0.0, 'applications': 0},
                'Retail': {'shares_offered': 0, 'shares_bid': 0, 'times': 0.0, 'applications': 0},
                'Employee': {'shares_offered': 0, 'shares_bid': 0, 'times': 0.0, 'applications': 0},
            }
            
            # Parse each row (skip header)
            for row in rows[1:]:
                cols = row.find_all('td')
                
                if len(cols) < 5:
                    continue
                
                category = clean_text(cols[0].get_text())
                shares_offered = safe_int(cols[1].get_text())
                shares_bid = safe_int(cols[2].get_text())
                times = safe_float(cols[3].get_text())
                applications = safe_int(cols[4].get_text())
                
                # Map category names (BSE uses different variations)
                category_key = self._normalize_category(category)
                
                if category_key and category_key in categories:
                    categories[category_key] = {
                        'shares_offered': shares_offered,
                        'shares_bid': shares_bid,
                        'times': times,
                        'applications': applications
                    }
            
            # Compute totals manually (don't trust total row)
            total_shares_offered = sum(cat['shares_offered'] for cat in categories.values())
            total_shares_bid = sum(cat['shares_bid'] for cat in categories.values())
            total_applications = sum(cat['applications'] for cat in categories.values())
            total_times = (total_shares_bid / total_shares_offered) if total_shares_offered > 0 else 0.0
            
            subscription_data = {
                'categories': categories,
                'totals': {
                    'shares_offered': total_shares_offered,
                    'shares_bid': total_shares_bid,
                    'times': round(total_times, 2),
                    'applications': total_applications
                }
            }
            
            logger.info(f"Successfully parsed subscription data. Total times: {total_times:.2f}x")
            return subscription_data
            
        except Exception as e:
            logger.error(f"Error parsing subscription data: {e}")
            self._save_debug_html(html, "bse_subscription_error.html")
            return None
    
    def _normalize_category(self, category: str) -> Optional[str]:
        """
        Normalize category name to standard key
        
        Args:
            category: Raw category name from BSE
        
        Returns:
            Normalized category key or None
        """
        category_upper = category.upper().strip()
        
        # Category mapping
        mapping = {
            'QIB': 'QIB',
            'QUALIFIED INSTITUTIONAL BUYERS': 'QIB',
            'NII': 'NII',
            'NON INSTITUTIONAL INVESTORS': 'NII',
            'BNII': 'bNII',
            'B NII': 'bNII',
            'BIG NII': 'bNII',
            'SNII': 'sNII',
            'S NII': 'sNII',
            'SMALL NII': 'sNII',
            'RETAIL': 'Retail',
            'RETAIL INDIVIDUAL INVESTORS': 'Retail',
            'EMPLOYEE': 'Employee',
            'EMPLOYEES': 'Employee',
        }
        
        for key, value in mapping.items():
            if key in category_upper:
                return value
        
        # Log unknown categories
        if 'TOTAL' not in category_upper:
            logger.warning(f"Unknown category: {category}")
        
        return None
    
    def _save_debug_html(self, html: str, filename: str):
        """Save HTML for debugging purposes"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"Saved debug HTML to {filename}")
        except Exception as e:
            logger.error(f"Failed to save debug HTML: {e}")
