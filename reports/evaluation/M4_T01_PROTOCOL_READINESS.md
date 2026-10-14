# M4-T01 — Protocol & Set Readiness (14/10/2026)

**RESULT: PARTIAL_ONLY. Preflight: PARTIAL ONLY.** Owner: Minh — Evaluation/Logic.
Final Reviewer: Thư — Study/Coordination. Approver: Project Coordinator.
This is a reviewable preparation packet, not official evaluation, gate acceptance or GO-A.
The earlier local preflight report is preserved verbatim below as historical evidence.

## 1. Revision, preflight and scope

- Verified remote baseline: `eaaeea88a59618b49219a20ae01a3cf3227cec87` (fresh
  `git ls-remote`, then `git fetch origin dev`; not the prior session's SHA).
- Repository/remote: `ThanhVu165/MLAi_VNG_A`, HTTPS GitHub origin verified.
- Branch: `sprint/m4-t01-evaluation-protocol`, newly created from verified origin/dev.
- Initial checkout: local dev `1251c3c116a302d519dd71d6c31c3191874d785b`.
- Tested implementation SHA: `8ebb9f1091e132ce3238563eb220c89d8dc0e8d2`;
  post-commit unit rerun passed. Final evidence-only commit is the task branch tip
  (`git rev-parse HEAD`); exact tip is also recorded in PR #52 and final chat handoff.
- Initial index/tracked tree clean; pre-existing untracked mandatory report and two slide
  decks preserved. Slides are outside task scope and will not be staged.
- Pre-existing report SHA-256: `7f5a161209bbb47f08163c6058400d5f2648eb01706812fd542105bc0414e2c8`.
  Its original bytes are retained after the historical checkpoint marker below; the
  new leading report supersedes its old current-status claims, not its observations.
  Hash preservation refers to working-tree bytes; Git applies its configured line-ending
  filters to text blobs. The committed historical text is retained without editing.
- No local/remote task branch; exact-head GitHub search returned no task PR. Broad
  M4-T01 search returned planning PR #28 only. No duplicate PR is being reused/overwritten.
- Fresh dev adds runtime/replay/Docker changes; foundation documents, types, policy and
  harness inspected on this baseline. No tracked evaluation files existed at either
  target directory. Production/cassette/Gold/expected labels are unchanged by this task.

Authorized writes: new files under `docs/evaluation/`, report and validation evidence
under `reports/evaluation/`. No helper outside these directories, dependency change,
STATUS update, Trello write, merge, runtime tuning or official dataset execution.

## 2. Task status and ownership evidence

Read the six required repository documents, live Task Contract, its attachments (none),
full open-board list (no remaining page), and relevant cards/comments. Metadata APIs
are read-only coordination access, distinct from prohibited application/provider calls.

| Source | Current observation | Disposition |
|---|---|---|
| [T01](https://trello.com/c/7EhgcMDv) | IN PROGRESS; Minh Owner; no comments or attachments | Preparation authorized by supplied prompt and contract |
| [T05](https://trello.com/c/7nEZN4bu) | Done list; Coordinator comment `6ace71aff2970f5050080db3` transfers final acceptance ownership away from Minh | Prior T05 capacity blocker resolved; no assumption of semantic/integration PASS |
| [14/10 coordination](https://trello.com/c/4TKE89rg) | Explicit sequence Minh finishes T01, then Gold sign-off, then T02 only with GO-A | T01 is current implementation; T02 is dependency-locked |
| [T02](https://trello.com/c/ocB3GjyJ) | Card is IN PROGRESS, Owner Minh, no comments | Board/status inconsistency: not authorization to run; Coordinator should correct queue |
| [M5-T02](https://trello.com/c/6WBLroGb) | Owner Thư, Minh final reviewer | Membership is not a second Minh implementation task |
| [M6-T03 evidence](../sprints/M6_T03_REPLAY_VERIFY.md) | Historical BLOCKED first section, later final AC1–AC7 PASS candidate on integrated revision | Keep both; do not infer official M4 GO from a status label |

The latest coordination text resolves implementation priority to T01 despite T02's
premature column placement. No concurrent T02 implementation is performed here. If
Coordinator instead considers T02 genuinely active, stop T01 implementation until capacity
is resolved. No private-access authorization was supplied by the card or attachment list.

## 3. Set A provenance timeline and evidence matrix

Only public planning/report/Git metadata reviewed. No Set A cases/Gold read, no private
paths searched, no new Set A hash generated. The following timeline does not manufacture
a creation, freeze or tuning cutoff for a dataset we have not been authorized to inspect.

| Time/event | Evidence | What it proves / does not prove |
|---|---|---|
| Set A creation / author/source | NOT VERIFIED; no authorized attestation or registry receipt supplied | No inferred author or creation date |
| Set A Gold author / reviewer / finalization | NOT VERIFIED | No proof Gold was independent or fixed before M2 |
| Set A historical dataset/Gold hash/version | NOT VERIFIED | New current hash would not repair historical preregistration |
| 06/10, 02:27 +07 M2-related runtime commit | `124b06d6b36b7af5f3c822faa459e34a0a0ac020`, subject `fix(m2.2): clarify applicability extraction semantics` | Observable tuning-related history; not proven earliest M2 tuning cutoff |
| 06/10, 10:07 +07 Step5 DEV preregistration | `1c3822567bc86b9bf524d9d0cb729ae2e812ae91` | DEV history only, not Set A preregistration |
| 06/10, 14:25 +07 reported DEV LIVE results | `9e23f4bc2587d63c0b3268e37191cccdbcdea0bf` | Exposure of DEV inputs; not Set A exposure evidence |
| 09/10 M2 conditional closeout | [closeout](../sprints/M2_FINAL_CLOSEOUT_AND_M1_M2_CHECKIN_20261009.md) | DEV evidence limitations; no held-out claim |
| Set A exposure/family overlap vs DEV/REGRESSION/M5 | NOT VERIFIED; access/tuning log and comparison attestation absent | No evidence of contamination, no evidence of independence |
| 14/10 T01 current checkpoint | Fresh metadata reads and offline tests in this report | Current preparation only; no retroactive preregistration |

**Set A disposition: NOT VERIFIED**, not ELIGIBLE and not NOT ELIGIBLE. Stop affected
eligibility verification until Coordinator supplies an approved metadata-only route,
custodian/independent reviewer, original commitment receipts and actual earliest M2 cutoff.
Do not use M2/full15 or M5 Gold as replacement independent evidence.

## 4. Set B protection/seal assessment

**Seal: NOT VERIFIED. Evidence level: planning requirement only.** Roadmap requires
independent author/Gold/hash, sealed until a single frozen M7 run, no tuning exposure.
No custodian seal receipt, ACL/access log, independent attestation or approved method
was supplied. We did not open/list/decrypt sealed content or inspect its Gold.
This session's absence of reads does not attest historical seal integrity.

Required evidence: sanitized signed custodian receipt, immutable version/commitment,
independent roles, access-policy and exposure-log attestation. Keep private paths,
case IDs/content and confidential digests out of public reports when restricted.

## 5. Implementation, rubric and definitions

Created [protocol](../../docs/evaluation/M4_T01_PROTOCOL.md),
[machine schema](../../docs/evaluation/M4_T01_SCHEMA.json),
[pure offline validation helper](../../docs/evaluation/protocol_validation.py),
[synthetic tests](../../docs/evaluation/test_protocol.py).
All examples are newly constructed synthetic metadata, not held-out inputs or Gold.

Protocol defines three stop types, P01–P05, ERROR/TECHNICAL_ERROR, INVALID_INPUT,
missing/malformed outputs, route vs stop vs rule vs citation/grounding judgments,
all metrics with raw n/N and N=0, full-planned coverage/failure reporting, missing-outcome
bounds and Wilson 95%. P04 is a content stop; provider/parse/timeout failure is ERROR.
Existing `_matches()` checks ACTIVE IDs/card structure but not complete content quality.
Its exported expected labels/input-derived text must remain private during official runs.

MER=FN/(TP+FN); OER=FP/(TN+FP), restricted to valid business decisions. Precision/recall,
stop/rule correctness, reviewed-content coverage and all-planned technical/missing/invalid
counts are explicit. M3-T02's total-population adaptation design is preserved, labeled
separately; no conflicting frozen M4 formula found in spec/roadmap. Coordinator reviews
definitions before freeze. No numeric business gate or approved model/config is invented.
Wilson formula checked against [NIST](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm);
independent sampling/representativeness caveats apply. This is not measured model quality.

Manifest specification binds exact bytes/ordered inventory/Gold/protocol/runtime/corpus/
policy/prompt/adaptation/config, authorization and separate signed digest receipt. The
machine preparation manifest deliberately rejects execution authorization and leaves
official config null. Full private official evidence-envelope/collector requirements are
specified; the existing public Verify output is not sufficient by itself. Official
collector selection/authorization remains pending, not silently implemented in production.

## 6. Validation and environment

Environment: Windows, PowerShell 7.6.5, Git 2.55.0.windows.5, Python **3.11.16**,
pytest **8.3.3**, installed jsonschema **4.23.0**. No package installed/changed.
Validation mode: OFFLINE_UNIT plus two existing harness tests with test doubles.
No product replay, LIVE inference, official Set A/B run or cassette recording.

| Command/check | Expected | Actual / disposition |
|---|---|---|
| `git ls-remote origin refs/heads/dev refs/heads/sprint/m4-t01-evaluation-protocol` | Fresh remote SHA | PASS after approved network escalation; sandbox DNS initially failed |
| `git fetch origin dev`, branch/status/scope inventory | Current baseline, preserve untracked work | PASS; baseline above, task branch created; Git index mutation required escalation |
| `python -m unittest discover -s docs/evaluation -p test_protocol.py -v` | All deterministic checks pass | **13 PASS**; [raw log](M4_T01_UNIT_VALIDATION.txt) |
| First unit iteration | Timestamp without timezone rejected | **FAIL** `ProtocolTest.test_schema_case_and_timestamp`, `AssertionError: True is not false` at original line 170; jsonschema optional format check did not enforce timezone in this environment |
| Corrective change and same test expectations | Enforce timestamp contract | PASS: explicit schema timezone pattern plus stdlib calendar/timezone validation; no expected/Gold change |
| `python -m pytest tests/test_harness.py::test_paste_inbox_and_verify_share_the_same_pipeline verify/test_harness.py::test_same_escalation_type_with_wrong_rule_does_not_pass -q` | Shared pipeline and distinct rule check | **2 PASS** after escalation; initial run failed before collection with `TEST_DATABASE_ISOLATION`, WinError 5 resolving sandbox temp; no test ID failed |
| `python -m black --workers 1 --check --line-length 100 docs/evaluation/protocol_validation.py docs/evaluation/test_protocol.py` | Formatted | Closing validation below; formatter applied with approved escalation after sandbox stalls |
| `python -m ruff check docs/evaluation/protocol_validation.py docs/evaluation/test_protocol.py` | No lint findings | PASS |
| Links / schema / leakage / byte preservation / scope / `git diff --check` | No broken local links, invalid schema, matched secret patterns or scope violations | Closing evidence records final result |
| Private provenance/seal verification | Authorized historical artifacts | **NOT RUN / BLOCKED**; no approved method/evidence |
| Official Set A/B / full suite / product replay / LIVE latency | Outside T01 | **NOT RUN**; no inference about model quality or final gate |

Synthetic arithmetic fixture: 9 planned / 5 valid; TP=2 FN=1 FP=1 TN=1;
MER 1/3, OER 1/2; technical 2/9 (1 ERROR + 1 malformed), missing 1/9,
INVALID_INPUT 1/9; stop correct 1/3, rule correct 2/5. These are deliberate artificial
outcomes exercising errors, not an Exodia accuracy result. Wilson tests cover exact
references 0/1,1/1,1/2,5/10,0/10,10/10, all n for N=1..30, invalid counts and N=0.
Manifest tests reject altered bytes/count/IDs/Gold version/digests or claimed GO.

## 7. AC1–AC7 evidence matrix

| AC | Verdict | Evidence and limits |
|---|---|---|
| AC1 Provenance | **NOT VERIFIED** | Section 3 evidence matrix identifies every missing author/Gold/hash/exposure fact; no authorized historical evidence |
| AC2 Independence | **NOT VERIFIED** | Sections 3–4; DEV boundary documented but actual Set A separation/Set B seal not established |
| AC3 Metrics | **PASS** preparation candidate | Protocol sections 3–5; 13 synthetic tests, three stops, technical denominators, raw counts and Wilson; reviewer acceptance pending |
| AC4 Protocol | **BLOCKED** final lock | Draft protocol/manifest/output specification complete for preparation; official model/config/corpus/adaptation/collector/authorization not locked |
| AC5 Reproducibility | **PASS** offline scope | Source schema alignment, synthetic manifest/schema checks and 2 existing harness tests; no product replay/official collector claim |
| AC6 Safety | **PASS** session boundary | Read-only production, no private payload/Gold read, Set B untouched, no tuning/LLM/provider/email; final scope/privacy check required |
| AC7 Evidence | **PASS** preparation packet | Report, exact tested implementation SHA, logs, final checks and Draft PR #52 are present; human self-review/final acceptance pending, no DONE claim |

## 8. Risks, limitations and Coordinator decision packets

| Problem | Impact | Proposed solution | Responsible | Decision needed | Safe work remaining |
|---|---|---|---|---|---|
| PROVENANCE-01: historical Set A author/Gold/hash/cutoff/exposure absent | No independent eligibility or official GO-A | Supply sanitized original receipts and authorized independent attestation; do not backdate/new-hash | Coordinator + custodian; Thư review | Access method, cutoff and ELIGIBLE/NOT VERIFIED/NOT ELIGIBLE disposition | Protocol arithmetic/schema and draft review |
| SEAL-01: Set B seal/access history absent | Cannot claim final set sealed | Signed metadata-only seal/ACL/exposure receipt, no content opening | Coordinator + Set B custodian | Authorize metadata disclosure and access roles | Maintain no-access boundary |
| CONFIG-01: run/config/collector not authorized or frozen | AC4 not final; no official execution | Lock exact revision/corpus/policy/prompts/adaptation/provider/model/config, sampling/gates/budget and private collector | Coordinator + Runtime Owner + Minh | Approve exact configuration, envelope and separate GO-A | Review specification and offline synthetic checks |
| QUEUE-01: T02 premature IN PROGRESS | Possible owner-capacity confusion | Follow latest 14/10 T01-first sequence; correct queued T02 status | Coordinator | Confirm queue reflects dependency lock; no concurrent implementation | Finish current T01 prep packet |
| REVIEW-01: owner/final review pending | No task DONE or accepted protocol | Minh understands/self-reviews packet; Thư final review on exact SHA | Minh → Thư → Coordinator | Accept/change request/hold after actual human review | Draft PR and handoff text only |

No affirmative contamination evidence observed in permitted sources. Lack of access
does not prove independence or contamination. No runtime/schema/Gold changes proposed.
Full suite and live latency intentionally not run: production unchanged; unit/harness
checks cannot certify semantics, real-world representativeness or deployment readiness.

## 9. M4-T02 entry and owner handoff draft

**M4-T02 ENTRY: NOT READY (recommendation, not GO authority).** Requires accepted T01,
resolved Set A eligibility/original preregistration, private access/envelope/collector,
frozen exact protocol/Gold/runtime/corpus/policy/adaptation/config, M3 safety + Stable
Integration on matching revision, explicit Coordinator GO-A and mode/LIVE budget if used.
Set B remains reserved for separately authorized frozen M7. Failure thresholds and any
rerun policy need approval before the first official result, not after inspecting outcomes.

Prepared for Minh to post manually; Codex has not posted a comment or changed any card:

```text
[M4-T01] OWNER HANDOFF — PARTIAL_ONLY
Changes: review-candidate protocol, metrics/rubric, preparation manifest/output schema,
synthetic validator/tests and current report; prior blocked checkpoint retained.
Validation: 13 unit PASS + 2 existing offline harness tests PASS; initial schema and
sandbox failures disclosed. No official quality claim.
Evidence: task PR / exact tested SHA in closing report section; baseline eaaeea88a59618b49219a20ae01a3cf3227cec87.
Set A: NOT VERIFIED. Set B seal: NOT VERIFIED. Official config: PENDING AUTHORIZATION.
AC1/AC2 not verified, AC4 blocked lock; AC3/AC5/AC6 preparation evidence available.
LIVE/API calls: 0 LLM/provider/email; read-only Trello/GitHub/Git access used.
Human self-review: PENDING Minh. Request: Thư reviews draft; Coordinator supplies
metadata-only provenance/seal route and resolves configuration/queue/GO conditions.
No DONE, merge or GO-M4-T02 claimed.
```

**Next:** Minh self-review/handoff → Thư final review → Coordinator decisions.
Protocol PASS ≠ evaluation PASS; synthetic PASS ≠ held-out accuracy; PR ≠ DONE.

## 10. Closing evidence

- Implementation commit and exact post-commit tested SHA: `8ebb9f1091e132ce3238563eb220c89d8dc0e8d2`.
- [Draft PR #52](https://github.com/ThanhVu165/MLAi_VNG_A/pull/52), head
  `sprint/m4-t01-evaluation-protocol`, base `dev`; attached to this chat. Not merged.
- Final source revision: implementation SHA above; closing commit changes only this
  report/validation artifacts. Final branch-tip SHA is resolvable from PR #52 or
  `git rev-parse HEAD`; do not conflate the evidence commit with a new runtime test.
- Post-commit unit rerun: **13 PASS**, exact implementation commit; raw log refreshed.
- Existing harness tests: **2 PASS** on the same unchanged runtime baseline using the
  repository network/provider guard and isolated DB; no further rerun needed.
- Black (`--workers 1 --check --line-length 100`): **PASS**, two files unchanged.
  Ruff: **PASS**. Staged and branch `git diff --check`: **PASS**.
- [Validation inventory](M4_T01_VALIDATION_EVIDENCE.json): link/UTF-8/whitespace/secret-pattern
  scan passed; historical working-tree suffix digest preserved. Artifact digests are
  exact working-tree bytes at validation, not a historical dataset commitment.
- Scope self-review: exactly 8 task files, all under docs/evaluation and reports/evaluation;
  no production, policy, infra, verify, cassette, Gold, STATUS or interface changes.
  Both pre-existing slide decks remain untracked and excluded from staging/PR.
- Manual review found no private cases/Gold, credentials or PII in added task content.
  Pattern scan is limited to known credential signatures; no claim of perfect detection.
- Remote dev recheck after push still equals baseline. Task branch push verified.
- Agent implementation self-review completed. **Minh human self-review PENDING**;
  **Thư final review PENDING**; **Coordinator ACCEPT/DONE/merge/GO-A not granted**.
- **LLM/provider/email LIVE/API calls = 0**, attempts/tokens/cost = 0/0/0.
  Read-only Trello/GitHub/Git coordination APIs were used; Git push and PR creation
  were performed as explicitly requested. No official Set A/B execution.

Use the PR and SHA above in the owner handoff draft; status stays **PARTIAL_ONLY**.
Nothing in the historical checkpoint below overrides this current report.


<!-- HISTORICAL_CHECKPOINT_20261013_ORIGINAL_BYTES -->

# M4-T01 — Protocol Readiness: BLOCKED_AT_PREFLIGHT

Checkpoint: **13/10/2026, 21:10–21:15 UTC+07:00** (Asia/Saigon).
Task Owner: **Minh — Evaluation/Logic**. Final Reviewer: **Thư**.
Approver: **Project Coordinator**.

**RESULT: BLOCKED. PREFLIGHT: BLOCKED.** Đây là decision packet từ preflight,
không phải implementation/handoff hoàn chỉnh. Không tuyên bố task DONE,
protocol accepted, Set A eligible, hoặc M4-T02 unlocked.

## Baseline và phạm vi thực hiện

- Repository remote: `https://github.com/ThanhVu165/MLAi_VNG_A.git`.
- Verified remote `dev`: `1251c3c116a302d519dd71d6c31c3191874d785b`.
- Current branch giữ nguyên: `sprint/m6-t05-runtime-replay`.
- Inspected HEAD: `5f5ee5619143dfa627299c9faa5f89ad1fb013fd`.
- Tested SHA: **NOT RUN cho protocol/schema/metrics/harness**; inspected HEAD trên
  chỉ là revision của read-only preflight, không phải M4-T01 implementation SHA.
- Target branch `sprint/m4-t01-evaluation-protocol`: chưa tồn tại local/remote tại
  checkpoint; không tạo hoặc checkout vì capacity gate chưa được giải quyết.
- Working tree và index ban đầu sạch, không có untracked non-ignored files.
- Files changed trong phiên: chỉ report này, **untracked, chưa stage/commit**.
- Không gộp report vào PR M6-T05 hoặc thay đổi evidence lịch sử.
- **CHƯA CÓ PR/EVIDENCE BÀN GIAO M4-T01**: chưa được phép bắt đầu implementation.
  Chỉ có decision packet local này; không commit/push khi preflight chưa hợp lệ.

## Phương pháp và nguồn kiểm tra

Đọc `AGENT.md`, [TEAM_WORKFLOW](../../docs/TEAM_WORKFLOW.md),
[TEAM_HANDOFF](../../docs/TEAM_HANDOFF.md), [PROJECT_SPEC](../../PROJECT_SPEC.md),
[STATUS](../../STATUS.md), [SPRINT_ROADMAP](../../docs/SPRINT_ROADMAP.md),
Task Contract và toàn bộ comments hiện trả về của hai card. Kiểm tra board mở
(27 cards, `hasNextPage=false`), Git branch/status/remote/tree/diff và GitHub PR.
Không đọc private evaluation artifacts, `.env`, DB, Set A/B hoặc Gold.

| Evidence | Quan sát thực tế | Ý nghĩa |
|---|---|---|
| [M4-T01 card](https://trello.com/c/7EhgcMDv) | `IN PROGRESS - Đang thực hiện`; contract Owner Minh; lastActivityAt `2026-10-13T14:01:47.405Z`; 0 comments, không còn trang comments | Contract yêu cầu bắt đầu sau khi M6-T05 kết thúc hoặc trạng thái được giải quyết; không giao hai task IN PROGRESS đồng thời |
| [M6-T05 card](https://trello.com/c/7nEZN4bu) | `IN PROGRESS - Đang thực hiện`; contract Owner Minh; lastActivityAt `2026-10-12T10:53:35.726Z`; 2 comments, không còn trang comments | Capacity conflict vẫn tồn tại |
| M6-T05 comment action `6accb8f4b731380929f71f9a`, `2026-10-12T10:39:48.317Z`, Minh Thuw | “Giữ task IN PROGRESS, PR #44 Draft” | Cho phép tiếp tục Phase 2 offline của M6-T05; không phải exception cho M4-T01 song song |
| M6-T05 comment action `6accbc2f1051ed46587d019f`, `2026-10-12T10:53:35.684Z`, Minh Thuw | Cho phép đọc local M2 captures/manifest/provenance; không cấp LIVE | Không phải quyền đọc Set A/B/Gold hoặc giải quyết capacity conflict |
| [Draft PR #44](https://github.com/ThanhVu165/MLAi_VNG_A/pull/44) | `state=open`, `draft=true`, `merged=false`; head `5f5ee5619143dfa627299c9faa5f89ad1fb013fd`; base `dev` SHA như trên | M6-T05 chưa được mặc định DONE; PR mô tả recovery/acceptance còn blocked |
| GitHub search `head:sprint/m4-t01-evaluation-protocol` (all states) | 0 PRs trả về | Chưa tìm thấy PR đúng target branch; không khẳng định mọi PR lịch sử đều không liên quan |
| GitHub search `M4-T01` (all states) | PR #28 DOC-T01 có tham chiếu kế hoạch | Planning context, không phải M4-T01 implementation/acceptance |
| `git ls-remote origin refs/heads/dev refs/heads/sprint/m4-t01-evaluation-protocol` | Chỉ remote dev SHA ở trên | Remote dev được xác minh qua network; target branch chưa có |
| [M3-T06 card](https://trello.com/c/bCP71uSH), [M6-T03 card](https://trello.com/c/jXUJK7Ru) | Board hiện M3-T06 IN REVIEW, M6-T03 READY | Chỉ status snapshot; không chứng minh runtime/safety/integration acceptance |
| [M6-T05 report](../readiness/M6_T05_REPLAY_COVERAGE.md) và PR #44 | Thiếu pack provenance/replay acceptance; các limitations giữ nguyên | Dependency cho official evaluation chưa được chứng nhận trong phiên này |

Không tìm thấy quyết định giải quyết capacity trong contract/comments của hai card
đã đọc. Đây là kết luận trong các nguồn đã kiểm tra, không khẳng định không thể có
quyết định ở nơi khác. Board member có thể là reviewer; không tính mọi card gắn
Minh là task do Minh sở hữu. Hai contract trên đều xác định Minh là Owner.

Local `dev` branch `282c73b` cũ; cached `origin/dev` trùng SHA remote vừa xác minh.
Không checkout local dev cũ. `origin/dev` không có file dưới `docs/evaluation/`
hoặc `reports/evaluation/` tại checkpoint. Không thấy collision ở report path,
nhưng chưa hoàn tất ownership audit cho implementation bị chặn.

## Disposition dữ liệu và protocol

- **Set A: NOT_VERIFIED.** Audit provenance chưa bắt đầu do capacity stop;
  chưa kiểm author, Gold author/finalization, creation timestamp, historical
  hash/immutable record, exposure/test/tuning hoặc thời điểm bắt đầu M2 tuning.
  Không đủ evidence để kết luận VERIFIED_ELIGIBLE hoặc contamination/NOT_ELIGIBLE.
  Không tạo hash/timestamp mới làm bằng chứng preregistration cũ.
- **Set B seal: NOT VERIFIED.** Chưa được kiểm metadata/attestation được cấp quyền;
  không mở nội dung/Gold hoặc chạy case. Việc không đọc trong phiên này không
  chứng minh toàn bộ lịch sử Set B vẫn sealed.
- Quyền private artifacts: **NOT VERIFIED**, chưa có phương thức cấp quyền Set A/B
  được xác minh. Quyền M2 captures trên M6-T05 không tự mở quyền này.
- DEV/full15 đã test/tuning phải giữ DEV/REGRESSION theo roadmap; không đổi nhãn
  thành held-out. Không dùng M5 Gold thay Set A.
- Protocol/rubric/metrics/Wilson CI/denominators: **NOT RUN / chưa triển khai**.
- Manifest/output schema và harness review/validation: **NOT RUN**.
- Runtime mode phiên này: **READ-ONLY PREFLIGHT + LOCAL REPORT**, không có model run,
  synthetic run, LIVE hoặc REPLAY evaluation evidence. Không có model-quality metrics.
- Không chốt rubric/Gold/contract mới hoặc giải quyết multi-stop precedence trong
  phiên bị chặn. Các phần đó phải đối chiếu spec/policy khi được phép tiếp tục.

## AC1–AC7 evidence matrix

Mọi hàng có inspected SHA `5f5ee5619143dfa627299c9faa5f89ad1fb013fd`;
tested implementation SHA **NOT RUN**. Verdict chỉ áp dụng cho phiên này.

| AC | Verdict | Evidence path/source | Limitation | Remaining action |
|---|---|---|---|---|
| AC1 Provenance | NOT RUN; disposition NOT_VERIFIED | Report này, Disposition dữ liệu | Chưa có provenance timeline/audit | Sau capacity decision: audit bằng phương thức được cấp quyền, mapping lịch sử và disposition trung thực |
| AC2 Independence | NOT VERIFIED | Report này; roadmap M4 | Không mở data; separation/seal chưa kiểm chứng | Xác minh DEV/Set A/Set B separation, exposure history và seal metadata |
| AC3 Metrics | NOT RUN | Report này, Disposition dữ liệu | Chưa có protocol/rubric hoặc tính toán kiểm chứng | Định nghĩa trước run, synthetic expected results/Wilson/zero denominator/strata tests |
| AC4 Protocol | NOT RUN | Report này, Disposition dữ liệu | Chưa có manifest/config/output contract | Chốt manifest, modes, revision/corpus/policy/adaptation/failure handling |
| AC5 Reproducibility | NOT RUN | Report này, Validation | Không schema/harness tests | Read-only harness review; helper tối thiểu nếu cần; targeted offline validation |
| AC6 Safety | PASS trong phiên preflight | Report này, Phạm vi và Validation | Không phải chứng nhận lịch sử độc lập hoặc Set B seal | Duy trì boundary và quét diff thực tế khi implementation được phép |
| AC7 Evidence | PARTIAL; chưa đạt handoff | Report này; Trello/GitHub references | Local packet không có commit/PR/tests/reviewer sign-off | Valid preflight, report trong Draft PR, exact tested SHA, Minh self-review, Thư review |

## Validation thực tế

Environment: Windows, PowerShell **7.6.5**, Git **2.55.0.windows.5**.
Không import/chạy production, không cài dependency hoặc chạy full suite.

| Command/check | Result | Phạm vi |
|---|---|---|
| `git remote -v`, `git branch -avv`, `git rev-parse HEAD origin/dev` | PASS | Remote/branch/revision metadata |
| `git status --porcelain=v1 --untracked-files=all`, `git ls-files --others --exclude-standard`, `git diff --cached --name-only` | PASS pre-write | Working tree/index sạch; không kiểm nội dung ignored data |
| `git ls-remote origin refs/heads/dev refs/heads/sprint/m4-t01-evaluation-protocol` trong sandbox | FAIL environment | DNS không resolve GitHub; không dùng thất bại này suy ra remote state |
| Cùng `git ls-remote` với approved network escalation | PASS | Verified remote dev; không fetch/push/mutate repository |
| Trello `get`, `list_comments` hai cards; `list_by_board` open cards | PASS access / BLOCKED capacity | Hai task vẫn IN PROGRESS; comments không có trang còn lại |
| GitHub `get_pr_info` #44, `search_prs` M4-T01 và target head | PASS access | #44 Draft/unmerged; target branch PR không thấy |
| `git ls-tree -r --name-only origin/dev -- docs/evaluation reports/evaluation` | PASS inventory | Không có file trên baseline trong hai thư mục |
| `git diff --name-only origin/dev HEAD` | PASS read-only inventory | 14 existing M6-T05 files; không phải changes của phiên này |
| `git diff --check` | PASS tracked tree | Trước report; untracked report cần kiểm riêng |
| Report UTF-8/required fields/local links/whitespace/private-data patterns | PASS | PowerShell đọc UTF-8; đủ required fields/7 AC rows; 6 local links tồn tại; không trailing whitespace hoặc matched key/private-key/raw-email patterns. Manual review không thấy private evaluation content; pattern scan không chứng minh tuyệt đối mọi dạng secret |
| Provenance consistency/schema/rubric/synthetic metrics/Wilson/manifest/harness tests | NOT RUN | Capacity gate; không ghi SKIP hoặc PASS thay kết quả chưa có |
| Official Set A/B, runtime smoke/replay, full tests, LIVE/model probe | NOT RUN | Không được thực hiện trong preflight bị chặn |

Privacy: report chỉ chứa task/revision/status và metadata team đã được cung cấp;
không có raw email, case text, private Gold, participant data, credentials hoặc
original provider captures. Không sao chép toàn bộ board vào repo.
**LLM/provider/email LIVE/API calls = 0; attempts/tokens/cost = 0/0/0.**
Trello/GitHub connector reads và Git remote verification đã thực sự dùng network;
con số 0 trên không áp dụng cho read-only coordination API requests.

## Failure IDs, risks và Coordinator decision packet

**CAPACITY-01 (BLOCKER):** M6-T05 và M4-T01 cùng IN PROGRESS với Owner Minh;
không có exception/resolution trong sources đã kiểm. **NET-01 (resolved):** sandbox
DNS fail; remote verification đã thành công với read-only approved escalation.
**PROVENANCE-01 / SEAL-01 (NOT VERIFIED):** chưa audit Set A hoặc seal Set B.
**HANDOFF-01:** chưa có PR/tested protocol SHA, human self-review và final review.

Prepared text để **Minh tự đăng**; agent không đăng Trello hoặc nhắn Coordinator:

```text
[M4-T01] BLOCKER
Problem: BLOCKED_AT_PREFLIGHT — Minh còn M6-T05 và M4-T01 cùng IN PROGRESS.
Evidence: https://trello.com/c/7nEZN4bu | https://trello.com/c/7EhgcMDv;
M6-T05 comment 6accb8f4b731380929f71f9a giữ T05 active/PR #44 Draft;
https://github.com/ThanhVu165/MLAi_VNG_A/pull/44 vẫn Draft, open, unmerged.
Verified dev: 1251c3c116a302d519dd71d6c31c3191874d785b.
Impact: Không bắt đầu M4-T01 implementation; AC1–AC5 chưa kiểm chứng,
AC7 chưa đủ handoff; M4-T02 chưa mở.
Solution: Coordinator giải quyết trạng thái/capacity trước; không mặc định T05 DONE.
Responsible: Coordinator quyết định; Minh xác nhận/self-review; Thư review T01 sau handoff.
Decision Needed: Chọn ưu tiên/điều chỉnh trạng thái task hợp lệ, hoặc ghi exception
rõ cho capacity và authorization M4-T01. Nêu quyền metadata/private artifacts riêng.
Safe Work: Read-only preflight + local report/decision packet đã hoàn thành;
không branch/commit/push/PR T01, không sửa production, không đọc Set A/B/Gold.
Affected AC: AC1–AC5, AC7; AC6 boundary giữ trong phiên này.
LIVE/API: 0 LLM/provider/email; đã đọc Trello/GitHub/Git metadata.
```

Prepared owner handoff cho checkpoint **BLOCKED**, không phải READY_FOR_REVIEW:

```text
[M4-T01] OWNER HANDOFF
Result: BLOCKED — preflight only.
Changes: Local reports/evaluation/M4_T01_PROTOCOL_READINESS.md, untracked.
Validation: Git/Trello/GitHub metadata checks; protocol/schema/metrics NOT RUN.
Evidence: dev SHA 1251c3c116a302d519dd71d6c31c3191874d785b;
inspected HEAD 5f5ee5619143dfa627299c9faa5f89ad1fb013fd; no T01 PR/commit.
AC1–AC7: NOT RUN / NOT VERIFIED / NOT RUN / NOT RUN / NOT RUN /
PASS session boundary only / PARTIAL.
Risks: Capacity unresolved; Set A provenance/Set B seal/private access NOT VERIFIED.
LIVE/API Calls: 0 LLM/provider/email; read-only coordination APIs used.
Self-review: PENDING — Minh human sign-off chưa có.
Request: Coordinator capacity/authorization decision; Thư final review sau implementation.
```

## Điều kiện tiếp tục và mở M4-T02

M4-T01 chỉ tiếp tục sau quyết định capacity/authorization hợp lệ được kiểm lại trên
nguồn authoritative, remote dev/working tree/ownership được recheck và quyền dữ
liệu được xác định. Giữ report local ngoài M6-T05 staging; chỉ đưa vào đúng branch
M4-T01 khi được phép, rồi cập nhật theo evidence thực tế.

M4-T02 cần M4-T01 accepted, exact protocol/revision lock, Set A eligibility disposition
được Coordinator xử lý, M3 gate phù hợp, Stable Integration/runtime readiness,
Coordinator GO và quyền execution mode/LIVE riêng nếu cần. M4-T01 acceptance không
tự cấp LIVE hoặc mở official evaluation. Set B vẫn dành cho frozen M7 theo contract.

Agent review chỉ kiểm packet preflight; final tracked diff/index không đổi,
`git diff --check` PASS; chỉ report này untracked. **OWNER SELF-REVIEW: PENDING**.
Không có final review/Coordinator ACCEPT/DONE/merge trong phiên này.
