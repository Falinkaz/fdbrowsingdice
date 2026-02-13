import time, random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ----------------------------------------
# CONFIGURATION
# ----------------------------------------
# Each entry is (search_url, candidate_name)
# postedDate=ONE = last 24 hours. Change to THREE (3 days), SEVEN, etc. as needed.
BASE_URLS = [
    # ── Elizabeth Lora Ruiz — Oracle EBS Functional (SCM + Financials) ──
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+EBS+Functional+Consultant", "Elizabeth"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+EBS+R12", "Elizabeth"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+EBS+SCM", "Elizabeth"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+EBS+Financials", "Elizabeth"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+Purchasing+Inventory", "Elizabeth"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+Order+Management", "Elizabeth"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+EBS+P2P", "Elizabeth"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+EBS+upgrade+R12", "Elizabeth"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+OCI+migration+EBS", "Elizabeth"),

    # ── Jose Froylan Castelan Vera — SAP ABAP / Fiori / BTP ──
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=SAP+ABAP+developer", "Jose"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=SAP+Fiori+SAPUI5", "Jose"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=SAP+ABAP+S4HANA", "Jose"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=SAP+BTP+developer", "Jose"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=SAP+ABAP+HCM+SuccessFactors", "Jose"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=SAP+CDS+Views+OData", "Jose"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=SAP+OpenText+VIM", "Jose"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=SAP+ABAP+Fiori", "Jose"),

    # ── Gerardo Ramos — Oracle Finance Functional (EBS & Cloud) ──
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+Financials+Consultant", "Gerardo"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+EBS+Finance", "Gerardo"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+Cloud+Financials", "Gerardo"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+Fusion+Finance", "Gerardo"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+GL+AR+AP", "Gerardo"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+EPM+FCCS", "Gerardo"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+EBS+Cloud+migration+Finance", "Gerardo"),
    ("https://www.dice.com/jobs?filters.postedDate=ONE&q=Oracle+R2R+Finance", "Gerardo"),

    # add more (url, candidate) tuples here
]
MAX_PAGES = 26  # adjust as needed

# Output CSV file path
OUTPUT_CSV = "dice_jobs_candidates.csv"

# ----------------------------------------
# FUNCTIONS
# ----------------------------------------
def smart_pause(min_sec=2, max_sec=5):
    pause = random.uniform(min_sec, max_sec)
    print(f"⏳ Sleeping for {pause:.2f} seconds...")
    time.sleep(pause)


def wait_for_element(selector, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )

# ----------------------------------------
# SET UP SELENIUM
# ----------------------------------------
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)

jobs = []

# ----------------------------------------
# SCRAPE EACH URL AND PAGINATION
# ----------------------------------------
for base_url, candidate in BASE_URLS:
    print(f"\n🔍 Scraping for {candidate}: {base_url}")
    for page in range(1, MAX_PAGES + 1):
        print(f"\n📄 Loading page {page}...")
        url = f"{base_url}&page={page}"
        driver.get(url)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        smart_pause(3, 5)

        # collect listing cards
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="listitem"]'))
            )
            cards = driver.find_elements(By.CSS_SELECTOR, 'div[role="listitem"]')
        except:
            print("⚠️ No cards found — stopping this base URL early.")
            break

        listing_jobs = []
        for card in cards:
            try:
                link = card.find_element(By.CSS_SELECTOR, 'a[data-testid="job-search-job-card-link"]').get_attribute('href')
            except:
                link = ''
            # extract listing info using updated selectors
            title_card = company_card = loc_card = ''
            try:
                title_card = card.find_element(
                    By.CSS_SELECTOR,
                    'a[data-testid="job-search-job-detail-link"]'
                ).text.strip()
            except:
                pass
            try:
                loc_card = card.find_element(
                    By.CSS_SELECTOR,
                    'p.text-sm.font-normal.text-zinc-600'
                ).text.strip()
            except:
                pass
            try:
                company_card = card.find_element(
                    By.CSS_SELECTOR,
                    'p.mb-0.line-clamp-2.text-sm.sm\\:line-clamp-1'
                ).text.strip()
            except:
                pass
            listing_jobs.append({
                'url': link,
                'title_card': title_card,
                'company_card': company_card,
                'loc_card': loc_card
            })

        if not listing_jobs:
            print("⚠️ No job links on this page — stopping.")
            break

        print(f"🔗 Found {len(listing_jobs)} job cards.")

        # iterate each listing record
        for idx, info in enumerate(listing_jobs):
            job_url = info['url']

            # handle redirect or empty link
            if not job_url or 'job-detail' not in job_url:
                print(f"🚫 Redirect or invalid link — recording listing info for: {job_url}")
                jobs.append({
                    'Candidate Fit': candidate,
                    'Job Title': info['title_card'],
                    'Company': info['company_card'],
                    'Recruiter Name': '',
                    'Location': info['loc_card'],
                    'Employment Type 1': '',
                    'Employment Type 2': '',
                    'Employment Type 3': '',
                    'Employment Type 4': '',
                    'Employment Type 5': '',
                    'Employment Type 6': '',
                    'Contract Duration': '',
                    'Corp To Corp': '',
                    'Pay': '',
                    'Work Type': '',
                    'Job Description': '',
                    'Job URL': job_url
                })
                continue

            # visit detail page
            try:
                print(f"➡️ Visiting job: {job_url}")
                driver.get(job_url)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                smart_pause(2, 5)

                try:
                    wait_for_element('h1', timeout=20)
                except:
                    print(f"⚠️ Timeout — recording listing info for: {job_url}")
                    raise

                # initialize detail fields
                title = location = recruiter = company = ''
                emp_types = [''] * 6
                duration = corp = pay = work_type = ''

                # simple fields with fallback
                try: title = driver.find_element(By.TAG_NAME, 'h1').text.strip()
                except: title = info['title_card']
                try: location = driver.find_element(By.CSS_SELECTOR, "li[data-cy='location']").text.strip()
                except: location = info['loc_card']
                try: recruiter = driver.find_element(By.CSS_SELECTOR, "p[data-testid='recruiterName']").text.strip()
                except: recruiter = ''
                try: company = driver.find_element(By.CSS_SELECTOR, "a[data-cy='companyNameLink']").text.strip()
                except: company = info['company_card']

                # badges
                try:
                    badges = driver.find_elements(By.CSS_SELECTOR, 'div.chip_chip__cYJs6 span')
                    emp_idx = 0
                    for b in badges:
                        text = b.text.strip()
                        b_id = b.get_attribute('id') or ''
                        if b_id.startswith('employmentDetailChip:'):
                            if 'corp to corp' in text.lower(): corp = text
                            elif 'month' in text.lower(): duration = text
                            elif emp_idx < 6:
                                emp_types[emp_idx] = text
                                emp_idx += 1
                        elif b_id.startswith('payChip:'): pay = text
                        elif b_id.startswith('location:'): work_type = text
                except: pass

                # description
                job_description = ''
                try:
                    job_description = driver.find_element(By.CSS_SELECTOR, 'div.job-description').text.strip()
                except: job_description = ''

                # collect
                jobs.append({
                    'Candidate Fit': candidate,
                    'Job Title': title,
                    'Company': company,
                    'Recruiter Name': recruiter,
                    'Location': location,
                    'Employment Type 1': emp_types[0],
                    'Employment Type 2': emp_types[1],
                    'Employment Type 3': emp_types[2],
                    'Employment Type 4': emp_types[3],
                    'Employment Type 5': emp_types[4],
                    'Employment Type 6': emp_types[5],
                    'Contract Duration': duration,
                    'Corp To Corp': corp,
                    'Pay': pay,
                    'Work Type': work_type,
                    'Job Description': job_description,
                    'Job URL': job_url
                })

            except Exception:
                # fallback: use listing info if detail fails
                jobs.append({
                    'Candidate Fit': candidate,
                    'Job Title': info['title_card'],
                    'Company': info['company_card'],
                    'Recruiter Name': '',
                    'Location': info['loc_card'],
                    'Employment Type 1': '',
                    'Employment Type 2': '',
                    'Employment Type 3': '',
                    'Employment Type 4': '',
                    'Employment Type 5': '',
                    'Employment Type 6': '',
                    'Contract Duration': '',
                    'Corp To Corp': '',
                    'Pay': '',
                    'Work Type': '',
                    'Job Description': '',
                    'Job URL': job_url
                })
                continue

# quit driver
driver.quit()

# ----------------------------------------
# SAVE TO CSV
# ----------------------------------------
print("\n🌍 Saving data to CSV...")
df = pd.DataFrame(jobs)

# deduplicate: if the same job URL appeared under multiple keywords,
# group candidate names together (e.g. "Elizabeth, Gerardo") and keep one row
df['Candidate Fit'] = df.groupby('Job URL')['Candidate Fit'].transform(lambda x: ', '.join(sorted(set(x))))
df = df.drop_duplicates(subset='Job URL', keep='first')

df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Done — {len(df)} unique jobs saved to '{OUTPUT_CSV}'")
