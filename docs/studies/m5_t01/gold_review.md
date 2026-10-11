# Gold review và lưu trữ có kiểm soát

**PENDING INDEPENDENT REVIEW** cho toàn bộ tám case. File này không chứa Gold.
Repository PUBLIC theo `gh repo view ThanhVu165/MLAi_VNG_A --json visibility,isPrivate`
ngày 11/10/2026; do đó không tạo/commit `gold_labels.md` hoặc đáp án đầy đủ.

## Phương án Coordinator cần quyết định

Đề xuất lưu bảng Gold trong thư mục Drive hoặc repository PRIVATE chỉ có Owner,
Minh và Coordinator. Chưa tạo kho hoặc xác nhận access control. Trước khi copy từ
Trello, Coordinator xác minh quyền card/board hiện tại, tắt public-link access ở
kho đích, kiểm thử tài khoản không được phép và ghi log quyền. Không xem Trello
là restricted khi chưa có bằng chứng. Không đưa URL chia sẻ có token vào public Git.

Coordinator ghi trong kho riêng: storage ID/location, custodian, access list,
version, hash, ngày khóa, retention/deletion date và reviewer verdict.
Không lưu Gold trong participant pack, UI, Study export cho participant hay PR này.

## Quy trình độc lập

1. Owner chuyển nguyên Gold Owner-side đã chốt trong FINAL OWNER SELF-REVIEW trên
   card vào bảng riêng; bảo toàn tám email hiện hành, gồm X4 có K49. Không thay
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

Owner đã sửa wording X3 trong `cases_xy.md` để nói rõ học kỳ, khóa và câu hỏi quy định chung, không xin duyệt hoàn tiền cá nhân. Independent reviewer phải đối chiếu ưu tiên P01 (authority) trước P02 (nguồn mâu thuẫn) trước P03 (thiếu fact) trong `policies/policy.yaml`; không được mặc định xung đột nguồn luôn thắng yêu cầu phê duyệt. Bảng Gold 8 case và rationale/locator chỉ được bàn giao qua kho restricted được Coordinator duyệt; mapping/đáp án không đưa vào public Git. **Kho Gold và quyền truy cập chưa được thiết lập/xác minh; CR-01 chưa PASS.**
