import os
import logging
from datetime import datetime
import database
import config
import backup
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
def run_cleaner():
    logging.info("Starting cleanup routine...")
    try:
        backup.backup_database()
    except Exception as e:
        logging.error(f"Daily database backup error: {e}")
    expired_images = database.get_expired_images()
    if not expired_images:
        logging.info("No expired or sold books to clean. Inventory is up to date.")
        return 0
    deleted_count = 0
    bytes_freed = 0
    for item in expired_images:
        file_path = item["local_path"]
        img_id = item["id"]
        reason = item.get("reason", "expired")
        if os.path.exists(file_path):
            try:
                size = os.path.getsize(file_path)
                os.remove(file_path)
                bytes_freed += size
            except Exception as e:
                logging.error(f"Error deleting file {file_path}: {e}")
        database.delete_image_record(img_id)
        deleted_count += 1
        logging.info(f"Cleaned item ID {img_id} ({reason}): {os.path.basename(file_path)}")
    mb_freed = bytes_freed / (1024 * 1024)
    logging.info(f"Cleanup complete. Removed {deleted_count} items, freed {mb_freed:.2f} MB.")
    return deleted_count
if __name__ == "__main__":
    run_cleaner()