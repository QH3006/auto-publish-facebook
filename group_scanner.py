import os
import re
import time
import hashlib
import logging
import requests
from typing import List, Dict
from datetime import datetime, date
import config
import database
import text_utils
import ai_engine
import telegram_bot
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
def is_seller_post(text: str) -> bool:
    if not text:
        return False
    norm = text_utils.normalize_text(text).lower()
    for kw in getattr(config, 'SELLER_EXCLUDE_KEYWORDS', []):
        if kw.lower() in norm:
            return True
    return False
def has_buyer_intent(text: str) -> bool:
    if not text or is_seller_post(text):
        return False
    norm_text = text_utils.normalize_text(text).lower()
    for kw in config.BUYER_INTENT_KEYWORDS:
        if kw.lower() in norm_text:
            return True
    return False
def scan_facebook_groups(max_days: int = 7, deep_scan: bool = True) -> int:
    group_urls = config.MONITORED_GROUP_URLS
    if not group_urls:
        logging.warning("Chưa cấu hình URL nhóm Facebook trong config.MONITORED_GROUP_URLS.")
        return 0
    scroll_count = 18 if deep_scan else 6
    logging.info(f"Bắt đầu quét {len(group_urls)} nhóm Facebook (Lọc bài trong {max_days} ngày gần nhất, cuộn {scroll_count} lần)...")
    from playwright.sync_api import sync_playwright
    new_leads_count = 0
    today = date.today()
    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(config.BROWSER_PROFILE_DIR),
            "headless": True,
            "args": ["--disable-notifications", "--disable-popup-blocking"],
            "viewport": {"width": 1280, "height": 900}
        }
        if config.BROWSER_CHANNEL:
            launch_kwargs["channel"] = config.BROWSER_CHANNEL
        context = p.chromium.launch_persistent_context(**launch_kwargs)
        page = context.pages[0] if context.pages else context.new_page()
        for g_idx, group_url in enumerate(group_urls, 1):
            logging.info(f"[{g_idx}/{len(group_urls)}] Đang truy cập nhóm: {group_url}")
            try:
                time.sleep(2.5)
                try:
                    page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
                except Exception:
                    time.sleep(3)
                    page.goto(group_url, wait_until="domcontentloaded", timeout=45000)
                time.sleep(3)
                try:
                    page.mouse.click(600, 400)
                    time.sleep(0.5)
                except Exception:
                    pass
                seen_texts = set()
                group_cards = []
                for s_i in range(scroll_count):
                    items = page.evaluate("""() => {
                        let out = [];
                        let feed = document.querySelector("div[role='feed']") || document.body;
                        let els = feed.querySelectorAll("div[dir='auto']");
                        for (let el of els) {
                            let t = el.innerText ? el.innerText.trim() : '';
                            if (t.length < 20) continue;
                            let p = el;
                            let postLink = '';
                            let dateText = '';
                            let imgs = [];
                            let level = 0;
                            while (p && p !== feed && level < 15) {
                                if (!postLink) {
                                    let a = p.querySelector("a[href*='/posts/'], a[href*='/permalink/'], a[href*='story_fbid']");
                                    if (a) postLink = a.href;
                                }
                                if (!dateText) {
                                    let links = p.querySelectorAll('a span, span');
                                    for (let l of links) {
                                        let txt = l.innerText || l.getAttribute('aria-label') || '';
                                        if (txt && (txt.includes('tháng') || txt.includes('ngày') || txt.includes('tuần') || txt.includes('hôm qua') || txt.includes('giờ') || txt.includes('phút'))) {
                                            dateText = txt;
                                            break;
                                        }
                                    }
                                }
                                if (imgs.length === 0) {
                                    let imgEls = p.querySelectorAll('img');
                                    for (let img of imgEls) {
                                        let src = img.src || '';
                                        if (src.includes('fbcdn.net') && !src.includes('emoji') && !src.includes('rsrc.php') && img.width > 90) {
                                            imgs.push(src);
                                        }
                                    }
                                }
                                p = p.parentElement;
                                level++;
                            }
                            out.push({ text: t, postLink: postLink, dateText: dateText, imgs: imgs });
                        }
                        return out;
                    }""")
                    for it in items:
                        t = it.get("text", "").strip()
                        if t and t not in seen_texts:
                            seen_texts.add(t)
                            group_cards.append(it)
                    for _ in range(3):
                        page.keyboard.press("PageDown")
                        time.sleep(0.3)
                    time.sleep(1.2)
                logging.info(f"-> Thu thập được {len(group_cards)} bài viết trong nhóm. Đang phân tích...")
                for item in group_cards:
                    try:
                        card_text = item.get("text", "")
                        raw_date_str = item.get("dateText", "")
                        post_link = item.get("postLink", "") or group_url
                        post_imgs = item.get("imgs", [])
                        if raw_date_str:
                            post_date_str = text_utils.parse_vietnamese_date(raw_date_str)
                            try:
                                p_date = datetime.strptime(post_date_str, "%Y-%m-%d").date()
                                age_days = (today - p_date).days
                                if age_days > max_days:
                                    continue
                            except Exception:
                                pass
                        if is_seller_post(card_text):
                            continue
                        has_intent = has_buyer_intent(card_text)
                        has_img_intent = len(post_imgs) > 0 and any(kw in card_text.lower() for kw in ["ai có như hình", "ai có như ảnh", "tìm như hình", "tìm như ảnh", "cần tìm như", "ai có mấy cuốn này", "ai có mấy quyển này", "tìm những cuốn này", "ai có trong hình", "ai có trong ảnh", "ai có cuốn này", "ai có quyển này", "ai còn cuốn", "ảnh đính kèm"])
                        if not has_intent and not has_img_intent:
                            continue
                        snippet = card_text.replace("\n", " ").strip()[:140]
                        logging.info(f"[PHÁT HIỆN BÀI ĐĂNG CÓ Ý ĐỊNH MUA]: \"{snippet}...\"")
                        matched_books = []
                        text_matches = database.search_available_books(card_text)
                        for b in text_matches:
                            b["matched_source"] = "Văn bản bài đăng"
                            matched_books.append(b)
                        if post_imgs:
                            temp_dir = config.STORAGE_DIR / "group_temp"
                            temp_dir.mkdir(parents=True, exist_ok=True)
                            for img_idx, img_url in enumerate(post_imgs[:2]):
                                try:
                                    resp = requests.get(img_url, timeout=12)
                                    if resp.status_code == 200:
                                        img_name = f"lead_{hashlib.md5(img_url.encode()).hexdigest()[:8]}.jpg"
                                        temp_path = str(temp_dir / img_name)
                                        with open(temp_path, "wb") as f:
                                            f.write(resp.content)
                                        logging.info(f"   [ĐỌC ẢNH ĐÍNH KÈM] Gọi Gemini Vision đọc bìa/ghi chú (ảnh {img_idx+1})...")
                                        vision_data = ai_engine.extract_buyer_inquiry_from_image(temp_path)
                                        time.sleep(2.5)
                                        found_titles = vision_data.get("titles", [])
                                        if found_titles:
                                            logging.info(f"   -> Đọc được từ ảnh: {found_titles}")
                                            for title in found_titles:
                                                v_matches = database.search_available_books(title)
                                                for vb in v_matches:
                                                    if not any(mb["id"] == vb["id"] for mb in matched_books):
                                                        vb["matched_source"] = f"Ảnh đính kèm ('{title}')"
                                                        matched_books.append(vb)
                                except Exception as img_err:
                                    logging.debug(f"Error scanning buyer image: {img_err}")
                        if not matched_books:
                            continue
                        for book in matched_books:
                            saved = database.save_lead(
                                group_url=group_url,
                                post_url=post_link,
                                content_snippet=snippet,
                                matched_book_id=book["id"],
                                matched_book_title=book["title"]
                            )
                            if saved:
                                new_leads_count += 1
                                disp_price = telegram_bot.format_price_vnd(book.get('price'))
                                price_info = f" (Giá kho: {disp_price})" if book.get('price') else ""
                                source_info = f" [{book.get('matched_source')}]" if book.get('matched_source') else ""
                                logging.info(f"-> [TRÙNG KHỚP KHO SÁCH!]{source_info} Khách hỏi: '{book['title']}'{price_info} | Link: {post_link}")
                                telegram_bot.notify_new_lead({
                                    "matched_book_title": book["title"],
                                    "price": book.get("price", ""),
                                    "category": book.get("category", ""),
                                    "matched_source": book.get("matched_source", ""),
                                    "content_snippet": snippet,
                                    "post_url": post_link
                                })
                    except Exception as err:
                        logging.debug(f"Error processing item: {err}")
                        continue
            except Exception as e:
                logging.error(f"Lỗi khi quét nhóm {group_url}: {e}")
        context.close()
    logging.info(f"Hoàn thành quét nhóm. Phát hiện {new_leads_count} khách hỏi mua trùng khớp kho sách.")
    return new_leads_count
if __name__ == "__main__":
    scan_facebook_groups(max_days=7, deep_scan=True)
