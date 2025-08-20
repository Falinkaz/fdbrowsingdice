import time, random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def smart_pause(min_sec=2, max_sec=5):
    pause = random.uniform(min_sec, max_sec)
    print(f"⏳ Sleeping for {pause:.2f} seconds...")
    time.sleep(pause)


# --- Set up browser
options = webdriver.ChromeOptions()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
driver = webdriver.Chrome(options=options)


def wait_for_element(selector, timeout=20):
    return WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )

BASE_URL = "https://www.dice.com/jobs?q=latin+america"
MAX_PAGES = 26  # increase this as needed


jobs = []

for page in range(1, MAX_PAGES + 1):
    print(f"\n📄 Loading page {page}...")
    url = f"{BASE_URL}&page={page}"
    driver.get(url)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    smart_pause(3, 5)

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="listitem"]'))
        )
        job_links = [
            e.get_attribute("href")
            for e in driver.find_elements(By.CSS_SELECTOR, 'a[data-testid="job-search-job-card-link"]')
        ]
    except:
        print("⚠️ No cards found — stopping early.")
        break

    if not job_links:
        print("⚠️ No job links on this page — stopping.")
        break

    print(f"🔗 Found {len(job_links)} job links.")

    for idx, job_url in enumerate(job_links):
        # skip redirect URLs (non-detail)
        if "job-detail" not in job_url:
            print(f"🚫 Redirect link — not scraping: {job_url}")
            jobs.append({
                "Job Title": "[SKIPPED: Redirect Link]",
                "Company": "",
                "Recruiter Name": "",
                "Location": "",
                "Employment Type 1": "",
                "Employment Type 2": "",
                "Employment Type 3": "",
                "Employment Type 4": "",
                "Employment Type 5": "",
                "Employment Type 6": "",
                "Contract Duration": "",
                "Corp To Corp": "",
                "Pay": "",
                "Work Type": "",
                "Job Description": "",
                "Job URL": job_url
            })
            continue

        try:
            print(f"➡️ Visiting job: {job_url}")
            driver.get(job_url)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            smart_pause(2, 5)

            # wait for page content
            try:
                wait_for_element("h1", timeout=20)
            except:
                print(f"⚠️ Timeout waiting for job content — skipping {job_url}")
                jobs.append({
                    "Job Title": "[TIMEOUT]",
                    "Company": "",
                    "Recruiter Name": "",
                    "Location": "",
                    "Employment Type 1": "",
                    "Employment Type 2": "",
                    "Employment Type 3": "",
                    "Employment Type 4": "",
                    "Employment Type 5": "",
                    "Employment Type 6": "",
                    "Contract Duration": "",
                    "Corp To Corp": "",
                    "Pay": "",
                    "Work Type": "",
                    "Job Description": "",
                    "Job URL": job_url
                })
                continue

            # initialize fields
            title = location = recruiter = company = ""
            emp_types = [""] * 6
            duration = corp = pay = work_type = ""

            # extract simple fields
            try:
                title = driver.find_element(By.TAG_NAME, "h1").text.strip()
            except Exception as e:
                print(f"⚠️ Failed to get title: {e}")
            try:
                location = driver.find_element(By.CSS_SELECTOR, "li[data-cy='location']").text.strip()
            except Exception as e:
                print(f"⚠️ Failed to get location: {e}")
            try:
                recruiter = driver.find_element(By.CSS_SELECTOR, "p[data-testid='recruiterName']").text.strip()
            except Exception as e:
                print(f"⚠️ Failed to get recruiter: {e}")
            try:
                company = driver.find_element(By.CSS_SELECTOR, "a[data-cy='companyNameLink']").text.strip()
            except Exception as e:
                print(f"⚠️ Failed to get company: {e}")

            # extract badges for emp types, pay, etc.
            try:
                badges = driver.find_elements(By.CSS_SELECTOR, "div.chip_chip__cYJs6 span")
                emp_idx = 0
                for b in badges:
                    text = b.text.strip()
                    b_id = b.get_attribute("id")
                    if not b_id:
                        continue
                    if b_id.startswith("employmentDetailChip:"):
                        if "corp to corp" in text.lower():
                            corp = text
                        elif "month" in text.lower():
                            duration = text
                        elif emp_idx < 6:
                            emp_types[emp_idx] = text
                            emp_idx += 1
                    elif b_id.startswith("payChip:"):
                        pay = text
                    elif b_id.startswith("location:"):
                        work_type = text
            except Exception as e:
                print(f"⚠️ Failed to get badges: {e}")

            # extract the full job description
            job_description = ""
            try:
                desc_elem = driver.find_element(By.CSS_SELECTOR, "div.job-description")
                job_description = desc_elem.text.strip()
            except Exception as e:
                print(f"⚠️ Failed to get job description: {e}")

            # append record
            jobs.append({
                "Job Title": title,
                "Company": company,
                "Recruiter Name": recruiter,
                "Location": location,
                "Employment Type 1": emp_types[0],
                "Employment Type 2": emp_types[1],
                "Employment Type 3": emp_types[2],
                "Employment Type 4": emp_types[3],
                "Employment Type 5": emp_types[4],
                "Employment Type 6": emp_types[5],
                "Contract Duration": duration,
                "Corp To Corp": corp,
                "Pay": pay,
                "Work Type": work_type,
                "Job Description": job_description,
                "Job URL": job_url
            })

            # random longer pause every 5 jobs
            if (idx + 1) % 5 == 0:
                print("💤 Taking a longer break...")
                smart_pause(10, 15)

        except Exception as e:
            print(f"⚠️ Skipped job due to error: {e}")
            jobs.append({
                "Job Title": "[ERROR: Could not scrape]",
                "Company": "",
                "Recruiter Name": "",
                "Location": "",
                "Employment Type 1": "",
                "Employment Type 2": "",
                "Employment Type 3": "",
                "Employment Type 4": "",
                "Employment Type 5": "",
                "Employment Type 6": "",
                "Contract Duration": "",
                "Corp To Corp": "",
                "Pay": "",
                "Work Type": "",
                "Job Description": "",
                "Job URL": job_url
            })
            continue

# clean up
driver.quit()

# save to CSV
print("\n🌍 Saving all collected entries...")
df = pd.DataFrame(jobs)
df.to_csv("dice_jobs_detailed.csv", index=False)
print(f"\n✅ Done — {len(df)} jobs saved to dice_jobs_detailed.csv")
