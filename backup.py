import os
import glob
import time
import zipfile
import sqlite3
import logging
from datetime import datetime
import config
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
BACKUP_DIR = config.BASE_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)
def backup_database() -> str:
    src_db = config.STORAGE_DIR / "database.db"
    if not src_db.exists():
        logging.warning("No database file found to backup.")
        return ""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst_db = BACKUP_DIR / f"database_{timestamp}.db"
    try:
        src_conn = sqlite3.connect(str(src_db))
        dst_conn = sqlite3.connect(str(dst_db))
        with dst_conn:
            src_conn.backup(dst_conn)
        dst_conn.close()
        src_conn.close()
        logging.info(f"Database backed up successfully to: {dst_db}")
        cleanup_old_backups(pattern="database_*.db", keep=7)
        return str(dst_db)
    except Exception as e:
        logging.error(f"Error backing up database: {e}")
        return ""
def create_full_backup_zip() -> str:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_path = BACKUP_DIR / f"backup_tiemsach_{timestamp}.zip"
    try:
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zipf:
            db_file = config.STORAGE_DIR / "database.db"
            if db_file.exists():
                zipf.write(str(db_file), arcname="storage/database.db")
            env_file = config.BASE_DIR / ".env"
            if env_file.exists():
                zipf.write(str(env_file), arcname=".env")
            images_dir = config.STORAGE_DIR / "images"
            if images_dir.exists():
                for root, _, files in os.walk(str(images_dir)):
                    for file in files:
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, str(config.BASE_DIR))
                        zipf.write(full_p, arcname=rel_p)
        logging.info(f"Full backup zip created at: {zip_path}")
        cleanup_old_backups(pattern="backup_tiemsach_*.zip", keep=5)
        return str(zip_path)
    except Exception as e:
        logging.error(f"Error creating full backup zip: {e}")
        return ""
def cleanup_old_backups(pattern: str, keep: int = 7):
    try:
        files = sorted(BACKUP_DIR.glob(pattern), key=lambda x: x.stat().st_mtime, reverse=True)
        for f in files[keep:]:
            f.unlink()
            logging.info(f"Removed old backup: {f.name}")
    except Exception as e:
        logging.error(f"Error cleaning old backups: {e}")
def send_weekly_backup_to_telegram() -> bool:
    import telegram_bot
    logging.info("Starting weekly full backup to Telegram...")
    zip_path = create_full_backup_zip()
    if not zip_path or not os.path.exists(zip_path):
        telegram_bot.send_alert_to_all("❌ Lỗi: Không thể tạo bản sao lưu toàn bộ kho sách tuần này.")
        return False
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    caption = (
        f"📦 [SAO LƯU ĐẦY ĐỦ ĐỊNH KỲ THỨ 2]\n\n"
        f"⏰ Thời gian: {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}\n"
        f"📁 Gói sao lưu: {os.path.basename(zip_path)}\n"
        f"📊 Dung lượng: {size_mb:.1f} MB (Bao gồm Database + File cấu hình + Toàn bộ ảnh bìa sách)\n\n"
        f"👉 Dữ liệu này được lưu trữ an toàn trên đám mây Telegram để dự phòng."
    )
    cids = telegram_bot.get_allowed_chat_ids()
    sent_any = False
    for cid in cids:
        if size_mb < 49:
            logging.info(f"Uploading backup ({size_mb:.1f} MB) to chat {cid}...")
            ok = telegram_bot.send_document(cid, zip_path, caption=caption)
            logging.info(f"Upload to chat {cid} result: {ok}")
        else:
            ok = telegram_bot.send_message(cid, f"{caption}\n(Dung lượng > 50MB nên được lưu trực tiếp tại ổ cứng máy tính)")
        if ok:
            sent_any = True
    return sent_any
if __name__ == "__main__":
    send_weekly_backup_to_telegram()