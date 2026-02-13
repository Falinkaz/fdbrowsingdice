#!/usr/bin/env python3
"""
Indeed Job Scraper v3 - Simple Setup (matches Dice scraper approach)
====================================================================
Uses standard Selenium like the Dice scraper, but with human-like behaviors.
No special Chrome installation needed - uses whatever Chrome is in the environment.
"""

import csv
import random
import re
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    StaleElementReferenceException,
    ElementClickInterceptedException
)

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
    "https://www.indeed.com/jobs?q=usa&l=&fromage=1&sc=0kf%3Aattr%28DSQF7%29attr%28NJXCK%29%3B&from=searchOnDesktopSerp&vjk=b3e358dbd83d96dc",
    
    # Add more URLs here:
    # "https://www.indeed.com/jobs?q=python+developer&l=remote&sort=date",
    # "https://www.indeed.com/jobs?q=data+engineer&l=Texas&sort=date",
]

# =============================================================================
# SETTINGS
# =============================================================================

MAX_PAGES = 7           # Pages per URL (Indeed shows ~15 jobs per page)
TEST_MODE = True        # True = only 3 jobs from page 1 (for testing)
OUTPUT_CSV = f"indeed_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# Delay settings (in seconds) - increase these if you get blocked
DELAY_MIN = 2
DELAY_MAX = 5

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def smart_pause(min_sec=DELAY_MIN, max_sec=DELAY_MAX):
    """Random pause like in your Dice scraper."""
    pause = random.uniform(min_sec, max_sec)
    print(f"  ⏳ Pausing {pause:.1f}s...")
    time.sleep(pause)


def human_scroll(driver):
    """Scroll down gradually like a human would."""
    scroll_height = driver.execute_script("return document.body.scrollHeight")
    current = 0
    while current < scroll_height * 0.4:
        scroll_amt = random.randint(150, 350)
        current += scroll_amt
        driver.execute_script(f"window.scrollTo(0, {current});")
        time.sleep(random.uniform(0.1, 0.3))
    # Sometimes scroll back up a bit
    if random.random() < 0.3:
        driver.execute_script(f"window.scrollBy(0, -{random.randint(50, 150)});")
        time.sleep(0.2)


def scroll_to_element(driver, element):
    """Scroll element into view smoothly."""
    driver.execute_script(
        "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
        element
    )
    time.sleep(random.uniform(0.3, 0.6))


def is_blocked(driver):
    """Check if Indeed blocked us."""
    page = driver.page_source.lower()
    url = driver.current_url.lower()
    
    blocked_signs = ["captcha", "robot", "unusual traffic", "verify you're human", 
                     "access denied", "blocked", "security check"]
    
    for sign in blocked_signs:
        if sign in page or sign in url:
            return True
    
    if "indeed.com" not in url:
        return True
    
    return False


def extract_location_from_description(html):
    """Pull location from job description text."""
    if not html:
        return ""
    
    patterns = [
        r'<b>Location:?</b>\s*([^<\n]+)',
        r'Location:?\s*</b>\s*([^<\n]+)',
        r'Location:?\s*([^\n<]{5,50})',
        r'100%\s*Remote\s*[–-]\s*([A-Z]{2,}|\w+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            loc = re.sub(r'<[^>]+>', '', match.group(1)).strip()
            if len(loc) > 3:
                return loc[:100]
    return ""


# =============================================================================
# MAIN SCRAPER
# =============================================================================

def setup_driver():
    """Set up Chrome - same approach as your Dice scraper."""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    # Extra stealth options
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=options)
    
    # Hide webdriver flag
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    return driver


def get_job_cards(driver):
    """Get all job card elements."""
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".job_seen_beacon"))
        )
        return driver.find_elements(By.CSS_SELECTOR, ".job_seen_beacon")
    except TimeoutException:
        return []


def extract_job_details(driver, job_card, index):
    """Click job card and extract details from side panel."""
    job = {
        "job_title": "",
        "company": "",
        "work_setting": "",
        "job_type": "",
        "pay": "",
        "location": "",
        "url": ""
    }
    
    try:
        # Find and click the job title link
        title_link = job_card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle")
        title_preview = title_link.text.strip()[:45]
        print(f"  [{index}] {title_preview}...", end=" ", flush=True)
        
        scroll_to_element(driver, title_link)
        time.sleep(random.uniform(0.5, 1.0))
        
        try:
            title_link.click()
        except ElementClickInterceptedException:
            driver.execute_script("arguments[0].click();", title_link)
        
        smart_pause(1.5, 3)
        
        # Check for block
        if is_blocked(driver):
            print("🚫 BLOCKED!")
            return None  # Signal to stop
        
        job["url"] = driver.current_url
        
        # Wait for detail panel
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    "[data-testid='jobsearch-ViewJobComponent'], .jobsearch-ViewJobLayout, #jobDescriptionText"))
            )
        except TimeoutException:
            print("⏳ timeout")
            return job
        
        # === EXTRACT FIELDS ===
        
        # Job Title
        for sel in ["h2.jobsearch-JobInfoHeader-title span", "h1[data-testid='jobsearch-JobInfoHeader-title'] span"]:
            try:
                job["job_title"] = driver.find_element(By.CSS_SELECTOR, sel).text.replace(" - job post", "").strip()
                break
            except NoSuchElementException:
                continue
        if not job["job_title"]:
            job["job_title"] = title_link.text.strip()
        
        # Company
        for sel in ["[data-testid='inlineHeader-companyName'] a", "[data-testid='inlineHeader-companyName']", 
                    ".jobsearch-JobInfoHeader-companyNameLink a", ".css-1h4l2d7"]:
            try:
                job["company"] = driver.find_element(By.CSS_SELECTOR, sel).text.strip()
                break
            except NoSuchElementException:
                continue
        
        # Metadata (Work Setting, Job Type, Pay)
        try:
            spans = driver.find_elements(By.CSS_SELECTOR, ".js-match-insights-provider-18uwqyc, [class*='match-insights-provider'] span")
            for span in spans:
                text = span.text.strip()
                if not text or len(text) < 3:
                    continue
                t = text.lower()
                
                if any(x in t for x in ["remote", "hybrid", "on-site", "in-person"]):
                    if not job["work_setting"]:
                        job["work_setting"] = text
                elif any(x in t for x in ["contract", "full-time", "part-time", "temporary", "internship"]):
                    if not job["job_type"]:
                        job["job_type"] = text
                elif "$" in text or any(x in t for x in ["hour", "year", "salary"]):
                    if not job["pay"]:
                        job["pay"] = text
        except:
            pass
        
        # Location from description
        try:
            desc = driver.find_element(By.CSS_SELECTOR, "#jobDescriptionText, .jobsearch-JobComponent-description")
            job["location"] = extract_location_from_description(desc.get_attribute("innerHTML"))
        except:
            pass
        
        status = "✓" if job["company"] else "△"
        print(f"{status} {job['company'][:25] if job['company'] else 'no company'}")
        
    except StaleElementReferenceException:
        print("⚠ stale")
    except Exception as e:
        print(f"✗ {str(e)[:30]}")
    
    return job


def get_next_page_url(driver, current_page):
    """Find URL for next page."""
    next_num = current_page + 1
    for sel in [f'a[data-testid="pagination-page-{next_num}"]', f'a[aria-label="{next_num}"]']:
        try:
            link = driver.find_element(By.CSS_SELECTOR, sel)
            return link.get_attribute("href")
        except NoSuchElementException:
            continue
    return None


def scrape_indeed():
    """Main scraping function."""
    print("\n" + "="*60)
    print("🚀 INDEED JOB SCRAPER v3")
    print("="*60)
    print(f"📋 Test Mode: {TEST_MODE}")
    print(f"📄 Max Pages: {MAX_PAGES}")
    print(f"🔗 URLs to scrape: {len(SEARCH_URLS)}")
    
    if not SEARCH_URLS:
        print("\n⚠ No URLs configured! Edit SEARCH_URLS in the script.")
        return
    
    driver = setup_driver()
    print("✓ Browser ready")
    
    all_jobs = []
    blocked = False
    
    try:
        for url_idx, search_url in enumerate(SEARCH_URLS, 1):
            if blocked:
                print("\n⛔ Blocked - stopping.")
                break
            
            print(f"\n{'='*60}")
            print(f"[{url_idx}/{len(SEARCH_URLS)}] 🔍 {search_url[:70]}...")
            print("="*60)
            
            driver.get(search_url)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            smart_pause(3, 5)
            
            if is_blocked(driver):
                print("🚫 Blocked on initial load!")
                blocked = True
                break
            
            current_page = 1
            
            while current_page <= MAX_PAGES and not blocked:
                print(f"\n📄 Page {current_page}")
                
                human_scroll(driver)
                time.sleep(0.5)
                
                cards = get_job_cards(driver)
                if not cards:
                    print("  ⚠ No job cards found - stopping this URL")
                    break
                
                print(f"  Found {len(cards)} jobs")
                
                if TEST_MODE:
                    cards = cards[:3]
                    print(f"  🧪 TEST MODE: Processing only {len(cards)}")
                
                for i, card in enumerate(cards, 1):
                    if blocked:
                        break
                    
                    # Re-fetch cards (DOM changes after clicks)
                    if i > 1:
                        current_cards = get_job_cards(driver)
                        if i <= len(current_cards):
                            card = current_cards[i - 1]
                        else:
                            continue
                    
                    job = extract_job_details(driver, card, i)
                    
                    if job is None:  # Blocked signal
                        blocked = True
                        break
                    
                    if job["job_title"]:
                        job["search_url"] = search_url
                        all_jobs.append(job)
                    
                    smart_pause(DELAY_MIN, DELAY_MAX)
                
                if TEST_MODE:
                    print("\n  🧪 TEST MODE: Stopping after page 1")
                    break
                
                # Next page
                next_url = get_next_page_url(driver, current_page)
                if next_url and current_page < MAX_PAGES:
                    print(f"\n  ➡ Going to page {current_page + 1}...")
                    driver.get(next_url)
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    smart_pause(3, 5)
                    
                    if is_blocked(driver):
                        print("  🚫 Blocked on pagination!")
                        blocked = True
                        break
                    
                    current_page += 1
                else:
                    break
            
            # Pause between different search URLs
            if url_idx < len(SEARCH_URLS) and not blocked:
                pause = random.uniform(5, 10)
                print(f"\n⏳ Waiting {pause:.0f}s before next URL...")
                time.sleep(pause)
    
    finally:
        driver.quit()
        print("\n✓ Browser closed")
    
    # Save to CSV
    if all_jobs:
        headers = ["Job Title", "Company", "Work Setting", "Job Type", "Pay", "Location", "URL", "Search URL"]
        with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for job in all_jobs:
                writer.writerow([
                    job["job_title"], job["company"], job["work_setting"],
                    job["job_type"], job["pay"], job["location"],
                    job["url"], job.get("search_url", "")
                ])
        print(f"\n💾 Saved {len(all_jobs)} jobs to {OUTPUT_CSV}")
    else:
        print("\n⚠ No jobs to save!")
    
    print("\n" + "="*60)
    status = "⚠ PARTIAL (blocked)" if blocked else "✓ COMPLETE"
    print(f"{status}: {len(all_jobs)} total jobs scraped")
    print("="*60)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    scrape_indeed()