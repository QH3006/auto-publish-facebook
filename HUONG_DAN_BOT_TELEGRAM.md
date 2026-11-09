# HƯỚNG DẪN SỬ DỤNG BOT TELEGRAM QUẢN TRỊ TIỆM SÁCH CỦA THƯƠNG
Bot Telegram `@tiemsachcuathuongbot` đóng vai trò là trợ lý ảo từ xa qua điện thoại giúp chủ tiệm tra cứu kho sách, thêm/sửa sách, kiểm tra sức khỏe máy chủ và nhận thông báo khách mua 24/7.
---
## 1. CÁC LỆNH TRA CỨU & QUẢN TRỊ KHO SÁCH
| Lệnh | Cú pháp ví dụ | Chức năng |
| :--- | :--- | :--- |
| `/start` hoặc `/help` | `/help` | Hiển thị bảng menu hướng dẫn toàn bộ lệnh. |
| `/tim` | `/tim Rừng Na Uy` hoặc `/tim Higashino` | Tìm sách có sẵn trong kho theo tựa đề hoặc tên tác giả. |
| `/theloai` | `/theloai Văn học Nhật Bản` | Lọc các cuốn sách theo thể loại chỉ định còn hàng. |
| `/gia` | `/gia 50k 100k` hoặc `/gia 70` | Lọc sách theo khoảng giá hoặc mức giá tối đa còn hàng. |
| `/kho` | `/kho` | Xem danh sách tóm tắt các cuốn sách sẵn sàng bán trong kho. |
| `/them` | `/them Tựa Sách \| Tác Giả \| Thể Loại \| Giá` | Thêm sách mới trực tiếp vào kho (tự động lấp vào các ID còn khuyết). |
| `/ban` | `/ban 146` | Đánh dấu sách có ID tương ứng là **Đã bán** (`sold_out`). |
| `/con` | `/con 146` | Khôi phục trạng thái sách có ID tương ứng thành **Còn hàng** (`available`). |
| `/thongke` | `/thongke` | Xem thống kê số lượng sách, trạng thái kho và số bài đăng. |
| `/server` | `/server` | Kiểm tra tài nguyên phần cứng (CPU, RAM, Uptime). |
---
## 2. THÔNG BÁO TỰ ĐỘNG KHÁCH HỎI MUA (LEADS ALERT)
Khi hệ thống quét các nhóm Facebook và phát hiện bài đăng của người mua khớp với sách trong kho tiệm, Bot sẽ tự động gửi thông báo với format:
```text
🎯 PHÁT HIỆN KHÁCH HỎI MUA SÁCH!
📖 Cuốn sách: Malorie - Hành Trình Chạy Trốn Tử Thần
💰 Giá kho: 70.000 đ
🏷️ Thể loại: Văn học phương Tây
💬 Trích dẫn bài đăng: "Mình cần tìm cuốn này, ai có pass lại cho mình với..."
🔗 Mở bài đăng Facebook: https://www.facebook.com/...
```
Chủ tiệm chỉ cần bấm vào đường link để vào bình luận hoặc nhắn tin báo giá ngay cho khách.
---
## 3. GIAO DIỆN WEB ADMIN NỘI BỘ
Ngoài bot Telegram, hệ thống còn cung cấp giao diện Web Admin trực quan tại mạng nội bộ:
* **Địa chỉ:** `http://localhost:8080` (hoặc qua IP nội bộ mạng Wi-Fi: `http://192.168.x.x:8080`)
* **Chức năng:**
  * Lọc thể loại sách theo menu xổ xuống.
  * Thêm, xóa danh mục thể loại mới tùy ý.
  * Xem, sửa thông tin giá, bìa sách và trạng thái kho.
  * Quản lý danh sách khách hỏi mua (mở bài đăng trực tiếp, đổi trạng thái Đã liên hệ, Xóa lead).