# M3-FIX-01 — Stale approval preview

## Provenance và baseline

Bổ sung lịch sử ngày 12/10/2026 (Asia/Saigon), trong scope reconciliation được Coordinator ủy quyền; không tạo Task ID mới. Owner: Project Coordinator theo PR body.

- Nguồn: [PR #35](https://github.com/ThanhVu165/MLAi_VNG_A/pull/35), body và metadata được đọc qua GitHub CLI.
- Baseline PR: `a877b32db72ba3cd5a1e10703531a8b0ee6d342c` (baseRefOid từ metadata; không thay xác minh remote của task gốc).
- Implementation checkpoint: [`311aa14a14117a49d38fa15e054fac4f1a1130ff`](https://github.com/ThanhVu165/MLAi_VNG_A/commit/311aa14a14117a49d38fa15e054fac4f1a1130ff).
- Merge commit đã có: `2071f59b68d34d4381d8a3463cc1105f15234393`.
- Files lịch sử: `pages/2_Hang_cho_duyet.py`, `tests/test_runtime_worker.py`.

## Phương pháp và kết quả

Bind immutable preview với recipient, payload và active corpus version; kiểm lại trong SQLite write transaction trước SENT, từ chối stale preview, không ghi success event.

Reconciliation chỉ đọc PR, commit/file inventory và repository reports; không chạy lại implementation/tests. Các con số dưới đây là **reported historical validation** trong PR body, không phải execution mới hoặc raw-log verification.

## Validation lịch sử

Trước fix hai regression FAIL (2.27s); sau fix 59 PASS / 0 FAIL / 0 SKIP (24.28s). Ruff/AST/diff/sensitive scope PASS theo PR. Lần setup lỗi temp permission không được tính PASS.

## Nghiệm thu và risks

Integration MERGED; PR ghi independent review/Coordinator acceptance pending lúc handoff. Không có human review mới được xác minh. UI hai bước integration không được chạy trong task này; thuộc PR #38.

Không suy integration thành M3/M5/M6 Gate PASS hoặc DONE mới. Log ngoài repository và self-review con người không được dựng lại. Baseline failures và mọi SKIP/NOT VERIFIED giữ nguyên.

## LIVE/API và bàn giao

PR báo application/LLM/provider/email LIVE calls: **0** trong task gốc. Reconciliation: **0** runtime/provider/email calls; GitHub/Trello/git HTTPS là truy cập evidence. Báo cáo này chờ Coordinator review cùng [bảng audit](SPRINT2_EVIDENCE_RECONCILIATION_20261012.md).
