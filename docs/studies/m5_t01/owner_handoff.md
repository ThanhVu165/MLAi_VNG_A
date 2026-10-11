# M5-T01 — Correction handoff / Owner self-review

**Result:** PUBLIC DOCS READY FOR INDEPENDENT RE-REVIEW; CR-01/control-store
handoff **PENDING COORDINATOR DECISION**. Independent verdict: **CHANGE REQUEST
not yet closed**. Không DONE, không M5 PASS. Next Task Unlocked: **NONE**.

## Baseline, scope và evidence

- Repository: ThanhVu165/MLAi_VNG_A (PUBLIC).
- Verified remote dev: `16f584fa213416db30b247a431b92fffb94be075`.
- Existing branch: `sprint/m5-t01-review-corrections`;
  [existing Draft PR #32](https://github.com/ThanhVu165/MLAi_VNG_A/pull/32).
- Inherited correction HEAD: `debe7c33686f9dce2ff8180a68f653cc4c97621a`.
  Các commit correction trước đó là bản nháp đã đọc lại, không mặc định đúng.
- Coordinator cho phép continuation trong worktree riêng trên cùng máy local;
  không sửa workspace UI đang dirty, không tạo task/remote branch/PR mới.
- Scope: `docs/studies/m5_t01/` only. No production/policy/corpus changes.
- [Task Contract và Independent Review](https://trello.com/c/nSzHYb2a#comment-6acb507ae1bdd51c41d186e4).
  Baseline chuẩn bị lịch sử `282c73b7dbf4ac7bf027d5710cce6ed673ab80d1` thuộc PR #30;
  không dùng kết quả kiểm tra cũ để chứng nhận correction hiện tại.

## Correction disposition

| Request | Owner work / evidence | Remaining acceptance |
|---|---|---|
| CR-01 | Gold matrix DRAFT 8 case lưu local ngoài Git, có email hash, rule priority, source hash/locator, rationale và forbidden inference; không upload/commit | Restricted storage/access, Owner confirmation, Minh verification 8/8 và Coordinator approval PENDING |
| CR-02 | [Public structural assessment](xy_equivalence_assessment.md); detailed source/decision/rule/missing-fact/conflict/difficulty comparison trong local draft riêng | Không claim equivalence; bàn giao chi tiết và independent verdict PENDING |
| CR-03 | [Recruitment/consent](recruitment_consent.md): role verification log, exception gate, independent sharing choices, evidence storage/access/retention/deletion plan | Coordinator điền/duyệt kho, recipient/BTC requirements và dates trước recruitment; Minh re-review PENDING |
| CR-04 | Correction continuation được Coordinator cho phép; không rewrite/revert/merge | Coordinator xác minh merge authorization và ghi deviation/acceptance; chưa đóng workflow finding |

Matrix là source-based candidate, không phải Gold đã ký; không lấy output B2
hoặc cân bằng nhãn để chỉnh Gold. Nội dung Gold và chi tiết kho local không nằm
trong PR. Google Drive PRIVATE chỉ là đề xuất, chưa tạo kho/cấp quyền/upload.
Đây là blocker bàn giao, không giả định đã có reviewer access.

Chú giải có thể suy ra đáp án theo case đã bỏ khỏi public protocol/equivalence/
Gold workflow/handoff. Public chỉ giữ email synthetic, cấu trúc, quy trình và
mẫu trống. Git history từng chứa chú giải nên residual exposure còn tồn tại;
không tuyên bố xóa HEAD đã bảo mật lịch sử. Screening exposure bắt buộc và
Coordinator phân xử trước allocation. Participant không được phát reviewer pack.

## AC status sau correction

| AC | Owner deliverable | Status/gate |
|---|---|---|
| AC1 | Recruitment plan, eligibility, separate consent, evidence plan | Design corrected; independent review/storage approval pending; 0 participant confirmed |
| AC2 | B0/B2 protocol, unchanged S1–S4, structural X/Y assessment, limitations | Detailed equivalence review pending with Gold; no equivalence claim |
| AC3 | Existing measurement forms, n/N, missing/technical handling | Retained; không tạo results hoặc feedback |
| AC4 | 8 synthetic emails + local Gold candidate matrix | PENDING controlled handoff and independent 8/8 sign-off |
| AC5 | Study unlock checklist | Checklist retained; no runtime/isolation acceptance inferred |
| AC6 | Correction docs + this evidence handoff | Independent verdict/Coordinator acceptance PENDING |

## Validation trên correction cuối

Offline document validation, không import app/pipeline/Verify, không seed DB.
[Reproducible checks và kết quả](validation_report.md) chứa kiểm tra link, UTF-8,
case/sequence, corpus manifest, scope và diff. Private draft kiểm đủ 8 ID/hash/
locator và PENDING signatures cục bộ; không đăng đáp án hoặc artifact riêng lên
Trello/PR. Reviewer khác máy đọc được public evidence từ PR; private verification
chỉ có thể tiếp tục sau access-approved handoff.

Runtime tests/full suite: **NOT RUN (docs-only)**. Study sessions: **0**.
LIVE provider calls: **0**. GitHub metadata/Git operations chỉ phục vụ PR hiện có.
Không gửi email, không liên hệ participant, không mở Set A/Set B, không merge.

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

## Blockers và review request

1. Coordinator phê duyệt kho restricted/access trước khi bàn giao Gold cho Minh;
   kiểm thử allowed/denied account, parent inheritance và retention. Chưa có
   phương án bàn giao được kiểm chứng: **PENDING**, không Gold PASS.
2. Minh independent re-review CR-01/02/03; không dùng self-review thay verdict.
3. CR-04 workflow disposition và final acceptance thuộc Coordinator.
4. Study riêng cần runtime/isolation proof, revision/mode được duyệt, >=3 người
   thực sự phù hợp có identity/role evidence, lịch/consent và storage plan đầy đủ.
   Task này không xác minh các điều kiện đó hoặc mở khóa study.

Public docs sẵn sàng để review, toàn M5-T01 vẫn chưa được nghiệm thu. Commit SHA
và validation cuối được báo trực tiếp cùng PR, không đăng nhiều comment Trello.
