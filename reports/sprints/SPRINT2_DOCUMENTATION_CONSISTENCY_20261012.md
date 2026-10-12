# Nhất quán tài liệu Sprint 2 — Báo cáo evidence

## Nhiệm vụ và ủy quyền

- Vai trò phiên: Task Owner — Documentation Maintenance.
- Nguồn ủy quyền cardless: người dùng trong cuộc trò chuyện Codex ngày 12/10/2026
  chỉ dẫn “bỏ qua việc check trello, làm thẳng” và, với micro-fix PR #43, “bỏ qua
  phần check trello, cho làm thẳng”. Danh tính và thẩm quyền Coordinator của người
  ủy quyền chưa được xác minh: `PENDING COORDINATOR CONFIRMATION`.
- Owner: `PENDING COORDINATOR CONFIRMATION`. GitHub xác nhận PR author là
  `AIVIETNAM-AIO-MinhThuw` và hai commit đã review ghi author Minh Thư; thông tin này
  chỉ xác định người tạo PR/commit, không được dùng để suy ra Task Owner hoặc Coordinator.
- Approver: Project Coordinator; chỉ Coordinator xác nhận `DONE` và cho phép merge.
- Phạm vi: `AGENT.md`, `docs/TEAM_HANDOFF.md`, `docs/SPRINT_ROADMAP.md` và báo cáo này.

## Baseline và workspace

- Remote: `origin` — `https://github.com/ThanhVu165/MLAi_VNG_A.git`.
- `origin/dev` đã xác minh: `b1214476c7e02776cb3aee0e2debaae86e3e3dee` sau
  `git fetch origin dev --prune` ngày 12/10/2026.
- Branch: `codex/sprint2-doc-consistency`, tạo trực tiếp từ `origin/dev` đã xác minh.
- Các file untracked có sẵn: `.pytest-m16*.db-shm/.db-wal` và
  `reports/readiness/CURRENT_RUNTIME_SMOKE.md`; không đọc sửa, xóa hoặc đưa vào scope.

## Phương pháp

Đối chiếu technical contract trong `PROJECT_SPEC.md` §5.4/§6, workflow trong
`docs/TEAM_WORKFLOW.md`, milestone trong `STATUS.md`, báo cáo đóng M2, báo cáo
feasibility M3-T02, implementation/test lỗi liên quan và ba tài liệu đích. Không
gọi ứng dụng, provider, LLM, Gmail hoặc email thật.

## Mâu thuẫn đã sửa và lý do

1. `AGENT.md` trước đây gộp lỗi LLM/dịch vụ vào `ESCALATE/P04`; sửa thành
   `Decision.ERROR / CaseStatus.ERROR`, giữ P04 cho content guard và giữ riêng ba
   kiểu dừng P01/P02/P03. `test_no_fail_open` được mô tả theo bất biến no-fail-open,
   không đổi kết quả test mong đợi.
2. `TEAM_HANDOFF.md` trước đây ghi “technical fail-safe/P04”; sửa cách phân loại và bổ sung
   ngắn các bất biến sản phẩm, giám sát có chọn lọc, phê duyệt đúng hành động/trạng
   thái cũ, giới hạn evidence/lời giải thích, tác động con người M5, VNG/BGK carryover
   và ranh giới Gmail.
3. Kết luận M3-T02 được giữ đúng phạm vi: `score=1.0` trên evidence đã chọn dẫn tới
   technical STOP cho baseline khảo sát; không suy thành GO, implementation/M3 PASS
   hay bất khả thi vĩnh viễn.
4. `SPRINT_ROADMAP.md` trước đây có thể hiểu mọi task fail đều chặn task tiếp theo và
   Gate luôn cần Code Review + Review Agent + Anti review. Sửa thành review theo
   dependency/rủi ro, cho phép task độc lập `READY` chạy song song và giữ Coordinator
   làm người quyết acceptance/gate.
5. Bổ sung phân loại evidence, nguyên tắc tích hợp runtime/replay và đường đọc
   context có giới hạn; không tạo milestone, checkpoint hay Exit Gate mới.

## Phát hiện ngoài phạm vi

- `core/policy_engine.py:188` có docstring “lỗi cấu hình luôn hạ về P04”, trong khi
  `_fallback()` tại dòng 176–184 trả `Decision.ERROR`, `rule_id=TECHNICAL_ERROR` và
  không có escalation type. Hành vi code phù hợp `PROJECT_SPEC.md`; chỉ comment code
  bị lỗi thời. Task này không được sửa Python, nên chuyển Coordinator quyết định một
  task dọn comment code riêng. Mức độ: LOW về runtime, MEDIUM về khả năng gây hiểu sai.

Không phát hiện đường xử lý lỗi kỹ thuật trong implementation trái §5.4 tại các phần
đã đọc: `core/pipeline.py` fail-safe trả `Decision.ERROR`/`CaseStatus.ERROR`; P04
guard được đưa vào queue riêng và không tự dispatch.

## Kiểm tra

Kết quả self-review trước commit:

- `git diff --check`: `PASS`.
- Cấu trúc/định dạng Markdown: `PASS` — heading, code fence và khoảng trắng cuối dòng.
- Liên kết cục bộ trong bốn file thuộc scope: `PASS` — mọi đích đều tồn tại.
- Tính nhất quán ERROR/P04/escalation và review/dependency: `PASS` qua targeted `rg`.
- Phạm vi, secret pattern và workspace state: `PASS`; chỉ bốn file được phép sẽ commit.
- Quy định ngôn ngữ cho toàn bộ nội dung mới/chỉnh sửa: `PASS` qua self-review.
- Xung đột PR: `PASS` — không có open PR nhắm `dev` tại thời điểm kiểm tra.
- Full pytest: `NOT RUN` — docs-only task; không dùng để claim runtime PASS.
- Runtime/LIVE/user study: `NOT RUN` / `NOT VERIFIED`.

Micro-fix trước nghiệm thu PR #43 được đối chiếu từ head đã review
`c63a06403f72f2d6521f93633cce3f2c75ef143e`: tách technical `ERROR` khỏi hàng chờ
con người và ghi Owner/authorization theo evidence thực có. Commit chứa micro-fix là
PR head sau push; SHA được ghi trong handoff review. Kiểm tra riêng cho micro-fix:
`git diff --check`, cấu trúc/định dạng Markdown, liên kết cục bộ, phạm vi hai file,
ERROR/P04/escalation và ngôn ngữ đều `PASS`. Full pytest, runtime và LIVE vẫn
`NOT RUN`.

## Rủi ro và giới hạn

- Trello bị bỏ qua theo chỉ dẫn cardless của người dùng; chưa xác minh quyết định
  Trello mới hơn, danh tính Owner hoặc thẩm quyền Coordinator của người ủy quyền.
- Đây là cập nhật tính nhất quán, không chứng nhận WAL, Docker, deployment, stale approval,
  adaptation, official evaluation hoặc real-user study đã PASS.
- Evidence lịch sử giữ nguyên; không suy rộng kết quả từ checkpoint cũ sang HEAD.

## Git, PR và các lượt gọi LIVE/API

- Commit chính: `a447f2082e98d190462860c1d84610c7e2961829`.
- Draft PR nhắm `dev`: [#43](https://github.com/ThanhVu165/MLAi_VNG_A/pull/43).
- Exodia runtime/provider/LLM/Gmail/email calls: **0**.
- Lượt mạng Git/GitHub đã xác nhận: 1 lần `git fetch origin dev --prune`, 1 lần
  `gh pr list`, 1 lần push commit chính và 1 lần tạo Draft PR. Một lần push bổ sung
  được dùng sau commit báo cáo này để đồng bộ evidence vào chính PR #43.
- Trello sau chỉ dẫn bỏ qua: **0**. Trước đó có **1** search read-only hoàn tất và
  1 batch read-only bị hủy nên không xác minh được số nested call đã hoàn tất; write: **0**.

## Bước tiếp theo

Project Coordinator review diff/evidence, quyết định cách xử lý finding ngoài phạm
vi, xác nhận acceptance và quyết định merge. Báo cáo `READY_FOR_REVIEW` không đồng
nghĩa `DONE`.
