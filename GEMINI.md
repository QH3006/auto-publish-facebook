# Project Coding Rules

1. **Tối đa 500 dòng mỗi file code**: Mỗi file mã nguồn (`.py`, v.v.) không được vượt quá 500 dòng.
2. **Không để dòng trống**: Tuyệt đối không chèn dòng trống (dòng enter thừa không có nội dung) trong các file code.
3. **Tách nhỏ thành nhiều file khi vượt giới hạn**: Khi triển khai tính năng mới hoặc mở rộng logic mà 1 file không đủ chứa trong giới hạn 500 dòng, phải chủ động chia nhỏ thành nhiều file/module theo chức năng rõ ràng (ví dụ: tách giao diện khỏi server như `web_view.py` và `web_admin.py`, hoặc tách parser/helper riêng).
