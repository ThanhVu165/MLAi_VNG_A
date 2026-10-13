# M6-T05 — Product Runtime Replay Coverage

## Authorized BASE execution — 13/10/2026 (current result)

**RESULT: PARTIAL COVERAGE; NOT DONE.** This section supersedes the pre-dispatch state below. Recording ran at exact HEAD `8371b34385c39696d8ccfd06dae93311fd3e58fa` after the Coordinator's conditional GO requirements were satisfied. The shared checkout was clean: the runtime-smoke Owner preserved `CURRENT_RUNTIME_SMOKE.md` on `codex/pytest-blocker-remediation` at `a7efface6c7ca2021664ff3bfcf75a71fa13290f`; the database Owner verified all five M16 databases with `integrity_check=ok`, empty checkpoints and unchanged logical/byte hashes, after which SQLite removed the ten unlocked WAL/SHM sidecars on close.

The authenticated `Default project` binding, `gpt-6-luna`, Standard/Global tier, source/config/input fingerprints and `$10` hard cap were rechecked before execution. The guard reserved `$0.3585` before each request. Actual execution used **21/22 attempts**, reserved worst-case **$7.5285**, and returned **42,993 input + 2,922 output tokens**. A conservative usage-priced upper bound at the approved maximum rates is **$0.01293975**; exact billed cost is unavailable in response metadata. Every response reported model `gpt-6-luna`, `service_tier=default`, a request ID and numeric usage. There were no provider failures, SDK retries, cache hits, Gold/Set A/B inputs or real PII.

[`M6_T05_BASE21_RECORDED_PACK.json`](M6_T05_BASE21_RECORDED_PACK.json) publishes sanitized provenance for 21 cassettes. Original SDK payloads remain in ignored quarantine. The validator checked original-response checksums, request/model/source/config/input bindings, both schemas, usage reconciliation and cassette equality: **21/21 PASS**, zero unreferenced files, and no privacy flags across 85 JSON artifacts. The validated parsed cassettes are in `tests/cassettes/`; Nam's independent provenance/privacy review remains pending.

Offline product replay used a fresh isolated DB per flow with socket, provider-live and cache-read traps. [`M6_T05_BASE21_REPLAY_RESULT.json`](M6_T05_BASE21_REPLAY_RESULT.json) records **24 observed calls: 21 hits, 3 misses, LIVE=0**. Five flows are zero-miss: `DEV_ROUTINE`, `V01`, `V02`, `V04`, `DEV_HUMAN_R11`. Three flows are blocked: `DEV_AUTHORITY`, `DEV_FACT`, `V03`. In each blocked flow, the recorded R7 question failed the strict contiguous-basis validator; replay then generated a new repair prompt. LIVE recording had already consumed that flow's fixed three-attempt cap, so no authorized provider response exists for the repair prompt. Quota was not transferred, the unused global attempt was not used, and no cassette was fabricated.

Business correctness is separate from cassette integrity. `DEV_ROUTINE`, `V01` and `V04` match. `V02` replays with zero miss but remains the known `5:00 p.m.` versus `17 giờ 00` groundedness false positive. `DEV_AUTHORITY`, `DEV_FACT` and `V03` end `TECHNICAL_ERROR` after basis validation. `DEV_HUMAN_R11` replays with zero miss, preserves the human decision, but the worker rejects the generated draft because it does not preserve the decision/reason; job=`failed`, drafts=0. These are production semantic/validator defects outside M6-T05's authorized scope; no production fix was made.

| AC | Current status | Evidence |
|---|---|---|
| AC1 Coverage matrix | PASS | All eight BASE flows, 21 recorded identities and three newly observed repair gaps are mapped with exact hashes |
| AC2 Provenance | PARTIAL | 21 genuine SDK-response chains PASS; three repair responses do not exist under the approved per-flow caps |
| AC3 Integrity/schema | PASS for recorded pack | 21/21 original → parsed cassette checks PASS; source/config/model/usage/privacy bindings verified |
| AC4 No critical miss | FAIL | 21/24 observed calls hit; three repair prompts miss in Authority, Fact and V03 |
| AC5 Runtime evidence | FAIL | Five zero-miss flows; three technical errors, V02 semantic mismatch and R11 failed draft |
| AC6 Data/cost safety | PASS | Synthetic/public inputs, no prohibited datasets/PII, 21/22 attempts, `$7.5285` reserved `< $10`, offline replay LIVE=0 |
| AC7 Reproducibility | PASS technical | Exact recording SHA, fingerprints, sanitized pack/replay manifests, cassettes and commands retained; human reviews pending |

The exact completion blocker is now evidenced rather than speculative: achieving zero-miss BASE replay requires valid responses for the three repair prompts, but the approved per-flow caps are exhausted. Resolving it requires a production semantic fix that prevents invalid basis output or a new Coordinator decision authorizing additional per-flow repair attempts. Both are outside the current M6-T05 authority. Minh self-review, Nam final review and Coordinator ACCEPT/DONE remain pending; PR #44 stays Draft and this task must not be marked DONE.

---

## Coordinator BASE22 directive — 13/10/2026 (latest authority)

Direct Coordinator instruction in this chat supersedes the earlier HOLD on implementation: **prioritize M6-T05; pause M4-T01 implementation; BASE_PACK_V1 scope approved, maximum22 attempts and fixed per-flow caps; no quota transfer; supplemental cited-R11 recording NOT approved.** The latest `$10 HARD CAP` decision grants conditional LIVE/API execution once every preflight condition passes; it does not require another budget approval. Coordinator owns Trello state changes. Historical code/reports/evidence remain preserved.

Approved spending is **maximum10 USD**. `cee0f06...` remains the implementation checkpoint reference; the execution authorization must bind the actual final HEAD. **Do not use17.36/18.93 as approved budgets.**

Preflight: remote dev `1251c3c116a302d519dd71d6c31c3191874d785b`; implementation/tested checkpoint `cee0f067660feeeb1f626582818607fe7334d472`; PR44 OPEN/DRAFT targeting dev. Existing unrelated staged smoke report and ten WAL/SHM files remain unchanged and currently block the runner's clean-checkout gate.

Decision packet: [`M6_T05_BASE22_FINAL_GO_PACKET.json`](M6_T05_BASE22_FINAL_GO_PACKET.json). It freezes the eight synthetic inputs, hashes, config and source/corpus fingerprints and selects BASE22 only. Private execution authorization will bind the final PR head after this commit.

Public model/context/output/rate bounds were reverified13/10 from [official model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna) and [pricing](https://developers.openai.com/api/docs/pricing). The authenticated project is Standard/Global, and [official request semantics](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) say omitted `service_tier` uses the project tier. Conservative envelope uses the full1,050,000 input +128,000 output maxima and maximum Standard long-context rates0.25/0.75 USD per million: **0.3585 USD/attempt ×22=7.887 USD**. This fits the approved10 hard cap and the available credit. The envelope is a full reservation, not predicted spend.

Authenticated dashboard evidence is complete for preflight: Build tier; gpt-6-luna allowed at5000RPM/2,000,000TPM/20,000,000TPD; project Standard/Global; Pay-as-you-go credit above the7.887 full reservation. The local `sk-proj` credential suffix matches the dashboard's Active `OPENAI_API_KEY` row for the same project without exposing the key. Full account/project/billing observations stay only in ignored `data/validation/m6-t05-account-readiness-private.json`; no key value, private account identifiers or raw balance are published.

The recording runner now requires a verified Standard/Global bound before dispatch, reserves0.3585 before every attempt, stops before the next request if global/per-flow/USD capacity is unavailable, and rejects a returned response whose actual `service_tier` is not `default` after preserving its original SDK JSON. Production provider code and public interfaces are unchanged; cache stays disabled and SDK retries remain zero. Targeted offline validation is54 PASS.

The only pre-dispatch blocker is the dirty shared checkout: unrelated staged `CURRENT_RUNTIME_SMOKE.md` plus ten untracked SQLite WAL/SHM files. The runner correctly refuses to bypass this condition. Associated owners must safely reconcile them; do not move/delete SQLite sidecars while writers may be active. After the tree is clean, create the ignored authorization bound to that exact HEAD and current fingerprints, then run once under the Coordinator's existing conditional GO. Raw responses/candidates remain ignored quarantine until origin/privacy checks and genuine product replay; no automatic cassette promotion.

Acceptance limitation: BASE22 can target eight flows and21 nominal calls, but excludes the two cited-R11 responses. Full cited-context AC coverage cannot be declared PASS from standalone R11. Coordinator must later provide independently valid cited responses or make an explicit acceptance/scope decision if those original full-contract requirements remain mandatory; no supplemental recording is authorized now. Six3-step flows have no retry headroom; unexpected provider/schema/business failures stop rather than borrow quota, raise caps or alter policy/expected outcomes.

AC remains AC1 NOT VERIFIED /AC2 FAIL /AC3 NOT VERIFIED /AC4 FAIL /AC5 FAIL /AC6 PASS offline /AC7 PASS checkpoint, based on preserved exact-checkpoint51-test and8-miss evidence; no new runtime acceptance claim. **Provider attempts/tokens/USD remain0/0/$0.** After valid GO: guarded BASE recording → original/manifest/privacy checks → fresh-DB network-trapped replay → separate LayerA zero-miss and LayerB business/draft/audit checks → reviewed pack/report commit and exact-SHA validation → Minh human self-review/handoff → Nam independent final review → Coordinator ACCEPT/DONE/merge on Trello. Human sign-offs remain PENDING.

---

## Continuation checkpoint — 13/10/2026 (latest)

**RESULT: PARTIAL_ONLY_BLOCKED.** Owner Minh; Final Reviewer Nam; Approver Coordinator.
This section supersedes availability/readiness claims below; historical evidence bytes remain unchanged.

### Preflight and authority

- Verified `origin/dev`: `1251c3c116a302d519dd71d6c31c3191874d785b`; PR44 starting/tested source HEAD: `5f5ee5619143dfa627299c9faa5f89ad1fb013fd`.
- PR [#44](https://github.com/ThanhVu165/MLAi_VNG_A/pull/44): OPEN / DRAFT, base `dev`, head `sprint/m6-t05-runtime-replay`; no reviews/comments at preflight.
- Initial checkout was `codex/sprint2-doc-consistency` at `2c4813288c6a28f89b116f4600a8bf04d326fa53`. Selected the existing remote task branch with a local tracking branch in the same checkout. No new remote branch, clone/worktree, reset, stash, merge or history rewrite.
- Preserved unrelated staged `reports/readiness/CURRENT_RUNTIME_SMOKE.md` and ten untracked SQLite WAL/SHM files. They are excluded from this commit; original staged content is retained.
- Read AGENT, workflow, technical spec, roadmap, STATUS, runbook and live Task Contract. Latest [Coordinator comment](https://trello.com/c/7nEZN4bu#comment-6accbc2f1051ed46587d019f), 12/10 10:53:35 UTC, permits local capture reads and explicitly denies LIVE. No later GO observed; no provider/model probe.
- M4-T01 also appears IN PROGRESS. User answered “có” to the continuation/parallel-authorization clarification; work proceeds under that direct instruction, without changing Trello or attributing a new Trello decision to Coordinator. Minh/Coordinator must reconcile the card states before human handoff.

### Changes and verified source availability

- `scripts/validate_recorded_replay_pack.py`: reject unreferenced files in the candidate cassette tree, duplicate `(prompt_hash, attempt_index)`, invalid attempt index, and manifest/authorization source SHA mismatch. Distinct retries may reuse a hash; each original is still validated against the shared cassette, so conflicting data fails. Pack findings prevent integrity PASS.
- Privacy scan now covers the decoded full SDK payload, including metadata outside message content, without editing or publishing the original. Token counts must be nonnegative integers (booleans/floats/strings rejected) and reconcile across original usage and attempt metadata.
- `tests/test_guarded_runtime_recording.py`: added inventory/retry/conflict, full-payload privacy preservation and token-type/usage-chain regressions. Unit markers are explicitly not provider responses or product cassettes.
- `scripts/audit_runtime_replay.py` and its tests: retain actual persisted audit events, case status, draft count and per-flow calls/misses/errors before destroying the isolated DB. Cited NOT_RUN flows have zero calls and do not acquire invented audit/draft evidence.
- **9/9 original M2 captures are now locally available and match all published SHA-256 checksums.** All nine local run manifests are available and fingerprinted. This corrects the prior workspace-availability blocker; it does not establish intermediate SDK-response provenance. Capture top-level fields are case/config/diagnostics/fixture hash/identity/observation/result. No conversion, re-key, raw capture publication or candidate promotion performed; valid product cassettes remain **0**.
- New sanitized evidence/manifest and refreshed **NOT_AUTHORIZED** decision packet: [`M6_T05_CONTINUATION_20261013.json`](M6_T05_CONTINUATION_20261013.json). Old GO request/final preparation/Phase1/Phase2 JSON are preserved; the new packet binds current tool fingerprints, leaves `source_sha=null` for approval of the final PR head, and carries historical pricing only as an unverified proposal.

### Runtime evidence and AC1–AC7

Actual pipeline, Verify harness, approval page and worker ran with replay/cache=0, socket/provider/cache-read traps and a fresh temporary DEV DB. No product doubles supplied responses. All eight observed hashes equal the historical observed hashes; no prompt/schema/expected changes. Each call's flow/step/hash/model/source/error and full per-flow outcomes are in the new JSON; config/source fingerprints are pinned there. The complete static downstream matrix below remains applicable.

| AC | Status | Concrete current evidence |
|---|---|---|
| AC1 | NOT VERIFIED | 8 actual R2/R11 hashes mapped; R4/R7 and cited R11 hashes unavailable without genuine upstream responses |
| AC2 | FAIL | 0 eligible product cassettes; 9/9 M2 checksums verified, but output/telemetry cannot supply original intermediate responses |
| AC3 | NOT VERIFIED | Validator safeguards/regressions PASS; no genuine pack to certify, no vacuous integrity PASS |
| AC4 | FAIL | 8 requests / 8 misses: 7 R2, 1 standalone R11; cited Authority/Fact R11 are NOT_RUN due to upstream state |
| AC5 | FAIL | Routine/Authority/Fact and V01–V04: technical ERROR; standalone human decision retained, job failed, drafts=0; business correctness NOT VERIFIED |
| AC6 | PASS offline | LIVE attempts/tokens/USD=0/0/$0; synthetic/public DEV; unrelated DB files and raw captures untouched; no secrets/Gold/Set A/B committed |
| AC7 | PASS checkpoint | New sanitized manifest, raw audit checksum/paths, source/config fingerprints, exact commands and final SHA in PR44; full recovery incomplete |

Layer A replay coverage **FAIL**; Layer B business semantics **NOT VERIFIED**. Upstream replay failures do not establish new production business defects. Standalone R11 failure is observed; cited resume **NOT_RUN**, never downstream FAIL manufactured from missing context. No production safety/policy/provider/schema changes.

### Reproduction and validation

Windows / Python 3.11.9 from existing `.venv`; no dependency changes. Tested working tree = starting HEAD above plus exact source fingerprints in the new JSON. Final commit SHA and post-commit exact-source validation are recorded in PR44; a committed document cannot contain its own commit hash.

```powershell
New-Item -ItemType Directory -Force data/validation/m6-t05-continuation-temp | Out-Null
$env:TEMP=(Resolve-Path data/validation/m6-t05-continuation-temp).Path
$env:TMP=$env:TEMP
$env:PYTHONIOENCODING='utf-8'
& .venv/Scripts/python.exe -m scripts.runtime_recording_readiness --output data/validation/m6-t05-continuation-20261013-readiness.json
# Program exit 2: NOT_AUTHORIZED; choose fresh output paths for reproduction.
& .venv/Scripts/python.exe -m scripts.audit_runtime_replay --include-cited-r11 --output-dir data/validation/m6-t05-continuation-20261013-snapshot-replay
# Program exit 2: 0 cassettes / 8 misses / LIVE0, two cited flows NOT_RUN.
& .venv/Scripts/python.exe -m pytest -q --tb=short tests/test_guarded_runtime_recording.py tests/test_runtime_recording_readiness.py tests/test_runtime_replay_audit.py tests/test_openai_provider.py::test_model_hash_isolates_cache_and_cassettes tests/test_offline_isolation.py
# PASS: 51 tests in 8.48s; logs data/validation/m6-t05-continuation-snapshot-final-tests.log.
& .venv/Scripts/python.exe -m black --check --line-length 100 scripts/audit_runtime_replay.py scripts/validate_recorded_replay_pack.py tests/test_runtime_replay_audit.py tests/test_guarded_runtime_recording.py
& .venv/Scripts/python.exe -m ruff check scripts/audit_runtime_replay.py scripts/validate_recorded_replay_pack.py tests/test_runtime_replay_audit.py tests/test_guarded_runtime_recording.py
git diff --check
```

Black/Ruff/diff checks PASS. First pytest invocation: 26 PASS / 19 setup errors, all `WinError 5` reading the OS `pytest-of-admin` temp directory; rerun with workspace TEMP passed. Snapshot development initially failed (1 failed / 47 passed / 3 setup errors) due to a wrong audit-helper import; corrected to `infra.audit.events_for_case`, with failure log retained at `data/validation/m6-t05-continuation-snapshot-tests.log`. Final 51 tests PASS; no outstanding failed unit IDs. Product failed flow IDs: DEV_ROUTINE, DEV_AUTHORITY, DEV_FACT, V01–V04, DEV_HUMAN_R11. Genuine candidate-pack validator CLI, LIVE recording, Docker/full suite/browser/deployment E2E NOT RUN; no valid candidate pack or need to repeat unrelated suites. No-GO CLI, network isolation, quota/budget and checksum safeguards are exercised by targeted tests.

### Decision packet and human handoff

Problem → impact → resolution/owner: no original intermediate responses or recording GO → AC1–AC5 and M6-T03 remain blocked → Coordinator provides an independently valid original pack or approves bounded recording; Minh validates pack/privacy/runtime; Vũ handles any production change separately.

Coordinator must choose BASE22 or explicitly supplemental cited24, approve **exact final SHA**, config/corpus/input hashes, account access/model/rate/tier/token maxima, verified worst-case USD cap, per-flow/global caps, SDK JSON capture/provenance/privacy, cache/retry/failure accounting and stop/operator authority. Historical $17.36/$18.93 and token/rate bounds remain proposals, **not reverified account facts or spending authority**. If a bound requires production adapter changes, assign the appropriate Owner; T05 does not change it. New source fingerprints invalidate a GO for the old tool revision. Guarded recording also requires a clean checkout: preserve/resolve unrelated staged work separately before any authorized recording.

**Owner technical blocker handoff is reviewable; final READY_FOR_REVIEW handoff is not yet eligible.** Minh human self-review **PENDING** on final exact SHA; Minh reviews full diff/AC/provenance/privacy and posts their own blocker/handoff. Nam may inspect safeguards but final task acceptance review remains pending valid Owner handoff and pack evidence. Coordinator acceptance/DONE/merge **not eligible**. Coordinator GO is required before any LIVE next step; further independently authorized offline work does not need LIVE GO. No Trello comments/sign-offs posted by Codex; PR stays Draft targeting dev; STATUS/milestone gates unchanged.

---

**Result: PARTIAL ONLY — Phase 2A/2B offline checkpoint; replay recovery FAIL, recording BLOCKED.**
Owner: Minh — Logic/Evaluation. Final reviewer: Nam. Approver: Project Coordinator.
Ngày: 12/10/2026, Asia/Saigon. [Task Contract](https://trello.com/c/7nEZN4bu).
Phase 2A/2B offline: **AUTHORIZED**; Phase 2C LIVE/record: **NOT AUTHORIZED**. Provider/LLM/email LIVE calls: **0**.

## Phase 2 checkpoint — latest handoff

### Final completion preparation — 12/10/2026

Result **PARTIAL_ONLY_BLOCKED** at LIVE boundary. Remote dev vẫn `1251c3c...`; starting head `cac4273...`. Option A không có source bytes đủ trên evidence hiện có; không tìm lại pack116 hoặc convert M2. Các mục Phase 2A/2B bên dưới là checkpoint lịch sử; các implementation gaps observer/runner đã được xử lý thêm trong update này.

**Implementation mới, không production change:**

- [`guarded_runtime_recording.py`](../../scripts/guarded_runtime_recording.py): GO/config/SHA/input/corpus/known sender checks trước import product; fresh interpreter/DB/output directory; per-request HEAD/tree/source/env drift checks. Wrapper `_request_openai` reserve quota và verified upper cost **trước** khi delegate hàm thật. SDK request vẫn chỉ nằm trong `infra.llm` với args không đổi. Failure giữ reservation; safety stop dùng BaseException để không bị swallowed/retry.
- Hook `_response_usage` lưu **đúng bytes `model_dump_json()` của full SDK payload trước parser**, checksum và request ID; giữ metadata/usage hoặc stop nếu thiếu. Đây là SDK JSON snapshot, **không HTTP wire bytes**. Coordinator phải duyệt capture format này; nếu bắt buộc wire capture thì Owner infra cần scope riêng. Response contents không sửa. Failed SDK requests có exception class/status và reservation, không tạo response khi không có payload.
- `_record_cassette` wrapper không overwrite: same hash/equal parsed data giữ file cũ; conflicting parsed response STOP, giữ các SDK snapshots/attempt sidecars. Candidates/raw responses chỉ viết vào ignored `data/validation/<fresh-run>`; không tự promote vào `tests/cassettes`/PR.
- [`validate_recorded_replay_pack.py`](../../scripts/validate_recorded_replay_pack.py): contained paths, raw checksum, full identity/schema digests, approved response model/ID, source/config/input/GO references, source+strict schemas, numeric usage chain và cassette-vs-original parsed data. Secret/email/phone/student-ID pattern flags quarantine response, không rewrite. Integrity checks không tự chứng minh origin, privacy hoặc business correctness: pack luôn NOT_APPROVED đến independent review/acceptance. Domain parsers và business guards phải được kiểm bằng actual guarded product replay.
- Audit có `--include-cited-r11`: reuse actual Authority/Fact cases → real page decision → worker/resume. Upstream thiếu/không AWAITING_HUMAN ghi NOT_RUN, không dựng extraction/evidence/human case. Negative regression giữ 8 misses và không tạo R11 hash giả. Runner và replay dùng shared helper.
- All four scripts được source-fingerprint; Phase1 và Phase2 JSON lịch sử giữ nguyên. [`M6_T05_FINAL_PREPARATION.json`](M6_T05_FINAL_PREPARATION.json) và [`M6_T05_COORDINATOR_GO_REQUEST.json`](M6_T05_COORDINATOR_GO_REQUEST.json) ghi preparation hiện hành, frozen scope variants và missing approvals. `prepared_on_sha=cac4273...` cộng tool fingerprints là working-tree checkpoint; exact final tested SHA sẽ nằm trong PR sau commit.

**Cost enforcement proposal:** adapter vẫn không đặt output cap. Thay vì dùng token estimate8000/1000 làm bound, reserve theo provider-enforced maxima 1,050,000 input /128,000 output; rate ceilings bảo thủ0.55/1.65 USD/million kết hợp public cache-write/long-context/Fast/regional multipliers. Bound public-envelope=**$0.7887/attempt**; base22=$17.3514 (USD cap proposal **$17.36**); cited24=$18.9288 (proposal **$18.93**). Đây là tính toán từ [official model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna), reverified12/10, **chưa là account proof, verified bill hoặc authorization**. Account maximum rates/token maxima phải được Coordinator xác minh; nếu lớn hơn, upper/cap phải tăng được duyệt. Nếu không chứng minh được envelope, STOP; không sửa adapter trong T05 hoặc tự áp USD cap cũ$0.033.

GO validator đòi prefund entire selected worst-case cap và reserves riêng trước mỗi attempt; unknown/invalid bound, underfunded budget, missing origin/usage hoặc drift không dispatch tiếp. Ledger integration đã code/offline tested; **genuine SDK integration chưa exercise vì NO GO**. Reserved cost không phải billed actual USD; thất bại/unknown usage không refund. Invoice/cost reconciliation vẫn phải ghi trung thực sau authorized run.

**Critical scope variants, không cap ngầm:** BASE_PACK_V1 giữ8 flows/21nominal/cap22 (six3-step cap3, V04cap3, standaloneR11cap1). BASE_PLUS_CITED_R11_V1 chỉ được nhận khi GO explicitly chọn scope + `cited_r11_scope_approved=true`, 10flows/23nominal/cap24. Exact human choices/reasons/input hashes có trong GO request. Không transfer quota, không tăng processing/resume hard budgets3/1. Sáu3-step flows vẫn không có retry headroom; completion không được bảo đảm nếu provider/schema/semantic fail.

**Một Coordinator GO request duy nhất:** chọn22/24scope; approve exact final PR head + source/corpus/input hashes/config/caps; cung cấp authoritative GO reference, account access/rates/tier và verified bound evidence; USD cap; allowed returned model IDs; SDK capture format/synthetic/provenance/privacy rules; retry/repair accounting và stop conditions. JSON booleans/URL strings chỉ là binding/completeness checks, không authenticate approver. Operator/agent phải đọc quyết định authoritative trước invocation. Request JSON default NOT_AUTHORIZED, tất cả approval fields false/unset; tuyệt đối không chạy file proposal như GO.

Commands cho preparation đã chạy: **43 targeted tests PASS**, Black/Ruff PASS; actual offline audit with cited flag exit2, 8misses/LIVE0 và two cited flows NOT_RUN; no-GO runner exit2 trước product import/output creation. Validator registry chặn external schema-resource retrieval để giữ validation offline. Replay/record config freeze cả timeout/retries và runtime guard thresholds theo defaults hiện hành trước imports; record environment được restore khi hooks thoát. Final validation và exact handoff SHA được cập nhật trong PR. New fixtures chỉ unit metadata/mechanics, không provider responses hoặc product acceptance doubles. Không full suite/Docker/LIVE; không keys/Gold/PII committed.

Sau **genuine verified GO**, execution protocol (chưa chạy):

```powershell
# Only AFTER authoritative GO, account/cost evidence and exact SHA review.
& .venv/Scripts/python.exe -m scripts.guarded_runtime_recording --authorization data/validation/approved-m6-go.json --output-dir data/validation/m6-t05-authorized-record-01
# Always inspect RECORDING_MANIFEST/raw snapshots/failures; exit2 is NOT acceptance.
& .venv/Scripts/python.exe -m scripts.validate_recorded_replay_pack data/validation/m6-t05-authorized-record-01 --output data/validation/m6-t05-integrity-01.json
& .venv/Scripts/python.exe -m scripts.audit_runtime_replay --cassette-dir data/validation/m6-t05-authorized-record-01/cassettes --output-dir data/validation/m6-t05-replay-01
# Add --include-cited-r11 only when validating the explicitly approved cited scope.
```

Then compare LayerA no-miss/provenance separately from LayerB expected/actual/grounding/draft states; keep FAIL and send outside-scope business defects to Vũ/Coordinator. Only original approved/privacy-reviewed cassettes may enter tests/cassettes; complete manifest/checksum/source/authorization mapping and human review before acceptance.

**Remaining boundaries:** no recording GO/account proof; no actual valid pack/downstream responses; genuine SDK hook/provenance checks not yet exercised. AC1 NOT VERIFIED /AC2 FAIL /AC3 NOT VERIFIED /AC4 FAIL /AC5 FAIL /AC6 PASS offline /AC7 PASS checkpoint. Actual provider attempts/tokens/USD=0/0/$0. Minh human self-review and Nam independent review must use new final SHA; neither sign-off is supplied by Codex.

Owner draft: `[M6-T05] FINAL PREPARATION HANDOFF / BLOCKER` — result PARTIAL_ONLY_BLOCKED; new runner/observer/validator/cited replay/tests and preserved historical evidence; exact SHA/PR44/report/GO request links; validation actual; AC statuses above; human self-review PENDING; LIVE0; request Coordinator one GO/NO-GO decision with complete metadata. Nam checklist: genuine-source preservation, pre-SDK reservations/retry caps/drift/DB isolation, no overwrite, schema/origin/privacy distinction, all actual critical replay/business rows and exact source. Coordinator acceptance request remains **CHANGE REQUEST/HOLD overall recovery**, not DONE/merge: technical preparation is reviewable, full AC/replay pack still missing.

Remote `dev` đã cập nhật thành `1251c3c116a302d519dd71d6c31c3191874d785b` (`docs(m2): add offline artifact handoff`). Đã fetch/pull theo yêu cầu rồi merge `origin/dev` vào cùng branch T05, không rewrite lịch sử: checkpoint trước implementation là `c5d8a1d72bacb48f8cc7b088d6ecf8238887848b`. Commit mới chỉ thêm handoff M2; production/corpus/config fingerprints vẫn trùng Phase 1 baseline `ffb7f79...`. Phần baseline/preflight bên dưới là lịch sử Phase 1.

**Correction:** Coordinator và [M2 artifact handoff](../M2_OFFLINE_ARTIFACT_HANDOFF_20261012.md) xác nhận **116 là số test offline PASS, không phải số cassette**. Không có bộ “116 cassette” cần tìm. Hai JSON Phase 1 giữ nguyên bytes để bảo toàn lịch sử; trường `reported_historical_count=116` trong manifest cũ là claim của brief đã được đính chính tại đây, không phải inventory. Tool mới xuất historical count=null và clarification.

Handoff có 9 tên capture/case, observation/trace ID và SHA-256 được công bố. Đã đọc cục bộ handoff và báo cáo provenance M2. Cả 9 `data/validation/m2_dev_live_probe_01…09/cases/<case>/capture.json` cùng các `live_manifest.json` hiện chưa có trong checkout này. Git bỏ qua `data/validation/`; pull chỉ đưa handoff vào checkout. Checksum được công bố là attestation; chưa đối chiếu được bytes của capture. Không kết luận artifacts ở workspace nguồn bị mất.

Capture M2 là output/telemetry, thiếu đầy đủ response trung gian keyed theo prompt identity. Coordinator yêu cầu việc dựng/chuyển đổi cassette phải có **task riêng, review và kiểm tra provenance**. Không copy/re-key/convert capture; conversion=0; recovered valid cassette=0. Phase 2A chưa có nguồn hợp lệ để khôi phục approved pack.

Quyền tiếp tục offline: [Coordinator comment](https://trello.com/c/7nEZN4bu#comment-6accb8f4b731380929f71f9a) và chỉ dẫn người dùng trong phiên. PR #44 giữ Draft, T05 giữ IN PROGRESS. Chưa có Minh human self-review/Nam final review được xác minh; không ký thay, không chuyển gate.

### Phase 2B implementation và giới hạn

- [`runtime_recording_readiness.py`](../../scripts/runtime_recording_readiness.py) tạo [`M6_T05_RECORDING_READINESS.json`](M6_T05_RECORDING_READINESS.json): frozen synthetic inputs/input hashes, source/corpus fingerprints, bảng 9 capture cùng published checksum/availability, GO requirements và cost blockers. Script chỉ dùng stdlib, không có đường thực thi provider.
- Ledger offline đặt trước verified upper cost, chặn per-flow/global caps và cost vượt giới hạn trước khi tăng counter; failed/unknown-usage attempt giữ nguyên reservation, không vay quota. Đây là **OFFLINE_UNIT_TESTED_ONLY**, chưa tích hợp actual SDK attempt observer hoặc runner. Các boolean evidence statements chỉ kiểm completeness, không tự cấp GO hoặc xác minh quyết định người có thẩm quyền.
- Sidecar lưu `<hash>.attempt-001.json`, append riêng từng attempt, exclusive create; ghi lại cùng index bị từ chối. Metadata unit fixture không có response và luôn NOT_VERIFIED về provider origin. Chưa có original response để kiểm schema/domain parser/provenance; không chứng nhận pack bằng unit tests.
- Audit nhận thư mục cassette thật qua `--cassette-dir`, luôn replay/cache=0, fresh DB, network/provider/cache traps. Không ghi đè evidence cũ. Isolation test được tách khỏi business failure; missing-pack regression dùng thư mục rỗng riêng nên vẫn có ý nghĩa khi repo có pack sau này.

Base proposal giữ **21 nominal / <=22 provider attempts**, gồm Routine/Authority/Fact, V01–V04 và standalone no-evidence R11. Sáu flow có 3 steps/cap 3 không có headroom cho retry/repair; spare của V04 không được chuyển. Timeout 30s; mọi transport retry/R7 repair/regeneration đều tính attempts. Không bảo đảm 22 attempts sẽ hoàn thành pack.

Supplemental cited R11 cần Coordinator duyệt riêng: dùng đúng frozen `DEV_AUTHORITY`/`DEV_FACT` trong readiness JSON; choice=`Quyết định khác`; Authority reason=`Chuyển đề nghị phúc khảo trễ đến cấp có thẩm quyền; chưa chấp thuận ngoại lệ.`; Fact reason=`Yêu cầu bổ sung khóa học và học kỳ trước khi xác định văn bản áp dụng.`. Mỗi context tối đa 1 resume attempt trên upstream case đã có; citations/evidence IDs/prompt hash chỉ ghi sau genuine upstream, hiện NOT VERIFIED. Nếu duyệt cả hai, đó là **đề xuất mới 23 nominal / <=24 attempts**, chưa thay cap 22 hoặc mở multi-intent.

Theo [official model documentation](https://developers.openai.com/api/docs/models/gpt-6-luna), kiểm ngày 12/10/2026, standard short-context input=$0.10/million, cache-write=$0.125/million, output=$0.50/million. Dùng mức input bảo thủ $0.125 và giả định 8,000 input + 1,000 output mỗi attempt: 21 nominal≈$0.0315; 22≈$0.033. Giá/tier/account access thực tế **NOT VERIFIED**, approved USD cap=null. Long-context/Fast/regional pricing có thể khác; đây là estimate, không phải dollar cap hoặc thay thế giá account.

Adapter hiện không đặt `max_completion_tokens` hay service tier. Vì vậy giả định 1,000 output không phải output bound có thể cưỡng chế; chưa có verified per-request upper cost và cost guard integrated. Không dùng post-request M2 telemetry như pre-attempt enforcement, không dùng runner/quota M2 cho T05. Recording vẫn **BLOCKED** ngay cả khi biết public list price.

**Stop trước LIVE:** thiếu GO có exact source/config/input hashes/global+per-flow caps/USD cap/account rate+access/data+provenance/stop conditions; output-cost bound chưa kiểm chứng; source/corpus drift; cache hit; thất bại provider/schema/semantic; unexpected branch/quota; PII/secret; production change ngoài scope. Không probe model availability. Coordinator cần chốt cách enforce bound trong scope hoặc giao Owner infra task riêng nếu phải đổi adapter.

### Phase 2D và validation checkpoint

Không thực hiện Phase 2C. Audit offline mới chạy pipeline/Verify/trang approval/worker thật với cùng config và 8 hash Phase 1: 7 R2 + 1 R11 miss, 0 provider attempts. Layer A coverage FAIL; downstream R4/R7/cited R11 NOT VERIFIED. Layer B: 3 DEV và V01–V04 TECHNICAL_ERROR; R11 giữ human decision/HUMAN_DECIDED nhưng job failed, drafts=0. Draft/grounding/approval/send success chưa được chứng minh. Không có pack để thực hiện acceptance Phase 2D.

[`M6_T05_PHASE2_VALIDATION.json`](M6_T05_PHASE2_VALIDATION.json) giữ actual calls/outcomes/config/source fingerprints và checksum của full raw audit tại thư mục validation bỏ qua bởi Git; prompt/schema bytes/hash đối chiếu với raw Phase 1 committed evidence. Tested SHA là checkpoint `c5d8a1d...` cộng tool/test working tree đã fingerprint, không giả final commit chứa chính report. Exact final tested handoff SHA nằm trong PR sau post-commit validation.

```powershell
# Same isolated TEMP and Python environment as the Phase 1 commands below.
& .venv/Scripts/python.exe -m scripts.runtime_recording_readiness --output data/validation/readiness-new.json
# exit 2 = recording blocked; never a LIVE runner
& .venv/Scripts/python.exe -m scripts.audit_runtime_replay --output-dir data/validation/replay-new
# exit 2 = actual replay misses / no provenance certification; choose unused paths
& .venv/Scripts/python.exe -m pytest -q tests/test_runtime_replay_audit.py tests/test_runtime_recording_readiness.py tests/test_openai_provider.py::test_model_hash_isolates_cache_and_cassettes tests/test_offline_isolation.py
& .venv/Scripts/python.exe -m black --check --line-length 100 scripts/audit_runtime_replay.py scripts/runtime_recording_readiness.py tests/test_runtime_replay_audit.py tests/test_runtime_recording_readiness.py
& .venv/Scripts/python.exe -m ruff check scripts/audit_runtime_replay.py scripts/runtime_recording_readiness.py tests/test_runtime_replay_audit.py tests/test_runtime_recording_readiness.py
git diff --check
```

AC1 NOT VERIFIED; AC2 FAIL; AC3 NOT VERIFIED; AC4 FAIL; AC5 FAIL; AC6 PASS offline; AC7 PASS for reproducible checkpoint only. Minh phải đọc diff/evidence và xác nhận self-review trên exact PR head; Nam independent review; Coordinator quyết định acceptance. LIVE/provider attempts/tokens/cost actual=0/0/$0, cassette conversion=0. Không claim T05 DONE hoặc gate PASS.

Phase 2 changes chỉ audit/readiness scripts/tests, report và hai checkpoint JSON mới; Phase 1 JSON giữ nguyên. Không production/corpus/policy/Verify/expected/Docker changes. Owner cần đưa capture/manifest tới đường dẫn được phép đọc nếu muốn kiểm bytes; conversion vẫn task riêng. Không chờ artifacts để thực hiện các safeguards offline độc lập.

Validation trên checkpoint `c5d8a1d...` cùng tool/test working tree đã fingerprint: **25 passed in 5.15s**, Black/Ruff PASS; audit ghi 8 misses/LIVE=0. Tests xác minh quota/cost reservations, append-only metadata, thiếu capture không thành checksum PASS, isolation/human decision và bảo toàn evidence cũ. Chúng không chứng nhận replay pack hoặc provider origin.

## Baseline và preflight

- Verified remote `dev`: `ffb7f79f827172537d731528394173f4ce4f8551`, kiểm bằng `git ls-remote origin refs/heads/dev`, fetch và đối chiếu `origin/dev`.
- Checkout ban đầu: `dev`, `282c73b7dbf4ac7bf027d5710cce6ed673ab80d1`, working tree sạch. Không dùng `b1214476...` làm baseline.
- Branch mới: `sprint/m6-t05-runtime-replay`, tạo từ `origin/dev` trong repository hiện có. Không worktree/clone/backup repository, không ghi đè branch/local changes.
- GitHub API `pulls?state=open&base=dev`: `[]` tại preflight. PR #43 đã merge vào baseline; không có conflict quan sát được. Phải kiểm lại nếu runtime/corpus đổi trong khi review.
- Đã đọc `AGENT.md`, `TEAM_WORKFLOW`, `TEAM_HANDOFF`, `PROJECT_SPEC`, `STATUS`, `SPRINT_ROADMAP`, `RUNBOOK` và source liên quan. M1 CLOSED, M2 CONDITIONAL_CLOSEOUT, M3 AUTHORIZED_WITH_CARRYOVER; không đổi gate.
- T05 đang `IN PROGRESS`. Activity `6acc97ad96a12602e4eef8de` cho thấy Minh chuyển BACKLOG → IN PROGRESS lúc 15:17 ngày 12/10; lịch sử không chứng minh Coordinator duyệt READY. Đã hỏi và người dùng xác nhận trong phiên này: **“đã cho phép rồi”**, trả lời câu hỏi về Coordinator cho phép **Phase 1 offline**. Xác nhận này giải quyết entry cho Phase 1, không cấp quyền Phase 2; không sửa trạng thái Trello thay Owner.
- [M4-T01](https://trello.com/c/7EhgcMDv) của Minh đang READY; không có task implementation IN PROGRESS khác của Minh. Minh là reviewer ở M5-T02, Owner là Thư.
- [M6-T02](https://trello.com/c/3g3RV87w) của Nam đang READY, scope Docker/config/runbook; cassette/manifest T05 nằm ngoài scope Nam. [M3-T06](https://trello.com/c/bCP71uSH) của Vũ đang READY. Runtime/policies/provider/pages/Verify chỉ đọc trong T05.
- [M6-T01 historical report](../sprints/M6_T01_HISTORY_REPORT.md) corroborate không có committed cassette trên baseline cũ. Audit được nhắc với 116 cassette chưa có artifact trong checkout/card T05; kết quả dưới đây tái lập độc lập, không coi con số được báo là inventory đã kiểm.
- Timebox Phase 1 09:30–11:00 là **đề xuất**, không thấy actual timebox được Coordinator xác nhận; không tự đổi lịch hay claim đúng timebox đó.

## Artifact và phương pháp

- Tool: [`scripts/audit_runtime_replay.py`](../../scripts/audit_runtime_replay.py).
- Manifest inventory/gaps: [`M6_T05_REPLAY_MANIFEST.json`](M6_T05_REPLAY_MANIFEST.json).
- Raw structured evidence: [`M6_T05_REPLAY_EVIDENCE.json`](M6_T05_REPLAY_EVIDENCE.json): từng prompt đầy đủ, schema/hash, case refs, outcomes, source/corpus fingerprints, config và tested SHA.
- `tested_sha` của committed evidence là production baseline `ffb7f79...`; tool mới chạy từ working tree trước commit. Hash chính tool cũng nằm trong evidence. Production files không đổi. Revision bàn giao cuối nằm trong PR/Git history; không giả SHA chứa chính report trước khi commit tồn tại.

Tool cưỡng chế replay/cache=0 trước khi import `infra.db` hoặc `corpus` (import corpus có thể seed). Mỗi run có SQLite mới trong `TemporaryDirectory`, seed bằng product code, rồi hủy DB tạm. Không đọc/ghi `data/app.db`, local cache hoặc DB study/demo.

Socket connect/DNS/sendto, `_call_live` và `_load_cache` bị chặn bằng exception ngoài `Exception` để runtime không nuốt violation thành business outcome. Observer `_run_mode` **delegates nguyên lời gọi/response thật**; không thay extraction, policy, evidence, draft, LLMResult hay expected labels. Hash được so sánh giữa SHA-256 độc lập và `infra.llm._prompt_hash` trên identity thật.

Ba synthetic DEV cases chạy `process_case`; V01–V04 chạy `verify.harness.run_cases` thật, từng ID, không visual fixture. R11 dùng email Japanese synthetic: R1 tạo thẻ OUT_OF_POLICY không cần LLM; Streamlit AppTest thao tác **trang hàng chờ thật**, lưu lựa chọn/lý do bằng handler sản phẩm; `worker_tick` xử lý job và gọi `resume_case`. Không tạo SQL case/human-state fixture để thay runtime evidence. Đây là kiểm định page/backend, không phải browser/deployment E2E hoặc chứng nhận M3.

## Inventory và provenance

| Kiểm tra | Kết quả thực tế |
|---|---|
| `tests/cassettes/` trong checkout | Không tồn tại; 0 JSON |
| `git ls-tree -r --name-only HEAD tests/cassettes` | Không có tracked cassette |
| Available cassette có provenance hợp lệ | 0 |
| Available cassette không đọc được / incompatible | 0 / 0; không có artifact để kiểm |
| Available cassette thiếu provenance / không được run tham chiếu | 0 / 0; không kết luận về artifact ở máy khác |
| 116 cassette được báo trong brief Phase 1 | CORRECTED: 116 offline tests PASS; không có bộ cassette này |
| Provider responses tái sử dụng được | Không có nguồn đáp ứng exact prompt/config/provenance được tìm thấy trong phạm vi đã kiểm |

Inventory tool kiểm JSON object, filename 64 hex, checksum file, model và matching current schemas. Matching schema chỉ là compatibility candidate; không chứng minh schema gốc, prompt identity, provider origin hoặc file chưa bị sửa kể từ record. Trạng thái “không được observed run tham chiếu” cũng không tự có nghĩa “không còn sử dụng” toàn repo.

M1 evidence có kết quả Verify và provider-attempt metadata; không có original response pack cùng full current prompt identity. `prompt_hash12` trong telemetry là SHA của **prompt text**, khác cassette key SHA của identity đầy đủ. R2 prompt ở log lịch sử khoảng 1.450 ký tự, hiện khoảng 4.300–4.400; không re-key/diễn giải decisions lịch sử thành response mới. Không dùng cache local không có provenance. Phase 2 đã xác nhận không có bộ 116 cassette; M2 capture cần task riêng nếu chuyển đổi.

Manifest hiện có `cassettes=[]`, `pack_status=NOT_APPROVED`, authorization=null. Tám `required_observed_calls` là **missing requests**, không phải recorded cassette. Không tạo, sửa hay hợp thức hóa phản hồi LLM viết tay.

## Replay Gap Matrix

Config **C** cho toàn bảng: OpenAI / `gpt-6-luna`, reasoning=`none`, temperature=0.0, replay/cache=0. Schema nguồn theo từng step; strict provider schema và schema nguồn có hash riêng trong JSON. Source **S(h)** = `tests/cassettes/<h>.json`, hiện thiếu; provenance **MISSING**. Hash đầy đủ ở bảng để đối chiếu, không phải hash12 telemetry.

| Flow | Runtime step | Prompt hash | Model/config | Cassette source | Provenance | Coverage status | Missing reason |
|---|---|---|---|---|---|---|---|
| Routine DEV | R2_extract | `b76ffb27344b722f37e9d7a2689dcdcfa493b9bec6456d2c989b2a0711b9b33b` | C | S(hash) | MISSING | FAIL | FileNotFound; actual ERROR/TECHNICAL_ERROR |
| AUTHORITY_REQUIRED DEV | R2_extract | `050a43d660e2def02f7599d979b06bedd19afe92b8cab0144d34ebba941126f8` | C | S(hash) | MISSING | FAIL | FileNotFound; actual ERROR/TECHNICAL_ERROR |
| FACT_UNRESOLVED DEV | R2_extract | `88e798ff394d209c3846f67c98f1ba316ea90f7876d96a51d433aac6985a7be6` | C | S(hash) | MISSING | FAIL | FileNotFound; actual ERROR/TECHNICAL_ERROR |
| Verify V01 | R2_extract | `22a3e3620f76e5eddaef6ad4b3583575926bc2011a517154924718bfb377f057` | C | S(hash) | MISSING | FAIL | Expected P05; actual ERROR/TECHNICAL_ERROR |
| Verify V02 | R2_extract | `76324c1a472a061da3d9e2d7ff6152c2593a81ddefe09b58f8047075a93c1b8d` | C | S(hash) | MISSING | FAIL | Expected P05; actual ERROR/TECHNICAL_ERROR |
| Verify V03 | R2_extract | `dc958213fb18e81826d94e6becafc06beb4f76f4f9cc9921ddd1024bd93fc3c2` | C | S(hash) | MISSING | FAIL | Expected P01/AUTHORITY; actual ERROR/TECHNICAL_ERROR |
| Verify V04 | R2_extract | `43b38848a6d84560402a872b0e33ed8982a2f96e256a2a27a53ef0c1f9336c14` | C | S(hash) | MISSING | FAIL | Expected P02/OUT_OF_POLICY; actual ERROR/TECHNICAL_ERROR |
| Human draft, no-evidence DEV | R11_resume | `2447ffcce6d7372fd5cdc1810653804259f0f7b82402b57472679884de20d015` | C | S(hash) | MISSING | FAIL | Real human decision retained; job failed; 0 drafts |
| Routine, V01, V02 | R4_select → R7_generate | NOT RECOMPUTABLE YET | C | None | NOT VERIFIED | NOT VERIFIED | R2 response absent; R4 includes extraction.raw_json/request/facts; R7 needs selected evidence and updated extraction |
| Authority, V03 | R4_select → R7_question | NOT RECOMPUTABLE YET | C | None | NOT VERIFIED | NOT VERIFIED | Upstream extraction/selection unavailable; subtype/requests/evidence needed |
| FACT_UNRESOLVED | R4_select → R7_question | NOT RECOMPUTABLE YET | C | None | NOT VERIFIED | NOT VERIFIED | P03 depends on real missing facts/scope; cannot assume extraction/selected chunks |
| V04, unsupported domain | R4_select conditional; R7_question expected | NOT RECOMPUTABLE YET | C | None | NOT VERIFIED | NOT VERIFIED | No R4 call if extracted domains all UNKNOWN; R7 still needs real extraction |
| Human resume after Authority/Fact | R11_resume with evidence | NOT RECOMPUTABLE YET | C | None | NOT VERIFIED | NOT VERIFIED | Different email/choice/reason/evidence → different hash; standalone no-evidence R11 cannot cover these contexts |
| Escalation conditional repair | R7_question_repair | NOT RECOMPUTABLE YET | C | None | NOT VERIFIED | NOT VERIFIED | Only if basis validation fails; prompt adds exact repair suffix |
| Escalation conditional regeneration | R8 invokes R7_question again | Same as original if same context | C | S(original hash) | NOT VERIFIED | NOT VERIFIED | Question Guard regeneration delegates same generator; deterministic replay can repeat the same invalid response, then fallback |
| Ground Guard P04/FACT_UNRESOLVED | R8/P04 deterministic card | N/A | No LLM | N/A | N/A | NOT VERIFIED | No extra LLM for this card; preceding R2/R4/R7 still need coverage; not P03 missing-fact evidence |
| All flows | R0/R1, R3 lock, R5, R6 policy, persistence/queue/approval/dispatch/audit | N/A | No LLM | N/A | N/A | Source mapping complete | Corpus search/index path does not create an additional runtime LLM step; R4 selection is the LLM boundary |

**Observed:** 8 actual call_json requests, 8 unique full identity hashes, 8 replay misses, 0 provider attempts. Pipeline and Verify preserve errors instead of mislabeling them as FACT_UNRESOLVED. Three DEV labels are proposed intentions, not proven business classifications. V01–V04 business matches are all false because of technical replay failures; no Gold/expected changes.

R11 intake passed R1 and UI saved `Yêu cầu bản dịch` plus the synthetic reason. Final status HUMAN_DECIDED, job failed, draft_count=0. Decision persistence is observed; draft generation/grounding/approval/send success **NOT VERIFIED**. No-evidence R11 flow does not certify Authority → human → draft with citations.

## Config/cache consistency và owner findings

- Identity hiện hành: `sha256(json.dumps([provider, model, schema, prompt, temperature], sort_keys=True, ensure_ascii=False).encode('utf-8'))`. Received timestamp affects R4 prompt; source/corpus metadata/order, extraction raw JSON/order, choice/reason affect downstream hashes. Freeze these inputs; do not re-key.
- Replay branch precedes cache. Actual run traps cache reads; targeted model identity regression also PASS. Record/live consult cache by default; cache hit returns before `_record_cassette`. **`LLM_MODE=record` alone does not prove recording.** Proposed record must force cache=0 and fresh DB.
- `.env.example` defaults live/cache=1 with model blank; `infra.settings` may read local `.env`. Tool overrides mode/provider/model/reasoning/cache and DB first, never publishes credentials or treats local config as authorization.
- `infra.llm._replay` accepts data objects without validating recorded model/schema/provenance. Strict schema checking and provider-origin verification must be external pack checks before accepting replay. No production change here.
- Reasoning effort/timeouts are **not included in cassette identity**, though reasoning affects provider request. Manifest must pin/check them. Report to Vũ/Coordinator if protection requires adapter/contract change; do not silently “fix” infra in T05.
- Budgets from runtime: processing max 3 provider attempts, resume max 1; overall contract max 4. R2 validation retries, R7 basis repair or multi-intent paths can consume this budget. A fifth call/new context is not authorized by the plan.

## Record Plan — proposal only, STOP before any LIVE

First ask Coordinator for existing original artifacts. Accept only if original provider response, authorization, recorded SHA, exact canonical prompt/schema/model/config, response/request metadata and file checksum can be linked. Re-run exact-hash/schema/PII checks. An artifact with unknown provenance remains excluded even if `_replay` reads it.

### Synthetic inputs and bounded call plan

New DEV inputs are literal constants in tool/evidence, sender `synthetic@example.invalid`, received time `2026-09-21T09:00:00+07:00`. They ask fee information, request a late-appeal exception, or ask which conduct regulation applies without supplying cohort/semester. Existing V01–V04 are public synthetic DEV/regression, not independent Set A/B. Japanese R11 input/choice/reason are frozen in `HUMAN_INPUT` and evidence, received time 09:04.

| Flow | Steps to record, if product takes intended path | Planned calls | Per-run provider cap |
|---|---|---:|---:|
| Routine DEV | R2, R4, R7_generate | 3 | 3 |
| Authority DEV | R2, R4, R7_question | 3 | 3 |
| Fact DEV | R2, R4, R7_question | 3 | 3 |
| V01 / V02 / V03 | Each R2, R4, R7_generate or question | 9 total | 9 total |
| V04 | R2, R7_question if UNKNOWN; otherwise review actual path | 2 | 3 |
| Standalone human no-evidence | Actual R1 intake/UI decision/worker, R11 only | 1 | 1 |
| **Total proposal** | Single pass per listed input; retries count as attempts | **21 nominal** | **22 maximum attempts** |

The eight known hashes above are concrete missing requests. Another **13 nominal** R4/R7 requests depend on genuine upstream provider responses; their exact hashes must be captured progressively during the authorized single pass. Freeze response bytes/corpus/order rather than invent extraction content. Failed provider attempts may leave fewer valid cassettes than calls; no automatic reruns to fill the gap.

This finite proposal excludes separate Authority/Fact R11 citation contexts and multi-intent pack expansion. If Coordinator wants those critical contexts, approve named input, human choice/reason and **+1 resume attempt per accepted existing upstream case**, then update plan/manifest; upstream rerun needed for a new case also counts. Current standalone R11 hash is not reusable for them. Conditional R7 repair must fit processing cap; stop/review when a path cannot fit. A repeated identical regeneration need not produce a new hash but still consumes a LIVE attempt.

**Exact config proposed:** verified production SHA above (reverify before GO), same seed fingerprints; `LLM_PROVIDER=openai`, `OPENAI_MODEL=gpt-6-luna`, `OPENAI_REASONING_EFFORT=none`, `LLM_MODE=record`, `LLM_CACHE=0`; temperature 0.0; timeout 30s/call, one transport retry where existing code allows; processing/resume caps 3/1. Provider endpoint `https://api.openai.com/v1`, Chat Completions JSON schema, strict schema via `_openai_schema`, SDK retries=0. No provider/model fallback. Model availability and actual account pricing remain NOT VERIFIED; do not probe without GO.

**Cost estimate assumptions:** 8,000 input + 1,000 output tokens per attempt, no cache discount. Nominal 21 attempts = 168,000 input + 21,000 output; max 22 = 176,000 + 22,000. Cost in USD = `0.176 * P_in + 0.022 * P_out`, where rates are USD/million tokens. For an **illustrative assumption**, not a provider price quote, P_in=1 and P_out=5 gives $0.286; +10% planning allowance ≈ **$0.32**. Coordinator must approve real rates and dollar budget before GO. Context/output can exceed assumptions; adapter has no configured max-output token cap, so this is not a guaranteed cost ceiling. Stop before the next call if usage/rate/cost reconciliation is missing or projected spend exceeds approved budget; request bounded alternative scope if a hard ceiling cannot be enforced without production change.

### Recording verification and manifest

- Fresh isolated DB and exact seed, cache=0, explicit authorization referencing cases/config/SHA/22-attempt cap/dollar cap. Record original input/received time/corpus fingerprints. Do not start Docker-dependent validation in T05.
- Use product `call_json`; actual SDK call remains inside `infra/llm.py`. An observational hook may capture actual response/request IDs, timestamp, model, usage and provider attempt correlation without replacing returned data or changing product modules. Existing telemetry alone lacks full cassette identity and response ID; obtain sidecar evidence from genuine responses. Preserve original response; do not edit it for parser/semantic PASS.
- Cassette path `tests/cassettes/<full identity hash>.json`. Sidecar manifest under `reports/readiness/`: flow/step, source kind=authorized_provider_recording, authorization reference, recorded/tested SHA, input/corpus fingerprints, canonical prompt or approved prompt digest, source/strict schema digests, provider/model/response_model, reasoning/temperature, HTTP/request/response metadata, numeric usage, recording timestamp, file SHA-256, cache bypass evidence, privacy disposition. No keys/headers/private account metadata.
- Verify filename hash independently, read/parse JSON, current source and strict schema, domain parser, model/config and original-vs-normalized output relation. Scan secret/PII patterns. Any failure stays FAIL/NOT VERIFIED; expected labels remain frozen.
- Then switch to replay/cache=0 on another fresh DB, run the same real pipeline/Verify/page-worker paths with LIVE/network guard. Require no miss for each **approved** pack step, compare outcomes separately; record complete errors and guards. No-evidence R11 needs preservation of human choice/reason, grounded draft and PENDING_APPROVAL before claiming draft success; human approval/send need their own M3 evidence.
- Source data only these synthetic DEV inputs and public seed. No private Gold/Set A/B, real student emails, consent or participant data. Provider IDs and sanitized usage are provenance metadata, not evidence of business correctness.

**Stop conditions:** no GO/budget; missing original provenance; changed SHA/corpus/model/schema/context; cache hit; provider failure/schema/domain invalid output; unexpected branch or call count; PII/secrets/contamination; cost unverified/exceeded; production changes needed; semantic defect. Minh stops affected recording and reports to Coordinator/Vũ; continue independent offline integrity checks. No new LIVE requests to make a report greener.

## AC disposition

| AC | Status | Evidence / limitation |
|---|---|---|
| AC1 Coverage Matrix | NOT VERIFIED (mapping complete) | R2/R11 exact hashes, all requested flows and conditional downstream steps mapped; downstream exact hashes remain NOT VERIFIED until genuine upstream responses exist |
| AC2 Provenance | FAIL | 0 original artifacts; missing inventory manifest is not a provider-provenance pack |
| AC3 Integrity/schema | NOT VERIFIED | No real cassette to certify; tool malformed/model/schema tests pass, expected/prompts/old cassettes unchanged |
| AC4 No critical miss | FAIL | 8/8 observed requests miss, approved product pack absent |
| AC5 Runtime evidence | FAIL | Separate actual outcomes retained for all flows; 7 technical ERROR, R11 drafting failed; business semantic outcomes NOT VERIFIED |
| AC6 Data safety/no unauthorized LIVE | PASS | Synthetic/public DEV only, no Gold/Set A/B read or edit, no keys/PII committed; provider/network/cache-read traps, 0 LIVE |
| AC7 Reproducibility | PASS for Phase 1 checkpoint | Report, inventory/gap manifest, structured actual outputs, hashes/config/tool/tests and Draft PR; full recovery acceptance remains incomplete |

Completed flow mapping does not certify AC1 downstream hash coverage. AC7 checkpoint PASS does not mean T05 DONE. AC1–AC5 require valid approved pack and additional real replay evidence. Nam reviews after Minh confirms self-review on exact handoff SHA; Coordinator alone ACCEPT/DONE/merge.

## Commands, environment and validation

Common environment: Windows, Python **3.11.16**, offline product config C, isolated DB. Source SHA for observations/checks below: `ffb7f79f827172537d731528394173f4ce4f8551` plus the new tool/test working tree, with production fingerprints in evidence. No requirements/production change.

Minimal validation dependencies installed in ignored `.venv`: pinned project PyYAML 6.0.2, pytest 8.3.3, openai 3.24.0, black 24.10.0, ruff 0.7.1, streamlit 1.39.0, rank-bm25 0.2.2, plus **jsonschema 4.23.0 for this audit**. This is a targeted validation environment, not a fresh-clone/full pinned dependency proof. Installation/download network traffic is not an LLM/provider call.

```powershell
# Python 3.11 required. Use an isolated venv containing the versions listed above.
New-Item -ItemType Directory -Force data/validation/m6-t05-temp | Out-Null
$env:TEMP=(Resolve-Path data/validation/m6-t05-temp).Path
$env:TMP=$env:TEMP
$env:PYTHONIOENCODING='utf-8'
& .venv/Scripts/python.exe -m scripts.audit_runtime_replay --output-dir data/validation/phase1-reproduction-new
# Expected exit 2: audit captured failures; no pack provenance/recovery certification.
& .venv/Scripts/python.exe -m pytest -q tests/test_runtime_replay_audit.py tests/test_openai_provider.py::test_model_hash_isolates_cache_and_cassettes tests/test_offline_isolation.py
& .venv/Scripts/python.exe -m black --check --line-length 100 scripts/audit_runtime_replay.py tests/test_runtime_replay_audit.py
& .venv/Scripts/python.exe -m ruff check scripts/audit_runtime_replay.py tests/test_runtime_replay_audit.py
git diff --check
git diff --name-only origin/dev
```

| Command/check | Result | Evidence |
|---|---|---|
| `git ls-remote`, fetch, rev-parse/status/branch; GitHub/Trello reads | PASS | Baseline/preflight above; live remote SHA matches baseline |
| `git ls-tree ... tests/cassettes`; actual directory inventory | PASS analysis | 0 cassettes; 116 historical count unavailable, not validated |
| `python -m scripts.audit_runtime_replay` | PASS audit / FAIL replay (exit 2) | 8 hashes independently recomputed, 8 misses, actual structured outcomes; script/corpus fingerprints |
| First audit with sandbox OS temp | FAIL environment | SQLite could not open sandbox virtual temp; retry used workspace TEMP, no production DB touched |
| First pytest under sandbox | FAIL environment | `TEST_DATABASE_ISOLATION: cannot create safe test database`; Windows denies `resolve(strict=True)` even on temporary child |
| Targeted pytest with offline guards, local TEMP, approved shell escalation | PASS | **11 passed in 4.59s** after final tool refactor; one subprocess deliberately inherits live/cache=1 and existing DB sentinel, tool forces replay and preserves sentinel |
| Post-commit `python -m scripts.audit_runtime_replay --output-dir data/validation/m6-t05-postcommit` | PASS audit / FAIL replay (exit 2) | Tested SHA `18291419971680cd71941668d49dafe1d950532b`: 8 misses, LIVE=0; same exact prompt hashes; original committed evidence preserved |
| Black / Ruff, changed Python only | PASS | Files formatted; lint clean |
| Scope/diff/secret/PII/Gold scan | PASS checkpoint self-check | Only tool/test/report/manifest/evidence added; synthetic original prompts only; source/corpus files unchanged |
| Cassette schema/provenance validation | NOT VERIFIED | No cassette files; no vacuous integrity PASS |
| Record/cache ordering | PASS static + replay runtime | Source `_run_mode`, actual replay cache trap, model hash regression; no record/provider execution |
| Docker, browser E2E, fresh clone, public deploy, full pytest, LIVE/record | NOT RUN | Outside authorized Phase 1 or unnecessary for this isolated evidence checkpoint |

Network guard violations raise outside normal product catches, aborting the audit. Tool exit 2 always refuses provider-provenance certification; it cannot turn new readable files into a recovery PASS. Unit-test fixtures are explicitly tool tests, not product cassettes. Repeat runtime observations from the safety test also have 8 misses/0 provider calls; committed evidence represents one named standalone audit run, not pooled samples.

## Risks, decisions and handoff

1. **P0 missing valid replay pack/provenance:** M6-T03 cannot claim miss=0. Không có bộ 116 cassette. Coordinator quyết định task riêng để kiểm nguồn/chuyển đổi M2 hoặc recording có bounds hợp lệ; Minh owns validation, Nam consumes only accepted SHA/pack.
2. **R4/R7 and cited R11 contexts unknown:** exact hashes cannot be completed without genuine extraction/selection. Coordinator chooses finite pack contexts; Vũ handles any runtime/business defect outside T05.
3. **Adapter identity/validation limits:** reasoning effort omitted from key; replay model/schema not enforced; record may read cache. Manifest must protect pack config and source. No adapter/schema changes in this checkpoint.
4. **Cost/model verification absent:** no default LIVE entitlement, model/pricing/22-attempt plan remain proposals. A GO must name approved calls, budget, synthetic data, source SHA and stop conditions; don't reuse M2 remaining quota as authorization.
5. **Downstream:** M6-T03 still needs accepted M6-T02 + replay pack; M3-T06 can use compatible offline evidence but no safety gate certified. M4-T02/M5-T03 remain subject to their independent Stable Integration/gate/GO requirements.

Changed files: this report, `M6_T05_REPLAY_MANIFEST.json`, `M6_T05_REPLAY_EVIDENCE.json`, `scripts/audit_runtime_replay.py`, `tests/test_runtime_replay_audit.py`. No production/corpus/policy/Verify/cassette/expected changes. Agent self-check completed; **Minh's human self-review confirmation remains required**.

Git handoff: [implementation/evidence commit `18291419971680cd71941668d49dafe1d950532b`](https://github.com/ThanhVu165/MLAi_VNG_A/commit/18291419971680cd71941668d49dafe1d950532b), `test(m6-t05): add offline runtime replay gap evidence`; [Draft PR #44](https://github.com/ThanhVu165/MLAi_VNG_A/pull/44) targets `dev`. This report-link follow-up changes documentation only; final branch head is the exact review SHA shown in PR. No merge/force-push/rewrite/DONE/gate update authorized.

Historical Phase 1 prepared text for **Minh to post**, not posted by agent; superseded by Phase 2 checkpoint above (including the 116-count correction):

```text
[M6-T05] PHASE 1 OWNER HANDOFF / BLOCKER
Result: PARTIAL ONLY — offline gap analysis ready for review; recovery FAIL.
Baseline: ffb7f79f827172537d731528394173f4ce4f8551; branch sprint/m6-t05-runtime-replay.
Changes: report, inventory/gap manifest, runtime evidence, offline audit tool/tests.
Validation: 0 cassette available; 8 observed unique misses (7 R2, 1 R11);
11 targeted tests + format/lint PASS. Business outcomes remain NOT VERIFIED.
Evidence: attach Draft PR + exact handoff SHA + reports/readiness/M6_T05_REPLAY_COVERAGE.md.
Self-review: Minh must read full diff/AC/provenance/privacy and confirm on handoff SHA.
LIVE/API: 0 provider/LLM/email calls; Phase 2 NOT AUTHORIZED.
Problem/Impact: original 116 pack absent; no provider provenance; M6-T03 replay blocked.
Solution/Responsible: Coordinator supply valid original pack or approve recording; Minh validates.
Decision Needed: GO/NO-GO finite 21 nominal / <=22 attempts, exact config/inputs/SHA,
actual rates/dollar cap; separately decide cited Authority/Fact R11 contexts.
Safe Work Completed: offline inventory/hash/runtime misses, no production changes.
Request: Nam reviews Phase 1 checkpoint after Minh confirms self-review; no T05 DONE claim.
```

Full M6-T05 completion remains pending valid provenance, approved replay pack, Nam final review and Coordinator acceptance.
