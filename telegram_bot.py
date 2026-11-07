import os
import time
import json
import logging
import requests
import psutil
from typing import Dict, Any, Optional
import config
import database
import web_admin
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
    msg = (
        f"🎯 [CÓ KHÁCH ĐANG TÌM MUA SÁCH]\n\n"
        f"📖 Sách trùng khớp: {lead.get('matched_book_title')}\n"
        f"{cat_info}"
        f"{price_info}"
        f"{matched_source_info}"
        f"💬 Trích đoạn: \"{lead.get('content_snippet')}\"\n"
        f"🔗 Link Facebook: {lead.get('post_url')}\n\n"
        f"👉 Bạn có thể bấm vào link Facebook trên để vào tư vấn hoặc chốt đơn với khách!"
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
            "- /them <Tựa> | <Tác giả> | <Thể loại> | <Giá> : Tự thêm cuốn sách mới hoàn toàn vào kho.\n"
            "- /soat : Soát lại các ảnh sách mới quét (xem bìa, giá, thể loại để duyệt hoặc sửa tay).\n"
            "- /duyet <ID> : Xác nhận duyệt sách ID đã đúng.\n"
            "- /sua <ID> <Tên sách> [| <Giá>] [| <Thể loại>] : Sửa nhanh thông tin cho sách ID.\n"
            "- /xoa <ID> : Xóa hoàn toàn sách và file ảnh khỏi kho.\n"
            "- /status hoặc /kho : Xem thống kê số lượng sách trong kho.\n"
            "- /system hoặc /sys : Xem tài nguyên CPU, RAM máy chủ."
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
            f"[TÀI NGUYÊN MÁY CHỦ]\n\n"
            f"* CPU: {metrics['cpu_percent']}%\n"
            f"* RAM: {metrics['ram_used_gb']} / {metrics['ram_total_gb']} GB ({metrics['ram_percent']}%)\n"
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
                    if "message" in update and "text" in update["message"]:
                        msg = update["message"]
                        chat_id = str(msg["chat"]["id"])
                        from_user_id = str(msg.get("from", {}).get("id"))
                        allowed_ids = get_allowed_chat_ids()
                        if allowed_ids and chat_id not in allowed_ids and from_user_id not in allowed_ids:
                            send_message(chat_id, "Xin lỗi, bạn không có quyền truy cập kho sách này.")
                            continue
                        handle_text_message(chat_id, msg["text"])
                    elif "callback_query" in update:
                        handle_callback_query(update["callback_query"])
            time.sleep(1)
        except Exception as e:
            logging.debug(f"Telegram polling loop error: {e}")
            time.sleep(5)
if __name__ == "__main__":
    run_telegram_bot_listener()
