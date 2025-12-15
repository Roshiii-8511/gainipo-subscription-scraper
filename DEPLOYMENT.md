# Deployment Guide

Step-by-step instructions for deploying the IPO Subscription Scraper.

## 1. Clone the Repository

```bash
git clone https://github.com/Roshiii-8511/gainipo-subscription-scraper.git
cd gainipo-subscription-scraper
```

## 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

## 3. Get Firebase Service Account Key

1. Go to Firebase Console: https://console.firebase.google.com/
2. Select your project (e.g., gainipo-prod)
3. Go to Project Settings → Service Accounts
4. Click "Generate New Private Key"
5. Save the JSON key file - you'll use this for secrets

## 4. Configure GitHub Secrets

Navigate to: Your Repository → Settings → Secrets and variables → Actions

Create these secrets:

### 4.1 FIREBASE_CREDENTIALS
- Copy entire JSON service account key contents
- Paste as value for FIREBASE_CREDENTIALS secret

### 4.2 FIRESTORE_PROJECT_ID
- Value: Your Firebase project ID (e.g., "gainipo-prod")

## 5. Verify GitHub Actions is Enabled

1. Go to Repository → Actions tab
2. Confirm Actions are enabled
3. You should see the "IPO Subscription Scraper" workflow

## 6. Manual Trigger (Test)

1. Go to Actions → IPO Subscription Scraper
2. Click "Run workflow"
3. Click green "Run workflow" button
4. Wait 1-2 minutes for execution
5. Check logs for success/errors

## 7. Monitor Automated Execution

The workflow runs automatically:
- **Schedule**: Every 5 minutes
- **Days**: Monday-Friday
- **Time**: 10:00 AM - 5:30 PM IST (4:30 AM - 12:00 PM UTC)

To view runs:
1. Go to Actions tab
2. Click "IPO Subscription Scraper"
3. View latest run and logs

## 8. Verify Firestore Data

1. Go to Firebase Console
2. Select your project
3. Go to Firestore Database
4. Check collection: `ipo_subscriptions`
5. You should see documents like: `icici-prudential-amc-ipo__20251215_1000`

## Troubleshooting

### Scraper Not Running
- Check that GitHub Actions is enabled
- Verify cron schedule is correct
- Check workflow status in Actions tab

### Firestore Write Failures
- Verify FIREBASE_CREDENTIALS secret is set correctly
- Check that Firestore is enabled in Firebase Console
- Verify service account has Firestore write permissions

### No Data Being Scraped
- Check that BSE website structure hasn't changed
- Review scraper logs for HTML parsing errors
- Verify IPO list page is accessible

### Logging into GitHub Actions

To see detailed logs:
1. Go to Actions → Latest Run
2. Click "Run scraper" step
3. Expand logs to see detailed output

## Production Considerations

1. **Rate Limiting**: Add delays between requests if needed
2. **Error Notifications**: Set up GitHub Notifications for workflow failures
3. **Backup**: Regularly export Firestore data
4. **Monitoring**: Set up Firestore alerts for collection size/growth
5. **Documentation**: Keep IMPLEMENTATION_GUIDE.md updated

## Next: Implement Source Code Files

See IMPLEMENTATION_GUIDE.md for detailed module-by-module implementation with code examples.

All Python source files should follow the architecture described in README.md and implement the specifications provided in detailed code sections.

---

For issues or questions, open a GitHub issue or check the documentation.
