# M3-FIX-03 — Atomic controls/correction

## Provenance và baseline

Bổ sung lịch sử ngày 12/10/2026 (Asia/Saigon), trong scope reconciliation được Coordinator ủy quyền; không tạo Task ID mới. Owner: Task Owner NOT VERIFIED; PR author AIVIETNAM-AIO-MinhThuw.

- Nguồn: [PR #37](https://github.com/ThanhVu165/MLAi_VNG_A/pull/37), body và metadata được đọc qua GitHub CLI.
- Baseline PR: `2934bf0e053d234ec465ee4e6bc6714ff8da01c4` (baseRefOid từ metadata; không thay xác minh remote của task gốc).
- Implementation checkpoint: [`07e6cae5ee8a84c6a29e010e426baa3c93449130`](https://github.com/ThanhVu165/MLAi_VNG_A/commit/07e6cae5ee8a84c6a29e010e426baa3c93449130).
- Merge commit đã có: `bc44dfb4aac2b70f1788b0bdf479aabba9bb36b6`.
- Files lịch sử: `core/controls.py`, `core/dispatch.py`, `tests/test_m3_atomicity.py`.

## Phương pháp và kết quả

Pause/resume setting và audit commit/rollback cùng transaction; kiểm parent SENT và tạo correction child/draft/audit dưới write lock, giữ public contract.

Reconciliation chỉ đọc PR, commit/file inventory và repository reports; không chạy lại implementation/tests. Các con số dưới đây là **reported historical validation** trong PR body, không phải execution mới hoặc raw-log verification.

## Validation lịch sử

Failure injection trước 18 FAIL / 15 PASS; sau 33 PASS. Targeted 179 PASS / 0 FAIL / 0 SKIP. Full baseline 457 PASS / 89 FAIL / 3 SKIP; hotfix 490 PASS / 89 FAIL / 3 SKIP, cùng failed/skip IDs. Ruff/AST/diff/signature/action/scoped mypy PASS theo PR.

## Nghiệm thu và risks

PR body ghi Coordinator trực tiếp nghiệm thu và miễn independent human review trong phiên; đây là reported decision, không review PASS. Integration MERGED được xác minh. Full suite exit 1; browser/disk-full/power-loss/load chưa chạy.

Không suy integration thành M3/M5/M6 Gate PASS hoặc DONE mới. Log ngoài repository và self-review con người không được dựng lại. Baseline failures và mọi SKIP/NOT VERIFIED giữ nguyên.

## LIVE/API và bàn giao

PR báo application/LLM/provider/email LIVE calls: **0** trong task gốc. Reconciliation: **0** runtime/provider/email calls; GitHub/Trello/git HTTPS là truy cập evidence. Báo cáo này chờ Coordinator review cùng [bảng audit](SPRINT2_EVIDENCE_RECONCILIATION_20261012.md).
