from playwright.sync_api import sync_playwright
from evidence import ROOT

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1400,'height':1100})
    for suffix,name in [('/tags','tags'),('','overview')]:
        url='https://hub.docker.com/r/asad3390/breast-cancer-triage-api'+suffix
        page.goto(url,wait_until='networkidle',timeout=60000)
        page.wait_for_timeout(2000)
        page.screenshot(path=str(ROOT/f'evidence/screenshots/task16-hub-{name}.png'),full_page=True)
        print('Captured Docker Hub page:',url)
        print(page.locator('body').inner_text()[:5000])
    browser.close()
