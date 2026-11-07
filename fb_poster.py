import os
import time
import logging
from typing import Dict, Any
from playwright.sync_api import sync_playwright
import config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
def publish_photo_to_facebook(image_path: str, caption: str, fanpage_url: str = None) -> Dict[str, Any]:
    target_page = fanpage_url or config.MY_FANPAGE_URL
    if not os.path.exists(image_path):
        logging.error(f"Image file to post does not exist: {image_path}")
        return {"success": False, "error": "Image file not found"}
    logging.info(f"--- STARTING BROWSER FANPAGE POSTING to: {target_page} ---")
    logging.info(f"Image: {os.path.basename(image_path)}")
    logging.info(f"Caption preview: {caption[:60]}...")
    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(config.BROWSER_PROFILE_DIR),
            "headless": True,
            "args": ["--disable-notifications", "--disable-popup-blocking"],
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1280, "height": 900}
        }
        if config.BROWSER_CHANNEL:
            launch_kwargs["channel"] = config.BROWSER_CHANNEL
        context = p.chromium.launch_persistent_context(**launch_kwargs)
        if config.COOKIES_PATH.exists():
            import json
            try:
                with open(config.COOKIES_PATH, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
            except Exception:
                pass
        page = context.new_page() if not context.pages else context.pages[0]
        try:
            logging.info(f"Navigating to Fanpage: {target_page}")
            page.goto(target_page, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)
            if "login" in page.url.lower() or page.locator("input[name='email'], input[name='pass'], [data-testid='royal_login_button']").count() > 0:
                logging.error("Facebook session has expired or requires login.")
                page.screenshot(path=str(config.STORAGE_DIR / "login_expired.png"))
                import telegram_bot
                telegram_bot.send_alert_to_all("[CẢNH BÁO] Phiên đăng nhập Facebook của bot đã hết hạn! Vui lòng mở Terminal chạy: python main.py --login-fb để cập nhật lại.")
                context.close()
                return {"success": False, "error": "Facebook session expired"}
            switch_btn = page.locator("div[role='button']:has-text('Chuyển ngay'), div[role='button']:has-text('Switch now'), div[aria-label*='Chuyển ngay'], div[aria-label*='Switch now']")
            if switch_btn.count() > 0:
                logging.info("Detected Facebook New Pages profile switch request. Switching...")
                switch_btn.first.click()
                time.sleep(5)
            composer_trigger = page.locator(
                "div[role='button']:has-text('Bạn đang nghĩ gì?'), "
                "div[role='button']:has-text('Tạo bài viết'), "
                "div[role='button']:has-text('Viết gì đó...'), "
                "span:has-text('Bạn đang nghĩ gì?'), "
                "div[role='button']:has-text(\"What's on your mind?\"), "
                "div[role='button']:has-text('Create post')"
            )
            if composer_trigger.count() == 0:
                page.screenshot(path=str(config.STORAGE_DIR / "fb_post_error.png"))
                err = "Could not locate Fanpage post composer box. Make sure your account is an Admin/Editor of the Page and logged in via: python main.py --login-fb"
                logging.error(err)
                context.close()
                return {"success": False, "error": err}
            composer_trigger.first.click()
            time.sleep(3)
            dialog = page.locator("div[role='dialog']").first
            dialog.wait_for(state="visible", timeout=12000)
            file_input = page.locator("input[type='file'][accept*='image']")
            if file_input.count() == 0:
                photo_btn = dialog.locator("div[aria-label*='Ảnh/video'], div[aria-label*='Photo/video'], [role='button']:has-text('Ảnh/video'), [role='button']:has-text('Photo/video')")
                if photo_btn.count() > 0:
                    photo_btn.first.click()
                    time.sleep(2)
                file_input = page.locator("input[type='file'][accept*='image']")
            if file_input.count() > 0:
                file_input.first.set_input_files(image_path)
                logging.info(f"Uploaded photo file: {os.path.basename(image_path)}")
                time.sleep(4)
            else:
                logging.warning("Photo upload input not detected, continuing with text only...")
            textbox = dialog.locator("div[role='textbox'], div[contenteditable='true']")
            if textbox.count() > 0:
                textbox.first.click()
                textbox.first.fill(caption)
                time.sleep(2)
            next_btn = dialog.locator("[role='button']:has-text('Tiếp'), [role='button']:has-text('Next')")
            if next_btn.count() > 0:
                logging.info("Clicking Next/Tiep step...")
                next_btn.first.click()
                time.sleep(4)
            # Step: Click the final Publish button
            # Note: Avoid loose :has-text('Đăng') as it matches "Lựa chọn lịch đăng" row!
            post_btn = dialog.locator("div[aria-label='Đăng'], div[aria-label='Post'], div[role='button'] span:text-is('Đăng'), div[role='button'] span:text-is('Post')")
            if post_btn.count() == 0:
                post_btn = dialog.locator("div[role='button']:has-text('Đăng'):not(:has-text('Lựa chọn'))")
            try:
                post_btn.first.wait_for(state="visible", timeout=12000)
            except Exception:
                time.sleep(3)
            if post_btn.count() > 0:
                post_btn.first.click()
                logging.info("Clicked real 'Đăng' button. Waiting for dialog to close and post to publish...")
                try:
                    dialog.wait_for(state="detached", timeout=25000)
                except Exception:
                    time.sleep(8)
                logging.info(f"[OK] Successfully posted book to Fanpage: {target_page}")
                context.close()
                return {
                    "success": True,
                    "simulated": False,
                    "post_id": f"browser_post_{int(time.time())}",
                    "message": "Post published to Fanpage via Playwright browser."
                }
            else:
                page.screenshot(path=str(config.STORAGE_DIR / "fb_post_error.png"))
                err = "Could not locate final 'Đăng' button in post dialog."
                logging.error(err)
                context.close()
                return {"success": False, "error": err}
        except Exception as e:
            page.screenshot(path=str(config.STORAGE_DIR / "fb_post_error.png"))
            logging.error(f"Error during Fanpage posting: {e}")
            context.close()
            return {"success": False, "error": str(e)}
if __name__ == "__main__":
    test_img = config.IMAGES_DIR / "test.jpg"
    if not test_img.exists():
        print("Create a test image in storage/images/test.jpg to test.")
    else:
        res = publish_photo_to_facebook(str(test_img), "Test bookstore automated post!")
        print(res)
