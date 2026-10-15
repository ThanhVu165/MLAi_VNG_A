# M4-T02 — Freeze readiness cho Post-Tuning Set A

- Task ID: `M4-T02`
- Owner: Minh — Evaluation/Logic
- Ngày audit/freeze-prep: 15/10/2026 (Asia/Saigon)
- Exact remote `dev`: `47a1fcd9686b5409674979b34a521ead2f65ae8d`
- Branch: `sprint/m4-t02-official-set-a`
- Coordinator amendment: Trello action `6ad04616863aaeb3c1fb352f`,
  `2026-10-15T03:18:46.576Z`
- Candidate authorization: Trello action `6ad04dd2fb6c52f6121deaa4`
- Private-storage authorization: Trello action `6ad04fd528b7095d4152b4c1`
- Kết quả: **BLOCKED**
- Freeze status: **FREEZE_INCOMPLETE**
- GO-A recommendation: **NO_GO_A**
- Official Set A runs: **0**
- Application LIVE/API/provider/email calls: **0**
- Private access: **Set A input-only authoring; Set B input-only overlap; Gold reads 0**

Đây là gói freeze-preparation cho một **POST-TUNING INDEPENDENT EVALUATION SET**
mới theo amendment. Báo cáo không claim pre-M2 held-out, historical preregistration
hoặc final sealed held-out; không tự cấp GO-A, budget hay quyền LIVE.

## 1. Authority, baseline và phương pháp

Coordinator đã chấp nhận audit tại PR #59 và sửa AC1: Set A mới chỉ cần chứng minh
independence/provenance từ lúc tạo sau M2, nhưng vẫn phải freeze đầy đủ trước execution.
Amendment giữ `GO-A = NOT YET GRANTED`, LIVE/API chưa được phép và budget bằng 0.

Remote `dev` đã đổi từ baseline audit cũ do PR #59 được merge. Audit này fetch và dùng
đúng `origin/dev@47a1fcd9686b5409674979b34a521ead2f65ae8d`; không dùng SHA cũ làm baseline.

Nguồn đã kiểm:

- Task Contract, amendment, authoring decision và private-storage decision trên Trello.
- Tracked tree/current Git history và GitHub PR #59.
- [`M4_T02_GO_A_READINESS.md`](M4_T02_GO_A_READINESS.md) và M4-T01
  [protocol](../../docs/evaluation/M4_T01_PROTOCOL.md),
  [case schema](../../docs/evaluation/M4_T01_SCHEMA.json),
  [freeze schema](../../docs/evaluation/M4_T01_FREEZE_SCHEMA.json),
  [freeze template](../../docs/evaluation/M4_T01_FREEZE_TEMPLATE.json) và
  [readiness report](M4_T01_PROTOCOL_READINESS.md).
- Candidate input-only/provenance trong controlled private store và đúng authorized
  M7 input-only candidate để overlap check; không mở Gold/reviewer material.

Candidate Set A được tạo sau khi Coordinator cấp quyền preparation và storage. Gold
chưa được tạo; không suy hoặc tạo expected labels trong authoring pass.

## 2. Set A mới

| Metadata bắt buộc | Kết quả | Evidence / giới hạn |
|---|---|---|
| Identifier | **RESOLVED** | `M4-SET-A-POSTTUNE` |
| Version | **RESOLVED** | `v1` |
| Case count | **RESOLVED** | `18`; coverage design, không phải numeric gate |
| Artifact reference | **RESOLVED** | `M4T02_PRIVATE_SET_A_STORE` (opaque) |
| SHA-256/hash | **RESOLVED** | `98d691c8437f1c466a6c2b7be1cd4ca3c34f4e0a0218f02376c2ae4f4a414385` |
| Creation/finalization | **RESOLVED** | `2026-10-15T04:01:59Z` / `2026-10-15T04:03:53Z` |
| Author | **RESOLVED** | Minh — Evaluation/Logic; authorized Codex assistance recorded |
| Creation method | **RESOLVED** | Synthetic input-only authoring from requirements/protocol/domain boundaries |
| Independence from outputs on same cases | **PASS** | No Exodia/model/harness execution; model output was not an authoring source |
| Access history từ creation đến freeze | **RESOLVED** | Sanitized two-event history in public receipt; full log private |
| DEV/regression overlap | **PASS** | 53 inputs; exact/fuzzy/template + offline family review |
| Set B input-only overlap | **PASS** | 16 inputs; no Gold/reviewer material read |

**Set A provenance: `PASS`; candidate eligibility: `ELIGIBLE_FOR_GOLD_REVIEW`.** Chi
tiết public-safe nằm tại
[`M4_T02_SET_A_CANDIDATE_PREPARATION.md`](M4_T02_SET_A_CANDIDATE_PREPARATION.md)
và receipt tương ứng. Eligibility này không phải GO-A hoặc execution authorization.

## 3. Gold

| Metadata bắt buộc | Kết quả | Evidence / giới hạn |
|---|---|---|
| Identifier/version/hash/reference | **NOT_RESOLVED** | Không có Gold artifact/sidecar |
| Author | **NOT_RESOLVED** | Không suy từ Task Owner |
| Independent reviewer | **NOT_RESOLVED** | Final Reviewer của task không được coi là Gold reviewer khi chưa có attestation |
| Binding với Set A version/hash | **NOT_VERIFIED** | Cả hai phía chưa có identity/hash |
| Finalization timestamp | **NOT_RESOLVED** | Không có signed freeze receipt |

Không đọc expected label hoặc rationale. Gold M5-T01 không được tái sử dụng cho M4-T02.
**Set A ↔ Gold binding: `NOT_VERIFIED`.**

## 4. Runtime/config freeze candidate

[`M4_T02_FREEZE_MANIFEST.json`](../../docs/evaluation/M4_T02_FREEZE_MANIFEST.json)
được tạo theo M4-T01 freeze schema và đã bind dataset identity/version/hash/reference.
Candidate receipt là current evidence, không phải historical preregistration.

| Field | Trạng thái | Giá trị / binding |
|---|---|---|
| Runtime source SHA | **RESOLVED** | `47a1fcd9686b5409674979b34a521ead2f65ae8d`, exact remote `dev` |
| Deployed accepted source reference | **RESOLVED reference** | `fe8c2dbca013e9344a678ba52f70588495c897ef`; không có thay đổi trong `core/`, `infra/`, `corpus/`, `policies/`, `verify/`, Dockerfile, requirements, Streamlit/pages từ SHA này tới baseline |
| Corpus identifier/version/hash/reference | **NOT_RESOLVED** | Historical `cv_f6eb04187bb0` không bind actual ACTIVE snapshot cho run mới |
| Policy | **RESOLVED** | `git-blob-sha1:381a80e095af8b0b9d9baa63fdeb9abbd67a3b3c` |
| Protocol | **RESOLVED** | SHA-256 `c8f55327d80e39770e5ec764c7bfcb50014398d9b012e6e46eb75189b2a0a982` |
| Case schema | **RESOLVED** | SHA-256 `653ab5de6b52b8d907b75e048242abaa44ba4a57ad17e9b26dbf0fe29167072f` |
| Freeze schema | **RESOLVED** | SHA-256 `47c0d5c562af015c66183b36185eada4979bffdb507509ac0035f190b1fc34de` |
| Prompt/config | **RESOLVED** | Exact Git blobs trong manifest cho settings, LLM, extract, retrieval, generate, question-gen và resume |
| Adaptation | **RESOLVED** | `NONE` / `NONE`; không feedback update trong run |
| Provider/model | **RESOLVED candidate** | `openai` / `gpt-6-luna`, kế thừa accepted M4-T01 template |
| Model parameters | **RESOLVED candidate** | `reasoning_effort=none`, `temperature=0` |
| Python/base image | **RESOLVED** | Python `3.11`, `python:3.11-slim` |
| Dockerfile/dependencies | **RESOLVED** | Git blobs `ad19ffc707e886b9fda9369cf5b9bcaca6c7161f` / `828309b78eb21a2e9642efe695638ffa819bb17a` |
| Compose config | **RESOLVED** | Git blob `dc9d75253e3190505e4c0d4acff8abc2b582cbd4`; compose mặc định replay, không thay planned official mode |
| Deployed image digest for baseline | **NOT_RESOLVED** | Deployment IDs/source SHA không thay immutable image digest |
| Planned execution mode | **RESOLVED candidate** | `LIVE` từ accepted M4-T01 template; **không được thực thi** trước quyền riêng |
| Authorization/budget | **RESOLVED safety state** | `execution_authorized=false`, `budget=0`, `GO-A=NOT GRANTED` |

`RESOLVED candidate` nghĩa là giá trị có nguồn exact để Coordinator review, không phải
Coordinator đã cấp quyền execution cho post-tuning Set A.

## 5. Collector và harness

| Artifact | Git blob tại baseline | SHA-256 exact Git-blob bytes | Kết luận |
|---|---|---|---|
| `docs/evaluation/collector.py` | `1958e0d90bf75e5e78ff7a22282f93583d51757d` | `3bcff1577f2fde9e0716a3a75f77eba766244e5b916b4195dbcf52d9885c0d68` | **BINDING IDENTIFIED** |
| `verify/harness.py` | `0ac9084450705b2cd1b48608c678946e6de3d2ba` | `76e476eb33b1bb8e5fa13f64b5c1ad45f2eb68ea4113774c2f66a87555b2109e` | **BINDING IDENTIFIED** |

Các digest trên thay binding cũ/stale trong M4-T01 template cho freeze candidate mới.
Chúng chỉ xác định exact bytes; independent review và manifest acceptance vẫn cần trước GO-A.

## 6. Metric, execution và abort gates

| Hạng mục | Trạng thái | Freeze rule / phần còn thiếu |
|---|---|---|
| Planned population/denominator | **Định nghĩa RESOLVED; candidate count 18** | `S` là toàn bộ planned eligible business cases; `V` là valid AUTO_REPLY/ESCALATE. Count không tự tạo gate |
| Sample size | **NOT_RESOLVED** | Candidate có 18 case nhưng chưa có Coordinator-approved numeric gate |
| Strata | **NOT_RESOLVED** | Domain/family/Gold-route minimum chưa được duyệt |
| Coverage | **Định nghĩa RESOLVED; threshold NOT_RESOLVED** | `count(V)/count(S)`; không có numeric requirement |
| Missingness | **RESOLVED** | `MISSING/count(S)`; aborted/unattempted IDs vẫn ở denominator |
| TECHNICAL_ERROR | **RESOLVED** | `(ERROR+MALFORMED)/count(S)`, tách subtype; không đổi thành business escalation |
| Wilson CI | **RESOLVED** | Wilson 95%, raw integer n/N; N=0 → null/`UNDEFINED` |
| Latency | **RESOLVED** | Attempted-case count, median, nearest-rank p95, wall time; success/failure strata; null/censored rõ |
| Stop-type metrics | **RESOLVED** | Exact stop trên Gold ESCALATE in V và conditional exact stop trên TP; rule correctness riêng |
| Quality/reporting | **Reporting RESOLVED; thresholds NOT_RESOLVED** | Raw n/N, confusion matrix, MER/OER, bounds, failures, content/citation/grounding; không có pass threshold |
| Abort threshold | **NOT_RESOLVED** | Không có Coordinator-approved numeric/condition source |
| Timeout/retry/deadline | **RESOLVED** | 30 giây / 1 retry / 60 giây mỗi case |
| Execution state | **RESOLVED safety state** | `execution_authorized=false`, budget `0`, GO-A `NOT GRANTED` |

Không được chọn numeric gate sau khi xem results. Vì sample size, strata, coverage,
quality gate và abort threshold chưa được duyệt, execution phải dừng trước GO-A.

## 7. Unresolved fields và blocker

1. Gold identity/version/hash/reference/author/reviewer/finalization và Set A binding.
2. Actual corpus snapshot identifier/version/hash/reference cho baseline.
3. Immutable deployed image digest, nếu Coordinator yêu cầu container/image execution.
4. Numeric sample-size, strata, coverage, quality và abort gates.
5. Independent review/acceptance của exact manifest và collector/harness binding.
6. GO-A, execution authorization và nonzero budget.

Do các field bắt buộc còn thiếu, không thể trả `READY_FOR_GO_A_DECISION`.

## 8. Privacy, validation và recommendation

- Chỉ mở Set A input-only để author/validate và đúng Set B input-only candidate để
  overlap; không mở Set B Gold/reviewer material hoặc Set A Gold.
- Không commit case, expected label, rationale, PII, secret hoặc private artifact path.
- DEV/regression và M7 Set B access chỉ phục vụ offline overlap validation; Set B
  access bị giới hạn ở đúng input-only candidate đã được ủy quyền.
- Official Set A runs: **0**.
- Application LIVE/API/provider/email: **0**; chỉ dùng GitHub/Trello read-only cho evidence.
- Freeze schema + runtime/collector/harness hash assertions: **PASS**.
- Offline evaluation unit tests: **18 protocol + 19 collector PASS**.
- Targeted harness contract: **2 PASS**. Lượt đầu có một setup error do quyền truy cập
  thư mục temp mặc định của Windows; clean rerun với isolated `--basetemp` PASS và temp
  artifact đã được xóa.
- Runtime/product/evaluation run: **NOT RUN**; production không đổi và task cấm official run.
- Link, sensitive-data và Git checks được ghi sau validation cuối của branch.

**FREEZE STATUS: `FREEZE_INCOMPLETE`.**

**GO-A RECOMMENDATION: `NO_GO_A`.** Independent reviewer cần tạo Gold và binding;
Coordinator còn phải chốt corpus/image disposition cùng numeric gates, rồi review exact
manifest. Một quyết định GO-A riêng mới có thể đổi execution state.
