"""Capture actual browser screenshots of Swagger and the bind-mounted page."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
from evidence import ROOT

out = ROOT/'evidence/screenshots'
out.mkdir(parents=True, exist_ok=True)
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path=r'C:\Program Files\Google\Chrome\Application\chrome.exe', headless=True)
    page = browser.new_page(viewport={'width': 1280, 'height': 1000}, device_scale_factor=1)
    page.goto('http://localhost:18082')
    page.screenshot(path=str(out/'task04-bind-browser.png'), full_page=True)
    page.goto('http://localhost:8001/docs')
    page.locator('#operations-default-predict_predict_post .opblock-summary').click()
    page.get_by_role('button', name='Try it out').click()
    page.locator('textarea').fill((ROOT/'sample.json').read_text())
    page.get_by_role('button', name='Execute', exact=True).click()
    page.wait_for_selector('.responses-inner .response-col_status:has-text("200")')
    page.wait_for_timeout(1000)
    page.screenshot(path=str(out/'task09-swagger-prediction.png'), full_page=True)
    box = page.locator('.curl-command').bounding_box()
    response = page.locator('.live-responses-table').bounding_box()
    page.screenshot(path=str(out/'task09-swagger-response.png'), full_page=True, clip={
        'x': box['x'], 'y': box['y'], 'width': box['width'],
        'height': response['y']+response['height']-box['y']})
    browser.close()
print('Captured bind-mounted page and executed Swagger prediction screenshots')
