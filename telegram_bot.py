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
        if os.path.exists(photo_path):
            with open(photo_path, "rb") as f:
                resp = requests.post(get_api_url("sendPhoto"), data=data, files={"photo": f}, timeout=30)
                return resp.status_code == 200
        else:
            return send_message(chat_id, f"{caption}\n(Khong tim thay file anh tren may)", reply_markup)
    except Exception as e:
        logging.error(f"Error sending Telegram photo: {e}")
        return False
def answer_callback_query(callback_query_id: str, text: str):
    try:
        requests.post(get_api_url("answerCallbackQuery"), json={"callback_query_id": callback_query_id, "text": text}, timeout=10)
    except Exception:
        pass
def notify_new_lead(lead: Dict):
    chat_id = config.TELEGRAM_CHAT_ID
    if not chat_id or not config.TELEGRAM_BOT_TOKEN:
        return
    msg = (
        f"[KHACH DANG TIM MUA SACH]\n\n"
        f"Sach trung khop: {lead.get('matched_book_title')}\n"
        f"Trich doan: \"{lead.get('content_snippet')}\"\n"
        f"Link Facebook: {lead.get('post_url')}\n\n"
        f"Ban co the bam vao link de tu tra loi cho khach!"
    )
    send_message(chat_id, msg)
def handle_text_message(chat_id: str, text: str):
    t = text.strip()
    if t in ["/start", "/help"]:
        msg = (
            "Chao ban! Day la Bot Tra Cuu Kho Sach.\n\n"
            "- Nhap ten cuon sach bat ky de kiem tra tinh trang con hang va xem anh bia.\n"
            "- /status hoac /kho : Xem thong ke so luong sach trong kho.\n"
            "- /system hoac /sys : Xem tai nguyen CPU, RAM, O cung may chu tu xa."
        )
        send_message(chat_id, msg)
        return
    if t in ["/system", "/sys"]:
        metrics = web_admin.get_system_metrics()
        msg = (
            f"[TAI NGUYEN MAY CHU (HEADLESS)]\n\n"
            f"* CPU: {metrics['cpu_percent']}%\n"
            f"* RAM: {metrics['ram_used_gb']} / {metrics['ram_total_gb']} GB ({metrics['ram_percent']}%)\n"
            f"* O cung: {metrics['disk_used_gb']} / {metrics['disk_total_gb']} GB ({metrics['disk_percent']}%)\n"
            f"* Thoi gian chay: {metrics['uptime']}\n"
            f"* IP Quan tri noi bo: http://{metrics['local_ip']}:8080\n"
            f"* Kho sach: {metrics['stats']['available_in_stock']} con / {metrics['stats']['sold_out']} ban"
        )
        send_message(chat_id, msg)
        return
    if t in ["/status", "/kho"]:
        stats = database.get_stats()
        msg = (
            f"[THONG KE KHO SACH]\n\n"
            f"* Sach con hang: {stats['available_in_stock']}\n"
            f"* Sach da ban: {stats['sold_out']}\n"
            f"* Tong so anh: {stats['total_images']}\n"
            f"* Khach cho phan hoi: {stats['pending_leads']}"
        )
        send_message(chat_id, msg)
        return
    books = database.search_available_books(t)
    if not books:
        send_message(chat_id, f"Khong tim thay cuon sach nao phu hop voi tu khoa: '{t}' trong kho con hang.")
        return
    send_message(chat_id, f"Tim thay {len(books)} cuon sach con hang trong kho:")
    for b in books[:3]:
        caption = (
            f"Ten sach: {b.get('title') or 'Sach hay'}\n"
            f"Tac gia: {b.get('author') or 'Chua cap nhat'}\n"
            f"Ngay dang: {b.get('post_date')}\n"
            f"Trang thai: CON HANG"
        )
        markup = {
            "inline_keyboard": [
                [{"text": f"Danh dau DA BAN (ID: {b['id']})", "callback_data": f"sold_{b['id']}"}]
            ]
        }
        send_photo(chat_id, b.get("local_path"), caption, markup)
def handle_callback_query(cq: Dict):
    cq_id = cq.get("id")
    data = cq.get("data", "")
    message = cq.get("message", {})
    chat_id = str(message.get("chat", {}).get("id"))
    if data.startswith("sold_"):
        try:
            book_id = int(data.split("_")[1])
            database.mark_book_sold(book_id)
            answer_callback_query(cq_id, f"Da danh dau sach ID {book_id} la DA BAN.")
            send_message(chat_id, f"[OK] Da cap nhat sach ID {book_id} thanh DA BAN.")
        except Exception as e:
            answer_callback_query(cq_id, f"Loi: {e}")
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
                        if config.TELEGRAM_CHAT_ID and chat_id != str(config.TELEGRAM_CHAT_ID):
                            send_message(chat_id, "Xin loi, tai khoan cua ban khong duoc phep truy cap kho sach nay.")
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

