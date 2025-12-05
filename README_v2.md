# Indeed Job Scraper v2 - Enhanced Anti-Detection

An Indeed job scraper with built-in bot detection evasion.

## What's Different in v2

| Feature | v1 | v2 |
|---------|----|----|
| ChromeDriver | Standard Selenium | Undetected ChromeDriver |
| Scrolling | Basic | Human-like patterns |
| Delays | Fixed ranges | Adaptive with backoff |
| Block Detection | None | Automatic detection |
| Recovery | None | Exponential backoff |
| User Agents | Single | Rotating pool |
| Viewports | Fixed | Randomized |
| Proxy Support | No | Yes (optional) |

## Quick Start

### 1. Copy to your Codespace

Put `indeed_scraper_v2.py` in your repo root.

### 2. Install dependencies

```bash
pip install selenium undetected-chromedriver
```

### 3. Configure your search URLs

Open `indeed_scraper_v2.py` and find this section near the top:

```python
SEARCH_URLS = [
    "https://www.indeed.com/jobs?q=sap+developer&l=remote&sort=date",
    # Add more URLs here:
    # "https://www.indeed.com/jobs?q=python+developer&l=remote&sort=date",
]
```

Just paste Indeed search URLs from your browser.

### 4. Run in test mode first

```bash
python indeed_scraper_v2.py
```

This scrapes only 3 jobs from page 1 to verify everything works.

### 5. Run full scrape

Edit the file and set:
```python
TEST_MODE = False
```

Then run again.

## Output

CSV saved to root folder: `indeed_jobs_YYYYMMDD_HHMMSS.csv`

Columns:
- Job Title
- Company
- Work Setting
- Job Type
- Pay
- Location
- URL
- Search URL (which search it came from)

## If You Get Blocked

The scraper automatically:
1. Detects blocks (CAPTCHAs, redirects, etc.)
2. Backs off with increasing delays
3. Stops after 3 consecutive failures to protect your IP

If you're getting blocked frequently, try:

1. **Increase delays** - Edit these values higher:
   ```python
   DELAY_BETWEEN_JOBS_MIN = 4.0  # was 2.5
   DELAY_BETWEEN_JOBS_MAX = 8.0  # was 5.0
   ```

2. **Reduce pages per URL**:
   ```python
   MAX_PAGES = 3  # was 7
   ```

3. **Add a proxy** (optional) - Set environment variable:
   ```bash
   export INDEED_PROXY="http://username:password@proxy-host:port"
   python indeed_scraper_v2.py
   ```

## Proxy Services (if needed)

If Indeed blocks you consistently, a residential proxy helps. Some options:

- **Bright Data** - Most reliable, starts ~$15/GB
- **Oxylabs** - Good for job sites
- **SmartProxy** - Budget option ~$8/GB

You only need a proxy if direct connection keeps getting blocked.

## Troubleshooting

**"Chrome not found"**
```bash
# Ubuntu/Codespace
sudo apt-get update && sudo apt-get install -y chromium-browser
```

**"undetected-chromedriver not found"**
```bash
pip install undetected-chromedriver --upgrade
```

**Jobs extracted but missing data**
Indeed's HTML changes frequently. The selectors may need updating. Open an issue with the job URL that's failing.
