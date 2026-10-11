# M5-T01 — Đánh giá X/Y equivalence sau CHANGE REQUEST (Owner)

**Status:** Owner assessment, PENDING independent review. Không có pilot, không có kết quả participant. Chỉ dùng năm nguồn ACTIVE ở cả B0/B2; nguồn SUPERSEDED chỉ phục vụ reviewer hậu kiểm.

| Case | Domain | Route/rule Owner đề xuất | Requests | Căn cứ ACTIVE cần kiểm tra | Bẫy/thông tin cần xử lý | Độ khó dự kiến |
|---|---|---|---:|---|---|---|
| X1 | conduct_score | AUTO_REPLY/P05 | 2 | RL-2026-3150 Điều 3–4 | Điểm giả định 85, không xác nhận hồ sơ cá nhân | Thấp–trung bình |
| X2 | grade_appeal | ESCALATE/P01 | 2 | PK-2026-204 Điều 3; QDPQ-2026-01 Điều 3 | Xin chấp thuận phúc khảo quá hạn; authority | Trung bình |
| X3 **đã sửa** | course_withdrawal | ESCALATE/P02 | 2 | RH-2026-101 Điều 3; HP-2026-1 Điều 3 | K50, HK1 2026–2027; yêu cầu quy định chung; xung đột ACTIVE 70/60 | Cao |
| X4 | conduct_score | ESCALATE/P03 | 1 | RL-2026-3150 mở đầu + Điều 2 | K49, đã bảo lưu/quay lại, thiếu thời điểm | Trung bình |
| Y1 | grade_appeal | AUTO_REPLY/P05 | 2 | PK-2026-204 Điều 1–2 | Phí và mẫu, không duyệt hồ sơ | Thấp |
| Y2 | course_withdrawal | ESCALATE/P01 | 2 | RH-2026-101 Điều 4; QDPQ-2026-01 Điều 2 | Ngoại lệ quá hạn; authority | Trung bình |
| Y3 | conduct_score | ESCALATE/P02 | 2 | RL-2026-3150 Điều 3; kiểm trạng thái RL-2025-2363 | ACTIVE không có ngưỡng Khá; không dùng SUPERSEDED làm luật | Cao |
| Y4 | grade_appeal | ESCALATE/P03 | 1 | PK-2026-204 mở đầu + Điều 2 | Thiếu ngày/thông báo công bố MA101 | Trung bình |

**Đếm cấu trúc:** X=4 case, Y=4; mỗi bộ 7 yêu cầu, 3 case đa ý định, 1 P01 / 1 P02 / 1 P03 / 1 P05. Mỗi bộ 1 AUTO_REPLY + 3 ESCALATE. X domain: 2 conduct/1 grade/1 withdrawal; Y: 1 conduct/2 grade/1 withdrawal. Loại thao tác nguồn **không đồng nhất**: X3 hai nguồn ACTIVE xung đột; Y3 kiểm ACTIVE thiếu ngưỡng và loại trừ bản SUPERSEDED; X4/y4 khác domain và điều kiện cần để áp dụng.

**Giới hạn:** Cùng số case, nhãn và nguồn tra cứu không chứng minh độ khó bằng nhau. X1 đọc hai điều, Y1 đọc hai điều; X3 cần so hai nguồn, Y3 cần phát hiện thiếu nguồn chính thức; burden/latency có thể lệch. Không gán điểm độ khó định lượng khi chưa có reviewer/pilot. Mẫu n=3 không cân bằng hoàn hảo giữa bốn sequence; giữ phân bổ trước nghiên cứu, báo số lượng/route/time theo set × condition × sequence và n/N. Không tuyên bố causal superiority hoặc significance. Nếu reviewer thấy X3 vẫn còn yêu cầu phê duyệt quyền lợi cá nhân, giữ GOLD_REVIEW_REQUIRED và sửa wording với Coordinator trước khi khóa Gold, không sửa nhãn để ép cân bằng.

**Kiểm soát contamination:** case public có thể lộ qua GitHub; hỏi exposure khi tuyển. Gold Owner-side từ Trello phải chuyển vào kho restricted do Coordinator duyệt; không để participant thấy ma trận Gold hoặc các chú giải review này. Bản X3 cũ trên Trello là lịch sử; khi review dùng bản X3 đã sửa ở participant pack branch này.

**Reviewer checklist:** xác minh mới X3 đúng P02 theo priority P01>P02>P03>P04>P05; xem nguồn/căn cứ từng case, so difficulty từng pair trên corpus ACTIVE-only, ghi PASS/CHANGE REQUEST/GOLD_REVIEW_REQUIRED, không suy diễn Gold từ output AI.