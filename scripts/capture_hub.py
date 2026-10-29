from playwright.sync_api import sync_playwright
from evidence import ROOT

with sync_playwright() as p:
    browser=p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe',headless=True)
    page=browser.new_page(viewport={'width':1400,'height':1100})
    for suffix,name in [('/tags','tags'),('','overview')]:
        url='https://hub.docker.com/r/asad3390/breast-cancer-triage-api'+suffix
        page.goto(url,wait_until='networkidle',timeout=60000)
        reject=page.get_by_role('button',name='Reject All',exact=True)
        if reject.is_visible():
            reject.click()
        page.wait_for_timeout(2000)
        page.screenshot(path=str(ROOT/f'evidence/screenshots/task16-hub-{name}.png'),full_page=True)
        print('Captured Docker Hub page:',url)
        print(page.locator('body').inner_text()[:5000])
    page.goto('https://hub.docker.com/r/asad3390/breast-cancer-triage-api/tags',wait_until='networkidle')
    from urllib.parse import urljoin
    import json, urllib.request
    tag=json.load(urllib.request.urlopen('https://hub.docker.com/v2/repositories/asad3390/breast-cancer-triage-api/tags/1.0.0'))
    digest=next(item['digest'] for item in tag['images'] if item['architecture']=='amd64')
    target=page.get_by_role('link',name=digest.removeprefix('sha256:')[:12],exact=False).first.get_attribute('href')
    page.goto(urljoin(page.url,target),wait_until='networkidle')
    page.wait_for_timeout(2000)
    page.screenshot(path=str(ROOT/'evidence/screenshots/task16-hub-digest.png'),full_page=True)
    print('Tag detail URL:',page.url)
    print(page.locator('body').inner_text()[:2500])
    browser.close()
