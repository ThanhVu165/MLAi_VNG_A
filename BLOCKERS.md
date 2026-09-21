# BLOCKERS.md

- [B-08][Agent B] Đã ghi `conflict_flag`/`conflict_with` cho chunk ACTIVE và test phát hiện cặp nguồn mâu thuẫn. [cập nhật 2026-09-21] `corpus.api` đã đọc index/nguồn ACTIVE thật; còn cần Agent A tiêu thụ `conflict_flag` trong Evidence Validator để xác minh runtime trả `OUT_OF_POLICY`. Không sửa `core/` vượt phạm vi B-08.

- [B-04][Agent B][đã xử lý 2026-09-21] Đã ghim `pdfplumber==0.11.4`; B-04 trích xuất PDF/DOCX và kiểm thử chuẩn hóa đã hoàn tất.

- [B-02][Agent B] Logic B-02 đã pass 7 pytest; không thể đạt `make check` toàn repo vì `black --check .` báo `infra/db.py` chưa đúng format và `mypy --ignore-missing-imports .` nhận cùng file dưới hai module `db` và `infra.db`. Cả hai đều nằm ngoài phạm vi Agent B. Cần Agent C xử lý rồi B chạy lại full check, commit và chuyển B-02 sang DONE.

  - [đã xử lý 2026-09-21] Sau cập nhật C-04/C-05, Black và Mypy toàn repo đã xanh; B-03 xác nhận full check với 15 test pass.

- [S-02][Agent C][đã gỡ] Migration đã chạy thành công trên SQLite DB trống và xác nhận tạo đủ 12 bảng; `ACTIONS` là `frozenset`. Agent A và B đã ACK rà soát schema.

- [B-01][Agent B] Contract mâu thuẫn: `corpus.api` phải nhận/trả `Domain` và `EvidenceChunk` theo Mục 5.3, nhưng hai type chỉ có trong `core.types` trong khi Mục 5.1 và chỉ dẫn Agent B cấm `corpus/` import `core/`. Không thể tạo instance `EvidenceChunk` hợp contract mà không vi phạm dependency; sao chép dataclass sẽ tạo type khác và phá consumer Runtime. Cần CONTRACT-CHANGE/ACK A+C để chọn: tách types dùng chung ra module trung lập hoặc cho phép riêng `corpus.api` import `core.types`.

  - [đã xử lý 2026-09-21] S-01 đã đóng băng `core/types.py`; theo chỉ đạo dự án, B-01 dùng trực tiếp các type contract này và không sửa `core/`.

- [S-02][Agent C] Môi trường hiện không có `python`, `py` hoặc `make` trên PATH (cũng không tìm thấy Python 3.11 tại các vị trí cài đặt Windows chuẩn), nên chưa thể xác minh migration tạo được SQLite DB trống hoặc chạy `make check`. DDL và danh mục action đã hoàn tất; Agent A và B đã ACK rà soát schema. Cần runtime Python 3.11 và Make/biến thể tương đương để tiếp tục kiểm thử và đánh dấu DONE.
- [C-01][Agent C] `origin` là `https://github.com/ThanhVu165/MLAi_VNG_A.git` và truy cập GitHub khi chưa đăng nhập trả 404, nên chưa thể xác nhận/chuyển repo sang public hoặc bật branch protection cho `main`. Cần phiên GitHub có quyền quản trị repository. Môi trường cũng thiếu Python và Make nên chưa thể cài dependency hoặc chạy `make check`.
- [C-03][Agent C] `infra/settings.py` đã có đủ ngưỡng và override environment. Chưa thể kiểm tra import, chạy `make check`, hoặc quét core/corpus vì môi trường thiếu Python/Make và hai thư mục đó chưa tồn tại.
# BLOCKERS

- [A-08][Agent A][đã gỡ 2026-09-21] Model `gemini-3.5-flash` hoạt động; xác thực thật đạt schema 8/8 và domain 8/8.

- [A-04][Agent A] Heuristic nhận diện ngôn ngữ đạt 10/10 mẫu; Black, Ruff và 34 pytest xanh. [cập nhật 2026-09-21] Agent B đã gỡ 15 lỗi Mypy; còn một lỗi ngoài phạm vi A tại `corpus/indexer.py:132`: `SentenceTransformer` không khớp protocol `Encoder`. Cần Agent B sửa typing này rồi A chạy lại full check để DONE.

- [A-02][Agent A][đã gỡ] Full `mypy .` was blocked by 17 errors in Agent C's audit page. Black, Ruff, mypy, and pytest now pass.

- [A-01] Full `make check` is unavailable: this repository has no Makefile and Python 3.11 has no `mypy` module. The targeted pytest smoke check plus Black and Ruff pass.
