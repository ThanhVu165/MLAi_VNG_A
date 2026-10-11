# Project Status

Last coordination update: **10/10/2026** (Asia/Saigon).

- Sprint 2 task authority: Trello.
- Technical source of truth: GitHub and repository evidence.
- Workflow: [docs/TEAM_WORKFLOW.md](docs/TEAM_WORKFLOW.md).
- Roadmap: [docs/SPRINT_ROADMAP.md](docs/SPRINT_ROADMAP.md).
- Internal submission-ready target: **15/10/2026**.
- Feature freeze target: **13/10/2026**.

## Current milestone

**M3 — Human Control + Feedback Adaptation: `M3_AUTHORIZED_WITH_CARRYOVER`.**

Authorization cho phép lập kế hoạch M3 với M2 carryover. Implementation vẫn cần
Task Contract và Coordinator phê duyệt riêng; adaptation cần feasibility GO/STOP
trước khi xem xét triển khai. Quyền lập kế hoạch không đồng nghĩa đã triển khai,
đạt gate hoặc được nghiệm thu, không đổi verdict M2 thành PASS, không xóa
historical failures và không tự cấp quyền LIVE/API.

Kế hoạch M3–M7 đã được Coordinator chốt trong DOC-T01; lịch hiện hành và ranh giới
chuẩn bị song song M5/M6 xem [SPRINT_ROADMAP.md](docs/SPRINT_ROADMAP.md).

## Closed milestones

### M1 — CLOSED

M1 Gate PASS ngày 06/10/2026: final full15 có **0/15 technical errors** và
**14/15 semantic labels**; verify4 4/4, escalation5 4/5 trong 44,48 giây.
Nguồn: [M1 runtime report](reports/sprints/M1_runtime_reliability.md) và
[immutable evidence](reports/evidence/m1/README.md).

### M2 — `M2_CONDITIONAL_CLOSEOUT`

M2 có positive evidence cho P01/P02/P03/P05 và đã được merge vào `dev`. Verdict
vẫn conditional vì coverage và semantic adjudication còn giới hạn:

- 9 independent LIVE observations, 6/12 unique frozen DEV cases.
- 103 criterion records trong narrative roll-up: 68 PASS, 5 FAIL,
  30 REVIEW_REQUIRED; đây không phải accuracy estimate.
- Historical semantic FAIL và TECHNICAL_FAILURE vẫn được giữ.
- Fallback handoff correction có regression offline nhưng chưa được exercise LIVE.
- Identifier-specific numeric branch không được claim là `VERIFIED_LIVE`.
- Không claim held-out evaluation, full 12-case coverage hoặc full semantic safety.

Nguồn authoritative:
[M2 final closeout](reports/sprints/M2_FINAL_CLOSEOUT_AND_M1_M2_CHECKIN_20261009.md).
LIVE ledger giữ **12/45 consumed, 33 remaining**; quota không phải authorization.

## Carryover vào M3

- Giữ hard authority/out-of-policy/suspicious-input boundaries; adaptation không
  được nới các rule này.
- Xác minh end-to-end pause/resume, human approval, escalation queue, cancel,
  correction/undo, payload-bound approval và audit trail.
- Tách dev, study và demo/judge data; không dùng frozen DEV/Gold trái mục đích.
- Mọi LIVE/API run cần authorization riêng của Project Coordinator.
- Không quảng bá correction chỉ có offline evidence thành `VERIFIED_LIVE`.
