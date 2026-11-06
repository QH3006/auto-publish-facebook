import os
import re
import time
import hashlib
import logging
import requests
from datetime import datetime, date, timedelta
from typing import List, Dict, Optional
import config
import database
import text_utils
import ai_engine
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
def parse_facebook_relative_time(time_text: str) -> Optional[date]:
    if not time_text:
        return None
    today = date.today()
    t_lower = time_text.strip().lower()
    match_week = re.search(r"(\d+)\s*(?:tuần|w|week)", t_lower)
    if match_week:
        weeks = int(match_week.group(1))
        return today - timedelta(days=weeks * 7)
    match_day = re.search(r"(\d+)\s*(?:ngày|d|day)", t_lower)
    if match_day:
        days = int(match_day.group(1))
        return today - timedelta(days=days)
    if re.search(r"\d+\s*(?:giờ|phút|h|m|hour|min)", t_lower) or "vừa xong" in t_lower:
        return today
    if "hôm qua" in t_lower or "yesterday" in t_lower:
        return today - timedelta(days=1)
    match_date = re.search(r"(\d{1,2})\s+tháng\s+(\d{1,2})(?:,?\s+(\d{4}))?", t_lower)
    if match_date:
        d = int(match_date.group(1))
        m = int(match_date.group(2))
        y = int(match_date.group(3)) if match_date.group(3) else today.year
        try:
            return date(y, m, d)
        except ValueError:
            pass
    return None
def compute_sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()
def download_and_save_image(image_url: str, post_id: str, post_date_str: str) -> Optional[str]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(image_url, headers=headers, timeout=20)
        if resp.status_code != 200 or not resp.content:
            return None
        img_hash = compute_sha256(resp.content)
        filename = f"{post_id}_{img_hash[:10]}.jpg"
        local_path = str(config.IMAGES_DIR / filename)
        if not os.path.exists(local_path):
            with open(local_path, "wb") as f:
                f.write(resp.content)
        meta = ai_engine.extract_book_info(local_path)
        book_title = meta.get("title", "")
        book_author = meta.get("author", "")
        saved = database.save_image(
            post_id=post_id,
            image_url=image_url,
            local_path=local_path,
            image_hash=img_hash,
            post_date=post_date_str,
            title=book_title,
            author=book_author
        )
        if saved:
            logging.info(f"-> Saved book: '{book_title}' ({filename})")
            return local_path
        else:
            return None
    except Exception as e:
        logging.error(f"Error downloading image {image_url}: {e}")
        return None
def run_scanner(page_url: Optional[str] = None) -> int:
    target_url = page_url or config.TARGET_PAGE_URL
    if not target_url or "YOUR_PAGE_URL_HERE" in target_url:
        logging.warning("TARGET_PAGE_URL is not configured in config.py.")
        return 0
    logging.info(f"Starting page scan: {target_url}")
    from playwright.sync_api import sync_playwright
    new_images_count = 0
    today = date.today()
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=str(config.BROWSER_PROFILE_DIR),
            headless=True,
            args=["--disable-notifications", "--disable-popup-blocking"],
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900}
        )
        if config.COOKIES_PATH.exists():
            import json
            try:
                with open(config.COOKIES_PATH, "r", encoding="utf-8") as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                    logging.info("Fallback cookies loaded.")
            except Exception:
                pass
        page = context.new_page() if not context.pages else context.pages[0]
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(3)
            try:
                close_btn = page.locator("div[aria-label='Đóng'], div[aria-label='Close'], [role='button']:has-text('Đóng')")
                if close_btn.count() > 0:
                    close_btn.first.click()
            except Exception:
                pass
            logging.info("Scrolling page to load older posts...")
            for _ in range(12):
                page.mouse.wheel(0, 1500)
                time.sleep(2)
            post_cards = page.locator("div[role='article']").all()
            logging.info(f"Found {len(post_cards)} post containers on page.")
            for card in post_cards:
                try:
                    card_text = card.inner_text()
                    if not card_text:
                        continue
                    post_date = None
                    time_elements = card.locator("a[role='link'] span, span[dir='auto']").all()
                    for t_el in time_elements:
                        t_text = t_el.inner_text().strip()
                        parsed_date = parse_facebook_relative_time(t_text)
                        if parsed_date:
                            post_date = parsed_date
                            break
                    if not post_date:
                        post_date = today - timedelta(days=10)
                    age_days = (today - post_date).days
                    if age_days < config.MIN_DAYS_OLD:
                        logging.debug(f"Post too recent ({age_days}d < {config.MIN_DAYS_OLD}d). Skip.")
                        continue
                    if age_days > config.MAX_DAYS_OLD:
                        logging.debug(f"Post too old ({age_days}d > {config.MAX_DAYS_OLD}d). Skip.")
                        continue
                    is_ok, reason = text_utils.check_post_eligibility(card_text)
                    if not is_ok:
                        logging.debug(f"Post skipped: {reason}")
                        continue
                    logging.info(f"[MATCH FOUND] Eligible post (age: {age_days} days).")
                    post_id = f"fb_post_{hashlib.md5(card_text[:50].encode('utf-8')).hexdigest()[:12]}"
                    post_date_str = post_date.strftime("%Y-%m-%d")
                    database.save_post(post_id, target_url, card_text, post_date_str)
                    img_elements = card.locator("img").all()
                    for img in img_elements:
                        src = img.get_attribute("src")
                        if not src:
                            continue
                        if "emoji.php" in src or "rsrc.php" in src or "p50x50" in src:
                            continue
                        saved_path = download_and_save_image(src, post_id, post_date_str)
                        if saved_path:
                            new_images_count += 1
                except Exception as card_err:
                    logging.warning(f"Error processing post card: {card_err}")
                    continue
        except Exception as e:
            logging.error(f"Error during scan: {e}")
        finally:
            context.close()
    logging.info(f"Scan completed. Downloaded {new_images_count} new eligible images.")
    return new_images_count
if __name__ == "__main__":
    run_scanner()