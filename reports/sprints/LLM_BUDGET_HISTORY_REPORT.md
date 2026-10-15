# Cardless — Four-attempt LLM budget

## Provenance và baseline

Bổ sung lịch sử ngày 12/10/2026 (Asia/Saigon), trong scope reconciliation được Coordinator ủy quyền; không tạo Task ID mới. Owner: Task Owner NOT VERIFIED; PR author AIVIETNAM-AIO-MinhThuw.

- Nguồn: [PR #29](https://github.com/ThanhVu165/MLAi_VNG_A/pull/29), body và metadata được đọc qua GitHub CLI.
- Baseline PR: `0c581ef2c0be97c4fcb943a45d3d6bc6f41a051c` (baseRefOid từ metadata; không thay xác minh remote của task gốc).
- Implementation checkpoint: [`717457a037ce736eca75e706fd7ebf4bf4afb9fb`](https://github.com/ThanhVu165/MLAi_VNG_A/commit/717457a037ce736eca75e706fd7ebf4bf4afb9fb).
- Merge commit đã có: `282c73b7dbf4ac7bf027d5710cce6ed673ab80d1`.
- Files lịch sử: `core/pipeline.py`, `core/resume.py`, `infra/llm.py`, `infra/settings.py`, `tests/test_guards.py`, `tests/test_llm_budget.py`, `tests/test_openai_provider.py`, `tests/test_provider_observability.py`, `tests/test_semantic_validator_compat.py`.

## Phương pháp và kết quả

Giới hạn lifecycle ở bốn provider attempts; initial processing ba attempts, R11 một. Không thay policy/schema/UI.

Reconciliation chỉ đọc PR, commit/file inventory và repository reports; không chạy lại implementation/tests. Các con số dưới đây là **reported historical validation** trong PR body, không phải execution mới hoặc raw-log verification.

## Validation lịch sử

Targeted 221 PASS; full offline 508 PASS / 3 SKIP; Ruff và Black scoped PASS. Full Black có 18 findings cũ; Mypy full bị duplicate module, scoped có bốn lỗi typing SDK cũ.

## Nghiệm thu và risks

Integration MERGED. Coordinator acceptance riêng NOT VERIFIED. Mocked/offline không chứng minh chất lượng LIVE; giữ M2 conditional.

Không suy integration thành M3/M5/M6 Gate PASS hoặc DONE mới. Log ngoài repository và self-review con người không được dựng lại. Baseline failures và mọi SKIP/NOT VERIFIED giữ nguyên.

## LIVE/API và bàn giao

PR báo application/LLM/provider/email LIVE calls: **0** trong task gốc. Reconciliation: **0** runtime/provider/email calls; GitHub/Trello/git HTTPS là truy cập evidence. Báo cáo này chờ Coordinator review cùng [bảng audit](SPRINT2_EVIDENCE_RECONCILIATION_20261012.md).
