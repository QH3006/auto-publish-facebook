import os
import json
import time
import random
import logging
from typing import List, Tuple
from playwright.sync_api import sync_playwright
import config
import database
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
GENERAL_GROUP_CAPTIONS = [
    "Tiệm gửi đến cả nhà một số tựa sách hay hôm nay, bạn ưng cuốn nào cứ nhắn tiệm nhé! #SachHay #TiemSachCuaThuong",
    "Ghé tiệm hôm nay để chọn cho mình một người bạn đồng hành nhé, bạn quan tâm cuốn nào nhắn tiệm nha! #SachHay #TiemSachCuaThuong",
    "Mỗi cuốn sách là một hành trình thú vị. Mời cả nhà tham khảo vài tựa sách đang có sẵn tại tiệm nhé! #SachHay #TiemSachCuaThuong",
    "Một vài đầu sách hay gửi bạn đọc, bạn nào cần thêm ảnh chi tiết cuốn nào cứ nhắn tiệm nha! #SachHay #TiemSachCuaThuong",
]
def _cleanup_browser_locks():
    for lf in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
        p = config.BROWSER_PROFILE_DIR / lf
        if p.exists():
            try: os.remove(p)
            except Exception: pass
def _load_cookies_fallback(context):
    if not config.COOKIES_PATH.exists():
        return
    try:
        with open(config.COOKIES_PATH, "r", encoding="utf-8") as f:
            cookies = json.load(f)
        clean = []
        for c in cookies:
            c2 = dict(c)
            if c2.get("sameSite") not in ("Strict", "Lax", "None"):
                c2["sameSite"] = "Lax"
            clean.append(c2)
        if clean:
            context.add_cookies(clean)
    except Exception:
        pass
def _send_tg_alert(msg: str):
    try:
        import telegram_bot
        telegram_bot.send_alert_to_all(msg)
    except Exception:
        pass
def _post_to_one_group(page, target_group: str, paths: List[str], caption: str) -> Tuple[bool, str]:
    try:
        page.goto(target_group, wait_until="domcontentloaded", timeout=60000)
        time.sleep(4)
        if "login" in page.url.lower() or page.locator("input[name='email'], input[name='pass'], [data-testid='royal_login_button']").count() > 0:
            logging.error("Facebook session has expired.")
            try: page.screenshot(path=str(config.STORAGE_DIR / "group_post_error.png"))
            except Exception: pass
            return False, "SESSION_EXPIRED"
        composer_trigger = page.locator(
            "div[role='button']:has-text('Bạn viết gì đi...'), "
            "div[role='button']:has-text('Tạo bài viết công khai...'), "
            "div[role='button']:has-text('Viết gì đó...'), "
            "div[role='button']:has-text('Bạn đang nghĩ gì?'), "
            "div[role='button']:has-text('Create a public post...'), "
            "div[role='button']:has-text('Write something...'), "
            "span:has-text('Bạn viết gì đi...'), "
            "span:has-text('Write something...')"
        ).first
        if composer_trigger.count() == 0:
            logging.error(f"Could not locate group post creation box in {target_group}.")
            try: page.screenshot(path=str(config.STORAGE_DIR / "group_post_error.png"))
            except Exception: pass
            return False, "Không thấy khung tạo bài viết (chưa tham gia nhóm hoặc giao diện khác)"
        composer_trigger.click()
        time.sleep(3)
        dialog = page.locator("div[role='dialog']").filter(has_text="Tạo bài viết").first
        if dialog.count() == 0:
            dialog = page.locator("div[role='dialog']").filter(has_text="Create post").first
        if dialog.count() == 0:
            dialog = page.locator("div[role='dialog']:visible").last
        dialog.wait_for(state="visible", timeout=12000)
        add_photo_btn = dialog.locator("div[aria-label='Ảnh/video'], div[role='button']:has-text('Ảnh/video'), div[aria-label*='Ảnh/video' i], div[aria-label*='Photo/video' i]").first
        if add_photo_btn.count() > 0:
            logging.info("Clicking Add photo button in group dialog...")
            add_photo_btn.click()
            time.sleep(2)
        file_input = dialog.locator("input[type='file']")
        if file_input.count() == 0:
            file_input = page.locator("div[role='dialog'] input[type='file']")
        if file_input.count() == 0:
            file_input = page.locator("input[type='file']")
        if file_input.count() > 0:
            try:
                file_input.first.set_input_files(paths)
                logging.info(f"Uploaded {len(paths)} photos to group composer dialog.")
                time.sleep(6)
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
        post_btn = dialog.locator("div[aria-label='Đăng'], div[aria-label='Post']").last
        if post_btn.count() == 0:
            post_btn = dialog.locator("div[role='button']:text-is('Đăng'), div[role='button']:text-is('Post')").last
        if post_btn.count() == 0:
            post_btn = page.locator("div[role='dialog'] div[aria-label='Đăng'], div[role='dialog'] div[aria-label='Post']").last
        if post_btn.count() > 0 and post_btn.is_visible():
            for _ in range(25):
                if post_btn.get_attribute("aria-disabled") != "true":
                    break
                time.sleep(1)
            post_btn.click()
            logging.info("Clicked real 'Đăng' button in Group. Waiting for dialog to detach...")
            closed = False
            for sec in range(60):
                time.sleep(1)
                if page.locator("div[role='dialog']:visible").count() == 0:
                    closed = True
                    break
                if sec >= 5:
                    has_editor = page.locator("div[role='dialog'] div[contenteditable='true']:visible").count() > 0
                    has_post_btn = page.locator("div[role='dialog'] div[aria-label='Đăng']:visible, div[role='dialog'] div[aria-label='Post']:visible").count() > 0
                    if not has_editor and not has_post_btn:
                        closed = True
                        break
            if not closed:
                logging.warning("Dialog did not close within 60s, waiting 8s extra...")
                time.sleep(8)
            logging.info(f"[OK] Successfully posted {len(paths)} book photos to Facebook Group: {target_group}")
            return True, "OK"
        logging.error(f"Could not find submit 'Đăng' button in group dialog: {target_group}")
        try: page.screenshot(path=str(config.STORAGE_DIR / "group_post_error.png"))
        except Exception: pass
        return False, "Không tìm thấy nút 'Đăng' trong hộp thoại"
    except Exception as e:
        logging.error(f"Error posting to Facebook Group {target_group}: {e}")
        try: page.screenshot(path=str(config.STORAGE_DIR / "group_post_error.png"))
        except Exception: pass
        return False, str(e)
def post_single_book_to_group(group_url: str = None, count: int = None) -> bool:
    _cleanup_browser_locks()
    target_groups = [group_url] if group_url else list(config.TARGET_POST_GROUP_URLS)
    if not target_groups:
        logging.warning("No target group URLs configured in config.TARGET_POST_GROUP_URLS.")
        return False
    num_images = count if count is not None else getattr(config, "GROUP_POST_IMAGES_COUNT", 10)
    logging.info(f"--- STARTING DAILY GROUP POSTING ({num_images} images/post at {config.GROUP_POSTING_HOUR}) across {len(target_groups)} group(s) ---")
    candidates = database.get_unposted_eligible_images(min_days=0, max_days=999)
    valid_candidates = [x for x in candidates if os.path.exists(x["local_path"])]
    if not valid_candidates:
        logging.warning("No eligible unposted book images found in inventory.")
        return False
    selected = random.sample(valid_candidates, min(num_images, len(valid_candidates)))
    paths = [x["local_path"] for x in selected]
    ids = [x["id"] for x in selected]
    logging.info(f"Selected {len(paths)} book images to upload to {len(target_groups)} group(s).")
    caption = random.choice(GENERAL_GROUP_CAPTIONS)
    logging.info(f"Group caption:\n{caption}")
    succeeded_groups, failed_groups = [], []
    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(config.BROWSER_PROFILE_DIR),
            "headless": True,
            "args": ["--disable-notifications", "--disable-popup-blocking"],
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1600, "height": 900},
        }
        if config.BROWSER_CHANNEL:
            launch_kwargs["channel"] = config.BROWSER_CHANNEL
        context = p.chromium.launch_persistent_context(**launch_kwargs)
        _load_cookies_fallback(context)
        page = context.new_page() if not context.pages else context.pages[0]
        try:
            for idx, target_group in enumerate(target_groups, 1):
                logging.info(f"[NHÓM {idx}/{len(target_groups)}] Đang đăng bài lên: {target_group}")
                ok, reason = _post_to_one_group(page, target_group, paths, caption)
                if reason == "SESSION_EXPIRED":
                    context.close()
                    _send_tg_alert("[CẢNH BÁO] Phiên đăng nhập Facebook của bot đã hết hạn! Vui lòng mở Terminal chạy: python main.py --login-fb để cập nhật lại.")
                    return False
                if ok:
                    succeeded_groups.append(target_group)
                else:
                    failed_groups.append((target_group, reason))
                if idx < len(target_groups):
                    delay_s = random.randint(60, 120)
                    logging.info(f"Đang nghỉ giãn cách {delay_s}s trước khi đăng nhóm tiếp theo để tránh spam...")
                    time.sleep(delay_s)
        finally:
            try: context.close()
            except Exception: pass
    if succeeded_groups:
        for img_id in ids:
            database.mark_image_group_published(img_id)
    summary_lines = [f"📢 [BÁO CÁO ĐĂNG NHÓM FACEBOOK] ({len(succeeded_groups)}/{len(target_groups)} nhóm thành công, {len(paths)} ảnh/bài)"]
    if succeeded_groups:
        summary_lines.append("\n✅ Thành công:")
        summary_lines.extend(f"- {u}" for u in succeeded_groups)
    if failed_groups:
        summary_lines.append("\n⚠️ Thất bại:")
        summary_lines.extend(f"- {u} ({r})" for u, r in failed_groups)
    _send_tg_alert("\n".join(summary_lines))
    return len(succeeded_groups) > 0
if __name__ == "__main__":
    post_single_book_to_group()
