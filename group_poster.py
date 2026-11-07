import os
import time
import random
import logging
from playwright.sync_api import sync_playwright
import config
import database
import ai_engine
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
def post_single_book_to_group(group_url: str = None) -> bool:
    target_groups = [group_url] if group_url else config.TARGET_POST_GROUP_URLS
    if not target_groups:
        logging.warning("No target group URLs configured in config.TARGET_POST_GROUP_URLS.")
        return False
    target_group = target_groups[0]
    logging.info(f"--- STARTING DAILY GROUP POSTING (1 post/day) to: {target_group} ---")
    candidates = database.get_unposted_eligible_images(min_days=config.MIN_DAYS_OLD, max_days=config.MAX_DAYS_OLD)
    if not candidates:
        logging.warning("No eligible unposted book images found in inventory.")
        return False
    selected = random.choice(candidates)
    image_id = selected["id"]
    local_path = selected["local_path"]
    logging.info(f"Selected book image ID {image_id} at: {local_path}")
    caption = ai_engine.generate_caption_for_image(local_path)
    logging.info(f"Generated caption:\n{caption}")
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
        page = context.new_page() if not context.pages else context.pages[0]
        try:
            page.goto(target_group, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)
            if "login" in page.url.lower() or page.locator("input[name='email'], input[name='pass']").count() > 0:
                logging.error("Facebook session has expired.")
                import telegram_bot
                telegram_bot.send_alert_to_all("[CẢNH BÁO] Phiên đăng nhập Facebook của bot đã hết hạn! Vui lòng mở Terminal chạy: python main.py --login-fb để cập nhật lại.")
                context.close()
                return False
            composer_trigger = page.locator("div[role='button']:has-text('Viết gì đó...'), div[role='button']:has-text('Bạn viết gì đi...'), div[role='button']:has-text('Tạo bài viết công khai...'), span:has-text('Viết gì đó...')")
            if composer_trigger.count() == 0:
                logging.error("Could not locate group post creation box. Ensure account has joined the group.")
                context.close()
                return False
            composer_trigger.first.click()
            time.sleep(3)
            dialog = page.locator("div[role='dialog']")
            dialog.wait_for(state="visible", timeout=10000)
            file_input = page.locator("input[type='file'][accept*='image']")
            if file_input.count() > 0:
                file_input.first.set_input_files(local_path)
                time.sleep(3)
            textbox = dialog.locator("div[role='textbox']")
            if textbox.count() > 0:
                textbox.first.click()
                textbox.first.fill(caption)
                time.sleep(2)
            post_btn = dialog.locator("div[aria-label='Đăng'], div[aria-label='Post'], [role='button']:has-text('Đăng')")
            if post_btn.count() > 0:
                post_btn.first.click()
                time.sleep(6)
                logging.info(f"[OK] Successfully posted 1 book to Facebook Group: {target_group}")
                database.mark_image_published(image_id)
                context.close()
                return True
            else:
                logging.error("Could not find submit 'Đăng' button.")
                context.close()
                return False
        except Exception as e:
            logging.error(f"Error posting to Facebook Group: {e}")
            context.close()
            return False
if __name__ == "__main__":
    post_single_book_to_group()