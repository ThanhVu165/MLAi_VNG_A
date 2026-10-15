# M5-T01 — Chuẩn bị nghiên cứu B0/B2

**Đối soát bằng chứng cuối — 15/10/2026:** M5-T01 giữ trạng thái lịch sử
**DONE**. Human independent review Gold đã **VERIFIED** với kết quả tổng hợp
`PASS_8_OF_8`, và Project Coordinator **ACCEPT** quyết định Gold cuối này. Việc
đối soát chỉ đóng khoảng trống bằng chứng Gold sign-off; không cấp `GO-STUDY` và
không đáp ứng thay các entry condition độc lập của M5-T02/M5-T03. Xem
[báo cáo đối soát public-safe](../../../reports/studies/M5_T01_GOLD_SIGNOFF_RECONCILIATION.md).

Trạng thái correction bên dưới được giữ làm trạng thái lịch sử đã ghi trước lần
đối soát cuối; nội dung đó đúng tại thời điểm được lập.

**Owner correction v1.2 — CHANGE REQUEST đang xử lý.** Independent re-review: **PENDING**.
Đây là sản phẩm chuẩn bị; chưa chạy session, chưa tuyển/consent người thật,
chưa nghiệm thu M5-T01 hoặc M5. Next Task Unlocked: **NONE**.

## Mục tiêu và nguồn

So sánh cách xử lý email hành chính thủ công (B0) và có Exodia hỗ trợ (B2),
theo thiết kế crossover trên cùng corpus và thước đo. Chỉ dùng synthetic data.

- [Task Contract và bàn giao Trello](https://trello.com/c/nSzHYb2a), gồm ba comment
  chuẩn bị và FINAL OWNER SELF-REVIEW ngày 11/10/2026.
- [Technical contract](../../../PROJECT_SPEC.md), đặc biệt §5.3–5.5 và §7.
- [Policy](../../../policies/policy.yaml),
  [workflow](../../TEAM_WORKFLOW.md), [M5 Exit Gate](../../SPRINT_ROADMAP.md),
  [milestone status](../../../STATUS.md), [AGENT](../../../AGENT.md).

Baseline correction xác minh lại ngày 11/10/2026: `origin/dev@16f584fa213416db30b247a431b92fffb94be075`.
Baseline chuẩn bị lịch sử: `282c73b7dbf4ac7bf027d5710cce6ed673ab80d1`.
Phiên bản tài liệu là Git commit chứa thư mục này. Corpus là đúng byte của sáu
JSON tại [data/seed_docs](../../../data/seed_docs/) trong baseline; manifest SHA-256
nằm trong [handoff](owner_handoff.md). Đây chưa phải corpus_version của Study DB;
trước session phải ghi cả version/hash thực tế và revision sản phẩm được duyệt.

## Artifact và cách dùng

| File | Người dùng và mục đích |
|---|---|
| [study_protocol.md](study_protocol.md) | Moderator: phân sequence, nguồn, timer, lỗi và unlock |
| [cases_xy.md](cases_xy.md) | Participant: chỉ email synthetic và domain |
| [gold_review.md](gold_review.md) | Coordinator/reviewer: quy trình review và lưu Gold có kiểm soát |
| [recruitment_consent.md](recruitment_consent.md) | Tuyển chọn, giới thiệu, consent và bảo vệ dữ liệu |
| [measurement_forms.md](measurement_forms.md) | Form trống, metrics, aggregation và trace cải tiến |
| [owner_handoff.md](owner_handoff.md) | Evidence AC1–AC6, validation và blocker |
| [xy_equivalence_assessment.md](xy_equivalence_assessment.md) | Đánh giá X/Y theo tiêu chí độ khó, không công bố Gold |
| [validation_report.md](validation_report.md) | Validation offline và lệnh tái lập cho reviewer |

Repository được xác minh **PUBLIC**. HEAD hiện hành không chứa `gold_labels.md`, bảng đáp án hoặc
chú giải lời giải theo case ngoài nội dung email synthetic. Lịch sử PR từng có
chú giải; xóa ở HEAD không xóa exposure trong lịch sử. Tách file trong public repo không bảo vệ Gold.
Coordinator đã phê duyệt review Gold tại chỗ, read-only và có giám sát trực tiếp.
Không bàn giao Gold qua Google Drive hoặc công khai nội dung. Technical semantic review
8/8 PASS theo báo cáo; independent reviewer sign-off và Coordinator acceptance vẫn PENDING.
Không sao chép nguyên comment có đáp án lên Git.

Participant chỉ nhận email thuộc condition hiện tại, corpus ACTIVE được đóng gói
và script hướng dẫn trung tính trong protocol; không phát toàn bộ thư mục GitHub,
Trello, Gold hoặc biểu mẫu chấm hậu kiểm. Các case công khai có nguy cơ được xem
trước: tuyển người chưa tiếp xúc và hỏi lại trước session; nếu đã thấy case/Gold,
dừng phân bổ và báo Coordinator, không tự thay case hoặc giữ trong phân tích chính.

Owner đã hoàn thiện nội dung và kiểm tra tài liệu. Minh cần review độc lập rồi
gửi PASS/CHANGE REQUEST; Coordinator quyết định acceptance/merge và điều kiện GO.
Gold local review đã được Coordinator phê duyệt; technical 8/8 PASS theo báo cáo,
independent reviewer sign-off vẫn PENDING. Participant evidence storage chưa được
Coordinator phê duyệt trước recruitment. Runtime/isolation M3-T03, revision sản phẩm,
consent/lịch >=3 người, retention/access và các study prerequisites chưa được nghiệm thu.
Xem checklist trong protocol.

Tám case là draft mới được chuẩn bị trên Trello khi **CHƯA TÌM THẤY BẢN GỐC**;
không gọi là tám case lịch sử hoặc N01–N08 robustness. Không mở/sử dụng Set A/Set B.

## Review correction sau PR #30

Correction docs-only trên PR #32, baseline `dev@16f584fa`; không chỉnh policy/seed.
Chú giải lời giải, locator và độ khó theo case đã đưa ra khỏi tài liệu public.
Public equivalence chỉ giữ cấu trúc, phương pháp và giới hạn; assessment chi tiết
đi cùng Gold matrix cục bộ ngoài Git, không upload. Coordinator đã cho phép local
supervised read-only review và hủy phương án Drive cho Gold. Technical review được
báo cáo 8/8 PASS; independent reviewer sign-off và Coordinator acceptance vẫn
PENDING. Consent tách các lựa chọn chia sẻ và có checklist role verification/storage.
Coordinator đã ghi nhận workflow deviation của PR #30; không coi merge là
acceptance, không revert/rewrite. Không thực hiện study hoặc công bố Gold.
