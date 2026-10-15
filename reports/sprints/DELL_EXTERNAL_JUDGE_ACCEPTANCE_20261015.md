# Dell External Judge Acceptance — 2026-10-15

## Kết luận

**Kết quả Phase A: PARTIAL. Phase B: NOT RUN.**

Luồng public tải được, bốn ca Verify bắt buộc đều PASS, các rào chắn public/restricted hoạt động, và hai phiên độc lập không đọc được case của nhau. Hai điểm chưa đạt để kết luận ACCEPTED là: bộ Escalation5 không có trên UI public và liên kết từ kết quả email sang Nhật ký kiểm toán mở tab mới, sau đó chính người vừa xử lý bị từ chối xem nhật ký. Đây là PUBLIC E2E FAILURE; deployed version và root cause NOT VERIFIED.

## Phạm vi và môi trường

| Mục | Giá trị |
|---|---|
| Work label | `DELL-JUDGE-ACCEPTANCE` |
| Owner | Thu — Dell |
| Authorization | Cardless; chỉ kiểm tra public/replay, không dùng LIVE/API |
| Repository | `ThanhVu165/MLAi_VNG_A` |
| Nhánh nguồn | `dev` |
| SHA `dev` đã kiểm tra | `3a36a2fd1513a7c3afea0bb98c417aaceb1cb3d8` |
| Đồng bộ tại thời điểm kiểm thử | `HEAD...origin/dev = 0/0` sau `git pull --ff-only origin dev` |
| Latest `origin/dev` tại closeout | `11bd04205e560e489203da43874e332505727a2a`, xác minh bằng fetch ngày 2026-10-15; không chạy lại browser smoke |
| URL public | <https://exodia-web-production.up.railway.app/> |
| SHA đang deploy | **NOT VERIFIED** — UI không công bố SHA; Railway account kết nối trong phiên không có project Exodia tương ứng |
| Chế độ runtime quan sát được | Public restricted demo; canonical/Verify dùng replay, thao tác gửi là mô phỏng |
| Máy/OS | Dell, Windows |
| Trình duyệt | Codex In-app Browser; hai tab tạo hai Streamlit session độc lập |
| Kích thước bằng chứng hình ảnh | khoảng `1091 × 759` px |
| Múi giờ báo cáo | Asia/Saigon (`UTC+07:00`) |

Không có bằng chứng về một đầu việc Thu đang hoạt động và xung đột phạm vi. Báo cáo UX cardless trước đó đã được merge qua PR #65; PR #66 đã đưa candidate kiểm thử input mới vào `dev`. Không suy diễn rằng SHA `dev` hiện đã được deploy.

## Kết quả kiểm tra

### A1 — Website public và điều hướng

**PASS, có lỗi luồng Audit ghi ở A4.**

- Trang chủ tải và sử dụng được sau khoảng 2–3 giây theo quan sát automation; đây không phải benchmark hiệu năng.
- Điều hướng public hiển thị: **Xử lý email**, **Quy định & căn cứ**, **Nhật ký kiểm toán**, **Kiểm thử**.
- UI công khai rõ trạng thái: chưa kết nối hộp thư, gửi được ghi nhận mô phỏng, môi trường mô phỏng an toàn.
- Trang quản trị quy định ở chế độ chỉ đọc và ghi rõ thao tác quản trị đã bị khóa phía máy chủ; không thấy upload hay mutation control.
- Hàng đợi đặc quyền không mở cho khách trên UI public.

### A2 — Verify4

**PASS: 4/4.**

Quan sát lúc `2026-10-15 18:58:00 +07:00` (`2026-10-15T11:58:00.609Z`).

| Case | Kết quả | Thời gian UI |
|---|---|---:|
| V01 | `AUTO_REPLY` — PASS | 0.1 s |
| V02 | `AUTO_REPLY` — PASS | 0.1 s |
| V03 | `ESCALATE` — PASS | 0.1 s |
| V04 | `ESCALATE` — PASS | 0.1 s |
| Tổng | **4 PASS, 0 FAIL (100%)** | **0.4 s** |

Thời gian automation từ click đến UI có kết quả là khoảng 3.47 giây, gồm rerender và polling của trình duyệt.

Bằng chứng ảnh trong phiên, không lưu thành file: SHA-256 `3943e57f456b1684cea9ccc8b3faea25a0fa740b6fcf9db82d54a033543d4d48`, 55,174 byte, chụp `2026-10-15T11:58:05.793Z`.

### A3 — Escalation5

**NOT AVAILABLE.**

Selector của trang Kiểm thử chỉ có **Bộ kiểm thử 4 ca bắt buộc (Sơ khảo)**. Không có Escalation5 để chạy trên public UI, vì vậy không ghi nhận PASS/FAIL giả định.

### A4 — Email canonical → kết quả → Audit

**FAIL ở bước mở Audit.**

Ca canonical thường:

- Mẫu: **Hỏi lệ phí phúc khảo**.
- Case ID: `c_01M4ZPVDR5K904ZY5CGSWS7ZWP`.
- Kết quả: `AUTO_REPLY · Tự động`, lý do đủ căn cứ, thời gian UI 0.1 giây.
- Xử lý lúc `2026-10-15 18:58:37 +07:00`.
- Bản nháp trả lời lệ phí 150.000 đồng/học phần, kèm dẫn chứng `PK-2026-204:seed:2`.

Bằng chứng ảnh trong phiên, không lưu thành file: SHA-256 `585e25f411f38c76baf15549f11352601102f009274dae4d0e7332cd052f9bf1`, 64,884 byte, chụp `2026-10-15T11:58:47.772Z`.

Ca cần thẩm quyền:

- Mẫu: **Xin phúc khảo trễ**.
- Case ID: `c_01M4ZPWTWXNETAMHZQJ20CBDAG`.
- Kết quả: `ESCALATE · Cần người`, lý do cần quyết định của Trưởng phòng Đào tạo, thời gian UI 0.1 giây.
- Xử lý lúc `2026-10-15 18:59:23 +07:00`.

**OBSERVED ON PUBLIC WEBSITE:** ở cả hai ca, liên kết **Nhật ký kiểm toán** dùng `target="_blank"` và mở tab mới; trang Audit trả về **“Bạn không có quyền xem nhật ký của case này trong phiên hiện tại.”** dù người dùng vừa xử lý case ở tab nguồn. Hành vi phù hợp với mất session ownership, nhưng nguyên nhân runtime chưa được xác minh.

**VERIFIED GITHUB CODE EVIDENCE:** [PR #64](https://github.com/ThanhVu165/MLAi_VNG_A/pull/64) đã MERGED; merge commit `b728d00ba6e53b8568554082fe7f4cb6a0dc03e1` là ancestor của latest `origin/dev`. Source tại SHA closeout trong `pages/1_Xu_ly_email.py` dùng `st.button`, `st.session_state["audit_case_id"]` và `st.switch_page` nhằm giữ điều hướng trong cùng Streamlit session. Đây là bằng chứng source, không chứng minh public đang chạy source đó.

**Classification: PUBLIC E2E FAILURE — DEPLOYED VERSION / ROOT CAUSE NOT VERIFIED.** Không kết luận đây là regression của source hiện hành. Cần xác minh actual deployed SHA và so sánh merged `dev` trước khi mở task sửa code hoặc redeploy. Không sửa code trong nhiệm vụ này.

**Mức độ: High cho hành trình judge.** Không thấy rò rỉ dữ liệu; cơ chế từ chối truy cập hoạt động, nhưng hành trình bắt buộc Email → Result → Audit bị đứt.

Cách tái hiện:

1. Mở trang Xử lý email trong một phiên mới.
2. Chọn email canonical và bấm xử lý.
3. Từ màn hình kết quả, bấm **Nhật ký kiểm toán**.
4. Quan sát tab mới báo không có quyền xem chính case vừa tạo.

### A5 — Hai phiên độc lập và cách ly case

**PASS cho session isolation; giới hạn môi trường được ghi nhận.**

- Phiên A giữ case thẩm quyền `c_01M4ZPWTWXNETAMHZQJ20CBDAG`.
- Phiên B xử lý mẫu **Văn bản rèn luyện áp dụng**, tạo case `c_01M4ZPYCARTBJ0WH0GPG57CSKV`, kết quả `ESCALATE · Cần bổ sung thông tin`, lúc `2026-10-15 19:00:14 +07:00`.
- Sau khi phiên B xử lý, phiên A vẫn giữ nguyên case của mình; không có ghi đè trạng thái.
- Dùng phiên B mở deep link Audit của case phiên A bị từ chối đúng với thông báo không có quyền trong phiên hiện tại.
- Không brute force, không stress, không thử vượt guard.

Bằng chứng ảnh phiên B, không lưu thành file: SHA-256 `ab81aa293453ac1106ed11599e3a4bbdf179a977bd68ff404788f054179afc1c`, 90,876 byte, chụp `2026-10-15T12:00:26.154Z`.

Hai phiên là hai tab IAB có Streamlit session độc lập trong cùng ứng dụng, không phải hai profile Chrome/Edge cấp hệ điều hành.

### A6 — Trạng thái input mới

**UI AVAILABLE; PROCESSING LOCKED.**

Các trường người gửi, tiêu đề và nội dung hiển thị và nhận nhập liệu. UI ghi rõ lane input mới chỉ hoạt động khi máy chủ được cấp quyền LIVE, còn hiện tại input mới chưa được lưu hoặc xử lý. Không submit input tùy ý vì phiên này không có quyền LIVE/API.

## Ma trận acceptance

| AC | Trạng thái | Bằng chứng |
|---|---|---|
| AC1 — xác nhận build/SHA | PASS | `dev` đúng SHA; deployed SHA được ghi rõ **NOT VERIFIED** |
| AC2 — public UX/navigation | PARTIAL | Website tải được; public Email → Audit FAIL, root cause NOT VERIFIED |
| AC3 — Verify4/Escalation5/Email-Audit | PARTIAL | Verify4 PASS; Escalation5 NOT AVAILABLE; Email-Audit FAIL |
| AC4 — hai session độc lập | PASS | Không ghi đè và deep link chéo bị từ chối; giới hạn IAB được nêu rõ |
| AC5 — không LIVE/API/prod change | PASS trong phạm vi thao tác | Không chủ động gọi LIVE/provider API, gửi thật hoặc deploy; UI báo replay/mô phỏng. Không có backend telemetry để xác nhận tổng số provider API call |
| AC6 — báo cáo và handoff | PASS | Môi trường, timestamp, evidence, bug và trạng thái đều có trong báo cáo này |
| AC7 — điều kiện Phase B | PASS | **Phase B NOT RUN** |

## Risk register và handoff

| Ưu tiên | Rủi ro | Chủ trì đề xuất | Hành động tiếp theo |
|---|---|---|---|
| P1 | Public Email → Audit FAIL; deployed version/root cause chưa xác minh | Deployment/Web owner | Xác minh actual deployed SHA, so sánh merged dev/PR #64 trước khi đề xuất sửa code hoặc redeploy |
| P1 | Escalation5 không xuất hiện trên public Verify UI | Verify/UI owner | Xác nhận đây là chủ ý hay thiếu cấu hình; công bố trạng thái rõ cho judge |
| P2 | Không xác minh được SHA đang deploy | Deployment owner | Hiển thị build SHA trên UI/health page hoặc cấp project evidence đọc-only |
| P3 | Chưa kiểm tra bằng hai browser profile OS độc lập | Dell owner | Chạy lại isolation trên Chrome/Edge profile riêng nếu cần bằng chứng mạnh hơn |

**Quyết định:** chưa khuyến nghị chạy Phase B. Điều kiện chuyển pha trong brief chưa thỏa vì Phase A còn lỗi hành trình Audit và Escalation5 chưa khả dụng.

## Tự rà soát

- Chỉ tạo/chỉnh sửa file báo cáo này.
- Không chủ động gọi LIVE/provider API, gửi email thật, deploy hoặc thay đổi production. Không có backend telemetry để khẳng định tổng số LIVE/API call bằng 0.
- Không ghi secret, token, cookie, header xác thực hay dữ liệu nhạy cảm.
- Không ghi nhận PASS cho bước không chạy hoặc không có bằng chứng.
- Các thư mục untracked có sẵn `.canva-review/` và `slides/` được giữ nguyên, không đưa vào phạm vi báo cáo.
- Closeout chỉ chỉnh báo cáo, không chạy lại pytest/browser smoke. Secret/PII scan và kiểm tra Markdown/diff được thực hiện trước khi commit; không có nội dung private Set A/B hoặc Gold trong báo cáo.
- Các email, case ID, nội dung trả lời và dẫn chứng trong phần quan sát thuộc mẫu synthetic/canonical; không trình bày thành dữ liệu cá nhân hoặc quy định thực tế đã xác minh.

## Closeout references

- Authorization: yêu cầu Phase A closeout cho phép commit, push và mở PR nhắm `dev`; không merge/deploy.
- Branch: `codex/dell-external-judge-acceptance`.
- Commit/PR: sẽ bổ sung sau khi tạo; commit chứa cập nhật reference được xác định qua lịch sử Git của file.

Ma trận AC1–AC7 ghi trạng thái kiểm tra và bằng chứng; hoàn tất ghi nhận Phase A không đồng nghĩa sản phẩm đạt acceptance. Kết luận sản phẩm vẫn là **PARTIAL**.
