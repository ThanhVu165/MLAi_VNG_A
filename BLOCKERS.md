# BLOCKERS.md

- [S-02][Agent C] Môi trường hiện không có `python`, `py` hoặc `make` trên PATH (cũng không tìm thấy Python 3.11 tại các vị trí cài đặt Windows chuẩn), nên chưa thể xác minh migration tạo được SQLite DB trống hoặc chạy `make check`. DDL và danh mục action đã hoàn tất; Agent A và B đã ACK rà soát schema. Cần runtime Python 3.11 và Make/biến thể tương đương để tiếp tục kiểm thử và đánh dấu DONE.
- [C-01][Agent C] `origin` là `https://github.com/ThanhVu165/MLAi_VNG_A.git` và truy cập GitHub khi chưa đăng nhập trả 404, nên chưa thể xác nhận/chuyển repo sang public hoặc bật branch protection cho `main`. Cần phiên GitHub có quyền quản trị repository. Môi trường cũng thiếu Python và Make nên chưa thể cài dependency hoặc chạy `make check`.
- [C-03][Agent C] `infra/settings.py` đã có đủ ngưỡng và override environment. Chưa thể kiểm tra import, chạy `make check`, hoặc quét core/corpus vì môi trường thiếu Python/Make và hai thư mục đó chưa tồn tại.
# BLOCKERS

- [A-01] Full `make check` is unavailable: this repository has no Makefile and Python 3.11 has no `mypy` module. The targeted pytest smoke check plus Black and Ruff pass.
