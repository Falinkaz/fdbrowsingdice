from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
import time

proxy_options = {
    'proxy': {
        'http': 'http://0ffaae09375798118ed0:9c24209a4e85f9d9@gw.dataimpulse.com:823',
        'https': 'http://0ffaae09375798118ed0:9c24209a4e85f9d9@gw.dataimpulse.com:823',
    }
}

options = Options()
options.add_argument('--headless=new')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('--window-size=1920,1080')
options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36')
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)

driver = webdriver.Chrome(options=options, seleniumwire_options=proxy_options)

driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
    'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
})

print('Trying Indeed...')
driver.get('https://www.indeed.com/jobs?q=developer&l=remote')

# Wait for Cloudflare challenge to complete
for i in range(6):
    time.sleep(5)
    title = driver.title
    print(f'  Check {i+1}: Title = "{title}"')
    driver.save_screenshot(f'indeed_wait_{i+1}.png')
    if 'moment' not in title.lower() and 'cloudflare' not in title.lower():
        print('  Cloudflare passed!')
        break

print(f'\nFinal URL: {driver.current_url}')
print(f'Final title: {driver.title}')
driver.save_screenshot('indeed_final.png')
driver.quit()
print('\nDone - check indeed_final.png')