# GAINIPO Subscription Scraper

Production-grade IPO subscription scraper for GAINIPO.com

Real-time BSE/NSE subscription tracking with Firestore integration and GitHub Actions automation.

## Quick Start

1. Install: `pip install -r requirements.txt`
2. Set GitHub Secrets: FIREBASE_CREDENTIALS, FIRESTORE_PROJECT_ID
3. Run: `python src/main.py`

## Features

- Real-time BSE & NSE IPO subscription data
- Intelligent routing (MainBoard vs SME)
- Firestore integration with auto-generated doc IDs
- Smart scheduling (trading hours only)
- State management for closed IPOs
- Robust error handling & logging

## Architecture

See docs/ARCHITECTURE.md for detailed design.

## Configuration

Trading hours: 10:00 AM - 5:30 PM IST, Mon-Fri
Scrape interval: Every 5 minutes
Random delay: +/- 30 seconds

## Firestore Document

{
  ipo_slug: string,
  board: MAINBOARD|SME,
  exchange: BSE|NSE,
  captured_at: ISO timestamp,
  categories: {
    QIB: {shares_bid, shares_offered, subscription},
    Retail: {...},
    NII: {BHNI, SHNI, subscription},
    Employee: {...}
  },
  total: {shares_bid, shares_offered, subscription}
}

## Business Rules

- Mainboard: BSE only
- BSE SME: BSE only
- NSE SME: NSE only
- Check accept_live_updates flag before scraping

## GitHub Actions

Scheduled workflow in .github/workflows/scraper.yml
Runs every 5 minutes during trading hours.

## Support

For issues, open a GitHub issue.

---

Built for GAINIPO.com - Indian IPO Tracking
