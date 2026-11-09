import os
import re
import time
import hashlib
import logging
from datetime import datetime, date
from typing import Optional, List, Dict
import requests
import config
import database
import text_utils
import ai_engine
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def parse_caption_price(text: str) -> str:
    if not text:
        return ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines:
        m = re.search(r"^\s*(\d{1,4}(?:[.,]\d{3})?)\s*(k|đ|vnd)?(?:\s*[\(\[].*?[\)\]]|\s+seal|\s+mới|\s+nguyên|\s+tập)?", line, re.IGNORECASE)
        if m:
            raw_num_str = m.group(1).replace(".", "").replace(",", "").strip()
            unit = (m.group(2) or "").lower()
            try:
                num = int(raw_num_str)
                if num <= 0:
                    continue
                if unit == "k" or num < 1000:
                    return str(num * 1000)
                else:
                    return str(num)
            except ValueError:
                pass
    return ""
def download_and_save_book_theater(image_url: str, post_id: str, post_date_str: str, price_str: str, default_category: str = "") -> Optional[str]:
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        resp = requests.get(image_url, headers=headers, timeout=20)
        if resp.status_code != 200 or not resp.content:
            return None
        img_hash = compute_sha256(resp.content)
        if database.is_image_hash_saved(img_hash):
            logging.info(f"Ảnh {img_hash[:10]} đã có trong cơ sở dữ liệu, bỏ qua.")
            return None
        filename = f"{post_id}_{img_hash[:10]}.jpg"
        local_path = str(config.IMAGES_DIR / filename)
        with open(local_path, "wb") as f:
            f.write(resp.content)
        logging.info(f"[PHÂN TÍCH ẢNH BÌA] Đang gọi Gemini AI đọc tựa sách: {filename}...")
        meta = ai_engine.extract_book_info(local_path)
        is_valid = meta.get("is_valid_book", True)
        book_title = meta.get("title", "").strip()
        book_author = meta.get("author", "").strip()
        book_category = default_category or meta.get("category", "").strip() or "Khác"
        if not is_valid or not book_title or book_title == "Nhiều cuốn sách":
            logging.info(f"-> [BỎ QUA] Ảnh chỉ là chồng sách/kệ sách hoặc không nhận diện được tựa sách chính ({filename}).")
            try:
                os.remove(local_path)
            except Exception:
                pass
            return None
        if price_str and database.is_duplicate_book(book_title, price_str):
            logging.info(f"-> [TRÙNG LẶP] Sách '{book_title}' cùng giá {price_str}đ đã có trong kho. Tự động bỏ qua.")
            try:
                os.remove(local_path)
            except Exception:
                pass
            return None
        saved = database.save_image(
            post_id=post_id,
            image_url=image_url,
            local_path=local_path,
            image_hash=img_hash,
            post_date=post_date_str,
            title=book_title,
            author=book_author,
            category=book_category,
            price=price_str,
            is_single_book=1,
            is_reviewed=0
        )
        if saved:
            price_display = f"{int(price_str):,} đ".replace(",", ".") if price_str else "Chưa có giá"
            logging.info(f"-> [LƯU THÀNH CÔNG] Sách: '{book_title}' | Thể loại: '{book_category}' | Tác giả: '{book_author}' | Giá: {price_display} | Chờ duyệt")
            return local_path
        return None
    except Exception as e:
        logging.error(f"Lỗi khi xử lý ảnh sách {image_url}: {e}")
        return None
def run_scanner(page_url: Optional[str] = None, min_days: Optional[int] = None, max_days: Optional[int] = None, scrolls: int = 10) -> int:
    target_url = page_url or config.TARGET_PAGE_URL
    scan_min_days = min_days if min_days is not None else config.MIN_DAYS_OLD
    scan_max_days = max_days if max_days is not None else config.MAX_DAYS_OLD
    if not target_url or "YOUR_PAGE_URL_HERE" in target_url:
        logging.warning("TARGET_PAGE_URL is not configured in config.py.")
        return 0
    logging.info(f"Starting page scan: {target_url} (Post age: {scan_min_days} to {scan_max_days} days)")
    from playwright.sync_api import sync_playwright
    new_images_count = 0
    today = date.today()
    with sync_playwright() as p:
        launch_kwargs = {
            "user_data_dir": str(config.BROWSER_PROFILE_DIR),
            "headless": True
        }
        if config.BROWSER_CHANNEL:
            launch_kwargs["channel"] = config.BROWSER_CHANNEL
        context = p.chromium.launch_persistent_context(**launch_kwargs)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)
            if "login" in page.url.lower() or page.locator("input[name='email'], input[name='pass']").count() > 0:
                logging.error("Facebook session has expired.")
                import telegram_bot
                telegram_bot.send_alert_to_all("[CẢNH BÁO] Phiên đăng nhập Facebook của bot đã hết hạn! Vui lòng mở Terminal chạy: python main.py --login-fb để cập nhật lại.")
                context.close()
                return 0
            logging.info(f"Cuộn trang {scrolls} lần và thu thập bài viết theo thời gian thực...")
            try:
                page.mouse.click(600, 400)
                time.sleep(1)
            except Exception:
                pass
            processed_cards = set()
            for scroll_idx in range(scrolls):
                for _ in range(3):
                    page.keyboard.press("PageDown")
                    time.sleep(0.4)
                time.sleep(1.8)
                dom_items = page.evaluate("""() => {
                    let out = [];
                    let seen = new Set();
                    let els = document.querySelectorAll("div[dir='auto']");
                    for (let el of els) {
                        let t = el.innerText ? el.innerText.trim() : '';
                        if (!t || t.length < 25 || seen.has(t)) continue;
                        seen.add(t);
                        let p = el;
                        let photoHref = '';
                        let dateText = '';
                        let level = 0;
                        while (p && p !== document.body && level < 25) {
                            if (!photoHref) {
                                let a = p.querySelector("a[href*='/photo/'], a[href*='fbid=']");
                                if (a) photoHref = a.href;
                            }
                            if (!dateText) {
                                let links = p.querySelectorAll('a[href*="/posts/"], a[href*="pfbid"], span');
                                for (let l of links) {
                                    let txt = l.innerText || l.getAttribute('aria-label') || '';
                                    if (txt && (txt.includes('tháng') || txt.includes('ngày') || txt.includes('tuần') || txt.includes('hôm qua'))) {
                                        dateText = txt;
                                        break;
                                    }
                                }
                            }
                            if (photoHref && dateText) break;
                            p = p.parentElement;
                            level++;
                        }
                        out.push({ text: t, photoHref: photoHref, dateText: dateText });
                    }
                    return out;
                }""")
                for it in dom_items:
                    try:
                        card_text = it.get("text", "").strip()
                        if not card_text or card_text in processed_cards:
                            continue
                        is_ok, reason = text_utils.check_post_eligibility(card_text)
                        if not is_ok:
                            continue
                        processed_cards.add(card_text)
                        raw_date_str = it.get("dateText", "")
                        post_date_str = text_utils.parse_vietnamese_date(raw_date_str)
                        try:
                            p_date = datetime.strptime(post_date_str, "%Y-%m-%d").date()
                            age_days = (date.today() - p_date).days
                            if age_days > scan_max_days:
                                logging.info(f"-> [BỎ QUA] Bài ngày {post_date_str} ({age_days} ngày trước) vượt quá mốc {scan_max_days} ngày.")
                                continue
                        except Exception:
                            pass
                        header_snippet = card_text.split('\n')[0][:50]
                        post_id = f"fb_post_{hashlib.md5((post_date_str + '_' + card_text).encode('utf-8')).hexdigest()[:12]}"
                        if database.is_post_saved(post_id):
                            logging.info(f"-> [BÀI ĐÃ LƯU] Bài ngày {post_date_str} ({post_id}) đã có trong kho, bỏ qua.")
                            continue
                        logging.info(f"[TÌM THẤY BÀI MỚI HỢP LỆ]: {header_snippet}... (Ngày: {post_date_str})")
                        post_category = text_utils.extract_category_from_post(card_text)
                        database.save_post(post_id, target_url, card_text, post_date_str)
                        photo_href = it.get("photoHref", "")
                        if photo_href:
                            logging.info(f"-> Mở chế độ xem chi tiết từng ảnh (Theater View) để đọc giá và bìa sách... (Thể loại bài: '{post_category or 'Chưa rõ'}')")
                            photo_page = None
                            try:
                                photo_page = context.new_page()
                                photo_page.goto(photo_href, wait_until="domcontentloaded", timeout=45000)
                                time.sleep(3)
                                seen_theater_urls = set()
                                max_photos = 50
                                for step in range(max_photos):
                                    current_url = photo_page.url
                                    if current_url in seen_theater_urls or "/photo/" not in current_url:
                                        break
                                    seen_theater_urls.add(current_url)
                                    price_raw = photo_page.evaluate("""() => {
                                        let dialog = document.querySelector("div[role='dialog']");
                                        let container = dialog || document.body;
                                        let textElements = container.querySelectorAll("div[dir='auto'], span[dir='auto']");
                                        for (let el of textElements) {
                                            let t = el.innerText.trim();
                                            if (/^\\s*\\d{1,4}(?:[.,]\\d{3})?(\\s*(k|đ|vnd))?(\\s*[\\(\\[].*?[\\)\\]]|\\s+seal|\\s+mới|\\s+nguyên)?\\s*$/i.test(t)) {
                                                return t;
                                            }
                                        }
                                        return "";
                                    }""")
                                    price_val = parse_caption_price(price_raw)
                                    img_src = photo_page.evaluate("""() => {
                                        let img = document.querySelector("div[data-visualcompletion='media-vc-image'] img, img[data-visualcompletion='media-vc-image']");
                                        return img ? img.src : "";
                                    }""")
                                    if img_src and "fbcdn.net" in img_src:
                                        saved_path = download_and_save_book_theater(img_src, post_id, post_date_str, price_val, default_category=post_category)
                                        if saved_path:
                                            new_images_count += 1
                                    photo_page.keyboard.press("ArrowRight")
                                    time.sleep(2.5)
                            except Exception as th_err:
                                logging.error(f"Lỗi khi duyệt ảnh trong bài viết: {th_err}")
                            finally:
                                if photo_page:
                                    try:
                                        photo_page.close()
                                    except Exception:
                                        pass
                    except Exception as card_err:
                        logging.error(f"Lỗi khi xử lý bài viết: {card_err}")
                        continue
        except Exception as e:
            logging.error(f"Error during scan: {e}")
        finally:
            context.close()
    logging.info(f"Scan completed. Downloaded {new_images_count} new eligible images.")
    if new_images_count > 0:
        try:
            import telegram_bot
            import web_admin
            ip = web_admin.get_local_ip()
            telegram_bot.send_alert_to_all(
                f"📚 [KHO VỪA THÊM {new_images_count} ẢNH SÁCH MỚI]\n\n"
                f"Các ảnh mới đã được đưa vào trạng thái 'Chờ soát lại' để bạn đối chiếu bìa font lạ/ảnh mờ.\n"
                f"👉 Mở Web Dashboard để soát và sửa tay: http://{ip}:8080\n"
                f"Hoặc gõ lệnh /soat trên Telegram để xem ảnh và duyệt trực tiếp!"
            )
        except Exception:
            pass
    return new_images_count
if __name__ == "__main__":
    run_scanner()
