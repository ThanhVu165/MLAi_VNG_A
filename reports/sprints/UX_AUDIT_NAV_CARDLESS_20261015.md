# UI-01 — Audit Navigation Session Preservation (cardless)

## Authorization, owner và môi trường

- **Authorization:** Project Coordinator chấp thuận triển khai UI-01 ngày 15/10/2026,
  cardless, không dùng Trello.
- **Owner:** Project Coordinator vận hành máy Mac cùng Codex implementation support.
- **Repository:** `ThanhVu165/MLAi_VNG_A`.
- **Môi trường:** macOS, Python 3.11.17, Streamlit 1.39.0, SQLite tạm, replay offline.
- **Baseline chính xác:** `dev@a6f3b7c7c564cb7bde13e124eb03f121eca0a114`.
- **Final validated implementation SHA:** `d8924c72ac62009570e8f2333607a020b744657b`.
- **Branch:** `codex/ux-audit-navigation-cardless`.
- **Pull request:** [#64](https://github.com/ThanhVu165/MLAi_VNG_A/pull/64), nhắm `dev`.
- **Result:** `READY_FOR_REVIEW`; không tự tuyên bố DONE.
- **LIVE/API calls:** 0.
- **Merge/deploy:** `NOT RUN`.

PR #62 được xác minh đã merged với merge commit đúng bằng baseline trên. Remote `dev`
được fetch và đối chiếu trước khi tạo branch. Branch UI-01 chưa tồn tại trên remote. Working
tree có các artifact M7 untracked từ trước; toàn bộ được giữ nguyên, không reset, clean, stash,
ghi đè hoặc đưa vào commit. Task trước trên branch `codex/ux-pre-m4-cardless` đã đóng qua PR #62,
không phát hiện xung đột Owner hay file ownership.

## Root cause và phương án sửa

Hai điểm điều hướng Email và Verify dùng `st.link_button` với URL
`/Nhat_ky_kiem_toan?case_id=...`. Trình duyệt xử lý đây như điều hướng URL thay vì lệnh chuyển
trang nội bộ của ứng dụng; phiên Streamlit có thể bị thay mới, làm mất
`restricted_demo_case_ids`. Audit sau đó từ chối một ca vốn thuộc phiên gốc.

UI-01 thay hai link này bằng nút gọi API chính thức `st.switch_page()` có sẵn trong Streamlit
1.39.0. Trước khi chuyển, ca đang chọn được ghi vào `st.session_state["audit_case_id"]`.
`st.switch_page` giữ cùng session và tự xóa query string. Audit đọc context trong session khi
không có query tương thích ngược, nhưng context chỉ chọn ca hiển thị; nó không cấp quyền.
Restricted DEMO vẫn lọc ca tồn tại trong `restricted_demo_case_ids` và gọi `case_is_owned()`
trước mọi truy xuất chi tiết.

## Files changed

| File | Thay đổi |
|---|---|
| `pages/1_Xu_ly_email.py` | Email → Audit dùng `st.switch_page` và session context của ca đang xem. |
| `pages/5_Verify.py` | Verify → Audit dùng `st.switch_page`, giữ đúng `case_ref` của ca được chọn. |
| `pages/4_Nhat_ky_kiem_toan.py` | Nhận context nội bộ; giữ query cũ để tương thích nhưng vẫn kiểm tra ownership; selector restricted vẫn dùng được. |
| `tests/test_audit_navigation_session.py` | 8 hồi quy UI-01 cho Email, Verify4, sidebar, phiên độc lập, session/query giả và mã bị chỉnh sửa. |

Không sửa `streamlit_app.py`, `ui/presentation.py`, `core/`, `policies/`, `corpus/`, `infra/`,
schema SQLite, Gold, Set A, Set B hay deployment.

## Acceptance criteria

| AC | Kết quả | Evidence |
|---|---|---|
| AC1 — Email canonical → Audit đúng ca, cùng phiên | **PASS** | AppTest xác nhận context + API chuyển trang; browser xử lý email “Hỏi lệ phí phúc khảo”, mở Audit đúng case và events, URL Audit không có `case_id`. |
| AC2 — Verify4 → Audit đúng ca đã chọn, cùng phiên | **PASS** | Verify4 browser đạt 4/4; nút ca V01 mở đúng Audit “Quy trình và thang điểm rèn luyện”, URL không có query. |
| AC3 — Phiên khác không đọc ca ngoài ownership | **PASS** | Tab trình duyệt độc lập truy cập case của phiên gốc nhận “Bạn không có quyền xem nhật ký của case này trong phiên hiện tại.”; AppTest phủ cả session context và query. |
| AC4 — ID giả/không tồn tại/chỉnh tay/ngoài phiên bị từ chối | **PASS** | AppTest phủ `case-khong-ton-tai`, `case-bi-chinh-sua`, query chỉnh tay lấn session hợp lệ; browser chỉnh tay cũng trả DENIED. |
| AC5 — Không regression canonical, Verify4, sidebar, private mode | **PASS** | Suite bắt buộc 57 passed; browser sidebar mở Audit trong cùng phiên; private mode hiển thị Audit và nút xuất báo cáo, không báo thiếu quyền. |
| AC6 — Không đổi business/policy/storage/admin/LIVE | **PASS** | Scoped diff chỉ gồm 3 UI pages + test; LIVE/API 0; không đổi authorization, schema hoặc storage. |
| AC7 — Tests, browser smoke, self-review, report, SHA và PR | **PASS** | Test mới 8 passed, browser smoke PASS, self-review bên dưới, implementation SHA và PR #64 đã ghi nhận. |

## Validation

Tất cả lệnh dùng `.venv` Python 3.11 và test harness offline. Browser smoke dùng hai database
SQLite tạm riêng cho restricted/private và `LLM_MODE=replay`, `OPENAI_API_KEY` rỗng,
`HF_HUB_OFFLINE=1`.

| Check | Kết quả | Chi tiết |
|---|---|---|
| Test mới UI-01 | **PASS** | `pytest tests/test_audit_navigation_session.py -q` → 8 passed. |
| Suite bắt buộc | **PASS** | `pytest tests/test_restricted_demo.py tests/test_email_input_ui.py tests/test_pre_m4_ux.py tests/test_audit_details.py tests/test_audit_coverage.py tests/test_runtime_replay_audit.py tests/test_audit_navigation_session.py -q` → 57 passed in 4.05s. |
| Black | **PASS** | `black --check --line-length 100` trên toàn bộ Python files thay đổi. |
| Ruff | **PASS** | `ruff check` trên toàn bộ Python files thay đổi. |
| Whitespace | **PASS** | `git diff --check`. |
| LIVE/API | **NOT RUN** | Bị cấm trong task; call count 0. |

## Browser smoke

1. Restricted DEMO local trên `127.0.0.1:8517`, database tạm và replay offline.
2. Chọn email canonical “Hỏi lệ phí phúc khảo”, nhấn **Xử lý email**; kết quả
   `AUTO_REPLY`, trạng thái sắp gửi phản hồi và căn cứ `PK-2026-204:seed:2` hiển thị.
3. Nhấn **Nhật ký kiểm toán** từ kết quả Email; trang chuyển đến
   `/Nhat_ky_kiem_toan` không query, đúng case/tiêu đề và đủ event từ tiếp nhận đến lên lịch.
4. Mở Verify trong cùng tab, chạy Verify4; kết quả 4 PASS, 0 FAIL.
5. Giữ ca V01 đang chọn và nhấn mở Audit; Audit hiển thị đúng case_ref, tiêu đề
   “Quy trình và thang điểm rèn luyện” và các event của ca.
6. Mở tab độc lập với case của bước 2 qua query cũ; Audit từ chối vì tab không sở hữu ca.
7. Sửa query thành `case-bi-chinh-sua`; Audit tiếp tục từ chối.
8. Trở lại Email rồi mở Audit bằng sidebar trong phiên gốc; trang vẫn hoạt động và giữ ca hợp lệ.
9. Private mode local trên `127.0.0.1:8518`, database tạm và replay offline; đủ sáu trang,
   Audit render bình thường, có **Xuất báo cáo**, không phát sinh cảnh báo quyền restricted.

Hai server local được dừng sau smoke. Không deploy, không mở cổng public và không dùng dữ liệu thật.

## Cross-session security

- `audit_case_id` là context trình bày, không phải capability hoặc token.
- Một giá trị được chèn vào `session_state` vẫn bị `case_is_owned()` từ chối nếu không nằm trong
  danh sách ca tồn tại mà phiên hiện tại sở hữu.
- Query tương thích ngược được ưu tiên để phát hiện thao tác chỉnh URL, nhưng không bypass
  ownership. Query giả không thể ẩn sau context session hợp lệ.
- Không thêm URL token, durable ownership, quyền guest/admin hoặc đường đọc DB mới.
- Cross-session denial và fail-closed khi session mất vẫn được giữ nguyên.

## Self-review

- Đã đọc toàn diff và xác nhận chỉ có 4 file implementation/test trong commit.
- Các cải tiến của PR #62 ở Email và Verify được giữ nguyên; chỉ thay đúng control điều hướng Audit.
- `case_is_owned()`, `restricted_demo_case_ids`, private-mode behavior và audit storage không đổi.
- Không có query parameter trong hai luồng điều hướng mới; `st.switch_page` chính thức tương thích
  Streamlit 1.39.0 và được xác nhận trên package đang cài.
- Không có secret, DB local, cache, output browser hay artifact M7 trong commit.
- `git diff --check`, Black, Ruff và toàn bộ suite bắt buộc đều PASS sau thay đổi cuối.

## Risks và limitations

1. Streamlit tiếp tục phát warning có sẵn về việc dùng `st.navigation` cùng thư mục `pages/`;
   đây là kiến trúc baseline và không gây lỗi trong smoke, nhưng ngoài scope UI-01.
2. Query deep-link cũ được giữ cho các caller ngoài scope. Trong Restricted DEMO nó vẫn chỉ hoạt
   động khi ca thuộc session hiện tại; mất session vẫn fail closed theo thiết kế HF1.
3. Evidence browser là local desktop smoke với synthetic replay, không chứng minh LIVE/provider,
   deployment public hay authentication bền vững.

## Handoff

- Baseline: `a6f3b7c7c564cb7bde13e124eb03f121eca0a114`.
- Final validated implementation SHA: `d8924c72ac62009570e8f2333607a020b744657b`.
- PR: [#64 — fix(ui-01): preserve audit navigation session](https://github.com/ThanhVu165/MLAi_VNG_A/pull/64).
- Recommendation: `READY_FOR_REVIEW` để Coordinator kiểm tra và quyết định acceptance/merge.
- Không tự merge, deploy hoặc đánh dấu DONE.
