# Giới hạn và lỗi đã biết

Không xóa mục cũ. Khi đã xử lý, giữ nguyên mục và thêm nhãn `[đã sửa]`.

- Hiện tượng: Chưa thể chạy một email từ đầu đến cuối. · Điều kiện tái hiện: Gọi ứng dụng ở trạng thái repository hiện tại. · Vì sao chưa sửa: `core/pipeline.py` và facade corpus chưa được tạo ở các task Agent A/B. · Hướng xử lý: Hoàn tất S-03 và kiểm thử tích hợp dọc ở checkpoint H28.
- Hiện tượng: Chưa thể xác minh migration, settings hoặc toàn bộ build bằng CI cục bộ. · Điều kiện tái hiện: Chạy `python`, `py` hoặc `make check` trên môi trường hiện tại. · Vì sao chưa sửa: Máy chưa có Python 3.11 và Make trên PATH. · Hướng xử lý: Cài runtime rồi chạy lại `make check` trước khi đánh dấu các task liên quan là DONE.
