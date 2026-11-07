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
    page.goto(config.TARGET_PAGE_URL, wait_until='domcontentloaded', timeout=60000)
    time.sleep(3)
    page.evaluate("window.scrollBy(0, 1800)")
    time.sleep(3)
    page.screenshot(path='storage/feed_scrolled_check.png')
    texts = page.locator("div[dir='auto']").all()
    for t in texts:
        txt = t.inner_text().strip()
        if "Sushi" in txt or "Gác lại" in txt or "Marian" in txt or "Văn học" in txt:
            print("FOUND POST ON WALL:\n", txt[:150])
            print("=" * 40)
    ctx.close()
