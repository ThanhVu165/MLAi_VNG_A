# M5-T02 — Study Readiness Report

## Result

`READY_FOR_COORDINATOR_REVIEW` — artifact readiness only. Không claim GO-STUDY,
M5-T02 DONE hoặc M5 gate PASS.

## Baseline và authorization

- Task ID: `M5-T02 — Recruitment, Consent & Study Readiness`.
- Authority/Owner/acceptance: Project Coordinator.
- Branch: `sprint/m5-t02-study-readiness`.
- Initial SHA: `2ce699c6a0d5b3d4ac6252a394468fb2aab329cd`.
- Evidence commit SHA: `52e7d8e9a26ec8af8a568ad833b76413e81d709a`.
- Pull Request: [#55](https://github.com/ThanhVu165/MLAi_VNG_A/pull/55), head
  `sprint/m5-t02-study-readiness`, base `dev`.
- `origin/dev` tại preflight: `2ce699c6a0d5b3d4ac6252a394468fb2aab329cd`.
- Initial tree: clean; task branch expected ahead of its remote.

## Methods và actual validation

Đã đọc contract/workflow/spec/roadmap và toàn bộ M5-T01 pack; đối chiếu Git bytes của
8 case, protocol, form và 6 seed; đọc cấu hình Compose cùng evidence M3/M6 hiện hành.
Không import app, mở DB, chạy Docker/pytest, đọc Gold/private material hoặc gọi network/
provider. Claims runtime được phân loại theo exact scope/SHA; evidence cũ không được nâng
thành Study runtime PASS.

Kết quả thực tế:

- Protocol: B0/B2, 8 case X1–X4/Y1–Y4, allocation X/Y và S1–S4 nhất quán.
- Corpus: 6 nguồn synthetic gồm 5 ACTIVE và 1 SUPERSEDED; hash nằm trong
  [environment check](../../docs/studies/m5_t02/protocol_and_environment_check.md).
- Measurement: case observation, condition summary, feedback, raw n/N,
  missing/interruption và improvement trace hiện diện.
- Participant: `0 confirmed / PENDING recruitment`; sessions `0`.
- Consent/storage plan: Coordinator đã phê duyệt custodian, private location, folder
  separation, access, retention, deletion và public/private boundary; actual consent/
  screening vẫn `NOT RUN`.
- Screening mechanism/process: `PASS` cho readiness; AC3 chính thức vẫn
  `NOT RUN / BLOCKED` vì confirmed participant = 0.
- Environment: prior offline/replay separation/safety evidence tồn tại; exact selected
  STUDY SHA/DB/mode/isolation `NOT VERIFIED`.
- Evidence package readiness: `PASS`; commit `52e7d8e9a26ec8af8a568ad833b76413e81d709a`
  đã được validation trên committed Git blobs và chứa report trong PR #55.
- LIVE/API/email thật: `0`.

## AC matrix

| AC | Status | Evidence |
|---|---|---|
| AC1 — Participants | FAIL | 0 confirmed; template P01–P04 không được tính |
| AC2 — Consent / Privacy | PASS candidate | Coordinator đã duyệt custodian/storage/access/retention/deletion; configuration proof và actual consent chưa chạy |
| AC3 — Gold / Case Exposure | NOT RUN / BLOCKED | Mechanism ready, nhưng actual screening `NOT RUN — 0 participants confirmed` |
| AC4 — Protocol | PASS | B0/B2, 8 cases, X/Y, S1–S4, 5 ACTIVE + 1 SUPERSEDED và forms khớp repo |
| AC5 — GO-STUDY Unlock Checklist | PASS | Checklist có READY/BLOCKED/NOT VERIFIED và không tự cấp GO |
| AC6 — Evidence | PASS | Evidence package, committed-SHA validation và PR #55 đã có; không suy ra DONE hoặc GO-STUDY |

## Validation

| Check | Result |
|---|---|
| Preflight branch/HEAD/origin-dev/clean tree | PASS |
| UTF-8 / NFC / Markdown structure / table width | PASS |
| Relative/internal links | PASS — 10 links resolved |
| Sensitive-data / obvious PII / secret heuristic scan | PASS |
| Case count và S1–S4 consistency | PASS |
| Corpus ACTIVE/SUPERSEDED, synthetic flags và hashes | PASS |
| Scope: đúng 6 artifact | PASS |
| `git diff --check` + whitespace check cho file untracked | PASS |
| Validation trên committed SHA `52e7d8e9...` | PASS — exact 6 files, clean tree, UTF-8/NFC và AC/privacy assertions |
| Runtime tests | NOT RUN — docs/readiness scope |
| Docker/Study runtime | NOT RUN — docs/readiness scope |
| Participant sessions / consent / screening | NOT RUN — participant count 0 |
| LIVE/API/email thật | NOT RUN — calls = 0 |

## Blockers

1. Chưa có >=3 participant thật đủ eligibility, role evidence, exposure screening,
   lịch và consent.
2. Private storage configuration/proof chưa được kiểm chứng trên kho thực tế.
3. Independent Gold sign-off của M5-T01 vẫn chưa verified trong post-merge audit.
4. Exact STUDY product SHA, Study DB/corpus_version, runtime mode/model và isolation
   trên candidate chưa được pin/rerun.
5. Coordinator chưa ban hành GO-STUDY.

## Risks

- Case/solution cues từng xuất hiện trong Git history; exposure screening là bắt buộc.
- X/Y lệch domain và source-reading burden; n nhỏ không cho phép claim causal effect,
  significance hoặc automation-bias prevalence.
- Offline/replay evidence trên revision/môi trường khác không tự chứng minh Study runtime.
- Misconfiguration quyền Google Drive có thể lộ PII/consent/role evidence; phải kiểm
  chứng `Restricted`, ba thư mục và access list trước recruitment.

## Privacy boundary

Project Coordinator là custodian. Google Drive PRIVATE `Restricted` tách
`01_consent_contact`, `02_eligibility_exposure` và `03_raw_study_results`; raw
identifiable data mặc định chỉ Coordinator truy cập. Public Git/Trello không chứa name,
contact, raw consent, role/exposure evidence hoặc raw identifying notes. Public artifacts
chỉ chứa participant code, aggregate metrics, de-identified results và sanitized feedback.
Retention tối đa 90 ngày sau study closure; deletion log không chứa PII. Gold giữ boundary riêng.

## Git / handoff

- Evidence commit: `52e7d8e9a26ec8af8a568ad833b76413e81d709a`.
- Push: `PASS` — branch `sprint/m5-t02-study-readiness`.
- PR: [#55](https://github.com/ThanhVu165/MLAi_VNG_A/pull/55), OPEN, nhắm `dev`.
- Final GO-STUDY: `BLOCKED — PARTICIPANT/CONSENT AND OTHER VERIFIED ENTRY CONDITIONS PENDING`.
- Recommended next step: Coordinator xác minh cấu hình Google Drive thực tế đúng
  `Restricted`, ba thư mục và quyền mặc định trước khi recruitment bắt đầu.
