# Exodia Sprint 2 — Internal Mini-Sprint Roadmap

Deadline: **15/10/2026** (Asia/Saigon, UTC+07:00).

## Overall Objective

Biến V1 thành một production-minded prototype:

- Runtime ổn định.
- Biết khi nào được hành động và khi nào phải dừng/escalate.
- Human control rõ.
- Audit/accountability.
- Evaluation không contamination.
- Đo human impact.
- Reproducible.
- Có production/scale readiness story.
- Final evidence đủ để submit VNG.

Project có **7 internal mini-sprints**, thực hiện theo thứ tự M1–M7.
Trạng thái hiện tại xem [STATUS.md](../STATUS.md); chi tiết M1 xem
[living report M1](../reports/sprints/M1_runtime_reliability.md).

## Global Workflow

Mỗi mini-sprint:

1. Đọc trạng thái repo + evidence sprint trước.
2. Phân tích sprint hiện tại.
3. Chia khoảng 3–7 micro-task theo dependency.
4. Chỉ thực hiện micro-task hiện tại.
5. Sau mỗi micro-task: thu evidence, coordinator review, cập nhật living sprint report.
6. Cuối sprint: tests, Code Review, Review Agent, Anti review, Sprint Gate Review.
7. Chỉ Gate PASS mới chuyển sprint tiếp.

Không được tự đánh dấu sprint PASS. Không được tự thay đổi sprint gate.
Micro-task tương lai có thể được điều chỉnh theo evidence; gate giữ nguyên.
Các micro-task dưới đây là kế hoạch, không phải ủy quyền tự chạy evaluation/provider
hoặc thực hiện toàn bộ sprint trong một task.

## Sprint Gate Enforcement Rules

### A. Micro-task validation

Sau mỗi micro-task:

1. Chạy validation đúng phạm vi task.
2. Thu evidence.
3. Không tự suy diễn DONE nếu validation chưa pass.
4. Coordinator/reviewer phải review evidence trước khi mở task tiếp theo.
5. Nếu task fail:
   - Không mở task kế tiếp.
   - Triage nguyên nhân.
   - Sửa hoặc diagnostic bổ sung.
   - Validate lại.

Implementation hoàn thành không đồng nghĩa micro-task DONE.

### B. Mini-sprint Gate

Mỗi mini-sprint phải kết thúc bằng Sprint Gate Review.

Sprint Gate Review phải gồm tối thiểu:

- Tests/evaluation phù hợp với sprint.
- Regression check.
- Code Review.
- Review Agent.
- Anti/independent review khi phù hợp.
- Evidence summary.
- Kết luận PASS / FAIL.

Chỉ PASS mới được chuyển sang mini-sprint tiếp theo.

### C. Gate FAIL behavior

Nếu Gate FAIL, **KHÔNG được chuyển sang sprint tiếp theo**.

Flow bắt buộc:

```text
Sprint Gate FAIL
→ Failure Triage
→ Root Cause Classification
→ Targeted Fix
→ Targeted Validation
→ Sprint Gate Rerun
```

Root cause classification tối thiểu:

- TECHNICAL.
- LOGIC.
- DATA / RETRIEVAL.
- TEST / HARNESS.
- ENVIRONMENT.
- UNKNOWN.

Không rerun mù chỉ để tìm PASS.

### D. Dynamic micro-task rule

Số micro-task của sprint **KHÔNG cố định**.

Ví dụ, M1 ban đầu có M1.1 → M1.6. Nếu M1.6 Gate FAIL, có thể sinh thêm:

- M1.7 Failure triage.
- M1.8 Reliability fix.
- M1.9 Targeted validation.
- M1.10 Gate rerun.

Tiếp tục cho tới khi:

- Gate PASS; hoặc
- Coordinator quyết định cần thay đổi roadmap/gate vì có evidence mới.

Agent không được tự tạo task mới ngoài scope mà không báo coordinator.

### E. Gate immutability rule

**KHÔNG được hạ hoặc thay đổi Gate chỉ vì hệ thống không đạt.**

Gate chỉ được thay đổi nếu:

- Requirement ban đầu sai.
- Metric không đo được.
- Metric mâu thuẫn với direct stakeholder requirement.
- Evidence mới chứng minh gate không còn hợp lệ.

Bất kỳ thay đổi gate nào đều cần:

- Evidence.
- Explicit coordinator approval.
- Update roadmap.
- Ghi lý do trong sprint report.

### F. Regression protection

Mỗi sprint PASS phải tạo một last-known-good checkpoint:

- Commit hoặc tag xác định rõ.
- Sprint report final.
- Gate evidence lưu lại.

Sprint sau phải kiểm tra không phá gate sprint trước khi cần.

Nếu regression làm sprint trước FAIL lại:

- STOP.
- Triage regression.
- Fix hoặc rollback.
- Chỉ tiếp tục khi previous gate được khôi phục.

### G. Sprint final output format

Cuối mỗi mini-sprint phải báo:

```text
Sprint: Mx
Gate: PASS / FAIL
Evidence:
Regression còn lại:
Technical debt:
Có được sang Mx+1 không: YES / NO
```

Nếu NO, ghi next remediation step.

### H. Authority

Agent không được tự đánh dấu sprint PASS.

PASS/FAIL cuối sprint chỉ được xác nhận sau:

- Evidence hoàn tất.
- Review hoàn tất.
- Coordinator chấp nhận.

## M1 — Runtime & LLM Reliability

### Objective

Làm pipeline ổn định về mặt kỹ thuật trước khi đánh giá decision correctness.

### Exit Gate

**TECHNICAL_FAILURE <= 1/15 trên full15 LIVE.**

### Scope

- LLM/runtime paths.
- Provider observability.
- Retry/budget.
- Quota/throttling.
- Provider errors.
- Runtime reliability.

### Out of Scope

Không tuning P01/P02/P03 correctness trong M1.

### Current Planned Micro-tasks

| Micro-task | Nội dung | Trạng thái hiện tại |
|---|---|---|
| M1.1 | Runtime evidence + LLM call map | DONE |
| M1.2 | Provider observability | NEXT |
| M1.3 | Offline verification + Code Review | NOT STARTED |
| M1.4 | Targeted LIVE diagnosis | NOT STARTED |
| M1.5 | Evidence-driven reliability fix | NOT STARTED |
| M1.6 | Full15 Gate + Sprint Review | NOT STARTED |

M1.5 không được định nghĩa cứng trước. Nội dung fix phải dựa trên evidence từ M1.4.
M1.6 gồm chuỗi review cuối sprint trong Global Workflow.
M1 chưa PASS; gate sau reliability fix chưa được đánh giá.

## M2 — Core Decision Correctness

### Objective

Xác minh đúng AUTO_REPLY / ESCALATE và đúng rule/lý do.

### Entry

**M1 PASS.**

### Exit Gate

Phải có evidence đúng cho:

- AUTHORITY_REQUIRED / P01.
- OUT_OF_POLICY / P02.
- FACT_UNRESOLVED / P03.
- AUTO_REPLY / P05.

P04/TECHNICAL failure không được tính thay P03.

### Scope

- Extraction correctness.
- Retrieval/evidence correctness.
- Deterministic policy behavior.
- Routing.
- Groundedness/error analysis.

## M3 — Human Control & Safety

### Objective

Đảm bảo AI không hành động vượt quyền và human có thể kiểm soát.

### Entry

**M2 PASS.**

### Exit Gate

E2E evidence cho:

- Pause/resume.
- Human approval.
- Escalation queue.
- Cancel before send.
- Correction/undo.
- Payload-bound approval.
- Audit trail.

## M4 — Evaluation & Locked Held-out

### Objective

Xây evaluation protocol không contamination.

### Exit Gate

- DEV/REGRESSION tách HELD-OUT.
- Held-out mới được khóa.
- Predefined gold labels.
- Harness reproducible.
- Metrics predefined.
- Wilson CI cho proportion metrics.
- Held-out chưa dùng để tuning.

Các set đã dùng để tune/test trước đó phải coi là DEV/REGRESSION,
bao gồm full15 đã dùng trong các lượt hiện tại.

## M5 — Human Impact Study

### Objective

Đo tác động thật lên human reviewer.

### Exit Gate

Exploratory evidence gồm:

- Review time.
- Final human decision.
- Acceptance/rejection planted-wrong AI recommendation.
- Raw n/N.
- Qualitative notes.
- Participants ngoài team.
- Consented participants.

Không claim automation-bias prevalence từ sample nhỏ.

## M6 — Reproducibility & Production Readiness

### Objective

Chứng minh project không chỉ chạy trên máy dev hiện tại.

### Exit Gate

- Fresh clone setup thành công.
- Python 3.11 reproducible.
- Docker image chạy.
- Migration/seed reproducible.
- Cassette record/replay trong exact Docker image.
- Replay cassette miss = 0.
- Basic concurrency/stress evidence.
- Production-scale architecture/migration story.

Không migrate thật Kafka/Postgres nếu chưa có evidence cần thiết.

## M7 — Freeze, Final Evaluation & Submission

### Objective

Khóa hệ thống và tạo final evidence.

### Target Timeline

| Mốc | Thời gian mục tiêu (2026, UTC+07:00) |
|---|---|
| Hard freeze | Tối 09/10 |
| Final held-out LIVE | Khoảng 10/10 |
| Reproduce/evidence/report | 11–13/10 |
| Package | 14/10 |
| Submit | 15/10 |

Đây là target timeline; không thay thế các sprint gate.

### Exit Gate

- Frozen revision/tag.
- Final held-out run.
- Protocol được tuân thủ.
- Reproducibility evidence.
- Final metrics/report.
- Demo/package.
- Repo clean.
- Submission ready.

Sau freeze không tuning dựa trên held-out.

## Agent Context Protocol

Mọi Codex/Anti task sau phải:

1. Đọc `docs/SPRINT_ROADMAP.md`.
2. Đọc `STATUS.md`.
3. Đọc living report của sprint hiện tại.
4. Chỉ đọc raw evidence report khi cần kiểm chứng claim.

Mọi agent trước khi làm task phải kiểm tra:

- Current sprint.
- Current micro-task.
- Current gate.
- Previous sprint gate status.
- Current task có được phép theo Sprint Gate Enforcement Rules hay không.

Repo files là source of truth cho project state.

Agent không được:

- Tự đổi roadmap.
- Tự đổi sprint gate.
- Tự đánh dấu sprint PASS.
- Dựa vào memory của chat/session cũ khi repo state có sẵn.

Nếu current sprint Gate = FAIL, agent không được tự nhảy sang sprint kế tiếp.
Nếu evidence mới làm previous sprint gate không còn đúng: **STOP và báo coordinator**.
Nếu evidence mới mâu thuẫn roadmap/status: **STOP và báo coordinator**.
