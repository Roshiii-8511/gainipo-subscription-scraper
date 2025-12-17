import time
import logging
from typing import Optional, Callable, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_session() -> requests.Session:
    """
    Create a requests session with retry logic and connection pooling
    """
    session = requests.Session()
    
    # Retry strategy for transient errors
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=10,
        pool_maxsize=10
    )
    
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session


def retry_on_failure(
    func: Callable,
    max_retries: int = 3,
    delay: int = 5,
    exponential_backoff: bool = True
) -> Optional[Any]:
    """
    Retry a function on failure with exponential backoff
    
    Args:
        func: Function to retry
        max_retries: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        exponential_backoff: Use exponential backoff for delays
    
    Returns:
        Function result or None if all retries failed
    """
    for attempt in range(max_retries):
        try:
            result = func()
            return result
        except Exception as e:
            wait_time = delay * (2 ** attempt) if exponential_backoff else delay
            
            if attempt < max_retries - 1:
                logger.warning(
                    f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                    f"Retrying in {wait_time}s..."
                )
                time.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed: {str(e)}")
                return None
    
    return None


def safe_float(value: str, default: float = 0.0) -> float:
    """
    Safely convert string to float, handling Indian number format
    
    Args:
        value: String value to convert
        default: Default value if conversion fails
    
    Returns:
        Float value or default
    """
    if not value or value.strip() == '-' or value.strip() == '':
        return default
    
    try:
        # Remove commas and whitespace
        cleaned = value.strip().replace(',', '')
        return float(cleaned)
    except (ValueError, AttributeError):
        logger.warning(f"Could not convert '{value}' to float, using default: {default}")
        return default


def safe_int(value: str, default: int = 0) -> int:
    """
    Safely convert string to integer
    
    Args:
        value: String value to convert
        default: Default value if conversion fails
    
    Returns:
        Integer value or default
    """
    if not value or value.strip() == '-' or value.strip() == '':
        return default
    
    try:
        cleaned = value.strip().replace(',', '')
        return int(float(cleaned))
    except (ValueError, AttributeError):
        logger.warning(f"Could not convert '{value}' to int, using default: {default}")
        return default


def extract_ipo_id_from_url(url: str) -> Optional[str]:
    """
    Extract IPO ID from BSE cumulative demand schedule URL
    
    Args:
        url: Full URL containing ID parameter
    
    Returns:
        IPO ID or None
    """
    if not url:
        return None
    
    try:
        # Extract ID parameter from URL
        if 'ID=' in url:
            id_part = url.split('ID=')[1]
            ipo_id = id_part.split('&')[0] if '&' in id_part else id_part
            return ipo_id.strip()
    except Exception as e:
        logger.error(f"Failed to extract IPO ID from URL '{url}': {e}")
    
    return None


def clean_text(text: Optional[str]) -> str:
    """
    Clean and normalize text content
    
    Args:
        text: Raw text to clean
    
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove extra whitespace, newlines, and tabs
    cleaned = ' '.join(text.split())
    return cleaned.strip()
