# GainIPO Subscription Scraper

This repository contains the **live IPO subscription scraper** used by GainIPO.

## What this scraper does

- Scrapes **live IPO subscription data only**
- Supports:
  - Mainboard IPOs → **BSE only**
  - SME IPOs → **Listing exchange only (BSE / NSE)**
- Runs automatically every **5 minutes**
- Stores raw exchange snapshots in **Firebase Firestore**
- Never overwrites closed IPO data
- Uses **GitHub Secrets** for secure authentication

---

## Data Source

### BSE
- Cumulative Demand Schedule  
  `https://www.bseindia.com/markets/publicIssues/CummDemandSchedule.aspx`

### NSE (SME only)
- Issue Information page  
  `https://www.nseindia.com/market-data/issue-information`

---

## Firestore Collections

### `ipos` (input / control)
Each IPO document must contain:

```json
{
  "slug": "icici-prudential-amc-ipo",
  "board": "MAINBOARD",
  "listing_exchange": "BSE",
  "status": "OPEN",
  "accept_live_updates": true,
  "bse_ipo_id": 7497,
  "nse_symbol": "ICICIAMC"
}
