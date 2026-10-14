# M5-T02 — Recruitment tracker

**Actual count:** `0 confirmed / PENDING recruitment`.

Các dòng P01–P04 là slot bằng code, không phải người tham gia giả hoặc bằng chứng đã
tuyển. File này không chứa tên, contact, employer cụ thể, raw consent, private role
evidence hoặc exposure evidence chi tiết.

| Code | Recruitment | Eligibility/role evidence | Exposure screening | Schedule | Consent | Counted in confirmed n |
|---|---|---|---|---|---|---|
| P01 | PENDING | NOT RUN | NOT RUN | PENDING | NOT RUN | NO |
| P02 | PENDING | NOT RUN | NOT RUN | PENDING | NOT RUN | NO |
| P03 | PENDING | NOT RUN | NOT RUN | PENDING | NOT RUN | NO |
| P04 | PENDING | NOT RUN | NOT RUN | PENDING | NOT RUN | NO |

## Điều kiện được tính là confirmed

Một code chỉ được tính khi tất cả điều kiện sau có evidence riêng ngoài Git:

1. Người thật, ngoài team, đủ 18 tuổi và đang trực tiếp xử lý email/hồ sơ sinh viên
   hoặc workflow hành chính tương ứng.
2. Identity/role evidence tối thiểu theo loại và cách xác minh đã được Coordinator duyệt.
3. Chưa thấy case/Gold; nếu đã thấy hoặc không chắc, giữ `PENDING` và chuyển
   Coordinator phân xử trước allocation.
4. Lịch được người đó xác nhận; invitation do người được giao gửi, không phải AI.
5. Đã nhận đúng consent/storage version và tự nguyện đồng ý tham gia.

Tự khai vai trò, code P01–P04 hoặc một slot lịch trống không làm tăng participant count.
Nếu còn dưới 3 confirmed thì AC1 giữ `FAIL`; không thay bằng participant hoặc dữ liệu giả.

## Quy trình cập nhật an toàn

- Public tracker chỉ đổi trạng thái tổng hợp và code.
- Project Coordinator là custodian. Private Google Drive dùng `General access = Restricted`;
  `01_consent_contact`, `02_eligibility_exposure` và `03_raw_study_results` tách nhau.
- Raw identifiable data mặc định chỉ Project Coordinator được truy cập; thành viên khác
  chỉ nhận dữ liệu de-identified khi thực sự cần.
- Private log giữ verifier, ngày, phương thức, evidence reference, exposure verdict,
  consent version và quyền chia sẻ; không sao chép nội dung private vào Git/Trello.
- Allocation S1–S4 chỉ thực hiện sau khi eligibility, exposure, consent, storage và
  GO-STUDY đều được xác nhận.
- Mọi yêu cầu rút/xóa đi qua custodian đã duyệt; không khôi phục dữ liệu để tăng n.
- Raw identifiable data được giữ tối đa 90 ngày sau khi Coordinator đóng study;
  deletion log chỉ giữ participant code, ngày xóa, status và người thực hiện.

## Trạng thái screening

- Cơ chế exposure/eligibility screening: `PASS` cho readiness của quy trình.
- Screening participant thực tế: `NOT RUN — 0 participants confirmed`.
- AC3 chính thức: `NOT RUN / BLOCKED`; readiness của cơ chế không đồng nghĩa
  participant screening đã hoàn tất.
- Invitation/email thật: `NOT RUN`.
