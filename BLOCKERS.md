# BLOCKERS.md

- [S-02][Agent C] Môi trường hiện không có `python`, `py` hoặc `make` trên PATH (cũng không tìm thấy Python 3.11 tại các vị trí cài đặt Windows chuẩn), nên chưa thể xác minh migration tạo được SQLite DB trống hoặc chạy `make check`. DDL và danh mục action đã hoàn tất; Agent A và B đã ACK rà soát schema. Cần runtime Python 3.11 và Make/biến thể tương đương để tiếp tục kiểm thử và đánh dấu DONE.
