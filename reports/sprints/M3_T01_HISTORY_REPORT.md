# M3-T01 — Approval safety regression

## Provenance và baseline

Bổ sung lịch sử ngày 12/10/2026 (Asia/Saigon), trong scope reconciliation được Coordinator ủy quyền; không tạo Task ID mới. Owner: Vũ; reviewer Nam.

- Nguồn: [PR #31](https://github.com/ThanhVu165/MLAi_VNG_A/pull/31), body và metadata được đọc qua GitHub CLI.
- Baseline PR: `282c73b7dbf4ac7bf027d5710cce6ed673ab80d1` (baseRefOid từ metadata; không thay xác minh remote của task gốc).
- Implementation checkpoint: [`c7f7ba490b5a33d349b7cff66469ac27e343bd00`](https://github.com/ThanhVu165/MLAi_VNG_A/commit/c7f7ba490b5a33d349b7cff66469ac27e343bd00).
- Merge commit đã có: `16f584fa213416db30b247a431b92fffb94be075`.
- Files lịch sử: `tests/test_runtime_worker.py`.

## Phương pháp và kết quả

Thêm 14 regression cases trong tests/test_runtime_worker.py. Tests tái hiện stale recipient/corpus preview vẫn chuyển SENT và có một success audit. Không sửa production trong task này.

Reconciliation chỉ đọc PR, commit/file inventory và repository reports; không chạy lại implementation/tests. Các con số dưới đây là **reported historical validation** trong PR body, không phải execution mới hoặc raw-log verification.

## Validation lịch sử

Checkpoint 54 PASS / 2 FAIL / 0 SKIP, 27.31s, exit 1; cases mới 12 PASS / 2 FAIL, 42 regression cũ PASS. Ruff/diff PASS theo PR; SQLite tạm, replay/network block. Browser multi-tab và outbound delivery NOT VERIFIED.

## Nghiệm thu và risks

Coordinator move Done được xác minh trong audit; kết quả lịch sử vẫn là hai safety FAIL, không đổi thành PASS hồi tố. Fix sau thuộc PR #35. Card board 69HYW10S khác URL Ik4fEVHU trong PR; mapping card cũ NOT VERIFIED.

Không suy integration thành M3/M5/M6 Gate PASS hoặc DONE mới. Log ngoài repository và self-review con người không được dựng lại. Baseline failures và mọi SKIP/NOT VERIFIED giữ nguyên.

## LIVE/API và bàn giao

PR báo application/LLM/provider/email LIVE calls: **0** trong task gốc. Reconciliation: **0** runtime/provider/email calls; GitHub/Trello/git HTTPS là truy cập evidence. Báo cáo này chờ Coordinator review cùng [bảng audit](SPRINT2_EVIDENCE_RECONCILIATION_20261012.md).
