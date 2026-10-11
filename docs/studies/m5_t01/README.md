# M5-T01 — Chuẩn bị nghiên cứu B0/B2

**Owner draft v1 — READY_FOR_INDEPENDENT_REVIEW.** Independent review: **PENDING**.
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

Baseline đã fetch ngày 11/10/2026: `origin/dev@282c73b7dbf4ac7bf027d5710cce6ed673ab80d1`.
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

Repository được xác minh **PUBLIC**. Không có `gold_labels.md`, bảng đáp án hoặc
lời giải theo case trong PR. Tách file trong public repo không bảo vệ Gold.
Coordinator phải chọn kho có kiểm soát, kiểm tra cả quyền của card Trello đang
chứa Gold, rồi cấp quyền reviewer. Không sao chép nguyên comment có đáp án lên Git.

Participant chỉ nhận email thuộc condition hiện tại, corpus ACTIVE được đóng gói
và script hướng dẫn trung tính trong protocol; không phát toàn bộ thư mục GitHub,
Trello, Gold hoặc biểu mẫu chấm hậu kiểm. Các case công khai có nguy cơ được xem
trước: tuyển người chưa tiếp xúc và hỏi lại trước session; nếu đã thấy case/Gold,
dừng phân bổ và báo Coordinator, không tự thay case hoặc giữ trong phân tích chính.

Owner đã hoàn thiện nội dung và kiểm tra tài liệu. Minh cần review độc lập rồi
gửi PASS/CHANGE REQUEST; Coordinator quyết định acceptance/merge và điều kiện GO.
Các blocker study gồm Gold sign-off/storage, isolation M3-T03, revision/runtime,
consent/lịch >=3 người và retention/access. Xem checklist trong protocol.

Tám case là draft mới được chuẩn bị trên Trello khi **CHƯA TÌM THẤY BẢN GỐC**;
không gọi là tám case lịch sử hoặc N01–N08 robustness. Không mở/sử dụng Set A/Set B.
