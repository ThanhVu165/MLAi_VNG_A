# Exodia Sprint 2 — Internal Mini-Sprint Roadmap

Internal submission-ready target: **15/10/2026** (Asia/Saigon, UTC+07:00).
Buffer: 16/10; onsite/demo-day working day: 17/10.

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

## Core Chain, Parallel Prep & Timeline

Core dependency chain: **M1 → M2 → M3 → M4 → M5 → M6 → M7**.

Parallel prep có thể bắt đầu theo scope được giao:

- P1: Recruit/schedule >=3 real users.
- P2: Author/gold/hash evaluation sets.
- P3: Live deployment readiness.
- P4: Defense notes/build log.

Parallel prep không được giả định sprint trước PASS, tune core bằng future
evaluation results, hoặc implement future core logic trước dependency.

| Mốc | Thời gian mục tiêu (2026, UTC+07:00) |
|---|---|
| M1.5 | 05–06/10 |
| Close M1 Gate | 07/10 |
| M2 | 07–08/10 |
| M3 | 08–09/10 |
| Mandatory scope-compression checkpoint | Tối 08/10 |
| Evaluation Set A | 09–10/10 |
| M5 user sessions | 10–11/10 |
| M6 reproducibility/deployment proof | 11–12/10 |
| Target freeze | Tối 12/10 |
| Final Sealed Set B on frozen revision | 13/10 |
| Slides/video/build log/interview rehearsal | 14/10 |
| Internal submission-ready target | 15/10 |
| Buffer | 16/10 |
| Onsite/demo-day working day | 17/10 |

Nếu hết 07/10 M1 chưa PASS: ghi **AT RISK** trong STATUS và không tự mở M2 core.
Timeline không override Gate rules; sprint sau chỉ mở khi dependency Gate PASS.

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
| M1.2 | Provider observability | DONE |
| M1.3 | Offline verification + Code Review | DONE |
| M1.4 | Targeted LIVE diagnosis | DONE |
| M1.5 | Evidence-driven reliability fix | IN PROGRESS |
| M1.6 | Full15 Gate + Sprint Review | NOT STARTED |

M1.5 không được định nghĩa cứng trước. Nội dung fix phải dựa trên evidence từ M1.4.
Remaining work:

- Diagnose historical ClientError nếu reproducible.
- Xác định limiter chạm trước: per-call retry / shared case budget / deadline /
  non-retryable error.
- Review call/budget/time headroom, gồm unseen-input topology.
- Evaluate minimal fix: retry / backoff / case budget / call reduction / provider
  fallback, chỉ khi evidence hỗ trợ.

Không mặc định backoff 3s, attempts 6 hoặc provider fallback.
Current local patch dùng bounded 1-second backoff; targeted LIVE có recovery ở
V01 nhưng 503 vẫn tồn tại ở E01/V02. M1 **NOT PASS YET**.

M1.6 gồm full15 LIVE Gate, escalation5 latency regression <=90s nếu requirement
này vẫn applicable với current verify mode, và final M1 review theo Global Workflow.

## M2 — Core Decision + Escalation Quality

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
Numeric M2 Gate chưa được chốt; không tự đặt ngưỡng.

Trước first M2 evaluation phải lock DEV protocol, pass criteria,
question-quality rubric và evaluator. Mọi DEV metrics phải ghi **DEV-ONLY**.

### Scope

- Extraction correctness.
- Retrieval/evidence correctness.
- Deterministic policy behavior.
- Routing.
- Groundedness/error analysis.
- P01/P02/P03/P05.
- Missed escalation và unnecessary escalation trên DEV.
- Escalation question quality.

M2 phải xác định có real soft decision threshold nào phù hợp để hỗ trợ M3
adaptation hay không; không tạo threshold giả chỉ để có adaptation.

## M3 — Human Control + Feedback Adaptation

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

Adaptation chỉ áp dụng với suitable soft decision variables; không nới hard P01
authority rule, hard OUT_OF_POLICY rule hoặc suspicious-input safety behavior.
Adaptation phải versioned, bounded, auditable, reversible; final evaluation dùng
frozen adaptation state.

Cuối M3 phải có live/study environment available. Tách dev DB, study DB và
demo/judge DB, kèm reset/seed procedure.

## M4 — Evaluation Set A + Final Sealed Set B

### Objective

Xây evaluation protocol không contamination.

### Exit Gate

- DEV/REGRESSION tách independent evaluation sets.
- Evaluation Set A: author/gold/hash trước M2 tuning; chạy sau M3. Khi mở results,
  Set A trở thành DEV/diagnostic và không được gọi final held-out nữa.
- Final Sealed Set B: author/gold/hash independently; không tuning từ results;
  chạy một lần trên frozen revision trong M7, làm final independent evidence.
- Harness reproducible.
- Metrics predefined.
- Wilson CI cho proportion metrics.
- Final Sealed Set B chưa dùng để tuning.

Nếu final Set B kém: báo trung thực, không tune sau khi xem results.

Các set đã dùng để tune/test trước đó phải coi là DEV/REGRESSION,
bao gồm full15 đã dùng trong các lượt hiện tại.

## M5 — Human Impact Study

### Objective

Đo tác động thật lên human reviewer.

### Exit Gate

Exploratory evidence gồm:

- Review time.
- Final human decision.
- Acceptance/rejection AI recommendation trong session.
- Raw n/N.
- Qualitative notes.
- Participants ngoài team.
- Consented participants.

Phải có >=3 participants thực sự xử lý loại workflow này; consent,
identity/role evidence theo yêu cầu và written feedback từ participant.
Phải có >=1 concrete product change từ feedback, kèm commit evidence.
Ưu tiên synthetic/anonymized session data; ghi rõ real vs synthetic data.
Extended planted-wrong study là optional scope, không thay các yêu cầu trên.

Không claim automation-bias prevalence từ sample nhỏ.

## M6 — Reproducibility & Deployment Proof

### Objective

Chứng minh project không chỉ chạy trên máy dev hiện tại.

### Exit Gate

- Fresh clone setup thành công.
- Live URL và clean-clone runbook.
- Python 3.11 reproducible.
- Docker image chạy.
- Migration/seed reproducible.
- Cassette record/replay trong exact Docker image.
- Replay cassette miss = 0.
- Verify judge-runnable và DB reset procedure.
- 2–3 concurrent-session smoke.

Không yêu cầu large stress test hoặc real Postgres/Kafka migration.

## M7 — Freeze + Final Evaluation + Submission + Defense

### Objective

Khóa hệ thống và tạo final evidence.

### Target Timeline

| Mốc | Thời gian mục tiêu (2026, UTC+07:00) |
|---|---|
| Target freeze | Tối 12/10 |
| Final Sealed Set B on frozen revision | 13/10 |
| Slides/video/build log/interview rehearsal | 14/10 |
| Internal submission-ready target | 15/10 |
| Buffer | 16/10 |
| Onsite/demo-day working day | 17/10 |

Đây là target timeline; không thay thế các sprint gate.

### Exit Gate

- Frozen revision/tag.
- Final Sealed Set B run một lần.
- Protocol được tuân thủ.
- Reproducibility evidence.
- Final metrics/report.
- Demo/package.
- Repo clean.
- Submission ready.
- Final test-data package.
- 5 slides, <=3 minute video và 1-page build log.
- Limitations, real/synthetic disclosure và defense notes.
- Onsite 17/10 kit: clean-clone runnable, runbook, known-good environment,
  API key/quota preflight, live path, cassette cho known demo only, video fallback,
  DB seed/reset và revision provenance.

Sau freeze không tuning dựa trên held-out.

## Scope Compression / Cut Policy

Mandatory scope-compression checkpoint: tối 08/10.

**DO NOT CUT:** live reliability; unseen-input robustness; independent evaluation;
missed/over-escalation metrics; minimal compliant adaptation; >=3 real users;
>=1 feedback-driven change; live URL; human control/audit; runbook/reproducibility;
5 slides; video; build log; test-data package; consent/evidence; interview preparation.

**CUT FIRST:** extended planted-wrong study; extra dashboard/UI polish; large
stress testing; real Postgres/Kafka migration; architecture polish; adaptation
depth beyond minimal compliant version.

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
