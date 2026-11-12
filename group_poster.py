import os
import time
import random
import logging
from playwright.sync_api import sync_playwright
import config
import database
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
GENERAL_GROUP_CAPTIONS = [
    "Tiệm gửi đến cả nhà một số tựa sách hay hôm nay, bạn ưng cuốn nào cứ nhắn tiệm nhé! #SachHay #TiemSachCuaThuong",
    "Ghé tiệm hôm nay để chọn cho mình một người bạn đồng hành nhé, bạn quan tâm cuốn nào nhắn tiệm nha! #SachHay #TiemSachCuaThuong",
    "Mỗi cuốn sách là một hành trình thú vị. Mời cả nhà tham khảo vài tựa sách đang có sẵn tại tiệm nhé! #SachHay #TiemSachCuaThuong",
    "Một vài đầu sách hay gửi bạn đọc, bạn nào cần thêm ảnh chi tiết cuốn nào cứ nhắn tiệm nha! #SachHay #TiemSachCuaThuong"
]
def post_single_book_to_group(group_url: str = None, count: int = None) -> bool:
    for lf in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
        p = config.BROWSER_PROFILE_DIR / lf
        if p.exists():
            try:
                os.remove(p)
            except Exception:
                pass
    target_groups = [group_url] if group_url else config.TARGET_POST_GROUP_URLS
    if not target_groups:
        logging.warning("No target group URLs configured in config.TARGET_POST_GROUP_URLS.")
        return False
    target_group = target_groups[0]
    num_images = count if count is not None else getattr(config, "GROUP_POST_IMAGES_COUNT", 10)
    logging.info(f"--- STARTING DAILY GROUP POSTING ({num_images} images/post at {config.GROUP_POSTING_HOUR}) to: {target_group} ---")
    candidates = database.get_unposted_eligible_images(min_days=0, max_days=999)
    valid_candidates = [x for x in candidates if os.path.exists(x["local_path"])]
    if not valid_candidates:
        logging.warning("No eligible unposted book images found in inventory.")
        return False
    selected = random.sample(valid_candidates, min(num_images, len(valid_candidates)))
    paths = [x["local_path"] for x in selected]
    ids = [x["id"] for x in selected]
    logging.info(f"Selected {len(paths)} book images to upload to group.")
    caption = random.choice(GENERAL_GROUP_CAPTIONS)
    logging.info(f"Group caption:\n{caption}")
    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(config.BROWSER_PROFILE_DIR),
            "headless": True,
            "args": ["--disable-notifications", "--disable-popup-blocking"],
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1600, "height": 900}
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
            composer_trigger = page.locator(
                "div[role='button']:has-text('Bạn viết gì đi...'), "
                "div[role='button']:has-text('Tạo bài viết công khai...'), "
                "div[role='button']:has-text('Create a public post...'), "
                "div[role='button']:has-text('Write something...')"
            ).first
            if composer_trigger.count() == 0:
                logging.error("Could not locate group post creation box. Ensure account has joined the group.")
                context.close()
                return False
            composer_trigger.click()
            time.sleep(3)
            dialog = page.locator("div[role='dialog']").filter(has_text="Tạo bài viết").filter(has_text="Đăng").first
            if dialog.count() == 0:
                dialog = page.locator("div[role='dialog']").filter(has_text="Tạo bài viết").first
            if dialog.count() == 0:
                dialog = page.locator("div[role='dialog']:visible").last
            dialog.wait_for(state="visible", timeout=12000)
            add_photo_btn = dialog.locator(
                "div[aria-label='Ảnh/video'], "
                "div[role='button']:has-text('Ảnh/video'), "
                "div[aria-label*='Ảnh/video' i]"
            ).first
            if add_photo_btn.count() > 0:
                logging.info("Clicking Add photo button in group dialog...")
                add_photo_btn.click()
                time.sleep(2)
            file_input = dialog.locator("input[type='file']")
            if file_input.count() == 0:
                file_input = page.locator("div[role='dialog'] input[type='file']")
            if file_input.count() > 0:
                try:
                    file_input.first.set_input_files(paths)
                    logging.info(f"Uploaded {len(paths)} photos to group composer dialog.")
                    time.sleep(8)
                except Exception as ex_file:
                    logging.warning(f"File upload warning: {ex_file}")
            else:
                logging.warning("Photo upload input not detected in group dialog.")
            textbox = dialog.locator("div[role='textbox'], div[contenteditable='true']").first
            if textbox.count() > 0:
                textbox.click()
                time.sleep(1)
                try:
                    page.keyboard.insert_text(caption)
                except Exception:
                    textbox.fill(caption)
                time.sleep(2)
            post_btn = dialog.locator(
                "div[role='button']:has-text('Đăng'), "
                "div[aria-label='Đăng'], "
                "div[aria-label='Post'], "
                "div[role='button']:has-text('Post')"
            ).first
            if post_btn.count() > 0 and post_btn.is_visible():
                post_btn.click()
                logging.info("Clicked real 'Đăng' button in Group. Waiting for dialog to detach...")
                closed = False
                for _ in range(60):
                    time.sleep(1)
                    if page.locator("div[role='dialog']").filter(has_text="Tạo bài viết").count() == 0:
                        closed = True
                        break
                if not closed:
                    logging.warning("Dialog did not close within 60s, waiting 8s extra...")
                    time.sleep(8)
                logging.info(f"[OK] Successfully posted {len(paths)} book photos to Facebook Group: {target_group}")
                for img_id in ids:
                    database.mark_image_group_published(img_id)
                context.close()
                import telegram_bot
                telegram_bot.send_alert_to_all(f"✅ [NHÓM FACEBOOK] Đã tự động đăng bài kèm {len(paths)} ảnh sách lên nhóm:\n🔗 {target_group}")
                return True
            else:
                logging.error("Could not find submit 'Đăng' button in group dialog.")
                context.close()
                import telegram_bot
                telegram_bot.send_alert_to_all(f"⚠️ [LỖI ĐĂNG NHÓM] Không tìm thấy nút 'Đăng' bài trong nhóm:\n🔗 {target_group}")
                return False
        except Exception as e:
            logging.error(f"Error posting to Facebook Group: {e}")
            context.close()
            import telegram_bot
            telegram_bot.send_alert_to_all(f"⚠️ [LỖI ĐĂNG NHÓM] Đăng bài lên nhóm Facebook thất bại: {e}")
            return False
if __name__ == "__main__":
    post_single_book_to_group()