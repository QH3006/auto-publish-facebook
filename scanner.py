import os
import re
import json
import time
import hashlib
import logging
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import requests
import config
import database
import text_utils
import ai_engine
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
_NOISE_LINE_RE = re.compile(
    r"(?:lúc\s+\d{1,2}:\d{2}|giờ\s+trước|phút\s+trước|ngày\s+trước|xem\s+bài\s+viết|\d{1,2}\s+tháng\s+\d{1,2}"
    r"|cho\s+thuê|/ngày|tiệm\s+sách\s+của\s+thương|chỉnh\s+sửa|quảng\s+bá"
    r"|chưa\s+có\s+bình\s+luận|hãy\s+là\s+người\s+đầu\s+tiên|chỉ\s+báo\s+trạng\s+thái)",
    re.IGNORECASE,
)
_PHONE_LINE_RE = re.compile(r"\b0\d{2,3}[.\-\s]?\d{3}[.\-\s]?\d{3,4}\b")
_TRAILING_NON_PRICE_UNIT_RE = re.compile(r"^\s*(?:cuốn|quyển|q\b|tập|bộ|cái|ngày|giờ|tuần|tháng|năm|trang|lượt|người)\b", re.IGNORECASE)
def cleanup_browser_locks():
    for lf in ["SingletonLock", "SingletonSocket", "SingletonCookie"]:
        p = config.BROWSER_PROFILE_DIR / lf
        if p.exists():
            try: os.remove(p)
            except Exception: pass
def compute_sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def _extract_fbid(url: str) -> str:
    if not url: return ""
    m = re.search(r"[?&]fbid=(\d+)", url)
    if m: return m.group(1)
    m2 = re.search(r"/photos?/[^/?]+/(\d+)", url)
    return m2.group(1) if m2 else ""
def _extract_fb_asset_key(image_url: str) -> str:
    if not image_url: return ""
    m = re.search(r"/(\d+_\d+_\d+)_[a-zA-Z0-9]+\.", image_url)
    return m.group(1) if m else ""
def _collect_gql_captions(obj: Any, out_map: Dict[str, str]) -> None:
    if isinstance(obj, dict):
        if obj.get("__typename") in ("Comment", "Story"):
            return
        oid = str(obj.get("id") or "")
        if oid.isdigit() and len(oid) >= 10:
            for field in ("message_preferred_body", "message"):
                body = obj.get(field)
                if isinstance(body, dict):
                    txt = body.get("text")
                    if isinstance(txt, str) and txt.strip():
                        if not out_map.get(oid): out_map[oid] = txt.strip()
                        break
        for v in obj.values():
            _collect_gql_captions(v, out_map)
    elif isinstance(obj, list):
        for item in obj:
            _collect_gql_captions(item, out_map)
def _to_vnd(raw_num_str: str, unit: str = "") -> str:
    s = (raw_num_str or "").strip()
    if not s: return ""
    u = (unit or "").strip().lower()
    m_k_short = re.match(r"^k(\d)$", u)
    if m_k_short:
        try:
            vnd = int(re.sub(r"[.,]", "", s)) * 1000 + int(m_k_short.group(1)) * 100
            return str(vnd) if 5000 <= vnd <= 5000000 else ""
        except ValueError: return ""
    if u in ("k", "nghìn", "ngàn"):
        m_dec = re.match(r"^(\d{1,3})[.,](\d)$", s)
        if m_dec:
            vnd = int(m_dec.group(1)) * 1000 + int(m_dec.group(2)) * 100
            return str(vnd) if 5000 <= vnd <= 5000000 else ""
    try: num = int(s.replace(".", "").replace(",", ""))
    except ValueError: return ""
    if num <= 0: return ""
    has_explicit_unit = u in ("k", "đ", "d", "vnd", "vnđ", "nghìn", "ngàn")
    if u in ("k", "nghìn", "ngàn"):
        vnd = num * 1000 if num < 10000 else num
    elif has_explicit_unit:
        vnd = num * 1000 if num < 1000 else num
    else:
        if 1900 <= num <= 2099: return ""
        vnd = num * 1000 if num < 1000 else num
    if has_explicit_unit: return str(vnd) if 5000 <= vnd <= 5000000 else ""
    return str(vnd) if 10000 <= vnd <= 2000000 else ""
def parse_caption_price(text: str) -> str:
    if not text: return ""
    norm = text_utils.normalize_text(text)
    lines = [l.strip() for l in norm.split("\n") if l.strip()]
    for line in lines:
        if _NOISE_LINE_RE.search(line): continue
        if _PHONE_LINE_RE.search(line) and not re.search(r"(?:giá|pass|k\b|đ\b|vnd)", line, re.IGNORECASE): continue
        m = re.search(r"(?:giá(?:\s+bán)?|pass|bán|đồng giá|sale|chỉ|còn)\s*[:\-=]?\s*(\d{1,3}(?:[.,]\d{3})+|\d{1,3}(?:[.,]\d)?|\d{5,7})\s*(k\d?|đ|vnd|vnđ|nghìn|ngàn)?(?![0-9%])", line, re.IGNORECASE)
        if m:
            unit, tail = m.group(2) or "", line[m.end():]
            if unit or not _TRAILING_NON_PRICE_UNIT_RE.match(tail):
                v = _to_vnd(m.group(1), unit)
                if v: return v
        m = re.search(r"(?<![\d.,])(\d{1,3})\s*k\s*(\d)(?![0-9%])", line, re.IGNORECASE)
        if m:
            vnd = int(m.group(1)) * 1000 + int(m.group(2)) * 100
            if 5000 <= vnd <= 5000000: return str(vnd)
        m = re.search(r"(?<![\d.,])(\d{1,3})[.,](\d)\s*k(?![a-zA-ZÀ-ỹ0-9%])", line, re.IGNORECASE)
        if m:
            v = _to_vnd(f"{m.group(1)}.{m.group(2)}", "k")
            if v: return v
        m = re.search(r"(?<![\d.,])(\d{1,3}(?:[.,]\d{3})+)\s*(k|đ|vnd|vnđ)?(?![0-9%])", line, re.IGNORECASE)
        if m:
            v = _to_vnd(m.group(1), m.group(2) or "")
            if v: return v
        m = re.search(r"(?<![\d.,])(\d{1,7})\s*(k|đ|vnd|vnđ|nghìn|ngàn)(?![a-zA-ZÀ-ỹ0-9%])", line, re.IGNORECASE)
        if m:
            v = _to_vnd(m.group(1), m.group(2))
            if v: return v
        m = re.match(r"^\s*(\d{2,3}|\d{5,6})(?!\s*(?:%|giờ|phút|giây|ngày|tuần|tháng|năm|trang|comment|bình luận|lượt|người|hours?|mins?|days?|weeks?))(?:\s*(?:$|/|[\(\[\-\.,!❤️✨📌🔥]|c\b|cuốn\b|quyển\b|q\b|bộ\b|tập\b|set\b|combo\b|mới\b|seal\b|nguyên\b|bìa\b|sách\b|hơi\b|ố\b|rách\b|đẹp\b|ạ\b|nhé\b|nha\b))", line, re.IGNORECASE)
        if m:
            v = _to_vnd(m.group(1))
            if v: return v
    return ""
def _dismiss_login_modal(pg) -> None:
    try:
        dialogs = pg.locator("div[role='dialog']")
        for i in range(dialogs.count()):
            dlg = dialogs.nth(i)
            has_inputs = dlg.locator("input[name='email'], input[name='pass']").count() > 0
            dlg_txt = ""
            try: dlg_txt = dlg.inner_text(timeout=1000)
            except Exception: pass
            if has_inputs or any(k in dlg_txt for k in ("Xem thêm trên Facebook", "See more on Facebook", "Đăng nhập", "Log in")):
                close_btn = dlg.locator("div[aria-label='Đóng'], div[aria-label='Close']").first
                if close_btn.count() > 0 and close_btn.is_visible():
                    close_btn.click(timeout=2000)
                    time.sleep(0.4)
    except Exception: pass
def _extract_theater_caption_dom(photo_page) -> str:
    try:
        return photo_page.evaluate(r"""() => {
            let root = document.querySelector("div[role='complementary']");
            if (!root) {
                for (let d of document.querySelectorAll("div[role='dialog']")) {
                    if (d.querySelector("input[name='email'], input[name='pass']")) continue;
                    let txt = d.innerText || "";
                    if (txt.includes("Xem thêm trên Facebook") || txt.includes("See more on Facebook")) continue;
                    if (d.querySelector("img, div[dir='auto'], span[dir='auto']")) { root = d; break; }
                }
            }
            if (!root) root = document.querySelector("div[role='main']") || document.body;
            const stopTexts = new Set(["thích", "like", "bình luận", "comment", "chia sẻ", "share", "chỉnh sửa", "edit", "quảng bá bài viết", "boost post", "chưa có bình luận nào", "no comments yet"]);
            let seen = new Set(), lines = [];
            for (let el of root.querySelectorAll("div[dir='auto'], span[dir='auto']")) {
                let cs = window.getComputedStyle(el);
                if (cs.display === "none" || cs.visibility === "hidden") continue;
                let t = (el.innerText || "").trim();
                if (!t) continue;
                if (stopTexts.has(t.toLowerCase())) break;
                if (el.closest("ul, form, [role='button'], [aria-label*='Bình luận' i], [aria-label*='Comment' i], [aria-label*='Cảm xúc' i], [aria-label*='Reaction' i]")) continue;
                if (t.length > 600) continue;
                for (let sub of t.split("\n")) {
                    let s = sub.trim();
                    if (s && !seen.has(s)) { seen.add(s); lines.push(s); }
                }
            }
            return lines.join("\n");
        }""")
    except Exception:
        return ""
def download_and_save_book_theater(image_url: str, post_id: str, post_date_str: str, price_str: str, default_category: str = "") -> Optional[str]:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
        resp = requests.get(image_url, headers=headers, timeout=20)
        if resp.status_code != 200 or not resp.content: return None
        img_hash = compute_sha256(resp.content)
        if database.is_image_hash_saved(img_hash):
            if price_str and database.backfill_image_price(price_str, image_hash=img_hash) > 0:
                logging.info(f"-> [CẬP NHẬT GIÁ] Đã bổ sung giá {price_str}đ cho ảnh {img_hash[:10]}.")
            else:
                logging.info(f"Ảnh {img_hash[:10]} đã có trong cơ sở dữ liệu, bỏ qua.")
            return None
        asset_key = _extract_fb_asset_key(image_url)
        matched_asset = database.find_image_by_asset_key(asset_key) if asset_key else None
        if matched_asset:
            if price_str and database.backfill_image_price(price_str, image_id=matched_asset["id"]) > 0:
                logging.info(f"-> [CẬP NHẬT GIÁ] Đã bổ sung giá {price_str}đ cho sách #{matched_asset['id']} ('{matched_asset.get('title', '')}').")
            else:
                logging.info(f"Ảnh asset {asset_key} đã có trong cơ sở dữ liệu (#{matched_asset['id']}), bỏ qua.")
            return None
        filename = f"{post_id}_{img_hash[:10]}.jpg"
        local_path = str(config.IMAGES_DIR / filename)
        with open(local_path, "wb") as f:
            f.write(resp.content)
        logging.info(f"[PHÂN TÍCH ẢNH BÌA] Đang gọi Gemini AI đọc tựa sách: {filename}...")
        meta = ai_engine.extract_book_info(local_path)
        is_valid, book_title, book_author = meta.get("is_valid_book", True), meta.get("title", "").strip(), meta.get("author", "").strip()
        book_category = default_category or meta.get("category", "").strip() or "Khác"
        is_clean, q_note = (1 if meta.get("is_clean_photo", True) else 0), meta.get("quality_note", "").strip()
        if not is_valid or not book_title or book_title == "Nhiều cuốn sách":
            logging.info(f"-> [BỎ QUA] Ảnh chỉ là chồng sách/kệ sách hoặc không nhận diện được tựa sách chính ({filename}).")
            try: os.remove(local_path)
            except Exception: pass
            return None
        if price_str:
            if database.backfill_price_by_title(book_title, price_str, post_date=post_date_str) > 0:
                logging.info(f"-> [CẬP NHẬT GIÁ THEO TỰA] Đã bổ sung giá {price_str}đ cho sách '{book_title}'.")
                try: os.remove(local_path)
                except Exception: pass
                return None
            if database.is_duplicate_book(book_title, price_str):
                logging.info(f"-> [TRÙNG LẶP] Sách '{book_title}' cùng giá {price_str}đ đã có trong kho. Tự động bỏ qua.")
                try: os.remove(local_path)
                except Exception: pass
                return None
        if database.save_image(post_id=post_id, image_url=image_url, local_path=local_path, image_hash=img_hash, post_date=post_date_str, title=book_title, author=book_author, category=book_category, price=price_str, is_single_book=is_clean, is_reviewed=0):
            price_display = f"{int(price_str):,} đ".replace(",", ".") if price_str else "Chưa có giá"
            if is_clean == 0:
                logging.info(f"-> [LƯU KHO - CHẶN ĐĂNG FANPAGE] Sách: '{book_title}' | Lý do: {q_note or 'Ảnh mờ/bụi'}")
            else:
                logging.info(f"-> [LƯU THÀNH CÔNG] Sách: '{book_title}' | Thể loại: '{book_category}' | Tác giả: '{book_author}' | Giá: {price_display} | Chờ duyệt")
            return local_path
        try: os.remove(local_path)
        except Exception: pass
        return None
    except Exception as e:
        logging.error(f"Lỗi khi xử lý ảnh sách {image_url}: {e}")
        return None
def run_scanner(page_url: Optional[str] = None, min_days: Optional[int] = None, max_days: Optional[int] = None, scrolls: int = 10, backfill_missing: bool = False) -> int:
    cleanup_browser_locks()
    target_url = page_url or config.TARGET_PAGE_URL
    scan_min_days = min_days if min_days is not None else config.MIN_DAYS_OLD
    scan_max_days = max_days if max_days is not None else config.MAX_DAYS_OLD
    if not target_url or "YOUR_PAGE_URL_HERE" in target_url:
        logging.warning("TARGET_PAGE_URL is not configured in config.py.")
        return 0
    logging.info(f"Starting page scan: {target_url} (Post age: {scan_min_days} to {scan_max_days} days)")
    from playwright.sync_api import sync_playwright
    new_images_count = 0
    global_missing_prices = database.has_any_scanned_missing_prices()
    with sync_playwright() as p:
        launch_kwargs: Dict[str, Any] = {"user_data_dir": str(config.BROWSER_PROFILE_DIR), "headless": True, "args": ["--disable-notifications", "--disable-popup-blocking"], "viewport": {"width": 1600, "height": 900}}
        if config.BROWSER_CHANNEL: launch_kwargs["channel"] = config.BROWSER_CHANNEL
        context = p.chromium.launch_persistent_context(**launch_kwargs)
        page = context.pages[0] if context.pages else context.new_page()
        try:
            page.goto(target_url, wait_until="domcontentloaded", timeout=60000)
            time.sleep(4)
            if "login" in page.url.lower() or page.locator("input[name='email'], input[name='pass']").count() > 0:
                if page.locator("div[role='dialog'] input[name='email']").count() > 0 and page.locator("div[dir='auto']").count() > 3:
                    _dismiss_login_modal(page)
                else:
                    logging.error("Facebook session has expired.")
                    import telegram_bot
                    telegram_bot.send_alert_to_all("[CẢNH BÁO] Phiên đăng nhập Facebook của bot đã hết hạn! Vui lòng mở Terminal chạy: python main.py --login-fb để cập nhật lại.")
                    context.close()
                    return 0
            _dismiss_login_modal(page)
            logging.info(f"Cuộn trang {scrolls} lần và thu thập bài viết theo thời gian thực...")
            try: page.mouse.click(600, 400); time.sleep(0.5)
            except Exception: pass
            processed_cards = set()
            for _ in range(scrolls):
                try: page.evaluate("window.scrollBy(0, 1400)")
                except Exception: pass
                try: page.keyboard.press("PageDown")
                except Exception: pass
                time.sleep(2.0)
                _dismiss_login_modal(page)
                dom_items = page.evaluate(r"""() => {
                    let out = [], seen = new Set();
                    for (let el of document.querySelectorAll("div[dir='auto']")) {
                        let t = el.innerText ? el.innerText.trim() : '';
                        if (!t || t.length < 25 || seen.has(t)) continue;
                        seen.add(t);
                        let p = el, photoHref = '', dateText = '', level = 0;
                        while (p && p !== document.body && level < 25) {
                            if (!photoHref) {
                                let aAlbum = p.querySelector("a[href*='set=pcb.']");
                                if (aAlbum) photoHref = aAlbum.href;
                                else { let a = p.querySelector("a[href*='/photo/'], a[href*='fbid=']"); if (a) photoHref = a.href; }
                            }
                            if (!dateText) {
                                for (let l of p.querySelectorAll('a[href*="/posts/"], a[href*="pfbid"]')) {
                                    let txt = l.innerText || l.getAttribute('aria-label') || '', tl = txt.toLowerCase();
                                    if (txt && (tl.includes('tháng') || tl.includes('ngày') || tl.includes('tuần') || tl.includes('hôm qua') || tl.includes('giờ') || tl.includes('phút') || /\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|yesterday|hour|day|week)\b/.test(tl))) { dateText = txt; break; }
                                }
                            }
                            if (!dateText) {
                                for (let s of p.querySelectorAll('span')) {
                                    let txt = s.innerText || s.getAttribute('aria-label') || '', tl = txt.toLowerCase();
                                    if (txt && txt.length <= 80 && !tl.includes('hàng ngày') && !tl.includes('cho thuê') && (tl.includes('tháng') || tl.includes('ngày') || tl.includes('tuần') || tl.includes('hôm qua') || tl.includes('giờ') || tl.includes('phút') || /\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|yesterday|hour|day|week)\b/.test(tl))) { dateText = txt; break; }
                                }
                            }
                            if (photoHref && dateText) break;
                            p = p.parentElement; level++;
                        }
                        out.push({ text: t, photoHref: photoHref, dateText: dateText });
                    }
                    return out;
                }""")
                for it in dom_items:
                    try:
                        card_text = it.get("text", "").strip()
                        if not card_text or card_text in processed_cards: continue
                        is_ok, _ = text_utils.check_post_eligibility(card_text)
                        if not is_ok: continue
                        processed_cards.add(card_text)
                        post_date_str = text_utils.parse_vietnamese_date(it.get("dateText", ""))
                        try:
                            age_days = (date.today() - datetime.strptime(post_date_str, "%Y-%m-%d").date()).days
                            if age_days > scan_max_days:
                                logging.info(f"-> [BỎ QUA] Bài ngày {post_date_str} ({age_days} ngày trước) vượt quá mốc {scan_max_days} ngày.")
                                continue
                        except Exception: pass
                        header_snippet = card_text.split("\n")[0][:50]
                        post_id = f"fb_post_{hashlib.md5((post_date_str + '_' + card_text).encode('utf-8')).hexdigest()[:12]}"
                        already_saved = database.is_post_saved(post_id)
                        needs_rescan = (not already_saved) or database.post_has_missing_prices(post_id) or (not database.post_has_images(post_id)) or backfill_missing or global_missing_prices
                        if already_saved and not needs_rescan:
                            logging.info(f"-> [BÀI ĐÃ LƯU] Bài ngày {post_date_str} ({post_id}) đã có trong kho, bỏ qua.")
                            continue
                        logging.info(f"-> [QUÉT BÙ GIÁ] Bài {post_id} có sách chưa có giá hoặc thiếu ảnh, mở Theater View để cập nhật..." if already_saved else f"[TÌM THẤY BÀI MỚI HỢP LỆ]: {header_snippet}... (Ngày: {post_date_str})")
                        post_category = text_utils.extract_category_from_post(card_text)
                        database.save_post(post_id, target_url, card_text, post_date_str)
                        photo_href = it.get("photoHref", "")
                        if photo_href:
                            logging.info(f"-> Mở chế độ xem chi tiết từng ảnh (Theater View) để đọc giá và bìa sách... (Thể loại bài: '{post_category or 'Chưa rõ'}')")
                            photo_page = None
                            try:
                                photo_page = context.new_page()
                                fbid_to_caption: Dict[str, str] = {}
                                def _on_gql_response(resp):
                                    if "/api/graphql" not in resp.url: return
                                    try:
                                        for line in resp.text().splitlines():
                                            line = line.strip()
                                            if line:
                                                try: _collect_gql_captions(json.loads(line), fbid_to_caption)
                                                except Exception: pass
                                    except Exception: pass
                                photo_page.on("response", _on_gql_response)
                                photo_page.goto(photo_href, wait_until="domcontentloaded", timeout=45000)
                                time.sleep(3.2)
                                _dismiss_login_modal(photo_page)
                                try:
                                    ssr_scripts = photo_page.evaluate(r"""() => {
                                        let arr = [];
                                        for (let sc of document.querySelectorAll("script[type='application/json']")) {
                                            let txt = sc.textContent || "";
                                            if (txt.includes("message_preferred_body") || txt.includes("CometPhotoRootContentQuery")) arr.push(txt);
                                        }
                                        return arr;
                                    }""")
                                    for raw_json in ssr_scripts:
                                        try: _collect_gql_captions(json.loads(raw_json), fbid_to_caption)
                                        except Exception: pass
                                except Exception: pass
                                seen_fbids, prev_img_src = set(), ""
                                for step in range(100):
                                    current_url = photo_page.url
                                    if "/photo/" not in current_url and "fbid=" not in current_url: break
                                    current_fbid = _extract_fbid(current_url)
                                    visit_key = current_fbid or current_url.split("&__cft__")[0]
                                    if visit_key in seen_fbids: break
                                    seen_fbids.add(visit_key)
                                    img_src = ""
                                    for _ in range(13):
                                        img_src = photo_page.evaluate(r"""() => { let img = document.querySelector("div[data-visualcompletion='media-vc-image'] img, img[data-visualcompletion='media-vc-image']"); return img ? img.src : ""; }""")
                                        if img_src and "fbcdn.net" in img_src and (step == 0 or img_src != prev_img_src): break
                                        time.sleep(0.2)
                                    if current_fbid and current_fbid not in fbid_to_caption:
                                        for _ in range(6):
                                            if current_fbid in fbid_to_caption: break
                                            time.sleep(0.2)
                                    raw_gql = fbid_to_caption.get(current_fbid, "") if current_fbid else ""
                                    price_val = parse_caption_price(raw_gql) or parse_caption_price(_extract_theater_caption_dom(photo_page))
                                    if img_src and "fbcdn.net" in img_src:
                                        prev_img_src = img_src
                                        if download_and_save_book_theater(img_src, post_id, post_date_str, price_val, default_category=post_category):
                                            new_images_count += 1
                                    photo_page.keyboard.press("ArrowRight")
                                    advanced = False
                                    for _ in range(8):
                                        time.sleep(0.2)
                                        if _extract_fbid(photo_page.url) != current_fbid and photo_page.url != current_url:
                                            advanced = True; break
                                    if not advanced:
                                        _dismiss_login_modal(photo_page)
                                        photo_page.evaluate(r"""() => { let btn = document.querySelector("div[aria-label='Ảnh tiếp theo'], div[aria-label='Next photo']"); if (btn) btn.click(); }""")
                                        for _ in range(10):
                                            time.sleep(0.2)
                                            if _extract_fbid(photo_page.url) != current_fbid and photo_page.url != current_url:
                                                advanced = True; break
                                    if not advanced: break
                                    time.sleep(0.4)
                            except Exception as th_err:
                                logging.error(f"Lỗi khi duyệt ảnh trong bài viết: {th_err}")
                            finally:
                                if photo_page:
                                    try: photo_page.close()
                                    except Exception: pass
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
            import telegram_bot, web_admin
            ip = web_admin.get_local_ip()
            telegram_bot.send_alert_to_all(f"📚 [KHO VỪA THÊM {new_images_count} ẢNH SÁCH MỚI]\n\nCác ảnh mới đã được đưa vào trạng thái 'Chờ soát lại' để bạn đối chiếu bìa font lạ/ảnh mờ.\n👉 Mở Web Dashboard để soát và sửa tay: http://{ip}:8080\nHoặc gõ lệnh /soat trên Telegram để xem ảnh và duyệt trực tiếp!")
        except Exception: pass
    return new_images_count
if __name__ == "__main__":
    run_scanner()
