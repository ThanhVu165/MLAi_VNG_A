# M6-T05 — Product Runtime Replay Coverage

**Result: PARTIAL ONLY — Phase 2A/2B offline checkpoint; replay recovery FAIL, recording BLOCKED.**
Owner: Minh — Logic/Evaluation. Final reviewer: Nam. Approver: Project Coordinator.
Ngày: 12/10/2026, Asia/Saigon. [Task Contract](https://trello.com/c/7nEZN4bu).
Phase 2A/2B offline: **AUTHORIZED**; Phase 2C LIVE/record: **NOT AUTHORIZED**. Provider/LLM/email LIVE calls: **0**.

## Phase 2 checkpoint — latest handoff

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
