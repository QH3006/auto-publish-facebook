import time
import logging
from playwright.sync_api import sync_playwright
import config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
def login_facebook_profile():
    logging.info("Opening visible browser to log in to Facebook...")
    logging.info(f"Session data will be stored in: {config.BROWSER_PROFILE_DIR}")
    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(config.BROWSER_PROFILE_DIR),
            "headless": False,
            "args": ["--disable-notifications"],
            "viewport": {"width": 1280, "height": 900}
        }
        if config.BROWSER_CHANNEL:
            launch_kwargs["channel"] = config.BROWSER_CHANNEL
        context = p.chromium.launch_persistent_context(**launch_kwargs)
        page = context.new_page()
        page.goto("https://www.facebook.com")
        print("\n" + "=" * 65)
        print(" [INSTRUCTION] LOG IN TO FACEBOOK IN THE OPENED WINDOW")
        print("=" * 65)
        print(" 1. Enter your Facebook account details and log in.")
        print(" 2. Once your Facebook News Feed is visible and loaded,")
        print("    return to this terminal and press Enter to save.")
        print("=" * 65 + "\n")
        try:
            input("Press Enter here AFTER logging in successfully...")
        except Exception:
            time.sleep(30)
        context.close()
    logging.info("[OK] Facebook session and cookies saved permanently to browser profile.")
    logging.info("[OK] From now on, background scanners will use this saved login automatically.")
if __name__ == "__main__":
    login_facebook_profile()

