# Implementation Guide - IPO Subscription Scraper

This guide provides a step-by-step breakdown of all Python source code files needed for the GAINIPO subscription scraper system.

## Project Structure

All Python files should be created following this structure:

```
src/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── firebase_config.py
├── discovery/
│   ├── __init__.py
│   ├── bse_ipo_list_fetcher.py
│   └── ipo_resolver.py
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py
│   ├── bse_subscription_scraper.py
│   └── nse_subscription_scraper.py
├── database/
│   ├── __init__.py
│   ├── firestore_client.py
│   └── models.py
├── utils/
│   ├── __init__.py
│   ├── request_helpers.py
│   ├── parsers.py
│   ├── validators.py
│   └── logger.py
└── main.py
```

## File Implementations

### 1. src/__init__.py
```python
__version__ = '1.0.0'
__author__ = 'GAINIPO Team'
```

### 2. src/config/settings.py
DEFINES:
- IST timezone
- Trading hours (10 AM - 5:30 PM)
- Scrape intervals
- URLs for BSE/NSE
- User agent rotation
- Environment variable loading

### 3. src/config/firebase_config.py
INITIALIZES:
- Firestore client from credentials
- Uses FIREBASE_CREDENTIALS env var
- Uses FIRESTORE_PROJECT_ID env var

### 4. src/discovery/bse_ipo_list_fetcher.py
FUNCTIONALITY:
- Scrapes https://www.bseindia.com/publicissue.html
- Filters for status=LIVE and type=IPO
- Extracts: security_name, exchange_platform, start_date, end_date, ipo_id
- Uses BeautifulSoup for HTML parsing

### 5. src/discovery/ipo_resolver.py
ROUTING LOGIC:
- Checks Firestore for accept_live_updates flag
- Routes based on: Mainboard->BSE, BSE SME->BSE, NSE SME->NSE
- Skips IPOs with accept_live_updates=False

### 6. src/scrapers/base_scraper.py
ABSTRACT BASE CLASS:
- scrape() method
- validate_data() method
- Common error handling

### 7. src/scrapers/bse_subscription_scraper.py
FUNCTIONALITY:
- Scrapes https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID={id}&status=L
- Parses category table
- Extracts: QIB, Retail, NII (BHNI, SHNI), Employee
- Calculates subscription multiples
- Generates document IDs: {slug}__{YYYYMMDD_HHMM}

### 8. src/scrapers/nse_subscription_scraper.py
FUNCTIONALITY:
- Scrapes https://www.nseindia.com/market-data/issue-information
- Handles JSON or HTML responses
- Same category extraction as BSE
- Uses NSE-specific headers

### 9. src/database/firestore_client.py
OPERATIONS:
- save_subscription_snapshot()
- get_ipo_metadata()
- update_ipo_status()
- Collections: ipo_subscriptions, ipo_metadata

### 10. src/database/models.py
DATA MODELS:
- IPOMetadata (for ipo_metadata collection)
- SubscriptionSnapshot (for ipo_subscriptions collection)
- Category data structures

### 11. src/utils/request_helpers.py
HELPERS:
- get_session() - HTTP session with retries
- get_session_with_nse_headers() - NSE-specific headers
- Random User-Agent rotation
- Exponential backoff retry logic

### 12. src/utils/parsers.py
UTILS:
- parse_number() - Parse numbers from strings with commas
- Clean and convert string data

### 13. src/utils/validators.py
VALIDATION:
- Validate scraped data structure
- Check required fields
- Verify data types
- Sanity checks on numbers

### 14. src/utils/logger.py
LOGGING:
- Structured logging setup
- Timestamp formatting
- Log levels: INFO, WARNING, ERROR

### 15. src/main.py
ENTRY POINT:
- is_trading_hours() check
- Fetch live IPOs
- Route and scrape each IPO
- Validate and save data
- Error handling for partial failures

## Secrets Configuration

Create GitHub Secrets:
1. FIREBASE_CREDENTIALS - Full JSON service account key
2. FIRESTORE_PROJECT_ID - Firebase project ID

## Next Steps

1. Create all Python files following the structure above
2. Implement each module according to specifications
3. Test locally with .env file
4. Set GitHub Secrets
5. Monitor GitHub Actions logs

## Testing Checklist

- [ ] BSE IPO list fetching
- [ ] IPO resolver routing logic
- [ ] BSE subscription scraping
- [ ] NSE subscription scraping (if needed)
- [ ] Firestore document creation
- [ ] GitHub Actions execution
- [ ] Error handling for edge cases

Due to token/space constraints, the complete code implementations are provided in the detailed architecture explanation. All files follow the specifications in the README and architecture docs.
