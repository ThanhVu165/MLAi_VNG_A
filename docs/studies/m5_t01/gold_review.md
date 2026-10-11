# Gold review và lưu trữ có kiểm soát

**PENDING INDEPENDENT REVIEW** cho toàn bộ tám case. File này không chứa Gold.
Repository PUBLIC theo `gh repo view ThanhVu165/MLAi_VNG_A --json visibility,isPrivate`
ngày 11/10/2026; do đó không tạo/commit `gold_labels.md` hoặc đáp án đầy đủ.

## Phương án Coordinator cần quyết định

Đề xuất Google Drive PRIVATE với General access = Restricted, chỉ cấp đích danh
Owner, Minh và Coordinator. Chưa tạo thư mục, upload hoặc xác nhận access control. Trước khi copy từ
Trello, Coordinator xác minh quyền card/board hiện tại, tắt public-link access ở
kho đích, kiểm thử tài khoản không được phép và ghi log quyền. Không xem Trello
là restricted khi chưa có bằng chứng. Không đưa URL chia sẻ có token vào public Git.

Coordinator ghi trong kho riêng: storage ID/location, custodian, access list,
version, hash, ngày khóa, retention/deletion date và reviewer verdict.
Không lưu Gold trong participant pack, UI, Study export cho participant hay PR này.

## Quy trình độc lập

1. Owner chuẩn bị Gold matrix dự thảo cho tám email tại correction HEAD, lưu
   cục bộ ngoài repository. Đối chiếu Owner-side lịch sử, không mặc định đã chốt
   hoặc đã ký; mọi khác biệt phiên bản phải có rationale/reviewer verdict. Không thay
   Gold theo output AI hoặc để đáp án được sinh từ kết quả chạy hệ thống.
2. Minh đọc [spec](../../../PROJECT_SPEC.md) §5.3–5.5,
   [policy](../../../policies/policy.yaml) và cả sáu văn bản seed ở baseline.
   Reviewer đọc ACTIVE cùng metadata ngày/phạm vi; đọc SUPERSEDED chỉ để kiểm
   tra loại trừ, không coi là căn cứ hiện hành.
3. Với mỗi case, review intent, dữ kiện đủ/thiếu, nguồn có thẩm quyền, ưu tiên rule,
   quyết định cần người, căn cứ Điều/Khoản/Điểm và kết luận cấm suy diễn.
   Phân biệt nguồn thiếu/mâu thuẫn với user fact thiếu; không dựa vào tên case.
4. Đối chiếu từng email với bản Trello, đặc biệt các điểm Owner đã đánh dấu trong
   FINAL OWNER SELF-REVIEW. Đánh giá cân bằng X/Y trên nguồn được phép thật sự
   dùng ở cả B0/B2; không giữ giả định B0 phải lọc nguồn cũ khi B2 chỉ thấy ACTIVE.
5. Ghi PASS hoặc CHANGE REQUEST có lý do từng case. Nếu chưa đủ căn cứ dùng
   `GOLD_REVIEW_REQUIRED`; không tự thông qua hoặc đổi technical contract.
6. Owner xử lý yêu cầu trong scope, Minh xác nhận lại; Coordinator phê duyệt
   phiên bản Gold/email/corpus trước session. Lưu reviewer/date/hash/approval.
   Mọi thay đổi sau khóa cần revision và impact review, không sửa hồi tố kết quả.

## Schema bảng riêng (trống)

| Case ID | Email version/hash | Gold decision | Gold rule | Corpus ID + locator + hash | Rationale | Required facts | Forbidden inference | Owner status | Independent verdict/date | Coordinator approval |
|---|---|---|---|---|---|---|---|---|---|---|
| ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ | ____ | PENDING | PENDING |

Một dòng mỗi case; restricted reviewer material. Bảng balance có route/rule theo
case và phân tích độ khó có lời giải cũng lưu riêng, không đưa vào participant pack.
Chỉ khi Gold được xác nhận mới hậu kiểm metrics; nếu chưa xác nhận, ghi UNKNOWN,
không tính nhãn pending thành sai/đúng. Việc tạo tài liệu quy trình này không đồng
nghĩa kho Gold đã được lập hoặc quyền reviewer đã được cấp.

## Correction workflow CR-01

Bản dự thảo 8 case có email/corpus hash, rationale, rule priority và locator;
chưa phải Gold được Owner/reviewer/Coordinator ký. Không upload, commit hoặc
đăng nội dung matrix vào PR/Trello trước phê duyệt kho và kiểm chứng access.
**PENDING COORDINATOR DECISION**; CR-01 chưa PASS, chấm correctness chưa được mở.

Checklist trước upload: Coordinator xác nhận custodian, tài khoản Owner/Minh/
Coordinator, quyền từng người, retention/deletion; kiểm tra thư mục cha và quyền
kế thừa, General access Restricted, không domain-wide/anyone-link access. Xác minh
Owner và reviewer mở được, tài khoản không được cấp quyền bị từ chối; lưu access
proof không chứa Gold trong handoff phù hợp. Không tự tạo kho hoặc gửi invitation.
Nếu chưa kiểm chứng được bất kỳ mục nào, giữ matrix cục bộ và không chia sẻ.
