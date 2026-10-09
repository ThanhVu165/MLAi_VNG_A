# Exodia — Bàn giao đội Sprint 2

Tài liệu này cung cấp bối cảnh chung cho bốn thành viên. Trạng thái công việc và
phân công nằm trên Trello; mã nguồn và evidence nằm trên GitHub. Quy trình phối hợp
chi tiết xem [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md).

## Mục tiêu sản phẩm và Sprint 2

Exodia (Escalation Referee) hỗ trợ văn phòng Công tác Sinh viên xử lý email về
điểm rèn luyện, rút học phần và phúc khảo điểm. Hệ thống tự trả lời câu hỏi thường
quy khi có căn cứ an toàn và chuyển cho con người khi yêu cầu vượt thẩm quyền,
ngoài chính sách hoặc thiếu dữ kiện quyết định.

Mục tiêu Sprint 2 đến **15/10/2026** là hoàn thiện kiểm soát con người, evaluation
độc lập, nghiên cứu tác động lên người xử lý, khả năng tái lập/deploy và bộ hồ sơ
nộp. Feature freeze mục tiêu là **13/10/2026**.

## Kiến trúc và luồng vận hành

```text
Streamlit/local input
  → SQLite lưu email, job, kết quả và audit
  → pipeline R0–R14
  → OpenAI qua infra.llm.call_json() để trích xuất/chọn căn cứ/diễn đạt
  → mã deterministic kiểm input, evidence, policy và groundedness
  → AUTO_REPLY/P05, ESCALATE/P01–P03 hoặc technical fail-safe/P04
  → hàng chờ con người, duyệt và gửi mô phỏng
```

Các contract và ranh giới module nằm trong [PROJECT_SPEC.md](../PROJECT_SPEC.md).
Runtime hiện tại **chỉ hỗ trợ OpenAI**; provider khác bị từ chối và không có
automatic fallback. LLM không tự quyết định `AUTO_REPLY` hay `ESCALATE`.

Các khả năng đã có trong code gồm tiếp nhận email, xử lý nền, quản lý nguồn quy
định, citation/evidence checks, policy routing, thẻ escalation, human decision,
approval, audit và Verify harness. M3 sẽ kiểm chứng end-to-end các kiểm soát con
người; việc có code không tự động được xem là evidence đã đạt gate.

## Trạng thái đã xác minh

### M1 — CLOSED

M1 đóng với final full15 **0/15 technical errors**, **14/15 semantic labels**;
verify4 đạt 4/4 và escalation5 đạt 4/5 trong 44,48 giây. Nguồn:
[M1 runtime report](../reports/sprints/M1_runtime_reliability.md) và
[immutable M1 evidence](../reports/evidence/m1/README.md).

### M2 — M2_CONDITIONAL_CLOSEOUT

M2 có positive evidence cho P01, P02, P03 và P05, nhưng không phải chứng nhận toàn
bộ semantic safety hoặc held-out accuracy. Chín LIVE observations chỉ bao phủ 6/12
frozen DEV cases; historical FAIL/TECHNICAL_FAILURE và các criterion
`REVIEW_REQUIRED` vẫn được giữ. Fallback handoff mới có regression offline nhưng
chưa được exercise LIVE; nhánh identifier-specific không được nâng thành
`VERIFIED_LIVE`. Không quảng bá hai giới hạn này thành evidence đã đạt.

Nguồn authoritative:
[M2 final closeout](../reports/sprints/M2_FINAL_CLOSEOUT_AND_M1_M2_CHECKIN_20261009.md).
M3 được Coordinator cho phép ở trạng thái **M3_AUTHORIZED_WITH_CARRYOVER**; quyền
này không đổi verdict M2 thành PASS và không xóa các giới hạn trên.

## Roadmap M3–M7

- **M3 — Human Control + Feedback Adaptation:** kiểm chứng pause/resume, approval,
  escalation queue, cancel, correction/undo, payload binding và audit; adaptation
  phải bounded, reversible và không nới hard safety rules.
- **M4 — Evaluation:** tách DEV/REGRESSION khỏi independent Set A và sealed Set B;
  preregister metrics, không tune theo held-out results.
- **M5 — Human Impact Study:** tối thiểu ba người dùng ngoài đội có consent, đo
  review time/quyết định và tạo ít nhất một thay đổi sản phẩm từ feedback.
- **M6 — Reproducibility & Deployment:** fresh clone, Docker, migration/seed,
  replay, live URL và concurrent-session smoke.
- **M7 — Freeze, final evaluation và submission:** khóa revision, chạy Set B một
  lần, hoàn thiện metrics, demo, slide, video, build log và defense kit.

Chi tiết gate và timeline: [SPRINT_ROADMAP.md](SPRINT_ROADMAP.md).

## Bắt đầu làm việc

Đọc theo thứ tự:

1. [README.md](../README.md) — cài đặt và chạy local.
2. [TEAM_WORKFLOW.md](TEAM_WORKFLOW.md) — nguồn phân công, Task Contract và review.
3. Task Contract được giao trên Trello.
4. [PROJECT_SPEC.md](../PROJECT_SPEC.md) — contract và kiến trúc liên quan task.
5. [RUNBOOK.md](RUNBOOK.md) — vận hành, test và dữ liệu.
6. [STATUS.md](../STATUS.md) và [SPRINT_ROADMAP.md](SPRINT_ROADMAP.md) — trạng thái
   milestone và gate hiện hành.

## Giới hạn cần công bố

- Streamlit hiện chạy local, chưa phải public deployment và chưa có xác thực tài khoản.
- Hộp thư ngoài chưa kết nối; thao tác gửi email chỉ được mô phỏng trong SQLite.
- Seed, frozen DEV cases và phần lớn evaluation data là synthetic.
- Offline tests không chứng minh provider LIVE đúng; LIVE/API chỉ chạy khi có ủy
  quyền cụ thể của Project Coordinator.
- Corpus hiện nhỏ; chưa có bằng chứng scale cho kho hàng nghìn văn bản hoặc tải lớn.
