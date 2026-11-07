from playwright.sync_api import sync_playwright
import time
import config
with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        str(config.BROWSER_PROFILE_DIR),
        headless=True,
        channel=config.BROWSER_CHANNEL,
        args=["--disable-notifications"],
        viewport={"width": 1280, "height": 900}
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    # Check what is on personal profile
    page.goto('https://www.facebook.com/me', wait_until='domcontentloaded', timeout=60000)
    time.sleep(4)
    page.screenshot(path='storage/me_check.png')
    print("Checked /me, current url:", page.url)
    # Check what is on page URL
    page.goto(config.TARGET_PAGE_URL, wait_until='domcontentloaded', timeout=60000)
    time.sleep(4)
    page.screenshot(path='storage/page_check.png')
    print("Checked page URL, current url:", page.url)
    ctx.close()
