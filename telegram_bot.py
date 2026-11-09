import os
import re
import time
import json
import hashlib
import logging
import requests
import psutil
from typing import Dict, Any, Optional
import config
import database
import web_admin
import ai_engine
import backup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
BASE_URL = "https://api.telegram.org/bot"
def get_api_url(method: str) -> str:
    return f"{BASE_URL}{config.TELEGRAM_BOT_TOKEN}/{method}"
def send_message(chat_id: str, text: str, reply_markup: Optional[Dict] = None) -> bool:
    if not config.TELEGRAM_BOT_TOKEN:
        return False
    payload = {"chat_id": chat_id, "text": text}
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        resp = requests.post(get_api_url("sendMessage"), json=payload, timeout=20)
        return resp.status_code == 200
    except Exception as e:
        logging.error(f"Error sending Telegram message: {e}")
        return False
def send_photo(chat_id: str, photo_path: str, caption: str, reply_markup: Optional[Dict] = None) -> bool:
    if not config.TELEGRAM_BOT_TOKEN:
        return False
    data = {"chat_id": chat_id, "caption": caption}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        if photo_path and os.path.exists(photo_path):
            with open(photo_path, "rb") as f:
                resp = requests.post(get_api_url("sendPhoto"), data=data, files={"photo": f}, timeout=30)
                return resp.status_code == 200
        else:
            return send_message(chat_id, f"{caption}\n(Không có ảnh bìa lưu trên máy)", reply_markup)
    except Exception as e:
        logging.error(f"Error sending Telegram photo: {e}")
        return False
def send_document(chat_id: str, doc_path: str, caption: str = "") -> bool:
    if not config.TELEGRAM_BOT_TOKEN or not os.path.exists(doc_path):
        return False
    data = {"chat_id": chat_id, "caption": caption}
    try:
        with open(doc_path, "rb") as f:
            resp = requests.post(get_api_url("sendDocument"), data=data, files={"document": f}, timeout=180)
            return resp.status_code == 200
    except Exception as e:
        logging.error(f"Error sending Telegram document: {e}")
        return False
def answer_callback_query(callback_query_id: str, text: str):
    try:
        requests.post(get_api_url("answerCallbackQuery"), json={"callback_query_id": callback_query_id, "text": text}, timeout=10)
    except Exception:
        pass
def format_price_vnd(price) -> str:
    if not price:
        return "Chưa có"
    try:
        val = int(str(price).replace(".", "").replace(",", "").replace("k", "").replace("K", "").strip())
        if 0 < val < 1000:
            val = val * 1000
        return f"{val:,} đ".replace(",", ".")
    except Exception:
        return f"{price} đ"
def get_allowed_chat_ids() -> list:
    raw = getattr(config, "TELEGRAM_CHAT_ID", "")
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        return [x.strip() for x in raw.split(",") if x.strip()]
    return [str(raw)] if raw else []
def send_alert_to_all(text: str):
    cids = get_allowed_chat_ids()
    for cid in cids:
        send_message(cid, text)
def notify_new_lead(lead: Dict):
    chat_ids = get_allowed_chat_ids()
    if not chat_ids or not config.TELEGRAM_BOT_TOKEN:
        return
    matched_source_info = f"🔍 Nguồn phát hiện: {lead.get('matched_source')}\n" if lead.get('matched_source') else ""
    price_info = f"💰 Giá trong kho tiệm: {format_price_vnd(lead.get('price'))}\n" if lead.get('price') else ""
    cat_info = f"🏷️ Thể loại: {lead.get('category')}\n" if lead.get('category') else ""
    p_url = (lead.get('post_url') or '').strip()
    is_direct = any(x in p_url for x in ['/posts/', '/permalink/', 'story_fbid', 'multi_permalinks'])
    link_line = f"🔗 Link bài viết: {p_url}\n\n👉 Bấm vào link trên để mở trực tiếp bài đăng và chốt đơn với khách!" if is_direct else f"🔗 Link nhóm: {p_url}\n⚠️ (Chưa bắt được permalink bài này, bạn bấm vào link nhóm trên để xem bài mới nhé!)"
    msg = (
        f"🎯 [CÓ KHÁCH ĐANG TÌM MUA SÁCH]\n\n"
        f"📖 Sách trùng khớp: {lead.get('matched_book_title')}\n"
        f"{cat_info}"
        f"{price_info}"
        f"{matched_source_info}"
        f"💬 Trích đoạn: \"{lead.get('content_snippet')}\"\n"
        f"{link_line}"
    )
    for cid in chat_ids:
        send_message(cid, msg)
def handle_text_message(chat_id: str, text: str):
    t = text.strip()
    bot_suffix = "@tiemsachcuathuongbot"
    if bot_suffix in t:
        t = t.replace(bot_suffix, "").strip()
    if t in ["/start", "/help"]:
        msg = (
            "Chào bạn! Đây là Bot Tra Cứu & Quản Lý Kho Tiệm Sách Của Thương.\n\n"
            "- Nhập tên cuốn sách bất kỳ (hoặc /tim <tên sách>) để kiểm tra tình trạng còn hàng.\n"
            "- /theloai <thể loại> : Tìm sách theo thể loại (ví dụ: /theloai Văn học Nhật Bản).\n"
            "- /gia <từ> <đến> : Lọc sách theo tầm giá (ví dụ: /gia 50k 100k).\n"
            "- /them <Tựa> | <Tác giả> | <Thể loại> | <Giá> : Tự thêm cuốn sách mới hoàn toàn vào kho.\n"
            "- /soat : Soát lại các ảnh sách mới quét (xem bìa, giá, thể loại để duyệt hoặc sửa tay).\n"
            "- /duyet <ID> : Xác nhận duyệt sách ID đã đúng.\n"
            "- /sua <ID> <Tên sách> [| <Giá>] [| <Thể loại>] : Sửa nhanh thông tin cho sách ID.\n"
            "- /xoa <ID> : Xóa hoàn toàn sách và file ảnh khỏi kho.\n"
            "- /status hoặc /kho : Xem thống kê số lượng sách trong kho.\n"
            "- /backup hoặc /saoluu : Tải bản sao lưu database kho sách về Telegram.\n"
            "- /backup full : Nén toàn bộ database + ảnh bìa (.zip) tải về Telegram.\n"
            "- /system hoặc /sys : Xem tài nguyên CPU, RAM, Ổ cứng, GPU máy chủ."
        )
        send_message(chat_id, msg)
        return
    if t.startswith("/them "):
        content = t[6:].strip()
        parts = [p.strip() for p in content.split("|")]
        new_title = parts[0] if len(parts) >= 1 else ""
        new_author = parts[1] if len(parts) >= 2 else ""
        new_category = parts[2] if len(parts) >= 3 else ""
        raw_price = parts[3] if len(parts) >= 4 else ""
        new_price = ""
        if raw_price:
            p_clean = raw_price.replace("k", "").replace("K", "").replace(".", "").replace(",", "").strip()
            if p_clean.isdigit():
                num_p = int(p_clean)
                if 0 < num_p < 1000:
                    num_p = num_p * 1000
                new_price = str(num_p)
            else:
                new_price = p_clean
        if new_title:
            b_id = database.add_book_manually(new_title, new_author, new_category, new_price, status="available", is_reviewed=1)
            disp_price = format_price_vnd(new_price)
            cat_str = f"\n🏷️ Thể loại: {new_category}" if new_category else ""
            author_str = f"\n✍️ Tác giả: {new_author}" if new_author else ""
            send_message(chat_id, f"✅ Đã thêm sách mới thành công (#{b_id}):\n📖 Tựa: '{new_title}'{author_str}{cat_str}\n💰 Giá: {disp_price}")
            return
        else:
            send_message(chat_id, "⚠️ Cú pháp: /them <Tựa sách> | <Tác giả> | <Thể loại> | <Giá>")
            return
    if t.startswith("/soat") or t.startswith("/review"):
        pending = database.get_pending_review_books(limit=5)
        if not pending:
            send_message(chat_id, "Tất cả sách trong kho đều đã được soát duyệt! Không có cuốn nào đang chờ duyệt.")
            return
        send_message(chat_id, f"Đang có {len(pending)} cuốn sách mới quét chờ soát duyệt (hiển thị tối đa 5 cuốn):")
        for b in pending:
            price_str = f"Giá: {format_price_vnd(b.get('price'))}\n"
            cat_str = f"🏷️ Thể loại: {b.get('category') or 'Chưa rõ'}\n"
            caption = (
                f"🔍 [SOÁT BÌA SÁCH #{b['id']}]\n"
                f"📖 Tựa đề: {b.get('title') or 'Chưa rõ'}\n"
                f"✍️ Tác giả: {b.get('author') or 'Chưa rõ'}\n"
                f"{cat_str}"
                f"💰 {price_str}\n"
                f"👉 Bấm nút bên dưới để Duyệt ngay hoặc gõ /sua {b['id']} <Tên mới> | <Giá>"
            )
            markup = {
                "inline_keyboard": [
                    [
                        {"text": f"✅ Duyệt ngay (#{b['id']})", "callback_data": f"approve_{b['id']}"},
                        {"text": f"❌ Đã bán", "callback_data": f"sold_{b['id']}"},
                        {"text": f"🗑️ Xóa", "callback_data": f"delete_{b['id']}"}
                    ]
                ]
            }
            send_photo(chat_id, b.get("local_path"), caption, markup)
        return
    if t.startswith("/duyet "):
        parts = t.split()
        if len(parts) >= 2 and parts[1].isdigit():
            b_id = int(parts[1])
            database.mark_book_reviewed(b_id)
            send_message(chat_id, f"✅ Đã duyệt sách #{b_id} thành công!")
            return
    if t.startswith("/xoa "):
        parts = t.split()
        if len(parts) >= 2 and parts[1].isdigit():
            b_id = int(parts[1])
            deleted = database.delete_image_record(b_id)
            if deleted:
                send_message(chat_id, f"🗑️ Đã xóa hoàn toàn sách #{b_id} khỏi kho và xóa file ảnh thành công.")
            else:
                send_message(chat_id, f"⚠️ Không tìm thấy sách #{b_id} để xóa.")
            return
    if t.startswith("/sua "):
        content = t[5:].strip()
        parts = content.split(" ", 1)
        if len(parts) >= 2 and parts[0].isdigit():
            b_id = int(parts[0])
            rest = parts[1]
            subparts = [p.strip() for p in rest.split("|")]
            new_title = subparts[0]
            new_price = ""
            new_cat = ""
            if len(subparts) >= 2:
                raw_p = subparts[1].replace("k", "").replace("K", "").replace(".", "").replace(",", "").strip()
                if raw_p.isdigit():
                    num_p = int(raw_p)
                    if 0 < num_p < 1000:
                        num_p = num_p * 1000
                    new_price = str(num_p)
                else:
                    new_price = subparts[1]
            if len(subparts) >= 3:
                new_cat = subparts[2]
            with database.get_connection() as conn:
                r = conn.execute("SELECT author, price, is_single_book, status, category FROM images WHERE id = ?", (b_id,)).fetchone()
                if r:
                    author = r[0] or ""
                    price = new_price or r[1] or ""
                    single = r[2] if r[2] is not None else 1
                    status = r[3] or "available"
                    category = new_cat or r[4] or ""
                    database.update_book_details(b_id, new_title, author, price, single, status, is_reviewed=1, category=category)
                    disp_price = format_price_vnd(price)
                    cat_disp = f"\n🏷️ Thể loại: {category}" if category else ""
                    send_message(chat_id, f"✅ Đã sửa sách #{b_id}:\n📖 Tựa mới: '{new_title}'{cat_disp}\n💰 Giá: {disp_price}\n(Đã tự động xác nhận duyệt)")
                    return
    if t in ["/system", "/sys"]:
        metrics = web_admin.get_system_metrics()
        msg = (
            f"🖥️ [TÀI NGUYÊN MÁY CHỦ]\n\n"
            f"* CPU: {metrics['cpu_percent']}%\n"
            f"* RAM: {metrics['ram_used_gb']} / {metrics['ram_total_gb']} GB ({metrics['ram_percent']}%)\n"
            f"* Ổ cứng: {metrics.get('disk_used_gb', 0)} / {metrics.get('disk_total_gb', 0)} GB ({metrics.get('disk_percent', 0)}%)\n"
            f"* GPU: {metrics.get('gpu_name', 'N/A')} ({metrics.get('gpu_percent', 0)}%)\n"
            f"* Thời gian chạy: {metrics['uptime']}\n"
            f"* Kho sách: {metrics['stats']['available_in_stock']} còn / {metrics['stats']['sold_out']} đã bán"
        )
        send_message(chat_id, msg)
        return
    if t in ["/status", "/kho"]:
        stats = database.get_stats()
        msg = (
            f"[THỐNG KÊ KHO SÁCH]\n\n"
            f"* Sách còn hàng: {stats['available_in_stock']}\n"
            f"* Sách đã bán: {stats['sold_out']}\n"
            f"* Tổng số ảnh: {stats['total_images']}\n"
            f"* Khách chờ phản hồi: {stats['pending_leads']}"
        )
        send_message(chat_id, msg)
        return
    if t in ["/backup", "/saoluu"]:
        send_message(chat_id, "⏳ Đang tạo bản sao lưu cơ sở dữ liệu kho sách...")
        db_path = backup.backup_database()
        if db_path and os.path.exists(db_path):
            cap = f"📦 Bản sao lưu kho sách ({time.strftime('%H:%M:%S %d/%m/%Y')})\nLưu trữ: {os.path.basename(db_path)}"
            if not send_document(chat_id, db_path, caption=cap):
                send_message(chat_id, f"✅ Đã sao lưu tại: {db_path}")
        else:
            send_message(chat_id, "❌ Lỗi khi tạo bản sao lưu cơ sở dữ liệu.")
        return
    if t in ["/backup full", "/saoluu full"]:
        send_message(chat_id, "⏳ Đang nén toàn bộ kho sách (gồm tất cả ảnh bìa)...")
        zip_path = backup.create_full_backup_zip()
        if zip_path and os.path.exists(zip_path):
            mb = os.path.getsize(zip_path) / (1024 * 1024)
            cap = f"📦 Gói sao lưu toàn bộ: {mb:.1f} MB"
            if mb < 49:
                send_document(chat_id, zip_path, caption=cap)
            else:
                send_message(chat_id, f"✅ Đã tạo gói sao lưu: {zip_path} ({mb:.1f} MB)")
        else:
            send_message(chat_id, "❌ Lỗi khi nén bản sao lưu toàn bộ.")
        return
    if t.startswith("/theloai "):
        cat_query = t[9:].strip()
        books = database.query_books(category=cat_query, status="available", limit=10)
        if not books:
            send_message(chat_id, f"Không tìm thấy sách nào thuộc thể loại '{cat_query}' còn hàng.")
            return
        send_message(chat_id, f"Tìm thấy {len(books)} cuốn sách thể loại '{cat_query}' còn hàng:")
        for b in books[:3]:
            disp_price = format_price_vnd(b.get('price'))
            price_str = f"Giá bán: {disp_price}\n" if b.get('price') else ""
            caption = f"📖 Tên: {b.get('title')}\n✍️ Tác giả: {b.get('author') or 'Chưa rõ'}\n🏷️ Thể loại: {b.get('category')}\n💰 {price_str}📦 Trạng thái: CÒN HÀNG"
            markup = {"inline_keyboard": [[{"text": f"❌ Đã bán (#{b['id']})", "callback_data": f"sold_{b['id']}"}]]}
            send_photo(chat_id, b.get("local_path"), caption, markup)
        return
    if t.startswith("/gia "):
        parts = t[5:].strip().split()
        p1 = parts[0] if len(parts) >= 1 else ""
        p2 = parts[1] if len(parts) >= 2 else ""
        def parse_k(v):
            if not v:
                return None
            c = v.lower().replace("k", "").replace(".", "").replace(",", "").strip()
            if c.isdigit():
                n = int(c)
                return n * 1000 if n < 1000 else n
            return None
        min_p = parse_k(p1)
        max_p = parse_k(p2)
        if min_p is not None and max_p is None and len(parts) == 1:
            max_p = min_p
            min_p = 0
        books = database.query_books(min_price=min_p, max_price=max_p, status="available", limit=10)
        p_desc = f"từ {format_price_vnd(min_p)} đến {format_price_vnd(max_p)}" if min_p and max_p else f"mức giá {format_price_vnd(max_p or min_p)}"
        if not books:
            send_message(chat_id, f"Không tìm thấy sách nào trong tầm giá {p_desc} còn hàng.")
            return
        send_message(chat_id, f"Tìm thấy {len(books)} cuốn sách {p_desc} còn hàng:")
        for b in books[:3]:
            disp_price = format_price_vnd(b.get('price'))
            caption = f"📖 Tên: {b.get('title')}\n✍️ Tác giả: {b.get('author') or 'Chưa rõ'}\n🏷️ Thể loại: {b.get('category')}\n💰 Giá: {disp_price}"
            markup = {"inline_keyboard": [[{"text": f"❌ Đã bán (#{b['id']})", "callback_data": f"sold_{b['id']}"}]]}
            send_photo(chat_id, b.get("local_path"), caption, markup)
        return
    search_query = t
    if t.startswith("/tim ") or t.startswith("/sach "):
        search_query = t.split(" ", 1)[1].strip()
    if not search_query:
        return
    books = database.search_available_books(search_query)
    if not books:
        send_message(chat_id, f"Không tìm thấy cuốn sách nào phù hợp với từ khóa: '{search_query}' trong kho còn hàng.")
        return
    send_message(chat_id, f"Tìm thấy {len(books)} cuốn sách còn hàng trong kho:")
    for b in books[:3]:
        disp_price = format_price_vnd(b.get('price'))
        price_str = f"Giá bán: {disp_price}\n" if b.get('price') else ""
        cat_str = f"🏷️ Thể loại: {b.get('category') or 'Khác'}\n"
        caption = (
            f"📖 Tên sách: {b.get('title') or 'Sách hay'}\n"
            f"✍️ Tác giả: {b.get('author') or 'Chưa cập nhật'}\n"
            f"{cat_str}"
            f"💰 {price_str}"
            f"📅 Ngày đăng: {b.get('post_date') or 'Mới đây'}\n"
            f"📦 Trạng thái: CÒN HÀNG"
        )
        markup = {
            "inline_keyboard": [
                [
                    {"text": f"❌ Đã bán (#{b['id']})", "callback_data": f"sold_{b['id']}"},
                    {"text": f"🗑️ Xóa", "callback_data": f"delete_{b['id']}"}
                ]
            ]
        }
        send_photo(chat_id, b.get("local_path"), caption, markup)
def handle_callback_query(cq: Dict):
    cq_id = cq.get("id")
    data = cq.get("data", "")
    message = cq.get("message", {})
    chat_id = str(message.get("chat", {}).get("id"))
    from_user_id = str(cq.get("from", {}).get("id"))
    allowed_ids = get_allowed_chat_ids()
    if allowed_ids and chat_id not in allowed_ids and from_user_id not in allowed_ids:
        answer_callback_query(cq_id, "Bạn không có quyền thực hiện thao tác này.")
        return
    if data.startswith("sold_"):
        try:
            book_id = int(data.split("_")[1])
            database.mark_book_sold(book_id)
            answer_callback_query(cq_id, f"Đã đánh dấu sách #{book_id} là ĐÃ BÁN.")
            send_message(chat_id, f"✅ Đã cập nhật sách #{book_id} thành ĐÃ BÁN.")
        except Exception as e:
            answer_callback_query(cq_id, f"Lỗi: {e}")
    elif data.startswith("approve_"):
        try:
            book_id = int(data.split("_")[1])
            database.mark_book_reviewed(book_id)
            answer_callback_query(cq_id, f"Đã duyệt sách #{book_id}!")
            send_message(chat_id, f"✅ Đã xác nhận duyệt sách #{book_id} thành công.")
        except Exception as e:
            answer_callback_query(cq_id, f"Lỗi: {e}")
    elif data.startswith("delete_"):
        try:
            book_id = int(data.split("_")[1])
            deleted = database.delete_image_record(book_id)
            if deleted:
                answer_callback_query(cq_id, f"Đã xóa sách #{book_id}!")
                send_message(chat_id, f"🗑️ Đã xóa hoàn toàn sách #{book_id} khỏi kho và xóa file ảnh.")
            else:
                answer_callback_query(cq_id, f"Không tìm thấy sách #{book_id}.")
        except Exception as e:
            answer_callback_query(cq_id, f"Lỗi: {e}")
def handle_photo_message(chat_id: str, photos: list, caption_text: str = ""):
    if not photos or not config.TELEGRAM_BOT_TOKEN:
        return
    best_photo = photos[-1]
    file_id = best_photo.get("file_id")
    if not file_id:
        return
    send_message(chat_id, "⏳ Đang tải ảnh và gọi Gemini AI đọc bìa sách...")
    try:
        res = requests.get(get_api_url("getFile"), params={"file_id": file_id}, timeout=20).json()
        if not res.get("ok"):
            send_message(chat_id, "❌ Không thể lấy file ảnh từ Telegram.")
            return
        file_path = res["result"]["file_path"]
        download_url = f"https://api.telegram.org/file/bot{config.TELEGRAM_BOT_TOKEN}/{file_path}"
        img_resp = requests.get(download_url, timeout=30)
        if img_resp.status_code != 200 or not img_resp.content:
            send_message(chat_id, "❌ Lỗi khi tải ảnh từ máy chủ Telegram.")
            return
        fname = f"manual_tg_{int(time.time())}_{hashlib.md5(img_resp.content).hexdigest()[:8]}.jpg"
        save_path = str(config.IMAGES_DIR / fname)
        with open(save_path, "wb") as f:
            f.write(img_resp.content)
        info = ai_engine.extract_book_info(save_path)
        title = info.get("title", "").strip() or "Sách chưa rõ tựa"
        author = info.get("author", "").strip()
        category = info.get("category", "").strip() or "Khác"
        price_val = ""
        if caption_text:
            m = re.search(r"(\d{1,4}(?:[.,]\d{3})?)\s*(k|đ|vnd)?", caption_text, re.IGNORECASE)
            if m:
                num = int(m.group(1).replace(".", "").replace(",", ""))
                if m.group(2) == "k" or num < 1000: num *= 1000
                price_val = str(num)
        if not price_val:
            price_val = info.get("price", "")
        new_id = database.add_book_manually(title, author, category, price_val, status="available", local_path=save_path, is_reviewed=1)
        disp_price = format_price_vnd(price_val)
        reply = (
            f"✅ [ĐÃ THÊM SÁCH VÀO KHO #{new_id}]\n\n"
            f"📖 Tên: {title}\n"
            f"✍️ Tác giả: {author or 'Chưa rõ'}\n"
            f"🏷️ Thể loại: {category}\n"
            f"💰 Giá bán: {disp_price}\n\n"
            f"👉 Để sửa lại thông tin cuốn này, bạn chỉ cần gõ:\n"
            f"/sua {new_id} <Tên mới> | <Giá> | <Thể loại>"
        )
        markup = {"inline_keyboard": [[{"text": f"❌ Đã bán (#{new_id})", "callback_data": f"sold_{new_id}"}, {"text": f"🗑️ Xóa (#{new_id})", "callback_data": f"delete_{new_id}"}]]}
        send_message(chat_id, reply, markup)
    except Exception as e:
        logging.error(f"Error handling Telegram photo: {e}")
        send_message(chat_id, f"❌ Lỗi khi xử lý ảnh sách: {e}")
def run_telegram_bot_listener():
    if not config.TELEGRAM_BOT_TOKEN:
        logging.warning("TELEGRAM_BOT_TOKEN chua duoc cau hinh trong config.py. Bo qua Telegram listener.")
        return
    logging.info("Khoi dong Telegram Bot Listener (sieu nhe ~15MB RAM)...")
    offset = 0
    while True:
        try:
            url = get_api_url("getUpdates")
            params = {"offset": offset, "timeout": 25}
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message")
                    if msg:
                        chat_id = str(msg["chat"]["id"])
                        from_user_id = str(msg.get("from", {}).get("id"))
                        allowed_ids = get_allowed_chat_ids()
                        if allowed_ids and chat_id not in allowed_ids and from_user_id not in allowed_ids:
                            send_message(chat_id, "Xin lỗi, bạn không có quyền truy cập kho sách này.")
                            continue
                        if "text" in msg:
                            handle_text_message(chat_id, msg["text"])
                        elif "photo" in msg:
                            handle_photo_message(chat_id, msg["photo"], msg.get("caption", ""))
                    elif "callback_query" in update:
                        handle_callback_query(update["callback_query"])
            time.sleep(1)
        except Exception as e:
            logging.debug(f"Telegram polling loop error: {e}")
            time.sleep(5)
if __name__ == "__main__":
    run_telegram_bot_listener()
