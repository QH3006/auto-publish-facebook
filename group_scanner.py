import re
import time
import logging
from typing import List, Dict
from datetime import datetime
import config
import database
import text_utils
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
def has_buyer_intent(text: str) -> bool:
    if not text:
        return False
    norm_text = text_utils.normalize_text(text).lower()
    for kw in config.BUYER_INTENT_KEYWORDS:
        if kw.lower() in norm_text:
            return True
    return False
def scan_facebook_groups() -> int:
    group_urls = config.MONITORED_GROUP_URLS
    if not group_urls:
        logging.warning("No Facebook Group URLs configured in config.MONITORED_GROUP_URLS.")
        logging.info("Tip: Add group URLs to config.py to start scanning for customer inquiries.")
        return 0
    logging.info(f"Starting group scan across {len(group_urls)} group(s)...")
    from playwright.sync_api import sync_playwright
    new_leads_count = 0
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
                    logging.info("Fallback cookies loaded.")
            except Exception:
                pass
        page = context.new_page() if not context.pages else context.pages[0]
        for group_url in group_urls:
            logging.info(f"Scanning group: {group_url}")
            try:
                page.goto(group_url, wait_until="domcontentloaded", timeout=60000)
                time.sleep(3)
                for _ in range(8):
                    page.mouse.wheel(0, 1500)
                    time.sleep(2)
                post_cards = page.locator("div[role='article']").all()
                logging.info(f"Analyzing {len(post_cards)} posts/comments in group...")
                for card in post_cards:
                    try:
                        card_text = card.inner_text()
                        if not card_text:
                            continue
                        if not has_buyer_intent(card_text):
                            continue
                        matched_books = database.search_available_books(card_text)
                        if not matched_books:
                            continue
                        post_link = group_url
                        links = card.locator("a[role='link']").all()
                        for lnk in links:
                            href = lnk.get_attribute("href") or ""
                            if "/posts/" in href or "/permalink/" in href or "story_fbid" in href:
                                if href.startswith("/"):
                                    post_link = f"https://www.facebook.com{href}"
                                else:
                                    post_link = href
                                break
                        for book in matched_books:
                            snippet = card_text.replace("\n", " ")[:200]
                            saved = database.save_lead(
                                group_url=group_url,
                                post_url=post_link,
                                content_snippet=snippet,
                                matched_book_id=book["id"],
                                matched_book_title=book["title"]
                            )
                            if saved:
                                new_leads_count += 1
                                logging.info(f"[LEAD MATCH] Customer looking for '{book['title']}' | Link: {post_link}")
                    except Exception as err:
                        logging.debug(f"Error processing card: {err}")
                        continue
            except Exception as e:
                logging.error(f"Error scanning group {group_url}: {e}")
        context.close()
    logging.info(f"Group scan completed. Found {new_leads_count} new potential buyer lead(s).")
    return new_leads_count
if __name__ == "__main__":
    scan_facebook_groups()