import sys
import time
import random
import logging
import argparse
from datetime import datetime
import config
import database
import text_utils
import cleaner
import backup
import ai_engine
import fb_poster
import scanner
import group_scanner
import login_helper
import telegram_bot
import group_poster
import web_admin
import settings_manager
import threading
file_handler = logging.FileHandler(config.STORAGE_DIR / "app.log", encoding="utf-8")
stream_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = [stream_handler, file_handler]
_post_lock = threading.Lock()
def execute_single_post(min_days: int = None, max_days: int = None):
    if not _post_lock.acquire(blocking=False):
        logging.warning("Đang có một tiến trình đăng bài Fanpage khác chạy song song, bỏ qua lượt này.")
        return False
    try:
        logging.info("--- STARTING SINGLE-IMAGE POSTING SESSION ---")
        p_min = min_days if min_days is not None else config.MIN_DAYS_OLD
        p_max = max_days if max_days is not None else config.MAX_DAYS_OLD
        candidates = database.get_unposted_eligible_images(
            min_days=p_min,
            max_days=p_max
        )
        if not candidates:
            msg = f"Kho chưa có sách đủ tuổi ({p_min}-{p_max} ngày) để đăng bài Fanpage."
            logging.warning(msg)
            telegram_bot.send_alert_to_all(f"⚠️ [LƯU Ý CỮ ĐĂNG] {msg}")
            return False
        selected = random.choice(candidates)
        image_id = selected["id"]
        local_path = selected["local_path"]
        age_days = selected["age_days"]
        logging.info(f"Selected image ID {image_id} (age: {age_days} days) at: {local_path}")
        database.mark_image_attempted(image_id)
        logging.info(f"Generating 3-5 line intro caption using [{config.AI_PROVIDER}]...")
        caption = ai_engine.generate_caption_for_image(local_path, book_info=selected)
        logging.info(f"Generated caption:\n{caption}")
        result = fb_poster.publish_photo_to_facebook(local_path, caption)
        if result.get("success"):
            database.mark_image_published(image_id)
            logging.info(f"SUCCESS: Image ID {image_id} published successfully.")
            title_disp = selected.get('title') or 'Sách hay'
            price_disp = f"\n💰 Giá: {telegram_bot.format_price_vnd(selected.get('price'))}" if selected.get('price') else ""
            telegram_bot.send_alert_to_all(f"✅ [TỰ ĐỘNG ĐĂNG BÀI] Đã đăng thành công lên Fanpage!\n📖 Tựa: '{title_disp}'{price_disp}")
            return True
        else:
            if result.get("submitted"):
                database.mark_image_published(image_id)
                logging.warning(f"Marked Image ID {image_id} as published because 'Đăng' was already clicked.")
            err_msg = result.get('error') or 'Lỗi không xác định'
            logging.error(f"Failed to publish: {err_msg}")
            telegram_bot.send_alert_to_all(f"⚠️ [LỖI ĐĂNG BÀI] Cữ đăng Fanpage thất bại:\nLý do: {err_msg}")
            return False
    finally:
        _post_lock.release()
def search_inventory(keyword: str):
    print(f"\nSearching available books matching: '{keyword}'...")
    results = database.search_available_books(keyword)
    if not results:
        print("No matching books found in current available inventory.\n")
        return []
    print(f"Found {len(results)} available book(s):\n")
    print(f"{'ID':<6} | {'Title':<30} | {'Author':<20} | {'Post Date':<10}")
    print("-" * 75)
    for b in results:
        t = b["title"] or "Untitled"
        a = b["author"] or "Unknown"
        print(f"{b['id']:<6} | {t[:28]:<30} | {a[:18]:<20} | {b['post_date']:<10}")
    print("-" * 75 + "\n")
    return results
def show_leads():
    leads = database.get_leads(status="pending")
    print("\n" + "=" * 70)
    print("      POTENTIAL CUSTOMER LEADS FOUND IN GROUPS")
    print("=" * 70)
    if not leads:
        print("No pending customer leads right now.")
        print("Tip: Run 'python main.py --scan-leads' to scan Facebook groups for buyers.\n")
        return
    print(f"Found {len(leads)} customer inquiry(ies) matching books in your inventory:\n")
    for idx, l in enumerate(leads, 1):
        print(f"[{idx}] LEAD ID: {l['id']} | MATCHED BOOK: '{l['matched_book_title']}' (Book ID: {l['matched_book_id']})")
        print(f"    Post Link: {l['post_url']}")
        print(f"    Content:   \"{l['content_snippet']}\"")
        print(f"    Detected:  {l['created_at']}")
        print(f"    Action:    Open the link to comment manually, then run: python main.py --done-lead {l['id']}")
        print("-" * 70)
    print()
def show_status():
    stats = database.get_stats()
    print("\n" + "=" * 60)
    print("      24/7 AUTO BOOK POSTER & INVENTORY STATISTICS")
    print("=" * 60)
    print(f" * Total posts tracked:               {stats['total_posts']}")
    print(f" * Total book images:                 {stats['total_images']}")
    print(f" * Books AVAILABLE in stock:          {stats['available_in_stock']}")
    print(f" * Books SOLD OUT:                    {stats['sold_out']}")
    print(f" * Published images:                  {stats['published_images']}")
    print(f" * Ready to post (7-30 days):         {stats['eligible_ready_to_post']}")
    print(f" * Pending Customer Leads (Groups):   {stats['pending_leads']}")
    print("-" * 60)
    print(f" * Active AI Provider:                {config.AI_PROVIDER.upper()}")
    print(f" * Monitored Groups Count:            {len(config.MONITORED_GROUP_URLS)}")
    print(f" * Browser Profile Directory:         {config.BROWSER_PROFILE_DIR}")
    print(f" * 3 Daily posting times:             {', '.join(config.POSTING_HOURS)}")
    print(f" * Daily group posting time (1 post): {config.GROUP_POSTING_HOUR}")
    print(f" * Daily scan schedule:               {config.SCAN_SCHEDULE_HOUR}")
    print(f" * Target Page URL:                   {config.TARGET_PAGE_URL}")
    print(f" * Web Admin Dashboard (LAN):         http://{web_admin.get_local_ip()}:8080")
    print("=" * 60 + "\n")
def run_scheduler_loop():
    logging.info("24/7 AUTO FACEBOOK POSTER ENGINE STARTED...")
    logging.info(f"AI Provider: {config.AI_PROVIDER.upper()}")
    logging.info(f"Daily posting schedule: {', '.join(config.POSTING_HOURS)}")
    logging.info(f"Scan schedule: {config.SCAN_SCHEDULE_HOUR} | Cleanup schedule: {config.CLEANUP_SCHEDULE_HOUR}")
    logging.info(f"Weekly Backup schedule: Monday at {config.WEEKLY_BACKUP_HOUR} to Telegram")
    if config.MONITORED_GROUP_URLS:
        logging.info(f"Group Lead Scanner active across {len(config.MONITORED_GROUP_URLS)} group(s).")
    if config.TELEGRAM_BOT_TOKEN:
        logging.info("Starting background Telegram Bot listener...")
        threading.Thread(target=telegram_bot.run_telegram_bot_listener, daemon=True).start()
    logging.info(f"Starting Web Admin Dashboard at: http://{web_admin.get_local_ip()}:8080 (LAN only for editing)...")
    threading.Thread(target=web_admin.run_web_admin, kwargs={"port": 8080}, daemon=True).start()
    last_posted_minute = ""
    last_scanned_day = ""
    last_cleaned_day = ""
    last_weekly_backup_day = ""
    last_group_posted_day = ""
    last_lead_scan_time = 0
    last_heartbeat_time = 0
    logging.info("Hệ thống đã sẵn sàng và đang ở chế độ CHỜ TRỰC CHIẾN 24/7 (Standby)...")
    while True:
        try:
            now = datetime.now()
            current_time_str = now.strftime("%H:%M")
            current_day_str = now.strftime("%Y-%m-%d")
            current_epoch = time.time()
            if current_time_str in config.POSTING_HOURS and current_time_str != last_posted_minute:
                logging.info(f"SCHEDULE TRIGGER: Posting time reached ({current_time_str})")
                threading.Thread(target=execute_single_post, daemon=True).start()
                last_posted_minute = current_time_str
            if config.TARGET_POST_GROUP_URLS and current_time_str == config.GROUP_POSTING_HOUR and current_day_str != last_group_posted_day:
                logging.info(f"SCHEDULE TRIGGER: Daily Group posting 1 post ({current_time_str})...")
                threading.Thread(target=group_poster.post_single_book_to_group, daemon=True).start()
                last_group_posted_day = current_day_str
            if current_time_str == config.SCAN_SCHEDULE_HOUR and current_day_str != last_scanned_day:
                logging.info(f"SCHEDULE TRIGGER: Starting daily scan ({current_time_str})...")
                threading.Thread(target=scanner.run_scanner, daemon=True).start()
                last_scanned_day = current_day_str
            if current_time_str == config.CLEANUP_SCHEDULE_HOUR and current_day_str != last_cleaned_day:
                logging.info(f"SCHEDULE TRIGGER: Starting cleanup for sold books ({current_time_str})...")
                threading.Thread(target=cleaner.run_cleaner, daemon=True).start()
                last_cleaned_day = current_day_str
            if now.weekday() == 0 and current_time_str == config.WEEKLY_BACKUP_HOUR and current_day_str != last_weekly_backup_day:
                logging.info(f"SCHEDULE TRIGGER: Starting weekly full backup to Telegram ({current_time_str} Monday)...")
                threading.Thread(target=backup.send_weekly_backup_to_telegram, daemon=True).start()
                last_weekly_backup_day = current_day_str
            if config.MONITORED_GROUP_URLS:
                interval_secs = config.LEAD_SCAN_INTERVAL_MINUTES * 60
                is_quiet = (now.hour >= config.LEAD_SCAN_QUIET_START_HOUR or now.hour < config.LEAD_SCAN_QUIET_END_HOUR)
                if is_quiet:
                    if (current_epoch - last_lead_scan_time) >= interval_secs:
                        logging.info(f"[NGHỈ ĐÊM 22h-06h] Hiện tại là {current_time_str}, tạm dừng quét nhóm để tiết kiệm tài nguyên. Sẽ quét lại lúc 06:00 sáng.")
                        last_lead_scan_time = current_epoch
                else:
                    if (current_epoch - last_lead_scan_time) >= interval_secs:
                        logging.info("SCHEDULE TRIGGER: Scanning Facebook Groups for buyer inquiries...")
                        threading.Thread(target=group_scanner.scan_facebook_groups, kwargs={"max_days": 2, "deep_scan": False}, daemon=True).start()
                        last_lead_scan_time = current_epoch
                        logging.info("-> Hoàn tất lượt quét nhóm. Đã quay lại trạng thái CHỜ...")
            if (current_epoch - last_heartbeat_time) >= 180:
                is_quiet = (now.hour >= config.LEAD_SCAN_QUIET_START_HOUR or now.hour < config.LEAD_SCAN_QUIET_END_HOUR)
                if is_quiet:
                    logging.info(f"[CHẾ ĐỘ NGHỈ ĐÊM] Lúc {now.strftime('%H:%M:%S')} | Web Admin: OK | Tạm dừng quét nhóm đêm (22h00 - 05h59) | Cữ đăng bài Fanpage sáng: {config.POSTING_HOURS[0]}")
                else:
                    next_mins = max(0, int(((last_lead_scan_time + (config.LEAD_SCAN_INTERVAL_MINUTES * 60)) - current_epoch) / 60))
                    logging.info(f"[CHẾ ĐỘ CHỜ 24/7] Bot đang hoạt động ngầm lúc {now.strftime('%H:%M:%S')} | Quét nhóm tiếp sau: ~{next_mins}p | Cữ đăng Fanpage: {', '.join(config.POSTING_HOURS)}")
                last_heartbeat_time = current_epoch
            time.sleep(20)
        except KeyboardInterrupt:
            logging.info("Stopped by user (Ctrl+C).")
            break
        except Exception as e:
            logging.error(f"Unexpected error in main loop: {e}")
            time.sleep(30)
def main():
    settings_manager.load_and_apply_settings()
    parser = argparse.ArgumentParser(description="24/7 Automated Facebook Book Poster & Inventory")
    parser.add_argument("--status", action="store_true", help="Display inventory stats and configuration")
    parser.add_argument("--post-now", action="store_true", help="Immediately test posting one image")
    parser.add_argument("--post-group-now", action="store_true", help="Immediately test posting 1 image to Facebook Group")
    parser.add_argument("--scan-now", action="store_true", help="Immediately scan target Facebook Page")
    parser.add_argument("--clean-now", action="store_true", help="Clean sold-out expired books")
    parser.add_argument("--backup-now", action="store_true", help="Immediately create full backup and send to Telegram")
    parser.add_argument("--search", type=str, help="Search available books in inventory by keyword")
    parser.add_argument("--sold", type=int, help="Mark book ID as sold out (e.g., --sold 5)")
    parser.add_argument("--available", type=int, help="Restore book ID as available (e.g., --available 5)")
    parser.add_argument("--scan-leads", action="store_true", help="Scan Facebook groups for customers looking for books")
    parser.add_argument("--leads", action="store_true", help="Show all detected customer leads")
    parser.add_argument("--done-lead", type=int, help="Mark lead ID as contacted/done (e.g., --done-lead 1)")
    parser.add_argument("--login-fb", action="store_true", help="Open visible browser to log in to Facebook once")
    parser.add_argument("--bot", action="store_true", help="Run standalone Telegram Bot listener")
    parser.add_argument("--admin", action="store_true", help="Run standalone Web Admin controller (port 8080)")
    args = parser.parse_args()
    if args.status:
        show_status()
    elif args.post_now:
        execute_single_post()
    elif args.post_group_now:
        group_poster.post_single_book_to_group()
    elif args.scan_now:
        scanner.run_scanner()
    elif args.clean_now:
        cleaner.run_cleaner()
    elif args.backup_now:
        backup.send_weekly_backup_to_telegram()
    elif args.search:
        search_inventory(args.search)
    elif args.sold:
        database.mark_book_sold(args.sold)
        print(f"[OK] Marked book ID {args.sold} as SOLD OUT.")
    elif args.available:
        database.mark_book_available(args.available)
        print(f"[OK] Restored book ID {args.available} as AVAILABLE.")
    elif args.scan_leads:
        group_scanner.scan_facebook_groups()
    elif args.leads:
        show_leads()
    elif args.done_lead:
        database.mark_lead_done(args.done_lead)
        print(f"[OK] Marked lead ID {args.done_lead} as CONTACTED.")
    elif args.login_fb:
        login_helper.login_facebook_profile()
    elif args.bot:
        telegram_bot.run_telegram_bot_listener()
    elif args.admin:
        web_admin.run_web_admin()
    else:
        run_scheduler_loop()
if __name__ == "__main__":
    main()
