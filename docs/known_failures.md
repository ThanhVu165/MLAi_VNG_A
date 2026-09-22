# Giới hạn và lỗi đã biết

Không xóa mục cũ. Khi đã xử lý, giữ nguyên mục và thêm nhãn `[đã sửa]`.

- Hiện tượng: Chưa thể chạy một email từ đầu đến cuối. · Điều kiện tái hiện: Gọi ứng dụng ở trạng thái repository hiện tại. · Vì sao chưa sửa: `core/pipeline.py` và facade corpus chưa được tạo ở các task Agent A/B. · Hướng xử lý: Hoàn tất S-03 và kiểm thử tích hợp dọc ở checkpoint H28.
- Hiện tượng: Chưa thể xác minh migration, settings hoặc toàn bộ build bằng CI cục bộ. · Điều kiện tái hiện: Chạy `python`, `py` hoặc `make check` trên môi trường hiện tại. · Vì sao chưa sửa: Máy chưa có Python 3.11 và Make trên PATH. · Hướng xử lý: Cài runtime rồi chạy lại `make check` trước khi đánh dấu các task liên quan là DONE.
- [đã sửa] Hiện tượng: Cấu hình Gemini mặc định lệch model đã xác thực. · Điều kiện tái hiện: Chạy khi không đặt `GEMINI_MODEL`, khiến wrapper dùng `gemini-3.5-flash-lite`. · Vì sao chưa sửa: Cấu hình mặc định không khớp A-08. · Hướng xử lý: Dùng mặc định `gemini-3.5-flash`; vẫn cho phép override qua biến môi trường.
- Hiện tượng: Lượt xử lý ở `LLM_MODE=live` có thể vượt 15 giây tại Gemini. · Điều kiện tái hiện: Dán email C-09 với API live không phản hồi trong môi trường hiện tại. · Vì sao chưa sửa: `process_case()` là lời gọi đồng bộ và không có callback tiến trình hay giới hạn thời gian end-to-end để UI hạ cấp sớm. · Hướng xử lý: Dùng replay cho CI/demo xác định; cân nhắc contract callback hoặc watchdog pipeline sau khi A/B ACK.
