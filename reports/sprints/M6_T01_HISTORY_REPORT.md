# M6-T01 — Deployment/replay readiness static audit

## Nguồn và baseline

Báo cáo lịch sử bổ sung ngày 12/10/2026 (Asia/Saigon) theo authorization reconciliation; không thực hiện lại task, không ký thay Owner.

- Owner: Nam; Approver: Project Coordinator.
- Nguồn trực tiếp: [Trello evidence comment](https://trello.com/c/DSIUsD0p#comment-6acb4b0d6bf5b88289e4a450). Comments được đọc hết qua list_comments, hasNextPage=false.
- Baseline do nguồn báo: [`282c73b7dbf4ac7bf027d5710cce6ed673ab80d1`](https://github.com/ThanhVu165/MLAi_VNG_A/tree/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1).
- Source đối chiếu: [infra/llm.py tại baseline](https://github.com/ThanhVu165/MLAi_VNG_A/blob/282c73b7dbf4ac7bf027d5710cce6ed673ab80d1/infra/llm.py).
- Task gốc READ_ONLY: không có implementation commit/PR; SHA trên là source baseline.

## Phương pháp và kết quả

Owner bàn giao BLOCKED — static audit completed; runtime evidence incomplete. Không có implementation commit/PR trong task read-only.

Đọc tree/setup/startup/dependencies/SQLite/seed/LLM/harness trên baseline. Không tìm Dockerfile/Compose/.dockerignore hoặc committed cassette JSON trong tree đã kiểm; replay cần cassette theo prompt hash. Startup/import có thể init/seed/ghi SQLite. Reconciliation kiểm pinned tree và infra/llm.py bằng git ls-tree/git show; không đọc cassette contents hoặc chạy setup.

## Validation và nghiệm thu

AC1 PASS static inventory; AC2 SKIP/NOT VERIFIED fresh-clone/install/startup; AC3 PASS static, isolation runtime NOT VERIFIED; AC4 BLOCKED replay/cassette availability; AC5 PASS static risks; AC6 BLOCKED review/acceptance trong handoff. Docker/public deploy/concurrency không chạy.

Tại audit 12/10, card thuộc **Done - Đã nghiệm thu**, do Coordinator move theo activity được đọc và dẫn trong [bảng audit](SPRINT2_EVIDENCE_RECONCILIATION_20261012.md). Ghi nhận quyết định trạng thái này; rationale để giải quyết các gap trong handoff **NOT VERIFIED**. Không ghi lại BLOCKED như trạng thái card hiện hành hoặc nâng runtime/gate thành PASS.

## Risks và Owner follow-up

Không chứng minh Docker/fresh-clone/replay/public URL hoặc mở khóa M6-T02. Không thấy committed cassette không chứng minh cassette không tồn tại ngoài Git. Self-review confirmation và independent review cần Owner/Reviewer bổ sung.

Source checks ở reconciliation chỉ corroborate các điểm nêu rõ; không chứng minh toàn bộ AC hoặc việc human review đã xảy ra. Báo cáo tóm tắt, comment gốc vẫn là provenance; không sửa evidence lịch sử.

## LIVE/API và handoff

Nguồn báo application/LLM/provider/email LIVE **0**. Reconciliation cũng **0** runtime/provider/email; chỉ GitHub/Trello/git evidence reads. Không app/DB/seed/reset/deploy/tests execution mới. Report mới chờ Coordinator nghiệm thu cùng audit; không mở dependency hoặc đổi gate.
