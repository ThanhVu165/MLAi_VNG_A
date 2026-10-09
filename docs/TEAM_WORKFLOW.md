# Exodia — Quy trình làm việc Sprint 2

Áp dụng cho bốn thành viên và các phiên ChatGPT/Codex trong Sprint 2. Tài liệu
Sprint 1 như `TASKBOARD.md` và `SYNC_PLAN.md` được giữ làm lịch sử, không còn là
nguồn phân công hoặc trạng thái công việc hiện hành.

## Nguồn chân lý

| Phạm vi | Nguồn authoritative |
|---|---|
| Phân công, ưu tiên, owner, deadline, trạng thái task | Trello |
| Mã nguồn, review diff, commit, PR, tags | GitHub |
| Evidence, specification, runbook, milestone status | Repository |
| Scope/gate/acceptance cuối cùng và merge vào `dev` | Project Coordinator |

Trello nằm ngoài repository. Không sao chép toàn bộ board vào file Git; mỗi task
chỉ cần liên kết đúng Task Contract và evidence liên quan.

## Vai trò và trách nhiệm

- **Project Coordinator:** chốt scope, Task Contract, quyền LIVE/API, milestone
  disposition, acceptance và merge vào `dev`.
- **Task Owner:** một trong bốn thành viên; chịu trách nhiệm hiểu yêu cầu, đọc và
  kiểm tra mọi thay đổi do công cụ tạo, chạy validation phù hợp và bàn giao evidence.
- **ChatGPT Task Coordinator:** hỗ trợ phân tích, chia việc và có thể đề xuất
  `READY_FOR_REVIEW`; không tự chứng nhận evidence chưa đọc và không phê duyệt cuối.
- **Codex:** trợ lý triển khai/review theo Task Contract; không tự mở rộng scope,
  tự gọi LIVE/API hoặc tự thay đổi gate.
- **Independent Reviewer:** được chỉ định theo rủi ro; đánh giá độc lập nhưng không
  thay Project Coordinator chấp nhận task hoặc merge.

Mỗi thành viên mặc định chỉ giữ **một task `IN PROGRESS`**. Coordinator có thể cho
phép ngoại lệ khi dependency hoặc deadline yêu cầu.

## Kanban và luồng task

```text
BACKLOG → READY → IN PROGRESS → IN REVIEW → DONE
                         ↑          ↓
                         └── CHANGES REQUESTED
```

- `BACKLOG`: ý tưởng hoặc việc chưa đủ contract/dependency.
- `READY`: Task Contract rõ, dependency và owner đã xác định.
- `IN PROGRESS`: owner đang triển khai; mặc định không nhận task active thứ hai.
- `IN REVIEW`: implementation, self-review và evidence đã bàn giao.
- `CHANGES REQUESTED`: reviewer/Coordinator yêu cầu sửa có phạm vi cụ thể.
- `DONE`: Project Coordinator đã chấp nhận evidence và trạng thái tích hợp yêu cầu.

Quy trình: **giao task → triển khai → self-review → validation/evidence → review →
Coordinator acceptance → merge khi được phép**. Commit hoặc PR không tự làm task
thành `DONE`.

## Task Contract tối thiểu

Mỗi Trello card ở trạng thái `READY` cần nêu:

1. Objective và phạm vi file/hành vi.
2. Baseline branch/SHA và dependencies.
3. Acceptance criteria cùng evidence cần giao.
4. Validation bắt buộc và điều kiện dừng.
5. Quyền LIVE/API, budget và data boundaries nếu áp dụng.
6. Những nội dung cấm sửa, yêu cầu Git và reviewer cần thiết.

Nếu contract thiếu thông tin làm thay đổi quyết định hoặc safety boundary, owner
đưa task về `BACKLOG` hoặc báo Coordinator; không tự suy diễn quyền mở rộng.

## Definition of Done và evidence handoff

Một task chỉ sẵn sàng để Coordinator chấp nhận khi:

- Thay đổi đúng Task Contract và owner hiểu được diff.
- Self-review không còn thay đổi ngoài scope hoặc dữ liệu nhạy cảm.
- Validation đúng rủi ro đã PASS; failure/skip được ghi trung thực.
- Evidence nêu baseline, commands/checks, kết quả, file thay đổi và giới hạn.
- Documentation/contract liên quan được cập nhật khi hành vi thực sự đổi.
- PR nhắm `dev`, có thể review, không chứa file local hoặc thay đổi ngoài scope.
- Reviewer yêu cầu đã hoàn tất; Coordinator đưa ra acceptance cuối.

ChatGPT/Codex có thể báo `READY_FOR_REVIEW`; chỉ Project Coordinator chuyển task
sang `DONE` và cho phép tích hợp vào `dev`.

## Validation và review theo rủi ro

- Documentation/UI nhỏ: link, format, targeted smoke và diff check khi phù hợp;
  không bắt buộc full suite nếu không chạm runtime contract.
- Logic dùng chung: targeted regression và các suite bị ảnh hưởng.
- Policy, routing, guards, authority, PII/audit, provider adapter, persistence,
  LIVE runner, evaluation/Gold/fixture: cần independent review trước acceptance.
- Full suite chỉ chạy khi Task Contract yêu cầu hoặc blast radius đủ rộng.

Không biến test xanh thành semantic evidence hoặc LIVE evidence. Reviewer chỉ xác
nhận những artifact và kết quả họ thực sự kiểm tra.

## Git và giới hạn an toàn

- Tạo branch task từ verified `dev`; PR nhắm `dev`. Không merge vào `main` trong
  workflow Sprint 2 nếu không có authorization riêng.
- Không force-push, rewrite history, reset/restore/clean/stash làm mất thay đổi,
  hoặc tự xử lý conflict có ảnh hưởng nghiệp vụ.
- Không commit `.env`, credentials, `data/app.db`, cache, `__pycache__` hoặc dữ liệu
  cá nhân thô.
- Không sửa frozen Gold, fixture, rubric, ledger hoặc historical evidence nếu Task
  Contract chưa cho phép chính xác thay đổi đó.
- Không gọi LIVE/API khi chưa có authorization cụ thể về case/run, provider, giới
  hạn và budget. Offline tests không tạo quyền LIVE.
- Không tự hạ gate, đổi expected result hoặc rerun để chọn kết quả đẹp hơn.

Blocker ảnh hưởng deadline, dependency, safety hoặc acceptance phải được ghi ngay
trên Trello và báo Project Coordinator. Ưu tiên scope hữu hạn đủ đạt gate trước
feature freeze **13/10/2026**.
