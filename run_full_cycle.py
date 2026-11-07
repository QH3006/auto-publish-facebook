import sys
import logging
import scanner
import group_scanner
import database
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("storage/app.log", encoding="utf-8")
    ]
)
if __name__ == "__main__":
    logging.info("=" * 60)
    logging.info("BẮT ĐẦU CHU KỲ QUÉT TOÀN DIỆN: FANPAGE (30 NGÀY) & CÁC NHÓM")
    logging.info("=" * 60)
    # Bước 1: Quét sâu Fanpage 30 ngày (65 lượt cuộn)
    logging.info("\n>>> BƯỚC 1: Quét Fanpage 'Tiệm sách của Thương'...")
    new_images = scanner.run_scanner(scrolls=65)
    total_books = len(database.get_all_books())
    logging.info(f">>> BƯỚC 1 HOÀN TẤT: Đã tải thêm {new_images} ảnh sách mới. Tổng kho hiện tại: {total_books} cuốn.")
    # Bước 2: Quét các nhóm khách hàng tìm sách
    logging.info("\n>>> BƯỚC 2: Quét các nhóm tìm mua sách và đối chiếu kho...")
    new_leads = group_scanner.scan_facebook_groups()
    logging.info(f">>> BƯỚC 2 HOÀN TẤT: Tìm thấy {new_leads} khách hàng tiềm năng khớp với kho sách.")
    logging.info("\n" + "=" * 60)
    logging.info("TOÀN BỘ TIẾN TRÌNH QUÉT ĐÃ HOÀN TẤT THÀNH CÔNG!")
    logging.info("=" * 60)