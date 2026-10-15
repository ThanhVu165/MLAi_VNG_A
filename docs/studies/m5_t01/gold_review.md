# Gold review và lưu trữ có kiểm soát

**PENDING INDEPENDENT REVIEW** cho toàn bộ tám case. File này không chứa Gold.
Repository PUBLIC theo `gh repo view ThanhVu165/MLAi_VNG_A --json visibility,isPrivate`
ngày 11/10/2026; do đó không tạo/commit `gold_labels.md` hoặc đáp án đầy đủ.

## Quyết định truy cập hiện hành

Coordinator đã hủy phương án bàn giao Gold qua Google Drive và cho phép review
tại chỗ trong môi trường local được duyệt. Chỉ phiên Codex hỗ trợ independent
reviewer, dưới sự giám sát trực tiếp của reviewer, được đọc Gold ở chế độ
read-only. Không upload, di chuyển hoặc chia sẻ Gold qua mạng; không công khai
vị trí private, Gold labels, rationale hoặc source locator theo case.

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
nghĩa independent reviewer đã ký hoặc Coordinator đã nghiệm thu Gold.

## Correction workflow CR-01

Bản dự thảo 8 case có email/corpus hash, rationale, rule priority và locator;
không upload, commit hoặc đăng nội dung matrix vào PR/Trello. Technical semantic
review được báo cáo **8/8 PASS** trong phiên local được duyệt. Independent reviewer
sign-off và Coordinator acceptance vẫn **PENDING**; kết quả Codex báo cáo không
thay chữ ký reviewer.

Trạng thái lịch sử **PENDING COORDINATOR DECISION** về kênh truy cập đã được giải
quyết bằng quyết định local supervised review; cụm này không còn là blocker.

Checklist review local: xác nhận đúng reviewer, giám sát trực tiếp, môi trường
được duyệt và read-only; không mở rộng quyền sang thư mục khác. Xác minh
reviewer được phép đọc được artifact và phiên không mở rộng sang người hoặc thư
mục khác; lưu access proof không chứa Gold trong handoff phù hợp. Không tự tạo kho,
gửi invitation hoặc chia sẻ artifact. Nếu chưa kiểm chứng được bất kỳ mục nào,
giữ matrix cục bộ và không chia sẻ.
