# M5-T01 — Owner Handoff

**Result:** READY_FOR_INDEPENDENT_REVIEW. **Independent Review:** PENDING.
Không phải DONE hoặc M5 PASS. **Next Task Unlocked:** NONE.

## Task, scope và verified baseline

Objective: đóng gói deliverables chuẩn bị B0/B2 từ
[card M5-T01](https://trello.com/c/nSzHYb2a) thành artifact Git có version, để Minh
review độc lập. Coordinator đã cho phép branch/PR riêng và scope
`docs/studies/m5_t01/` trong chỉ thị hoàn thiện GitHub; đây là phần tiếp tục task
hiện hành, không tạo task mới. Owner cuối và approver do Coordinator xác nhận;
card ghi Coordinator, comment phân công đề xuất Thư; reviewer đề xuất Minh.

Ngày 11/10/2026, fetch `origin --prune` xác minh:

- dev SHA: `282c73b7dbf4ac7bf027d5710cce6ed673ab80d1`.
- Original workspace HEAD: `0c581ef2c0be97c4fcb943a45d3d6bc6f41a051c`, branch
  `task/ui-human-review-workspace`; có thay đổi UI/test/bytecode và evidence local
  không thuộc task. Không checkout/reset/clean/rebase/ghi đè tại đó.
- Không có open PR ở thời điểm kiểm baseline; latest dev là merge PR #29 về LLM
  budget, không làm thay policy/corpus hoặc scope chuẩn bị đã bàn giao.
- Branch mới `sprint/m5-t01-study-preparation` tạo từ verified remote dev trong
  worktree riêng; không có artifact M5 hiện hữu tại đích, không có file overlap.
- Repository PUBLIC; không commit Gold. [Gold review/storage](gold_review.md)
  thay cho `gold_labels.md`; kho có kiểm soát còn chờ Coordinator quyết định.

Đã đọc current AGENT, TEAM_WORKFLOW, PROJECT_SPEC, SPRINT_ROADMAP (M5), STATUS,
policy và sáu seed docs; đọc Task Contract cùng toàn bộ 5 comment (pagination
không còn trang sau), đặc biệt FINAL OWNER SELF-REVIEW. Technical contract hiện
hành ở spec được giữ; không sửa policy/runtime hoặc dùng lỗi kỹ thuật làm P03.

## Changes và artifact paths

| Artifact | Nội dung |
|---|---|
| [README.md](README.md) | Baseline, audience, nguồn và blockers |
| [study_protocol.md](study_protocol.md) | Crossover, bốn sequence, fairness, timer, errors, unlock |
| [cases_xy.md](cases_xy.md) | Đúng tám email cuối Trello, X4 có K49, không đáp án |
| [gold_review.md](gold_review.md) | Restricted-storage proposal và independent review workflow |
| [recruitment_consent.md](recruitment_consent.md) | >=3 người, lịch dự kiến, consent và storage plan |
| [measurement_forms.md](measurement_forms.md) | Sáu nhóm form, metrics, raw n/N và trace cải tiến |
| [owner_handoff.md](owner_handoff.md) | AC evidence, validation, manifest và pending review |

Khác biệt có chủ đích so với draft Trello: corpus kiểm kê vẫn sáu nguồn nhưng B0
và B2 chỉ được dùng năm ACTIVE; nguồn SUPERSEDED dành cho reviewer archive.
Làm rõ pause marker không đổi primary wall-clock, denominator từng metric,
technical outcomes và AI action overlap. Không đổi email hoặc Gold Owner-side;
không công bố bảng đáp án/balance nhãn theo case vào public Git.

## AC1–AC6 evidence matrix

| AC | Checklist Trello đã đọc | Owner evidence | Phần còn chờ |
|---|---|---|---|
| AC1 | COMPLETE | recruitment_consent: tiêu chí, tiếp cận >=3, lịch/backup, consent | Tuyển/lịch/consent thật trước study |
| AC2 | COMPLETE | study_protocol: crossover, sequence, cùng corpus ACTIVE, timer/errors | Minh review, Coordinator approval |
| AC3 | COMPLETE | measurement_forms: observation, condition/session feedback, minimization, n/N | Independent review |
| AC4 | COMPLETE Owner-side | cases_xy: đủ 8 email, X4 mới; policy/sáu corpus đối chiếu; Gold giữ trên Trello | Gold/equivalence sign-off; restricted storage |
| AC5 | COMPLETE về checklist điều kiện | study_protocol: unlock revision, isolation, access, runtime, consent/lịch | Runtime proof M3-T03 và actual unlock chưa xác nhận |
| AC6 | INCOMPLETE | measurement_forms: aggregation/trace; Handoff này và Trello đầy đủ phần Owner | Minh independent verdict + Coordinator acceptance |

Không tự tick AC6; không chuyển card DONE. AC1–AC5 COMPLETE là trạng thái checklist
chuẩn bị Owner-side đã đọc, không chứng minh đã có người tham gia hoặc study GO.

## Validation và self-review

Validation tài liệu offline, không import/chạy app, pipeline, seed hoặc Verify.
Commit/PR URL và final SHA được đăng trong comment handoff mới trên card
(không tự chèn hash của commit vào chính nó).

| Lệnh/check thực tế | Kết quả |
|---|---|
| `git fetch origin --prune`; `git rev-parse HEAD origin/dev` | Baseline như trên; fetch thành công |
| `gh repo view ThanhVu165/MLAi_VNG_A --json visibility,isPrivate` | PUBLIC, isPrivate=false |
| `gh pr list --repo ThanhVu165/MLAi_VNG_A --state open --json number,title,headRefName,baseRefName` | 0 PR tại baseline check |
| `python -X utf8 -` với assertions file/link/case/secret patterns | 7 Markdown; 32 link tương đối tồn tại; đủ ID X1–X4/Y1–Y4; không Gold trong case pack; không gold_labels; scoped sensitive patterns PASS |
| So sánh tám email trích từ comment Trello với tám blockquote Git | 8/8 exact match, X4 có K49 |
| `git show origin/dev:data/seed_docs/<ID>.json` + SHA-256/JSON assertions | 6 nguồn synthetic; 5 ACTIVE, 1 SUPERSEDED; manifest bên dưới |
| `git diff --cached --check` | PASS sau bỏ 8 Markdown hard-break trailing spaces |
| `git diff --cached --name-only` và full diff self-review | Chỉ 7 file trong scope; không production code, PII thật, đáp án Gold hoặc Set A/Set B |

Lần validation đầu gặp lỗi console encoding cp1252 khi in tiếng Việt; đã chạy lại
bằng UTF-8/JSON escaped output và hoàn tất assertions. Secret scan là heuristic
trên artifact mới cộng manual review, không phải audit toàn lịch sử repository.
Không chạy runtime tests/full suite vì thay đổi chỉ là tài liệu; không tạo LIVE
evidence hoặc khẳng định environment đã được kiểm chứng từ validation này.

## Corpus manifest

SHA-256 theo byte file từ baseline Git, không theo working-tree newline conversion.
Manifest này không cấp quyền tra cứu nguồn SUPERSEDED cho participant.

| File | Status | SHA-256 |
|---|---|---|
| HP-2026-1.json | ACTIVE | `765a65530d7edc78ef004c984ca5514a08a3720f332b47216f031eebcc6243bd` |
| PK-2026-204.json | ACTIVE | `5b24c84754a69e9fcb317589b8c0b2c3608ef26d40ceb1c3e48c454ca3d0a15d` |
| QDPQ-2026-01.json | ACTIVE | `8809607390cd0b261e1a2648bc21c6dcdeb2ce6f852ff55e06cb4af261c59aac` |
| RH-2026-101.json | ACTIVE | `7f2e3c2188a2613f95399324bb163c6e59ad279d0b0e5ff67bd587bf2d9b597e` |
| RL-2025-2363.json | SUPERSEDED | `7b0f41bc63dc9558b95a3573b681d79f3ff7af255b49d51c6051cd6381995012` |
| RL-2026-3150.json | ACTIVE | `fcfe0098e313bbf9a5c25e71bfdd08dae14e6ca27b0e4c27f77ae43dcca685f6` |

## Remaining risks và review request

- Gold Owner-side và equivalence chưa được Minh xác nhận. Chưa có Gold storage
  access proof; Coordinator chọn kho riêng và kiểm tra quyền Trello có Gold.
- Cases đã public trong Git; screening exposure là bắt buộc, vẫn có residual
  contamination risk. Participant không nhận lời giải hoặc toàn bộ reviewer pack.
- Environment M3-T03 trong handoff Trello trước ghi BLOCKED; chưa có runtime proof
  mới được xác nhận ở task này. Không coi DB setting/static audit là isolation PASS.
- Không có participant/recruitment/consent/session thật trong task; lịch chỉ dự kiến.
  Storage retention, owner/due, product/runtime revision và allocation cần chốt.
- N nhỏ, X/Y khác nội dung/domain và n=3 không cân bằng hết thứ tự. ACTIVE-only
  cần reviewer đánh giá lại độ khó; không claim đã có reviewer difficulty score.
- B2 runtime/human control cần kiểm chứng trên revision dùng thực tế trước study;
  tài liệu không khẳng định mọi chức năng đã VERIFIED_LIVE.

Minh review diff và Gold ở kho được cấp quyền, gửi **PASS** hoặc **CHANGE REQUEST**
có căn cứ. Coordinator quyết định acceptance/merge và GO study sau đủ unlock.
Production code/policy/schema/UI changes: **0**. Study sessions: **0**.
LIVE LLM/API calls: **0** (GitHub/Trello metadata/document operations không phải
provider execution). Không gửi email, không mở Set A/Set B, không merge.
