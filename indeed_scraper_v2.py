#!/usr/bin/env python3
"""
Indeed Job Scraper v2 - Enhanced Anti-Detection
================================================
Features:
- Undetected ChromeDriver (bypasses bot detection)
- Human-like behavior (random scrolling, variable delays)
- Block detection with smart backoff
- Optional proxy support
- User agent rotation
- Easy URL configuration

Author: Fast Dolphin Growth Team
"""

import csv
import random
import re
import time
import os
from datetime import datetime
from typing import List, Dict, Optional


# =============================================================================
# ███████╗███████╗ █████╗ ██████╗  ██████╗██╗  ██╗    ██╗   ██╗██████╗ ██╗     ███████╗
# ██╔════╝██╔════╝██╔══██╗██╔══██╗██╔════╝██║  ██║    ██║   ██║██╔══██╗██║     ██╔════╝
# ███████╗█████╗  ███████║██████╔╝██║     ███████║    ██║   ██║██████╔╝██║     ███████╗
# ╚════██║██╔══╝  ██╔══██║██╔══██╗██║     ██╔══██║    ██║   ██║██╔══██╗██║     ╚════██║
# ███████║███████╗██║  ██║██║  ██║╚██████╗██║  ██║    ╚██████╔╝██║  ██║███████╗███████║
# ╚══════╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝     ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
#
# ADD YOUR INDEED SEARCH URLS BELOW
# Just copy/paste the URL from your browser after doing a search on Indeed
# =============================================================================

SEARCH_URLS = [
    # Example URLs - replace with your own searches
    "https://www.indeed.com/jobs?q=sap+developer&l=remote&sc=0kf%3Aattr%28DSQF7%29attr%28NJXCK%29%3B&radius=25&sort=date",
    
    # Add more URLs here:
    # "https://www.indeed.com/jobs?q=python+developer&l=remote&sort=date",
    # "https://www.indeed.com/jobs?q=data+engineer&l=Texas&sort=date",
]

# =============================================================================
# SETTINGS - Adjust these as needed
# =============================================================================

# How many pages to scrape per URL (Indeed shows ~15 jobs per page)
MAX_PAGES = 7

# Test mode: Set to True for quick testing (only 3 jobs from page 1)
# Set to False for full scraping
TEST_MODE = True

# Output filename (saved to root folder)
OUTPUT_FILE = f"indeed_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# =============================================================================
# ADVANCED SETTINGS - Only change if you know what you're doing
# =============================================================================

# Delays (in seconds) - Higher = safer but slower
DELAY_BETWEEN_JOBS_MIN = 2.5
DELAY_BETWEEN_JOBS_MAX = 5.0
DELAY_BETWEEN_PAGES_MIN = 4.0
DELAY_BETWEEN_PAGES_MAX = 7.0
DELAY_AFTER_LOAD_MIN = 3.0
DELAY_AFTER_LOAD_MAX = 5.0

# Block detection settings
MAX_CONSECUTIVE_FAILURES = 3  # Stop after this many failures in a row
BACKOFF_MULTIPLIER = 2.0      # How much to increase delay after each failure

# Proxy (optional) - Set via environment variable INDEED_PROXY
# Example: export INDEED_PROXY="http://username:password@proxy-host:port"
PROXY = os.environ.get("INDEED_PROXY", None)

# =============================================================================
# END OF CONFIGURATION - Code below
# =============================================================================

# Rotating user agents (real browser fingerprints)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]

# Viewport sizes to randomize
VIEWPORT_SIZES = [
    (1920, 1080),
    (1366, 768),
    (1536, 864),
    (1440, 900),
    (1280, 720),
]


class IndeedScraperV2:
    """Enhanced Indeed scraper with anti-detection measures."""
    
    def __init__(self):
        self.driver = None
        self.jobs_data: List[Dict] = []
        self.consecutive_failures = 0
        self.current_delay_multiplier = 1.0
        self.blocked = False
        
    def setup_driver(self):
        """Initialize undetected ChromeDriver with stealth settings."""
        try:
            import undetected_chromedriver as uc
        except ImportError:
            print("⚠ undetected-chromedriver not installed. Installing...")
            import subprocess
            subprocess.check_call(["pip", "install", "undetected-chromedriver", "-q"])
            import undetected_chromedriver as uc
        
        # Random viewport size
        viewport = random.choice(VIEWPORT_SIZES)
        
        # Chrome options
        options = uc.ChromeOptions()
        options.add_argument(f"--window-size={viewport[0]},{viewport[1]}")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        
        # Add proxy if configured
        if PROXY:
            options.add_argument(f"--proxy-server={PROXY}")
            print(f"✓ Using proxy: {PROXY.split('@')[-1] if '@' in PROXY else PROXY}")
        
        # Random user agent
        user_agent = random.choice(USER_AGENTS)
        options.add_argument(f"--user-agent={user_agent}")
        
        # Initialize undetected chromedriver
        self.driver = uc.Chrome(options=options, headless=True)
        
        # Set page load timeout
        self.driver.set_page_load_timeout(30)
        
        print(f"✓ Browser initialized ({viewport[0]}x{viewport[1]})")
        
    def random_delay(self, min_sec: float, max_sec: float):
        """Sleep for a random duration with current multiplier applied."""
        base_delay = random.uniform(min_sec, max_sec)
        actual_delay = base_delay * self.current_delay_multiplier
        time.sleep(actual_delay)
        
    def human_scroll(self):
        """Simulate human-like scrolling behavior."""
        # Scroll down in chunks with random pauses
        scroll_height = self.driver.execute_script("return document.body.scrollHeight")
        current_position = 0
        
        while current_position < scroll_height * 0.3:  # Scroll about 30% of page
            scroll_amount = random.randint(100, 300)
            current_position += scroll_amount
            self.driver.execute_script(f"window.scrollTo(0, {current_position});")
            time.sleep(random.uniform(0.1, 0.3))
        
        # Sometimes scroll back up a bit (like a human would)
        if random.random() < 0.3:
            scroll_back = random.randint(50, 150)
            self.driver.execute_script(f"window.scrollBy(0, -{scroll_back});")
            time.sleep(random.uniform(0.2, 0.5))
            
    def scroll_to_element(self, element):
        """Scroll element into view with human-like behavior."""
        # First, scroll to general area
        self.driver.execute_script(
            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
            element
        )
        time.sleep(random.uniform(0.3, 0.6))
        
        # Add small random offset (humans don't scroll perfectly)
        offset = random.randint(-30, 30)
        self.driver.execute_script(f"window.scrollBy(0, {offset});")
        time.sleep(random.uniform(0.1, 0.3))
        
    def detect_block(self) -> bool:
        """Check if we've been blocked or hit a CAPTCHA."""
        page_source = self.driver.page_source.lower()
        current_url = self.driver.current_url.lower()
        
        block_indicators = [
            "captcha",
            "robot",
            "automated",
            "unusual traffic",
            "verify you're human",
            "access denied",
            "blocked",
            "security check",
        ]
        
        for indicator in block_indicators:
            if indicator in page_source or indicator in current_url:
                return True
        
        # Check if we got redirected away from Indeed
        if "indeed.com" not in current_url:
            return True
            
        return False
    
    def handle_failure(self):
        """Handle a scraping failure with exponential backoff."""
        self.consecutive_failures += 1
        self.current_delay_multiplier *= BACKOFF_MULTIPLIER
        
        if self.consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
            print(f"\n⛔ Too many consecutive failures ({self.consecutive_failures}). Stopping to avoid ban.")
            self.blocked = True
            return False
        
        wait_time = 10 * self.current_delay_multiplier
        print(f"  ⚠ Failure #{self.consecutive_failures}. Backing off for {wait_time:.0f}s...")
        time.sleep(wait_time)
        return True
    
    def handle_success(self):
        """Reset failure counters on success."""
        self.consecutive_failures = 0
        self.current_delay_multiplier = max(1.0, self.current_delay_multiplier * 0.9)  # Slowly reduce multiplier
        
    def extract_location_from_description(self, description_html: str) -> str:
        """Extract location from job description text."""
        if not description_html:
            return ""
        
        patterns = [
            r'<b>Location:?</b>\s*([^<\n]+)',
            r'Location:?\s*</b>\s*([^<\n]+)',
            r'Location:?\s*([^\n<]{5,50})',
            r'100%\s*Remote\s*[–-]\s*([A-Z]{2,}|\w+)',
            r'Remote\s*[–-]\s*([A-Z]{2,}|\w+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description_html, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                # Clean up common artifacts
                location = re.sub(r'<[^>]+>', '', location)  # Remove HTML tags
                location = location.split('<')[0].strip()     # Take text before any tag
                if len(location) > 3:  # Minimum reasonable location length
                    return location[:100]  # Cap length
        
        return ""
    
    def extract_job_details(self, job_card, index: int) -> Dict:
        """Click on a job card and extract details from the side panel."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import (
            TimeoutException, 
            NoSuchElementException,
            StaleElementReferenceException,
            ElementClickInterceptedException
        )
        
        job_data = {
            "job_title": "",
            "company": "",
            "work_setting": "",
            "job_type": "",
            "pay": "",
            "location": "",
            "url": "",
            "search_url": ""
        }
        
        try:
            # Find the clickable job title link
            title_link = job_card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle")
            job_title_preview = title_link.text.strip()[:50]
            
            print(f"  [{index}] {job_title_preview}...", end=" ", flush=True)
            
            # Human-like scroll to element
            self.scroll_to_element(title_link)
            
            # Random delay before click (humans don't click instantly)
            time.sleep(random.uniform(0.5, 1.5))
            
            # Click with fallback to JS click
            try:
                title_link.click()
            except ElementClickInterceptedException:
                self.driver.execute_script("arguments[0].click();", title_link)
            
            # Wait for panel to load
            self.random_delay(1.5, 2.5)
            
            # Check for blocks
            if self.detect_block():
                print("🚫 BLOCKED")
                self.handle_failure()
                return job_data
            
            # Get current URL (changes when job is selected)
            job_data["url"] = self.driver.current_url
            
            # Wait for detail panel
            try:
                WebDriverWait(self.driver, 8).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 
                        "[data-testid='jobsearch-ViewJobComponent'], .jobsearch-ViewJobLayout, #jobDescriptionText"))
                )
            except TimeoutException:
                print("⏳ panel timeout")
                return job_data
            
            # === EXTRACT JOB TITLE ===
            title_selectors = [
                "h2.jobsearch-JobInfoHeader-title span",
                "h1[data-testid='jobsearch-JobInfoHeader-title'] span",
                ".jobsearch-JobInfoHeader-title span",
                "h2.jobTitle span"
            ]
            for selector in title_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    job_data["job_title"] = elem.text.replace(" - job post", "").strip()
                    break
                except NoSuchElementException:
                    continue
            
            if not job_data["job_title"]:
                job_data["job_title"] = title_link.text.strip()
            
            # === EXTRACT COMPANY ===
            company_selectors = [
                "[data-testid='inlineHeader-companyName'] a",
                "[data-testid='inlineHeader-companyName']",
                ".jobsearch-JobInfoHeader-companyNameLink a",
                ".css-1h4l2d7",
                "[data-company-name='true']"
            ]
            for selector in company_selectors:
                try:
                    elem = self.driver.find_element(By.CSS_SELECTOR, selector)
                    job_data["company"] = elem.text.strip()
                    break
                except NoSuchElementException:
                    continue
            
            # === EXTRACT METADATA (Work Setting, Job Type, Pay) ===
            metadata_selectors = [
                ".js-match-insights-provider-18uwqyc",
                "[class*='match-insights-provider'] span",
                ".jobsearch-JobMetadataHeader-item",
                "[data-testid='attribute_snippet_testid']"
            ]
            
            for selector in metadata_selectors:
                try:
                    spans = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for span in spans:
                        text = span.text.strip()
                        if not text or len(text) < 3:
                            continue
                        
                        text_lower = text.lower()
                        
                        # Work setting detection
                        if any(s in text_lower for s in ["remote", "hybrid", "on-site", "in-person", "in person"]):
                            if not job_data["work_setting"]:
                                job_data["work_setting"] = text
                        
                        # Job type detection
                        elif any(t in text_lower for t in ["contract", "full-time", "full time", "part-time", 
                                                            "part time", "temporary", "internship", "permanent"]):
                            if not job_data["job_type"]:
                                job_data["job_type"] = text
                        
                        # Pay detection
                        elif "$" in text or any(p in text_lower for p in ["hour", "year", "month", "week", "salary", "annually"]):
                            if not job_data["pay"]:
                                job_data["pay"] = text
                except NoSuchElementException:
                    continue
            
            # === EXTRACT LOCATION FROM DESCRIPTION ===
            try:
                desc_elem = self.driver.find_element(By.CSS_SELECTOR, "#jobDescriptionText, .jobsearch-JobComponent-description")
                desc_html = desc_elem.get_attribute("innerHTML")
                job_data["location"] = self.extract_location_from_description(desc_html)
            except NoSuchElementException:
                pass
            
            # Success!
            self.handle_success()
            status = "✓" if job_data["company"] else "△"
            print(f"{status} {job_data['company'][:20] if job_data['company'] else 'no company'}")
            
        except StaleElementReferenceException:
            print("⚠ stale element")
        except Exception as e:
            print(f"✗ {str(e)[:30]}")
            
        return job_data
    
    def get_job_cards(self):
        """Get all job card elements on the current page."""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.common.exceptions import TimeoutException
        
        try:
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".job_seen_beacon"))
            )
            return self.driver.find_elements(By.CSS_SELECTOR, ".job_seen_beacon")
        except TimeoutException:
            return []
    
    def get_next_page_url(self, current_page: int) -> Optional[str]:
        """Find the URL for the next page of results."""
        from selenium.webdriver.common.by import By
        from selenium.common.exceptions import NoSuchElementException
        
        next_page = current_page + 1
        selectors = [
            f'a[data-testid="pagination-page-{next_page}"]',
            f'a[aria-label="{next_page}"]',
            'a[data-testid="pagination-page-next"]',
        ]
        
        for selector in selectors:
            try:
                link = self.driver.find_element(By.CSS_SELECTOR, selector)
                return link.get_attribute("href")
            except NoSuchElementException:
                continue
        
        return None
    
    def scrape_page(self, page_num: int, search_url: str) -> int:
        """Scrape all jobs on the current page."""
        print(f"\n  📄 Page {page_num}")
        
        # Human-like scrolling to load lazy content
        self.human_scroll()
        time.sleep(random.uniform(0.5, 1.0))
        
        job_cards = self.get_job_cards()
        
        if not job_cards:
            print("  ⚠ No job cards found")
            return 0
        
        print(f"  Found {len(job_cards)} jobs")
        
        # Limit in test mode
        if TEST_MODE:
            job_cards = job_cards[:3]
            print(f"  🧪 TEST MODE: Processing {len(job_cards)} jobs only")
        
        jobs_scraped = 0
        
        for i, card in enumerate(job_cards, 1):
            if self.blocked:
                break
                
            try:
                # Re-fetch cards (DOM may have changed after clicks)
                if i > 1:
                    current_cards = self.get_job_cards()
                    if i <= len(current_cards):
                        card = current_cards[i - 1]
                    else:
                        continue
                
                job_data = self.extract_job_details(card, i)
                job_data["search_url"] = search_url
                
                if job_data["job_title"]:
                    self.jobs_data.append(job_data)
                    jobs_scraped += 1
                
                # Random delay between jobs
                self.random_delay(DELAY_BETWEEN_JOBS_MIN, DELAY_BETWEEN_JOBS_MAX)
                
            except Exception as e:
                print(f"  ✗ Error on job {i}: {str(e)[:40]}")
                continue
        
        return jobs_scraped
    
    def scrape_url(self, search_url: str) -> int:
        """Scrape all pages for a given search URL."""
        print(f"\n{'='*60}")
        print(f"🔍 Scraping: {search_url[:70]}...")
        print(f"{'='*60}")
        
        try:
            self.driver.get(search_url)
        except Exception as e:
            print(f"  ✗ Failed to load URL: {e}")
            return 0
        
        self.random_delay(DELAY_AFTER_LOAD_MIN, DELAY_AFTER_LOAD_MAX)
        
        # Check for immediate block
        if self.detect_block():
            print("  🚫 Blocked on initial load!")
            self.handle_failure()
            return 0
        
        total_jobs = 0
        current_page = 1
        
        while current_page <= MAX_PAGES and not self.blocked:
            jobs_on_page = self.scrape_page(current_page, search_url)
            total_jobs += jobs_on_page
            
            if TEST_MODE:
                print(f"\n  🧪 TEST MODE: Stopping after page 1")
                break
            
            if jobs_on_page == 0:
                break
            
            # Try next page
            next_url = self.get_next_page_url(current_page)
            
            if next_url and current_page < MAX_PAGES:
                print(f"\n  ➡ Navigating to page {current_page + 1}...")
                self.random_delay(DELAY_BETWEEN_PAGES_MIN, DELAY_BETWEEN_PAGES_MAX)
                
                try:
                    self.driver.get(next_url)
                    self.random_delay(DELAY_AFTER_LOAD_MIN, DELAY_AFTER_LOAD_MAX)
                    
                    if self.detect_block():
                        print("  🚫 Blocked on pagination!")
                        self.handle_failure()
                        break
                        
                    current_page += 1
                except Exception as e:
                    print(f"  ✗ Navigation failed: {e}")
                    break
            else:
                break
        
        print(f"\n  📊 Total from this URL: {total_jobs} jobs")
        return total_jobs
    
    def save_to_csv(self):
        """Save all scraped jobs to CSV file."""
        if not self.jobs_data:
            print("\n⚠ No jobs to save!")
            return
        
        headers = ["Job Title", "Company", "Work Setting", "Job Type", "Pay", "Location", "URL", "Search URL"]
        
        with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for job in self.jobs_data:
                writer.writerow([
                    job["job_title"],
                    job["company"],
                    job["work_setting"],
                    job["job_type"],
                    job["pay"],
                    job["location"],
                    job["url"],
                    job["search_url"]
                ])
        
        print(f"\n💾 Saved {len(self.jobs_data)} jobs to {OUTPUT_FILE}")
    
    def run(self):
        """Main execution method."""
        print("\n" + "="*60)
        print("🚀 INDEED JOB SCRAPER v2 - Enhanced Anti-Detection")
        print("="*60)
        print(f"📋 Test Mode: {TEST_MODE}")
        print(f"📄 Max Pages: {MAX_PAGES}")
        print(f"🔗 URLs to scrape: {len(SEARCH_URLS)}")
        print(f"🌐 Proxy: {'Configured' if PROXY else 'None (using direct connection)'}")
        
        if not SEARCH_URLS:
            print("\n⚠ No search URLs configured! Edit SEARCH_URLS in the script.")
            return
        
        try:
            self.setup_driver()
            
            for i, url in enumerate(SEARCH_URLS, 1):
                if self.blocked:
                    print(f"\n⛔ Scraper blocked. Skipping remaining URLs.")
                    break
                    
                print(f"\n[{i}/{len(SEARCH_URLS)}]", end="")
                self.scrape_url(url)
                
                # Delay between different search URLs
                if i < len(SEARCH_URLS) and not self.blocked:
                    delay = random.uniform(5, 10)
                    print(f"\n⏳ Waiting {delay:.0f}s before next URL...")
                    time.sleep(delay)
            
            self.save_to_csv()
            
        except KeyboardInterrupt:
            print("\n\n⚠ Interrupted by user. Saving collected data...")
            self.save_to_csv()
        except Exception as e:
            print(f"\n✗ Fatal error: {e}")
            self.save_to_csv()  # Try to save whatever we got
            raise
        finally:
            if self.driver:
                self.driver.quit()
                print("✓ Browser closed")
        
        print("\n" + "="*60)
        status = "⚠ PARTIAL (was blocked)" if self.blocked else "✓ COMPLETE"
        print(f"{status}: {len(self.jobs_data)} total jobs scraped")
        print("="*60)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    scraper = IndeedScraperV2()
    scraper.run()
