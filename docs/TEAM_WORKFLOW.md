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
chỉ cần liên kết đúng Task Contract và evidence liên quan. Coordinator có thể ủy quyền
một việc cardless; khi đó báo cáo `.md` trong repository phải ghi rõ authorization,
baseline và thay thế cho trạng thái card.

## Vai trò và trách nhiệm

- **Project Coordinator:** chốt scope, Task Contract, quyền LIVE/API, milestone
  disposition, acceptance và merge vào `dev`.
- **Task Owner:** một người chịu trách nhiệm đến cùng; hiểu mọi thay đổi do mình và AI
  tạo, hoàn tất AC/checklist, tự review, chạy validation và bàn giao evidence.
- **ChatGPT Project MLAI:** nghiên cứu, phân tích, phản biện và điều phối. Session phải
  ghi rõ vai trò (Coordinator, Owner, Research/Review, Architecture/Strategy hoặc Daily
  Checkpoint), mục tiêu, scope, đầu ra, quyền hạn và điều kiện chuyển bước. ChatGPT không
  tự sửa repository, commit, push, mở PR hoặc cập nhật Trello.
- **Codex:** phân tích sâu repository, triển khai, validation, runtime smoke và lưu
  artifact theo scope được giao; không tự mở rộng scope, gọi LIVE/API hoặc đổi gate.
- **Independent Reviewer:** được chỉ định theo rủi ro, đặc biệt với routing, policy,
  approval, persistence, audit, safety và evaluation; không mặc định cần hai người.

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

Quy trình implementation: **phân tích nhiệm vụ → giao task/authorization → triển khai →
self-review → validation/evidence → review theo rủi ro → Coordinator acceptance → merge
khi được phép**. Research/review có thể kết thúc ở báo cáo chuyên đề mà không tạo code.
ChatGPT phải chờ người thực hiện đồng ý với phương án trước khi chuyển bước và chỉ tạo
prompt Codex khi người thực hiện yêu cầu hoặc cho phép. Commit hoặc PR không tự làm task
thành `DONE`.

## Task Contract tối thiểu

Mỗi Trello card ở trạng thái `READY`, hoặc authorization cardless của Coordinator, cần nêu:

1. Objective và phạm vi file/hành vi.
2. Baseline branch/SHA và dependencies.
3. Acceptance criteria cùng evidence cần giao.
4. Validation bắt buộc và điều kiện dừng.
5. Quyền LIVE/API, budget và data boundaries nếu áp dụng.
6. Những nội dung cấm sửa, yêu cầu Git và reviewer cần thiết.
7. Với việc cardless: người ủy quyền, phạm vi ủy quyền và cách ghi nhận thay cho card.

Nếu contract/authorization thiếu thông tin làm thay đổi quyết định hoặc safety boundary,
owner đưa task về `BACKLOG` hoặc báo Coordinator; không tự suy diễn quyền mở rộng. Không
được báo `BLOCKED` chỉ vì thiếu hướng dẫn cho một thao tác kỹ thuật thông thường nằm
trong scope.

## Definition of Done và evidence handoff

Một task chỉ sẵn sàng để Coordinator chấp nhận khi:

- Thay đổi đúng Task Contract và owner hiểu được diff.
- Self-review không còn thay đổi ngoài scope hoặc dữ liệu nhạy cảm.
- Validation đúng rủi ro đã PASS; failure/skip được ghi trung thực.
- Evidence nêu baseline, commands/checks, kết quả, file thay đổi và giới hạn.
- Có báo cáo `.md` trong repository ghi Task ID hoặc cardless authorization, Owner,
  SHA, phương pháp, validation, evidence, risks và PR/commit liên quan.
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

- Mặc định dùng **một repository và một branch riêng cho task**. Không tự tạo worktree,
  clone hoặc backup repository phụ.
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

Blocker ảnh hưởng deadline, dependency, safety hoặc acceptance phải báo Project
Coordinator. Nội dung tối thiểu: **Vấn đề → Ảnh hưởng → Giải pháp → Ai xử lý →
Coordinator cần quyết định gì**. Nếu task có card thì owner ghi trên Trello; nếu
cardless thì ghi trong evidence `.md`. Ưu tiên scope hữu hạn đủ đạt gate trước
feature freeze **13/10/2026**.
