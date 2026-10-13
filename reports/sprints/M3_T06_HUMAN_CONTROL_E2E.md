# M3-T06 — Human Control & Safety E2E Verification

## 0. Current disposition — Phase 2 validation 14/10/2026

**Current result: AUDIT EXECUTION COMPLETE / AC6 FAIL / PRODUCT GATE HOLD / M3-T06 NOT DONE.** Validation offline
được thực hiện trên integrated runtime `dev@8e32ee43158160ac3dda6a84906871f3e3c183f2`;
test/report checkpoint của PR #46 là `972b17157a9da35126a2ee24d35b4c3d1dfed7d8`.
Kết quả giữ nguyên **13 PASS / 3 FAIL** của suite T06 trên integrated runtime,
**107 PASS** targeted regressions, F01, V02, R11 và aggregate harness FAIL.

Các Mục 1–20 là checkpoint Phase 1 ngày 12/10/2026 và được giữ nguyên để bảo toàn lịch sử.
Mục 21–28 là disposition hiện hành, thay thế các kết luận readiness/AC cũ khi review PR #46.
`23/23 + 1/1` replay hits chỉ là hai lượt quan sát tách biệt; không phải complete E2E PASS.
Không LIVE/API, không gửi email, không sửa production/test/cassette/manifest/expected result.
Phiên 14/10 tiếp tục theo ủy quyền trực tiếp của Project Coordinator trong chat; Trello không được
truy cập hoặc cập nhật, vì vậy báo cáo không suy diễn một thay đổi quyền hay trạng thái board mới.

## 1. Metadata và disposition

Ngày 12/10/2026, Asia/Saigon. Owner: Vũ — Runtime/Safety. Final reviewer: Nam.
Approver: Project Coordinator. Session: Owner Implementation & Self-Review Support.
[Task Contract hiện hành](https://trello.com/c/E5cQmSXj), đã đọc toàn bộ qua connector,
card ở `READY - đã duyệt, nhận task`. Không ký thay Owner/reviewer/Coordinator.

**Result: PHASE1_CHECKPOINT / PARTIAL ONLY.** Phase 2 chưa đủ entry conditions.
Phát hiện lỗi audit R2 tái lập được; giữ nguyên các assertion FAIL và production.
Không tuyên bố M3-T06 DONE, M3 Gate PASS hoặc downstream GO.

## 2. Baseline dev

- Fetch `origin` thành công; remote `dev` kiểm lại bằng `git ls-remote`:
  `1251c3c116a302d519dd71d6c31c3191874d785b`.
- Checkout ban đầu: `sprint/m3-t01-approval-tests`, HEAD
  `da77e5400672fa3d14c00fcc6529cbe8c499e4c6`, working tree sạch.
- Không dùng HEAD của branch cũ làm baseline. Tạo task branch từ verified `origin/dev`.
- Task branch chưa tồn tại local/remote khi preflight; không reset/clean/stash/restore,
  không tạo worktree/clone, không sửa lịch sử.

## 3. Task branch và tested revision

Branch: `sprint/m3-t06-human-control-e2e`. Production/source tested SHA:
`1251c3c116a302d519dd71d6c31c3191874d785b`, cộng test mới trong working tree.
Validated test checkpoint: `ec75eb4f0bb272b5ef14cd9119a1f36458aac38d`;
post-commit classification chạy đúng SHA này (Mục 20).
Full 116 cases chạy trước commit trên source/test content giống checkpoint, có fingerprint đối chiếu.
Thay đổi sau checkpoint chỉ cập nhật metadata evidence trong report; test/production không đổi.
Không gọi SHA baseline là commit chứa test/report mới; report không thể tự chứa SHA của chính nó.

## 4. Source, ownership và lịch sử

Đã đọc `AGENT.md`, `docs/TEAM_WORKFLOW.md`, `docs/TEAM_HANDOFF.md`, `PROJECT_SPEC.md`,
`docs/SPRINT_ROADMAP.md`, `docs/RUNBOOK.md`, `STATUS.md`.
Technical expectations: spec §§3, 5.4, 8, 9; roadmap M3 Exit Gate; AGENT §§7–8.
Current milestone vẫn `M3_AUTHORIZED_WITH_CARRYOVER`, M2 vẫn conditional.

Preflight board IN PROGRESS đọc hết (`hasNextPage=false`): Minh M6-T05, Thư M5-T02,
Nam M6-T02; không có task IN PROGRESS khác của Vũ trên board hiện hành.
Không đổi trạng thái card hoặc đăng xác nhận cá nhân thay Vũ.
Open PR search: chỉ [Draft PR #44](https://github.com/ThanhVu165/MLAi_VNG_A/pull/44)
thuộc M6-T05. Phạm vi scripts/tests/readiness của PR44 không trùng hai file mới T06.

| Historical evidence đọc tại baseline | Kết luận sử dụng |
|---|---|
| `M3_T01_HISTORY_REPORT.md`, PR31 | 54 PASS/2 stale approval FAIL là lịch sử; không giữ verdict đó cho code mới |
| `M3_FIX_01_HISTORY_REPORT.md`, PR35 | Recipient/payload/corpus preview binding đã merge; tái kiểm regression hiện hành |
| `M3_FIX_02_HISTORY_REPORT.md`, PR36 | Atomic finalization/P04/fail-closed; tái kiểm bằng failsafe suite |
| `M3_FIX_03_HISTORY_REPORT.md`, PR37 | Atomic controls/correction; tái kiểm failure-injection suite |
| `M3_T03_HISTORY_REPORT.md` | Historical isolation chỉ static/partial; lần này kiểm hooks/runtime trên DB tạm |
| `SPRINT2_EVIDENCE_RECONCILIATION_20261012.md`, M3-T04 row | Latest historical handoff NOT_STARTED; không có audit matrix để tái sử dụng |
| `M3_T05_HISTORY_REPORT.md` | Source findings cũ về approval/atomicity/feedback traceability; không tự suy đã fix mọi gap |

Historical Trello URLs trong report cũ không được coi là quyền implementation mới.
Link M6-T05 cũ trong contract không truy cập được; board hiện hành có
[M6-T05](https://trello.com/c/MVi0chxI). Scope của T06 đã được xác minh trên card mới.

Được sửa: duy nhất test mới `tests/test_m3_t06_human_control.py` và report này.
Callers, fixtures, config, exports, production và tests lịch sử đều read-only.
Reuse fixture `runtime`, `approval_case` và `_email` trong `test_runtime_worker.py`;
fixtures không bị sửa. Không thêm dependency hoặc đổi `requirements.txt`.

## 5. Environment và methodology

Windows, CPython 3.11.9, SQLite 3.45.1, executable `.venv/Scripts/python.exe`.
Fresh local venv cài từ requirements: pytest 8.3.3, OpenAI 3.24.0, Streamlit 1.39.0,
Black 24.10.0, Ruff 0.7.1, PyYAML 6.0.2, sentence-transformers 3.2.1.
Resolved transitive versions: numpy 2.4.6, torch 2.14.1, transformers 4.57.6.
`pip check` PASS. Transitive dependencies không được lock toàn bộ; không claim hermetic build.

Isolation: `tests/conftest.py::pytest_configure` thiết lập fresh absolute SQLite path
trước import, `LLM_MODE=replay`, chặn socket connect/connect_ex/sendto/create_connection,
DNS ngoài literal IP, OpenAI/AsyncOpenAI. Per-test fixture dùng `tmp_path/runtime.db`.
`TEMP`/`TMP` chỉ vào `data/validation/m3-t06/tmp`; không dùng DEV/study/demo DB.
Restart tests tạo tiến trình Python mới đọc cùng DB, tự chặn socket/DNS/OpenAI và
mọi boundary LLM trước gọi `worker_tick()` hai lần. Không chỉ reload module.

Synthetic input dùng chung: sender `student@example.test`, subject `Hỏi lệ phí phúc khảo`,
body `Em muốn biết lệ phí phúc khảo.`, received_at aware UTC; synthetic source `rule`
ACTIVE từ 2020-01-01, citation `fee`, lệ phí 150.000 đồng. Không đọc/chỉnh Gold/Set A/B.

Evidence classes:

- Existing approval/controls/atomicity: real handlers + SQLite, stub LLM boundary.
- Worker/pipeline happy path: stubbed integration, deterministic product-state evidence.
- Restart: fresh-process SQLite integration trên state đã tạo bằng stub; không phải complete replay E2E.
- Error schema: payload sai đi qua validator R2 thật; provider response vẫn là stub.
- Missing-pack R2/R11: real adapter replay, real pipeline/worker, empty private cassette directory;
  upstream/human context synthetic; chỉ negative replay evidence.
- Streamlit AppTest hiện có: isolated UI integration; không phải browser multi-tab thật.

## 6. Human Control source-to-flow matrix

Tất cả rows dùng source SHA ở Mục 3. `T` = `tests/test_m3_t06_human_control.py`,
`W` = `tests/test_runtime_worker.py`, `A` = `tests/test_m3_atomicity.py`,
`F` = `tests/test_m3_failsafe.py`. Evidence là assertion DB/audit trong test được chạy;
commands và raw local artifacts ở Mục 12. Matrix disposition là product behavior ở lớp đã test.

| ID / Flow → input/precondition | Source reference | Expected → actual / persisted before → after | Audit / test evidence | Disposition / giới hạn |
|---|---|---|---|---|
| HC01 Global pause/resume; routine đã lên lịch, deadline hết | controls:62/72; dispatch:132 | Pause giữ PENDING_SEND/deadline qua process restart; resume cho gửi đúng một lần → đúng | PAUSE_AUTOMATION, RESUME_AUTOMATION, SEND_DISPATCHED=1; T `test_pause_resume_pending_send_survives_process_restart` | PASS SQLite/stub; chưa browser/runtime replay |
| HC02 Pause trước pipeline và human approval | pipeline; page:287 | P05 lúc pause → PENDING_APPROVAL; explicit approval → SENT dù global pause còn bật → đúng | HUMAN_APPROVED_SEND=1, không SEND_DISPATCHED; T `test_global_pause_allows_explicit_human_approval_and_persists` | PASS; pause tự động không chặn thao tác người theo RUNBOOK |
| HC03 Queue → human decision → R11 retry; global pause | dispatch:108; page:102/214; worker:204 | PENDING_SEND → AWAITING_HUMAN → HUMAN_DECIDED; soạn lỗi giữ choice/reason/job failed; retry → PENDING_APPROVAL; duyệt → SENT → đúng | CASE_QUEUED/HUMAN_DECISION/CASE_ERROR/CASE_RESUMED/HUMAN_APPROVED_SEND; T `test_queue_human_decision_resume_failure_and_retry` | PASS stub R11; resume case không xóa global pause |
| HC04 Cancel trước deadline và restart | dispatch:83 | PENDING_SEND → CANCELLED, deadline NULL; repeat bị từ chối → đúng | CANCEL_SEND=1, không send; T `test_cancel_before_send_survives_restart_and_rejects_repeat` | PASS; sau SENT không recall |
| HC05 Cancel thất bại giữa giao dịch | dispatch:83 | Inject audit exception → case/deadline/audit giữ nguyên; retry cancel thành công → đúng | No event khi rollback, CANCEL_SEND=1 sau retry; T `test_cancel_audit_failure_rolls_back_then_retry_succeeds` | PASS injected exception; không disk-full/power-loss |
| HC06 Correction sau gửi | dispatch:246; page:287 | Parent SENT nguyên vẹn; child correction PENDING_APPROVAL + parent_case_id; không tự gửi; explicit child approval → SENT → đúng | CORRECTION_CREATED(parent/output_ref child), HUMAN_APPROVED_SEND(child); T `test_correction_preserves_sent_parent_and_requires_approval`; A correction tests | PASS; correction là thư mới, không undo/recall |
| HC07 Terminal review operations | page:253/287/336 | SENT không cho edit/return/approve stale preview; case/draft/audit không đổi → đúng | T `test_terminal_sent_rejects_stale_review_operations[edit/return/approve]`; W finalized override/requeue | PASS deterministic; không suy mọi terminal enum đã exercise |
| HC08 Stale payload | page:59/139/287 | Preview A; đổi subject/body/citations/draft ID → từ chối, giữ PENDING_APPROVAL, không success audit → đúng | W `test_m3_t01_stale_preview_rejected`; saved-draft fresh-preview test | PASS SQLite; exact fields của contract hiện hành, không đổi fingerprint algorithm |
| HC09 Stale recipient | page:287 | Recipient đổi sau preview hoặc sau validation trước lock → từ chối; fresh preview mới được duyệt → đúng | W `test_m3_t01_recipient_change_requires_new_preview`, `test_m3_fix_01_change_after_validation_before_lock_rejected`, fresh-preview test | PASS; historical defect không tái hiện trong scenarios này |
| HC10 Stale corpus | page:139/287 | Corpus đổi sau preview/trong validation/trước lock → từ chối; fresh preview mới có quyền → đúng | W corpus-change tests + FIX01 tests, no approval event for stale preview | PASS active corpus version; chưa kiểm policy file hot replacement riêng |
| HC11 Repeated/double/concurrent approval | page:287 | Hai session cùng preview cạnh tranh → một SENT + một rejection; duplicate/retry không gửi thêm → đúng | W `test_m3_t01_approval_retry_is_rejected_and_audit_matches`, `test_m3_t01_two_sessions_concurrent_approval`, approval-vs-return/edit tests | PASS Barrier/Event synchronized schedule; không claim exhaustive race proof/browser multi-tab |
| HC12 Approval audit rollback | page:287 | Inject audit exception → PENDING_APPROVAL và no success event → đúng | W `test_m3_t01_audit_failure_rolls_back_approval` | PASS injected exception |
| HC13 Atomic pause/correction/persistence/send | controls; dispatch; pipeline finalization | Failure injection rollback state/audit; valid snapshot send once; incomplete snapshot không cấp quyền gửi | A suite; F suite; W dispatch audit failure | Targeted result ở Mục 7; không hardware failure test |
| HC14 Interrupted process/lease | worker:108/128 | PROCESSING expired → ERROR/TECHNICAL_ERROR; HUMAN_DECIDED expired giữ quyết định, job failed; second tick không duplicate → đúng | CASE_ERROR=1; T `test_expired_worker_lease_recovered_in_new_process[PROCESSING/HUMAN_DECIDED]`; W recovery tests | PASS fresh process; không kill -9 tại mọi instruction |
| HC15 TECHNICAL_ERROR R2 timeout/schema | extract:270; pipeline:727 | ERROR/TECHNICAL_ERROR, no escalation/send, display đúng; một transition event expected → actual CASE_ERROR=2 | T `test_technical_error_state_audit_and_display_are_consistent[extract_timeout/extract_schema]`, DB properties | **FAIL audit**, state/display fail-safe PASS |
| HC16 Guard technical exception | pipeline:727 | ERROR/TECHNICAL_ERROR, no business escalation/send, CASE_ERROR=1 → đúng | T `[guard_exception]`; F real guard service error | PASS classification, injected failure |
| HC17 Missing real replay R2/R11 | llm:534; extract; worker:204 | R2 → ERROR/no draft/send nhưng 2 error audits; R11 → HUMAN_DECIDED/job failed/no draft/send/choice giữ nguyên và 1 error audit | T `test_real_replay_missing_pack_fails_safe[R2/R11]`, recorded prompt hashes | R2 audit FAIL; R11 fail-safe PASS; complete runtime NOT VERIFIED |
| HC18 Complete Routine/Authority/Fact/R2/R11→preview→approval→send/restart | pipeline/resume/page/worker | Valid pack + pipeline thật + business outcomes cần được đối chiếu | Pack không tồn tại hợp lệ; Mục 8–9 | **NOT VERIFIED**; không dùng HC01–17 thay AC6 |

## 7. Phase 1 validation results

Initial new suite: **13 PASS / 3 FAIL / 0 SKIP**, 99.79s, pytest exit 1.
Refined classification run (state/UI assertions trước audit assertion, expected giữ nguyên):
**2 PASS / 3 FAIL / 11 deselected**, 53.79s. R2 audit defect tái hiện ở cả hai lần.
Raw classification XML chứa DB/audit fields trước failing assertion.

Final-state new suite: **13 PASS / 3 FAIL / 0 SKIP**, 150.77s, exit 1.
Current-source existing targeted regressions: **100 PASS / 0 FAIL / 0 SKIP**, 475.31s, exit 0:
runtime worker 34, atomicity 33, failsafe 21, database isolation 5, offline isolation 7.
Distinct final cases: **113 PASS / 3 FAIL / 0 SKIP**, 116 executed.
Black/Ruff/diff checks PASS; `pip check` PASS. Full suite NOT RUN.
Không tổng số các rerun như independent cases hoặc cộng reported historical counts.

## 8. Phase 2 readiness/provenance

Read-only `origin/sprint/m6-t05-runtime-replay` tại
`cac427346adf96f1696d83637769c1cee7c0140a`, đối chiếu PR44.
Git diff production/core/corpus/policy/infra/pages/Verify/config/requirements với baseline T06 rỗng.
Đã đọc pack report/manifest/inventory từ Git object; không checkout/cherry-pick hoặc chạy tool chưa merge.
Manifest/report thuộc Minh, không sửa. Task này không tự cấp quyền dùng unmerged checkpoint.

M6-T05 reported: 0 valid cassette, 7 R2 + 1 R11 misses, recording BLOCKED,
9 capture paths/checksums không phải complete prompt-keyed cassettes.
“116” là offline PASS test count, không phải số cassette.
Inventory hiện hành không có `tests/cassettes/` files ở baseline hoặc branch T05.
Provider/model/source fingerprint compatibility không thể chứng nhận response provenance khi không có pack.
Chưa có pack được nghiệm thu hoặc quyền Phase 2 dùng unmerged pack.

**Entry NOT MET:** thiếu genuine response/provenance/coverage. Dừng positive runtime Phase 2;
không record/re-key/fabricate cassette, không LIVE, không lấy M2 capture làm cassette.

## 9. Phase 2 runtime dispositions

| Required flow | T06 actual runtime evidence | Disposition |
|---|---|---|
| Routine / AUTHORITY_REQUIRED / FACT_UNRESOLVED | Không có valid pack cho complete chain | NOT VERIFIED |
| R2 extraction | Negative replay thật: missing cassette → ERROR; duplicate error audit | Coverage FAIL trong empty-pack probe; semantic success NOT VERIFIED |
| R11 human decision/resume | Negative replay thật: missing cassette → job failed, HUMAN_DECIDED/choice giữ nguyên | Recovery fail-safe PASS; successful R11 NOT VERIFIED |
| Draft/preview/approval/simulated send | Có deterministic/stub evidence riêng ở Phase 1 | Positive replay E2E NOT VERIFIED |
| Persistence/audit/restart của complete runtime chain | Có isolated SQLite/fresh-process evidence riêng | AC6 runtime chain NOT VERIFIED |

Actual T06 negative replay hashes (không phải recovered pack):

- R2: `df52ddc0217d09d8fe5b02a1b6d84e142ff5dfe815a7bc5acb615bac85eace88`.
- R11: `d805d04031b1e21b4cea28e59d3eeddd1d46ed865e59efcb5beea4ddfb8c7297`.

Mỗi probe đi qua một `_replay` miss. Đây không phải các 8 T05 misses hoặc coverage estimate.
Test R11 fixture tạo human context synthetic; không chứng minh upstream Authority/Fact extraction.

## 10. AC1–AC7 mapping

Dispositions dưới đây đánh giá completeness của **audit checkpoint**, tách product correctness.

| AC | Evidence | Disposition | Missing / limits |
|---|---|---|---|
| AC1 Matrix | HC01–18, source/test/DB/audit refs | PASS Phase 1 matrix | Runtime rows vẫn NOT VERIFIED |
| AC2 Approval | HC08–12, W regression suite | PASS deterministic | Full runtime/browser E2E chưa có |
| AC3 Controls | HC01–07,13–14 | PASS deterministic | Undo/recall không được sản phẩm hỗ trợ; correction đã tách đúng nghĩa |
| AC4 Persistence/audit | HC05–06,11–17, A/F/W suites | PASS defect evidence; **product audit FAIL** | Duplicate CASE_ERROR cần remediation; hardware failure chưa test |
| AC5 Error classification | HC15–17, 3 preserved failing IDs, DB/UI props | PASS classification/evidence | State đúng/audit sai; không đồng nhất thành UI mismatch hoặc unsafe send |
| AC6 Runtime | Mục 8–9 | **NOT VERIFIED** | Valid replay pack và successful complete chain thiếu |
| AC7 Delivery | Commands/env/SHA/report/tests + Draft PR46 | PASS checkpoint delivery | Chưa phải final task handoff; Owner/final reviewer sign-off pending |

## 11. PASS/FAIL/NOT VERIFIED breakdown

- Three failing test IDs chứng minh **một audit defect**, không phải ba independent product defects.
- State/send safety và display assertions chạy trước audit FAIL trong final tests.
- Guard exception, R11 resume failure/restart giữ domain state đúng theo contract.
- Complete runtime/business semantic verification: NOT VERIFIED; không suy pytest PASS thành product PASS.
- Final counts và command-level exit codes ở Mục 12/20.

## 12. Reproducible commands và artifacts

Từ repository root, sau cài môi trường Python 3.11:

```powershell
python -m venv .venv
& .venv/Scripts/python.exe -m pip install -r requirements.txt
New-Item -ItemType Directory -Force data/validation/m3-t06/tmp | Out-Null
$env:TEMP=(Resolve-Path data/validation/m3-t06/tmp).Path
$env:TMP=$env:TEMP
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONIOENCODING='utf-8'

& .venv/Scripts/python.exe -m pytest -q tests/test_runtime_worker.py tests/test_m3_atomicity.py tests/test_m3_failsafe.py tests/test_database_isolation.py tests/test_offline_isolation.py --junitxml=data/validation/m3-t06/regressions.xml -o junit_family=legacy
& .venv/Scripts/python.exe -m pytest -q tests/test_m3_t06_human_control.py --junitxml=data/validation/m3-t06/final-new-tests.xml -o junit_family=legacy
& .venv/Scripts/python.exe -m pytest -q tests/test_m3_t06_human_control.py -k 'technical_error or real_replay' --junitxml=data/validation/m3-t06/error-classification.xml -o junit_family=legacy
& .venv/Scripts/python.exe -m black --check --line-length 100 tests/test_m3_t06_human_control.py
& .venv/Scripts/python.exe -m ruff check tests/test_m3_t06_human_control.py
& .venv/Scripts/python.exe -m pip check
git diff --check
```

Final-suite stdout/stderr được redirect vào `data/validation/m3-t06/final-new-tests.log`;
pytest exit code giữ nguyên. Error-classification wrapper in ra tail log và kết thúc shell 0;
**pytest bên trong là FAIL/exit 1**, xác minh từ 3 failure nodes/XML và summary, không ghi PASS.
Local XML/logs trong ignored `data/validation/`; không commit DB/cache/venv.
Reviewer có committed tests, matrix, hashes, actual DB/audit excerpt và commands để tự tái lập.
Không coi local artifacts là đã có trong PR; report này là reviewer-accessible evidence summary.

Setup failures giữ minh bạch: system Python thiếu openai (collection NOT RUN);
pip trong sandbox lỗi DNS, cài escalated thành công; sandbox `Path.resolve(strict=True)` trên
fresh temp directory bị WinError 5 nên offline tests chạy với quyền thực thi được duyệt.
Không bỏ isolation hook hoặc dùng DB mặc định để vượt lỗi.

## 13. Failed IDs / traceback

```text
tests/test_m3_t06_human_control.py::test_technical_error_state_audit_and_display_are_consistent[extract_timeout]
tests/test_m3_t06_human_control.py::test_technical_error_state_audit_and_display_are_consistent[extract_schema]
tests/test_m3_t06_human_control.py::test_real_replay_missing_pack_fails_safe[R2]

assert actions.count("CASE_ERROR") == 1
AssertionError: assert 2 == 1
actual actions: ['CASE_RECEIVED', 'CASE_SANITIZED', 'CASE_ERROR', 'CASE_ERROR']
```

Extract timeout reproduction: `core.extract.call_json` trả failed LLMResult synthetic timeout;
schema reproduction: successful LLMResult có `{"language":"invalid"}`, thiếu requests;
validator retry 2 lần rồi error `requests phải là mảng`. Negative R2 dùng adapter thật và empty directory.
Exceptions ở `_process_case`, `core/pipeline.py:520`, được fail-safe handler xử lý.
Các expected assertions không xfail/skip và không đổi thành expected duplicate audit.

## 14. Safety findings / severity

**F01 — MEDIUM / P2, audit consistency FAIL; không quan sát fail-open.**
`core/extract.py:270–277` ghi CASE_ERROR khi extraction thất bại rồi trả llm_error;
`core/pipeline.py:520` raise, fail-safe handler `:727` ghi CASE_ERROR lần nữa khi chuyển ERROR.
Expected theo AGENT §8: mỗi state transition đúng một event. Actual: hai terminal-action events
cho một lỗi R2 trong một lần process. Không có escalation business, schedule hoặc send.
Ảnh hưởng: người đọc audit/consumer đếm CASE_ERROR có thể hiểu sai số lần lỗi/transition.
Severity là đề xuất kỹ thuật, không quyết định thay Coordinator.

Không có critical unsafe-send defect tái hiện trong phạm vi tests đã hoàn tất.
Điều này không chứng nhận production an toàn tuyệt đối hoặc runtime chain PASS.

## 15. Persistence/audit và TECHNICAL_ERROR classification

Actual persisted excerpt từ XML properties:

```json
{
  "status": "ERROR",
  "decision": "ERROR",
  "rule": "TECHNICAL_ERROR",
  "display": "Chưa xử lý được",
  "audit": [
    {"actor": "SYSTEM", "action": "CASE_ERROR", "rule_id": null,
     "reason": "Trích xuất dữ kiện thất bại: synthetic timeout"},
    {"actor": "SYSTEM", "action": "CASE_ERROR", "rule_id": "TECHNICAL_ERROR",
     "reason": "Chưa xử lý được email do lỗi dịch vụ hoặc dữ liệu hệ thống. Hãy kiểm tra kết nối và chạy lại; chưa có thư nào được gửi."}
  ]
}
```

Classification F01: **state đúng, audit duplicate**; UI label/helper và snapshot reload đúng.
Guard exception: state/audit/UI đều đúng, fail-safe. Resume failure: HUMAN_DECIDED được giữ,
job failed + CASE_ERROR; đây là contract-preserving recovery, không phải domain-state mismatch.
Historical F persistence injection có trường hợp ERROR write cũng thất bại: còn PROCESSING/P05 cũ
nhưng không finalization/deadline/quyền gửi; báo bounded fail-safe, không claim DB state ERROR luôn lưu được.

Approval event kiểm case/actor/time/sources/corpus; payload/recipient so trực tiếp trong write transaction.
Event schema không lưu riêng immutable recipient/draft fingerprint; không tự đổi audit interface hoặc
claim immutable action payload record ngoài các fields hiện có.

## 16. Remaining gaps / limitations

Positive complete replay E2E, Authority/Fact semantic outcomes, cited R11, successful runtime restart chain
đều NOT VERIFIED. Không LIVE/email, không browser multi-tab thật, không load stress/disk-full/power-loss,
không full suite/type-check/deploy. Concurrent approval tests dùng Barrier/Event, xác minh các lịch chạy
được dựng chứ không chứng minh mọi race. Không riêng biệt thay policy YAML sau preview.
Correction gửi một email đính chính mới; original SENT không bị thu hồi.

## 17. Remediation và blockers

| Problem | Impact | Evidence | Proposed solution / responsible | Decision needed | Safe work continuing |
|---|---|---|---|---|---|
| F01 duplicate CASE_ERROR | Audit row product FAIL; counts/trace misleading | 3 failed IDs; extract:270, pipeline:727, DB excerpt | Runtime Owner Vũ; deduplicate transition logging qua task production riêng, giữ diagnostic reason | Coordinator chốt scope/Owner/reviewer và product gate disposition; không tự mở T07 | Report/tests/checkpoint PR, independent validation |
| Valid replay pack absent | AC6 và complete runtime chưa được kiểm chứng | T05 PR44/manifest inventory + T06 negative hashes | Minh M6-T05 cung cấp genuine pack/provenance/config/revision + approval | Coordinator quyết định recovery/record scope/budget hoặc accepted pack use; T06 không xin LIVE mặc định | Phase 1 deterministic, error classification, report |

## 18. Downstream impact

Không tự mở Stable Integration, official M4/M5 hoặc M3 gate. Cần xử lý audit disposition,
valid runtime evidence trên integrated/authorized SHA và Coordinator GO. T06 không giải quyết adaptation
feasibility STOP, deployment hoặc người dùng study.

## 19. Self-review / human handoff

- [x] Codex kiểm scope: hai file mới; không sửa production/tests lịch sử/cassette/manifest.
- [x] Expected theo source contract; preserved FAIL, không skip/xfail để xanh.
- [x] SQLite riêng, subprocess offline traps; synthetic inputs, không secret/real PII/Gold.
- [x] Phân biệt source/stub/SQLite/replay-negative/runtime-positive evidence.
- [x] Report ghi failure, source revision, env, commands, limits và proposed Owner.
- [ ] Vũ đọc/hiểu diff, matrix, error classification và tự xác nhận Owner self-review.
- [ ] Code Review sau khi Vũ xác nhận self-review, theo chỉ dẫn trong phiên.
- [ ] Nam independent final review exact SHA.
- [ ] Coordinator acceptance/DONE/merge authorization.

Agent Review/Anti chưa gọi: chưa quan sát critical safety defect cần phản biện riêng.
AI support không thay các checkbox human sign-off.

## 20. Checkpoint commit/PR và actual calls

Test/report checkpoint: [`ec75eb4f0bb272b5ef14cd9119a1f36458aac38d`](https://github.com/ThanhVu165/MLAi_VNG_A/commit/ec75eb4f0bb272b5ef14cd9119a1f36458aac38d).
Delivery: [Draft PR #46](https://github.com/ThanhVu165/MLAi_VNG_A/pull/46), base `dev`.
Post-commit validation trên exact `ec75eb4...`: **2 PASS / 3 FAIL / 11 deselected**, 26.68s, exit 1,
cùng ba failed IDs. Không thay thế hay cộng rerun này vào 116 distinct cases.
Command: lệnh classification ở Mục 12, đổi XML output thành `data/validation/m3-t06/post-commit.xml`;
stdout/stderr `post-commit.log`, wrapper giữ đúng pytest exit 1.
Draft PR chỉ dành cho Phase 1 checkpoint, không tự chuyển ready hoặc merge.
Final test file SHA-256:
`ee51d4c691464f7f1884f74d7c11cd92f3a26324646cab97480df2fb5ebaad7b`.
Local raw artifact SHA-256:

| Artifact | SHA-256 |
|---|---|
| regressions.xml | `196ce68b544b393564d06c33ea7edd0d33e1fe0f194f634d6b1dff68533d2715` |
| final-new-tests.xml | `954e4f3d80062b0bcef47f753e0b356ba62d04983358b8a3531b7e06e8103e91` |
| final-new-tests.log | `085c0aef174a033ced8159c56c1f86a48b51209be84cadd5d05ca5d628c44cb4` |

Application LLM/provider LIVE calls: **0**. Real outbound email calls: **0**.
Synthetic send chỉ chuyển SQLite state + audit. GitHub/Trello evidence reads và pip dependency downloads
không phải application LIVE calls. Không model availability probe, recording hoặc cassette conversion.

Owner cần dùng trạng thái `PHASE1_CHECKPOINT / PARTIAL ONLY` khi tự báo tiến độ;
chưa đăng READY_FOR_REVIEW toàn task hoặc Self-review COMPLETED trước khi thực sự xác nhận.
Next step: review checkpoint/F01; Minh cung cấp pack hợp lệ; tiếp tục Phase 2 trên cùng branch/PR
sau reverify remote/source/config/provenance/permissions.

## 21. Phase 2 baseline và preflight hiện hành

Phase 2 được tách khỏi Phase 1 như sau:

- Phase 1 là test Human Control deterministic/stub và negative missing-pack đã commit trong PR #46.
- Phase 2 là validation read-only của test T06 và replay runtime trên source tích hợp `dev`.
- Source under test: `8e32ee43158160ac3dda6a84906871f3e3c183f2`.
- T06 test/report checkpoint: `972b17157a9da35126a2ee24d35b4c3d1dfed7d8`.
- Merge base của hai checkpoint: `1251c3c116a302d519dd71d6c31c3191874d785b`.
- Remote `dev` và remote `sprint/m3-t06-human-control-e2e` lần lượt trỏ đúng hai SHA trên
  tại thời điểm preflight. Working tree sạch trước khi chỉ sửa báo cáo này.
- Triple-dot diff của PR chỉ có `reports/sprints/M3_T06_HUMAN_CONTROL_E2E.md` và
  `tests/test_m3_t06_human_control.py`; không có production/cassette/manifest change.
- macOS 26.6 arm64; Python 3.11.17; SQLite 3.53.1; pytest 8.3.3;
  Streamlit 1.39.0; OpenAI 3.24.0; Git 2.50.1.
- Cấu hình application: `LLM_MODE=replay`, `LLM_CACHE=0`, không API key, socket/provider LIVE
  bị chặn; DB, pytest temp và output ở ngoài repository.
- Có 24 cassette trên integrated source; cả 24 hash khớp manifest, 24 hash duy nhất,
  model `gpt-6-luna`. Replay hit không tự chứng minh business outcome.

Không chạy `pip check`: `.venv` hiện tại không có module `pip`; dependency imports và installed
metadata cần thiết cho validation đều đọc được. Không cài thêm phần mềm theo restriction.

## 22. Commands đã chạy và kết quả Phase 2

Các lệnh dưới đây được chạy từ snapshot read-only
`/Users/nguyenvoviettrinh/exodia-t06-work/validation/m3-t06-phase2/integrated-source`
trừ các lệnh Git preflight chạy tại repository. Giá trị environment áp dụng cho mọi runtime run:
`LLM_MODE=replay`, `LLM_CACHE=0`; application network, `_call_live` và cache-load bị trap.

```bash
git ls-remote origin refs/heads/dev refs/heads/sprint/m3-t06-human-control-e2e
git merge-base 8e32ee43158160ac3dda6a84906871f3e3c183f2 972b17157a9da35126a2ee24d35b4c3d1dfed7d8
git diff --name-status 8e32ee43158160ac3dda6a84906871f3e3c183f2...972b17157a9da35126a2ee24d35b4c3d1dfed7d8

env LLM_MODE=replay LLM_CACHE=0 \
  /Users/nguyenvoviettrinh/exodia-t06-work/MLAi_VNG_A/.venv/bin/python -m pytest -q \
  tests/test_m3_t06_human_control.py \
  --basetemp=/Users/nguyenvoviettrinh/exodia-t06-work/validation/m3-t06-phase2/pytest-phase1 \
  --junitxml=/Users/nguyenvoviettrinh/exodia-t06-work/validation/m3-t06-phase2/m3-phase1-on-integrated.xml

env LLM_MODE=replay LLM_CACHE=0 \
  /Users/nguyenvoviettrinh/exodia-t06-work/MLAi_VNG_A/.venv/bin/python -m pytest -q \
  tests/test_runtime_worker.py tests/test_m3_atomicity.py tests/test_m3_failsafe.py \
  tests/test_database_isolation.py tests/test_offline_isolation.py \
  tests/test_runtime_replay_audit.py \
  --basetemp=/Users/nguyenvoviettrinh/exodia-t06-work/validation/m3-t06-phase2/pytest-regressions \
  --junitxml=/Users/nguyenvoviettrinh/exodia-t06-work/validation/m3-t06-phase2/integrated-regressions.xml

env LLM_MODE=replay LLM_CACHE=0 \
  /Users/nguyenvoviettrinh/exodia-t06-work/MLAi_VNG_A/.venv/bin/python \
  -m scripts.audit_runtime_replay \
  --output-dir /Users/nguyenvoviettrinh/exodia-t06-work/validation/m3-t06-phase2/replay-aggregate \
  --cassette-dir tests/cassettes
```

| Run | PASS | FAIL | SKIP | Exit | Result |
|---|---:|---:|---:|---:|---|
| T06 Phase 1 test trên integrated runtime | 13 | 3 | 0 | 1 | FAIL — F01, cùng ba test IDs ở Mục 13 |
| Targeted integrated regressions | 107 | 0 | 0 | 0 | PASS trong phạm vi sáu test modules |
| Aggregate replay harness | n/a | 1 harness failure | n/a | 1 | FAIL tại R11 AppTest `KeyError: choice_<case_id>`; không ghi aggregate artifact |

Hai lượt quan sát bổ sung gọi trực tiếp các hàm hiện hữu
`scripts.audit_runtime_replay.observe_runtime` và `write_artifacts` trong tiến trình Python một lần,
với fresh `TemporaryDirectory`, socket/provider/cache traps và không sửa source:

- Pipeline-only: **23/23 hits, 0 misses, LIVE=0**; flows `DEV_ROUTINE`, `DEV_AUTHORITY`,
  `DEV_FACT`, `V01`–`V04`.
- R11-only: **1/1 hit, 0 misses, LIVE=0**; flow `DEV_HUMAN_R11`.

Hai lượt này cố ý tách ra sau khi aggregate harness FAIL để thu thập evidence chẩn đoán. Vì không
là một execution chain liền mạch qua UI/human approval/send/restart, chúng không được cộng thành
complete E2E PASS. Full suite, typecheck, LIVE, real email và browser multi-tab: **NOT RUN**.

## 23. AC6 coverage matrix hiện hành

`VERIFIED` chỉ có nghĩa là bước nêu trong row có evidence trên đúng integrated SHA; không mở rộng
sang các bước downstream. `FAIL` giữ nguyên lỗi tái hiện. `NOT VERIFIED` không được suy thành PASS.

| AC6 path | Phase 2 evidence / actual | Disposition |
|---|---|---|
| Routine | Replay pipeline tạo `AUTO_REPLY/P05`, case `PENDING_SEND`, một draft, audit qua `DRAFT_GENERATED` và `SEND_SCHEDULED` | VERIFIED đến schedule; send/restart NOT VERIFIED |
| `AUTHORITY_REQUIRED` | `ESCALATE/AUTHORITY_REQUIRED/P01`, `AWAITING_HUMAN`, 4/4 replay calls hit, card/evidence/audit persisted | VERIFIED classification/queue; downstream human chain NOT VERIFIED |
| `FACT_UNRESOLVED` | `ESCALATE/FACT_UNRESOLVED/P03`, `AWAITING_HUMAN`, 4/4 calls hit | VERIFIED classification/queue; downstream human chain NOT VERIFIED |
| R2 extraction/error | R2 replay chạy trong pipeline; negative/error suite vẫn tạo hai `CASE_ERROR` cho một transition | **FAIL — F01 audit consistency** |
| R11 human decision/resume | 1/1 hit; choice/reason/actor persisted nhưng validator raise `ValueError("Bản nháp phải giữ nguyên quyết định và lý do của chuyên viên.")`; final case `HUMAN_DECIDED`, job failed, drafts=0 | **FAIL — R11** |
| Draft | Routine có một draft; R11 không tạo draft | Partial; **FAIL cho human-resume chain** |
| Preview | Chỉ có Phase 1 deterministic/stub evidence | **NOT VERIFIED trong replay chain** |
| Approval | Chỉ có Phase 1 deterministic/stub evidence | **NOT VERIFIED trong replay chain** |
| Simulated send | Phase 1 chỉ chuyển SQLite/audit; Phase 2 không dispatch | **NOT VERIFIED trong replay chain** |
| Restart | Phase 1 fresh-process tests PASS; Phase 2 không restart complete replay chain | **NOT VERIFIED trong replay chain** |
| Persistence | Fresh temp SQLite lưu pipeline outcomes và R11 human decision/job state | VERIFIED cho state đã quan sát; không phải full chain |
| Audit | Flow events được lưu; F01 duplicate `CASE_ERROR` còn tái hiện | **FAIL — F01** |

**AC6 kết luận: FAIL / CHƯA ĐẠT.** Replay coverage đủ để phát hiện business/runtime failures,
không đủ để chứng nhận complete Human Control E2E.

## 24. Business observations và defect preservation

### F01 — duplicate `CASE_ERROR`

Ba failed test IDs và actual actions giữ nguyên như Mục 13:
`['CASE_RECEIVED', 'CASE_SANITIZED', 'CASE_ERROR', 'CASE_ERROR']` thay vì một terminal
transition event. State vẫn fail-safe `ERROR/TECHNICAL_ERROR`, không queue/send. Severity đề xuất
vẫn MEDIUM/P2; không đổi assertion hay production để làm xanh.

### V02 — clock normalization mismatch

Expected `AUTO_REPLY/P05`; actual `ESCALATE/FACT_UNRESOLVED/P04`. Draft/replay dùng `5:00 p.m.`
trong khi source dùng `17 giờ 00`; audit ghi `GROUNDEDNESS_FAILED` với
`groundedness_failed:number`. Đây là business FAIL mới được tái lập trên integrated runtime,
không đưa vào scope sửa M3-T06.

### R11 — quyết định/lý do human không qua validator

Cassette hit và trả subject/body/citations, nhưng body không giữ đủ cả lựa chọn lẫn lý do theo
validator hiện hành. Worker giữ choice/reason/actor, để case `HUMAN_DECIDED`, đánh dấu job failed,
không tạo draft và không gửi. Fail-safe hoạt động, nhưng successful resume/draft/preview/approval
không xảy ra nên R11 và AC6 đều FAIL.

### Aggregate harness

Aggregate dừng ở R11 AppTest với `KeyError: choice_<case_id>` sau bảy pipeline flows. Không có
evidence rằng lỗi này là cassette miss; separate observations có 23/23 và 1/1 hit. Đây là harness/UI
selector failure cần giữ riêng, không được che bằng cách gọi hai lượt tách biệt là aggregate PASS.

## 25. AC1–AC7 disposition hiện hành

| AC | Evidence hiện hành | Disposition |
|---|---|---|
| AC1 — source-to-flow matrix | Mục 6 lịch sử + Mục 23 integrated replay | VERIFIED |
| AC2 — approval safety | Phase 1 deterministic tests; stale/concurrent/rollback cases | VERIFIED ở Phase 1; replay chain NOT VERIFIED |
| AC3 — controls/restart | Phase 1 pause/resume/cancel/correction/fresh-process evidence | VERIFIED ở Phase 1; complete replay restart NOT VERIFIED |
| AC4 — persistence/audit | 107 regressions PASS, fresh DB evidence; F01 duplicate terminal event | **FAIL product audit** |
| AC5 — error classification | State/display fail-safe và exact failed IDs preserved | VERIFIED classification; **FAIL audit consistency** |
| AC6 — complete runtime replay E2E | Mục 23; R11 FAIL, preview/approval/send/restart incomplete | **FAIL / CHƯA ĐẠT** |
| AC7 — delivery/review | Report, commands, hashes và handoff packet có sẵn; human sign-off chưa có | NOT VERIFIED cho acceptance/DONE |

Không thay `13 PASS / 3 FAIL` bằng 107 PASS: đây là hai scopes khác nhau. Không thay AC6 bằng
replay-hit metric. PR #46 vẫn Draft và M3-T06 chưa được tuyên bố DONE.

## 26. Evidence artifacts và integrity

Artifacts nằm ngoài repository, không đưa DB/cache/raw prompt payload vào PR. Sáu file dưới đây đã
được scan theo pattern API key/password/private key và không có match. SHA-256:

| Artifact | SHA-256 |
|---|---|
| `m3-phase1-on-integrated.xml` | `416f312a51c716ed88b73231acfdd42b73ab83ff63a477ecfa1815ad482caa06` |
| `integrated-regressions.xml` | `55837a2fd6c07519135bee05c7d7c614df15d698776e94fdb195a156869a724b` |
| `replay-base24/M6_T05_REPLAY_EVIDENCE.json` | `e5ce81f6ef9674167d34b32c41e5ac5dbe4b93c2dc4475fb7207bda56b124c7e` |
| `replay-base24/M6_T05_REPLAY_MANIFEST.json` | `be6e962ba6af067d00fcbaac4559705e53350b3b4d9c0e74072b6d5d894ad7ed` |
| `replay-r11/M6_T05_REPLAY_EVIDENCE.json` | `dc954df1a9203ef3869d950ce5095459ed7f8b59134236311bdde8fb0e10d37f` |
| `replay-r11/M6_T05_REPLAY_MANIFEST.json` | `9be2a38c50540f217e035ba3460068a5589d17a49b89f52799da682672b22358` |

Evidence root:
`/Users/nguyenvoviettrinh/exodia-t06-work/validation/m3-t06-phase2/`.
T06 test blob SHA-256 vẫn
`ee51d4c691464f7f1884f74d7c11cd92f3a26324646cab97480df2fb5ebaad7b`.
Raw JSON có synthetic input/prompt detail nên chỉ bàn giao theo đường dẫn local + hash; không commit.

## 27. Defects, blockers và Coordinator decisions

| Item | Owner đề xuất | Required decision / next action |
|---|---|---|
| F01 duplicate `CASE_ERROR` | Vũ — Runtime/Persistence | Coordinator cấp task/scope riêng để deduplicate audit transition; quyết định gate disposition |
| R11 validator/replay mismatch | Vũ + replay-pack Owner Minh | Xác định production validator hay accepted cassette/expected behavior cần correction; mọi source/cassette change phải được phê duyệt riêng |
| V02 clock normalization | Pipeline/grounding Owner do Coordinator chỉ định | Triage ngoài M3-T06; giữ expected và business FAIL hiện tại |
| Aggregate AppTest selector `choice_<case_id>` | QA/Infrastructure Owner Nam | Sửa/ổn định harness trong task riêng rồi rerun aggregate trên exact integrated SHA |
| Complete preview→approval→simulated send→restart evidence | Vũ + Nam | Chỉ rerun sau khi R11/harness được xử lý và Coordinator duyệt baseline/scope; vẫn replay-only |

Nếu bước tiếp theo cần LIVE/API, secret, recording, private participant data, production DB, real email,
production/cassette/manifest/expected change hoặc branch rewrite thì dừng và xin authorization; không bypass.

## 28. Self-review và handoff packet

- [x] Phân biệt Phase 1 và Phase 2; current disposition supersedes readiness cũ.
- [x] Ghi đúng integrated SHA, T06 checkpoint, environment, commands và exit status.
- [x] Ghi đúng 13 PASS / 3 FAIL và 107 PASS theo hai scopes riêng.
- [x] Không gọi 23/23 + 1/1 replay hits là complete E2E PASS.
- [x] Bảo toàn F01, V02, R11 và aggregate harness FAIL.
- [x] Chỉ đưa summary/hash cần thiết; raw evidence/DB/cache ở ngoài repository.
- [x] Không sửa production/test/cassette/manifest/expected result; không LIVE/email.
- [ ] Owner Vũ xác nhận self-review và quyền handoff.
- [ ] Nam review report/diff/evidence trên exact SHA.
- [ ] Coordinator quyết định remediation scope, gate disposition và acceptance.

Handoff cho review:

- PR: [Draft #46](https://github.com/ThanhVu165/MLAi_VNG_A/pull/46), base `dev`.
- Validated production SHA: `8e32ee43158160ac3dda6a84906871f3e3c183f2`.
- T06 checkpoint trước report update: `972b17157a9da35126a2ee24d35b4c3d1dfed7d8`.
- File thay đổi trong phiên hoàn thiện: chỉ report này. Exact final commit/pushed SHA được ghi trong
  handoff ngoài report vì report không thể tự chứa SHA của commit chứa chính nó.
- Review focus: Phase 2 counts, Mục 23 matrix, F01/V02/R11/aggregate findings, artifact hashes,
  và các human/Coordinator checkboxes chưa hoàn tất.
- Verdict phải dùng khi bàn giao: **AC6 FAIL / CHƯA ĐẠT; M3-T06 NOT DONE**.

Không tự chuyển PR sang Ready, không merge, không cập nhật Trello và không tuyên bố DONE.

## 29. Final audit acceptance assessment

### A. Audit completion

Audit execution và evidence packet đã hoàn tất trong phạm vi read-only/offline được giao:

- AC1–AC7 đều có evidence và disposition; không có row bị suy diễn từ replay hit.
- AC6 đã được chạy tới blocker R11 bằng replay runtime trên exact integrated SHA. R11 hit cassette
  nhưng worker fail trước draft, nên preview/approval/simulated send/restart downstream không thể
  có runtime evidence trong chain này.
- Commands, environment, exit status, JUnit, replay artifacts, hashes, root-cause findings,
  limitations và `LIVE/API/email=0` đã được bàn giao.

Điều này đủ để review kết quả audit, nhưng **chưa đủ để chấp nhận M3-T06 theo AC6 hiện hành**.
Muốn đóng task chỉ với evidence blocker thay vì complete E2E, Coordinator phải ban hành quyết định
điều chỉnh/ngoại lệ acceptance rõ ràng; yêu cầu FINAL CLOSEOUT hiện tại cho phép hoàn thiện report,
commit và push nhưng không ghi `CONTRACT-CHANGE` hoặc waive AC6. Owner Vũ self-review và Nam
independent review cũng chưa được ghi nhận hoàn tất.

### B. Product readiness

- Complete Human Control E2E: **FAIL**.
- F01 duplicate `CASE_ERROR`: chưa remediation.
- R11 human decision/resume: worker failed, không draft; chưa remediation.
- V02 semantic mismatch và aggregate AppTest selector failure: chưa được xử lý/tái kiểm.
- Stable Integration/Safety Gate: **HOLD**.
- GO-STUDY/LIVE: **không được phép**.

### Current closeout verdict

**HOLD_WITH_EXACT_GAP.** Các gap đóng audit/task còn lại:

1. AC6 downstream runtime evidence thiếu: R11 draft → preview → approval → simulated send → restart.
2. F01 và R11 cần remediation trong task production riêng, sau đó rerun exact affected chain.
3. Aggregate harness cần chạy lại thành công; V02 cần disposition/triage độc lập.
4. Owner Vũ self-review và reviewer Nam sign-off exact pushed SHA chưa có.
5. Coordinator phải chọn một trong hai: giữ AC6 và chờ remediation/rerun, hoặc ban hành thay đổi
   acceptance rõ ràng để nghiệm thu audit ở blocker boundary. Không tự coi yêu cầu closeout là waiver.
