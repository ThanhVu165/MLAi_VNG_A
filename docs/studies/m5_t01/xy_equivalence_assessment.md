# M5-T01 — X/Y equivalence assessment

**Status:** Structural comparison checked. Local supervised Gold review đã được
Coordinator cho phép; technical review được báo cáo hoàn tất, independent reviewer
sign-off PENDING. Không có pilot hoặc participant results. Không tuyên bố equivalence.

## So sánh public không chứa lời giải

| Tiêu chí | X | Y | Ý nghĩa |
|---|---|---|---|
| Email | 4 | 4 | Cùng số tác vụ |
| Yêu cầu theo email 1→4 | 2 / 2 / 2 / 1 | 2 / 2 / 2 / 1 | 7 yêu cầu, 3 email đa ý định mỗi bộ |
| conduct_score | 2 | 1 | Lệch domain |
| grade_appeal | 1 | 2 | Lệch domain |
| course_withdrawal | 1 | 1 | Cùng số email, không suy ra cùng độ khó |
| Nguồn được phép tra cứu | Cùng 5 ACTIVE | Cùng 5 ACTIVE | Cùng toàn văn/metadata, không gợi ý đoạn theo case |
| Email lặp giữa B0/B2 trong một session | 0 | 0 | Giảm học thuộc, không tạo cặp cùng email |

Số request đếm mục tiêu trả lời/ra quyết định trong email; thông tin bối cảnh
không tính thành request. Cùng số lượng không chứng minh cùng burden tìm nguồn,
đọc hiểu, quyết định hoặc thời gian. Không báo số nguồn *cần* đọc như số tài liệu
đã đọc thực tế; chỉ số thực tế phải ghi nhận trong session.

## Assessment chi tiết — chỉ lưu ngoài public Git

Owner chuẩn bị bảng 8 case gồm domain, decision type, rule/priority, số và locator
nguồn cần đọc, thông tin thiếu, xung đột, rationale và độ phức tạp dự kiến.
Các trường này có thể suy ra đáp án nên không công bố kể cả dưới nhãn RESTRICTED.
Bảng dự thảo lưu cục bộ ngoài repository và không được upload. Coordinator đã
duyệt review tại chỗ, read-only, dưới giám sát trực tiếp của reviewer. Technical
review báo cáo route/rule distribution cân bằng giữa hai bộ, nhưng domain
distribution và source-reading burden vẫn khác nhau. Technical review đã đánh giá
bốn cặp vị trí và toàn bộ hai set; independent sign-off vẫn **PENDING**. Không dùng
output B2 để xác lập Gold hoặc chỉnh bộ cho cân bằng.

## Giới hạn và cách báo cáo

- Chênh lệch domain và thao tác đọc/đối chiếu nguồn có thể gây lệch độ khó.
  Nhận định độ khó là giả thuyết Owner, chưa phải pilot hoặc reviewer verdict.
- Giữ nguyên S1–S4 và quy tắc phân bổ trong [protocol](study_protocol.md),
  không thay allocation theo kết quả. Với n=3 không cân bằng đủ bốn sequence.
- Báo completion, time, final human decision, AI action và raw n/N theo
  set × condition × sequence; giữ missing/interruption/exclusion và paired n.
  Không gọi chênh lệch B0/B2 là tác động nhân quả hoặc có ý nghĩa thống kê.
- Nếu không chứng minh được equivalence, vẫn nêu giới hạn và phân tầng như trên;
  Coordinator quyết định protocol có đủ cơ sở GO, không tự gán equivalence PASS.
- Screening exposure bắt buộc: case và các chú giải đã từng public có thể đã
  được đọc. Xóa chú giải ở HEAD không xóa lịch sử Git. Không rewrite history;
  người đã thấy hoặc không chắc exposure cần Coordinator phân xử trước allocation.

**CR-02:** **PASS — exploratory study design only** theo technical review được báo
cáo. Kết quả không chứng minh difficulty equivalence, statistical significance
hoặc causal effect. Independent reviewer sign-off vẫn PENDING.
