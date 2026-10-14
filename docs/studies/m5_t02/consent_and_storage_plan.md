# M5-T02 — Consent và storage plan

**AC2 hiện tại:** `PASS candidate`. Project Coordinator đã phê duyệt storage/privacy
plan dưới đây. Consent participant thực tế vẫn `NOT RUN`; approval này không mở GO-STUDY.

## Consent boundary

Trước session, người được giao phải giải thích mục tiêu B0/B2, thời lượng 45–60 phút,
dữ liệu synthetic, dữ liệu được ghi, rủi ro/bất tiện, quyền bỏ câu hỏi/nghỉ/dừng,
quyền rút/xóa, retention và người có quyền truy cập. Không tick sẵn lựa chọn.

Các lựa chọn độc lập:

- tham gia tự nguyện;
- giữ hoặc xóa dữ liệu đã thu nếu dừng;
- dùng trích dẫn đã loại định danh;
- chia sẻ identity/role evidence tối thiểu với recipient được nêu;
- chia sẻ phản hồi định danh hoặc đã loại định danh.

Đồng ý một mục không cấp quyền cho mục khác. Thiếu/không rõ consent thì không bắt đầu.
Raw consent, signature, contact và identifiable feedback không được commit.

## Storage decision register — APPROVED

| Quyết định | Quyết định đã phê duyệt |
|---|---|
| Custodian và đầu mối nhận yêu cầu rút/xóa | Project Coordinator |
| Private storage | Google Drive PRIVATE; `General access = Restricted` |
| Consent/contact | Thư mục `01_consent_contact` |
| Eligibility/exposure evidence | Thư mục `02_eligibility_exposure` |
| Raw study results/identifying notes | Thư mục `03_raw_study_results` |
| Raw identifiable data access | Project Coordinator only by default |
| Thành viên khác | Chỉ nhận dữ liệu de-identified khi thực sự cần |
| Retention | Tối đa 90 ngày sau khi study được Project Coordinator đóng |
| Participant rút consent | Ngừng sử dụng và xóa identifiable/raw evidence trong phạm vi team kiểm soát |
| Hết retention | Xóa contact, consent, identity/role evidence, exposure evidence và raw identifying results/notes |
| Deletion log | Chỉ participant code, ngày xóa, status và người thực hiện; không PII |

Không lưu PII, raw consent, role evidence, exposure evidence hoặc raw identifying
notes trên GitHub/Trello. Quyết định này không áp dụng cho private Gold; Gold tiếp tục
theo boundary riêng.

## Public/private separation

| Public artifacts | Private, access-controlled |
|---|---|
| Participant code, aggregate metrics, de-identified results, sanitized feedback, template và synthetic protocol/cases | Name/contact, raw consent/signature, identity/role evidence, exposure evidence, raw identifying notes/results |

Public report chỉ dùng aggregate n/N đã review và quote vừa opt-in vừa loại định danh.
Không ghi âm/ghi hình. Nếu dữ liệu thật vô tình xuất hiện: dừng thu, không chụp/log/
commit, báo custodian và xử lý theo plan đã duyệt.

## Retention và deletion workflow

1. Custodian ghi ngày Coordinator đóng study và hạn xóa không quá 90 ngày sau đó.
2. Nếu participant rút consent, ngừng sử dụng rồi xóa identifiable/raw evidence thuộc
   phạm vi team kiểm soát, không chờ hết retention.
3. Khi hết retention, custodian xóa dữ liệu thuộc ba thư mục theo danh mục đã duyệt.
4. Chỉ giữ deletion log tối thiểu gồm participant code, ngày xóa, status và người
   thực hiện; log không chứa PII hoặc nội dung evidence.

## Điều kiện chuyển trạng thái

AC2 là `PASS candidate` cho plan đã phê duyệt. Trước recruitment, custodian vẫn phải
xác minh cấu hình thực tế đúng ba thư mục, `Restricted`, quyền mặc định chỉ Coordinator
và không có dữ liệu cũ ngoài boundary. Consent participant thực tế vẫn là `NOT RUN`
cho đến khi có người thật và GO-STUDY.
