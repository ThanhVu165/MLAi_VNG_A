# M1 — Runtime & LLM Reliability

## Goal

**TECHNICAL_FAILURE <= 1/15 on full15 LIVE.**

Làm pipeline ổn định về mặt kỹ thuật trước khi đánh giá decision correctness.
Không tuning P01/P02/P03 correctness trong M1.

## Gate

Status: **PASS / CLOSED**, theo final evidence và coordinator-authorized closure
ngày 06/10/2026 (Asia/Saigon). **TECHNICAL_FAILURE = 0/15** trên final full15 LIVE,
ngưỡng giữ nguyên <=1/15. 15/15 executed, 14/15 semantic labels đúng.

M1 overall **PASS**; M1.6 **DONE**. M1.5 code checkpoint `c4d2f8d` và các
historical claims bên dưới giữ nguyên thời điểm ghi nhận. Subsequent M1.6 evidence
đóng Gate sau reliability fixes; không dùng credential replacement hoặc R2 probe
đơn lẻ làm Gate proof. Starting POST-AUTH TECHNICAL_FAILURE = 11/15 là historical
failure, không thay thế final run. Next: **M2 — Core Decision + Escalation Quality**,
chưa bắt đầu. Curated evidence: [manifest + SHA-256](../evidence/m1/README.md).

## Starting Evidence

References:

- [Baseline full15 actual — 2026-10-02](../baseline_full15_live_actual_2026-10-02.md).
- [Full15 LIVE post-auth-fix — 2026-10-02](../full15_live_post_auth_fix_2026-10-02.md).

Summary:

- Original auth-problem run, trước thay credential: **2/15 PASS**, 13/15 technical failures.
- Credential replaced.
- Diagnostic R2 probe **SUCCESS**: một synthetic email mới, model gemini-3.6-flash,
  temperature=0, JSON MIME, timeout=30s, không retry; latency 7242 ms,
  JSON/schema parse SUCCESS. Nguồn: diagnostic session trước POST-AUTH run;
  chưa có standalone probe raw artifact trong repo. Claim này được ghi nhận
  theo diagnostic session và bootstrap của coordinator, không suy từ full15.
- POST-AUTH full15: **4/15 PASS**, **11/15 FAIL**.
- Technical failures: **11/15**, tất cả actual rule TECHNICAL_ERROR.
- Exact provider reason của các lỗi baseline/post-auth chưa được wrapper lưu;
  không suy ra tất cả 4xx là auth hoặc quota.
- Python **3.11.9**, google-genai **2.25.0**, runtime model **gemini-3.6-flash**.
- LIVE validation DB: `data/validation/manual-live.db`, schema 2; 5 ACTIVE sources,
  1 SUPERSEDED, 72 chunks; 60/60 ACTIVE candidates resolve được trong preflight.
- POST-AUTH run đúng một lần, không rerun case/suite. Corpus và baseline evidence
  được giữ nguyên; DB có 15 case instances mới bên cạnh 15 instances baseline.

Raw evidence để kiểm chứng khi cần:

- `data/validation/full15_live_post_auth_fix_2026-10-02.json`: labels, outcomes,
  latency và mapping case_id → case_ref.
- `data/validation/full15_live_post_auth_fix_2026-10-02_case_evidence.json`:
  persisted results, LLM step timings và audit của từng case.
- `data/validation/full15_live_post_auth_fix_2026-10-02_stderr.txt`:
  exception classes và wrapper retry sequence.
- `data/validation/full15_live_post_auth_fix_2026-10-02_preflight.json`,
  `_process.json`, `_summary.json`: runtime, readiness, integrity và summary.
- `data/validation/full15_live_post_auth_fix_2026-10-02_before.db`:
  snapshot SQLite nhất quán trước POST-AUTH run.

Các raw artifacts/DB dưới `data/validation` được gitignore; session trên máy khác
phải kiểm tra khả năng truy cập, không coi link/path là bằng chứng file hiện diện.

## Micro-task Status

Current Sprint: **M1 — Runtime & LLM Reliability (CLOSED)**.
Next sprint: **M2 — Core Decision + Escalation Quality (NEXT; chưa bắt đầu)**.

| Micro-task | Progress |
|---|---|
| M1.1 | DONE |
| M1.2 | DONE — provider observability |
| M1.3 | DONE — offline verification/review |
| M1.4 | DONE — targeted LIVE diagnosis |
| M1.5 | DONE — OpenAI provider path + production smoke |
| M1.6 | DONE — Gate PASS + final reviews |

### M1.1 — Runtime evidence + LLM call map

Status: **DONE**.

Confirmed:

1. Không có runtime Gemini call bypass `infra/llm.py`.

   Common path:

   ```text
   call_json
   → _run_mode
   → _call_live
   → _attempt_timeout
   → _request_gemini
   → generate_content
   ```

2. Stage mapping:

   | Stage | Exact path |
   |---|---|
   | R2 | extract_facts → call_json("R2_extract") |
   | R4 | retrieve_evidence → _select → call_json("R4_select") |
   | R7 AUTO_REPLY | generate_reply → call_json("R7_generate") |
   | R7 escalation | generate_escalation_card → call_json("R7_question") |
   | R7 multi-intent | generate_reply rồi generate_escalation_card, qua cùng wrapper |
   | R8 groundedness | local only, không gọi Gemini |
   | R8 Question Guard | có thể regenerate qua call_json("R7_question") |

   R4 không gọi Gemini nếu không có supported domain hoặc candidate chunks.
   Regenerate do R8 kích hoạt vẫn ghi step R7_question, nên step name chưa thể
   phân biệt initial generation với regenerate.

3. POST-AUTH run evidence:

   - **22 wrapper calls**: 11 OK, 11 FAIL.
   - R2_extract=13; R4_select=6; R7_generate=2; R7_question=1.
   - Reconstruct được **28 SDK invocations**, gồm 6 wrapper retries; log có
     28 lần tạo SDK client. HTTP attempts chưa được lưu thành records riêng.
   - Không có Question Guard failure/regenerate trong run này.
   - Read-only query toàn bộ step_latencies có 485 rows / 30 case instances:
     baseline 238 rows, POST-AUTH 247 rows; tách bằng case_ref của mỗi run.
   - Tổng wrapper latency POST-AUTH = 167413 ms. Đây là tổng các call_json
     durations, không phải thời gian riêng từng provider attempt.

4. Retry/budget:

   - CASE_TIMEOUT_SECONDS = **60**.
   - LLM_MAX_ATTEMPTS = **4**, shared per process_case invocation.
   - LLM_TIMEOUT_S default **30**, có thể override qua env.
   - LLM_RETRIES default **1**, wrapper clamp tối đa một retry.
   - ServerError có wrapper retry tối đa 1; ClientError không wrapper retry.
   - SDK internal retry không bật trên exact project path: retry_options=None
     trong SDK 2.25.0 dùng một HTTP attempt; không áp default 5 attempts của
     retry-options object chưa đặt attempts.
   - Wrapper retry tiêu chung case attempt budget. Extraction parse retry và
     Question Guard regenerate cũng tiêu budget khi đi tới provider attempt.
   - R2 typed parsing tối đa hai wrapper calls; JSON decode failure trong wrapper
     trả FAIL ngay, không kích hoạt typed parse retry của extract_facts.
   - 60s là deadline kiểm tra trước attempt; không có cancellation timer cưỡng
     bức toàn pipeline đúng giây 60.

5. Environment loading:

   `load_local_env` dùng `os.environ.setdefault()`.

   - Process env thắng `.env`, kể cả process value là chuỗi rỗng.
   - `.env` không overwrite process env; chỉ bổ sung biến chưa tồn tại.

6. Hypothesis state:

   **CONFIRMED:**

   - ClientError và ServerError đều đã xảy ra.
   - Có transient ServerError rồi retry thành công: V02 R4, V03 R2.

   **SUPPORTED:**

   - Có provider 5xx: SDK map HTTP 500–599 sang ServerError; exact code chưa lưu.

   **POSSIBLE:**

   - Quota/rate-limit gây một phần ClientError nhanh.
   - Input/schema-specific 4xx.

   **NOT SUPPORTED:**

   - Tất cả lỗi vẫn do auth.
   - Tất cả lỗi chỉ do quota.
   - Tất cả lỗi chỉ do 5xx.
   - V02 fail vì global attempt budget exhausted.

Historical open question: exact HTTP status / provider status / reason của nhiều
failures vẫn **UNVERIFIED**. Historical ClientError/ServerError evidence có trước
observability hiện tại; không dùng targeted evidence mới để gán ngược exact status
cho historical failures.

Observability limitation đã xác minh: pipeline rows R0–R14 luôn ghi ok=1;
stage bị skip được điền 0 ms; R14 là finalize marker. Không dùng các rows này
để chứng minh stage thành công hoặc đã chạy. Wrapper rows R2_extract/R4_select/
R7_generate/R7_question mới chứa wrapper outcome; OK chưa chứng minh caller
schema/semantic parsing thành công.

Code references cho call-map/budget claims:

- `infra/llm.py`, `infra/settings.py`.
- `core/pipeline.py`, `core/extract.py`, `core/retrieval.py`.
- `core/generate.py`, `core/question_gen.py`, `core/question_guard.py`,
  `core/ground_guard.py`.
- Installed google-genai 2.25.0: `google/genai/_api_client.py`, `types.py`,
  `models.py`, `errors.py`.

Conclusion: **M1.1 đạt mục tiêu**. Không cần thêm read-only mapping trước khi
chuyển M1.2. DONE của micro-task không đồng nghĩa sprint Gate PASS.

### M1.2 — Provider observability

Status: **DONE**.

Goal: ghi sanitized provider-level evidence theo từng attempt để phân biệt:

- 400 / invalid input/schema.
- 429 / quota/rate-limit.
- 5xx / provider failure.
- Retry/budget interaction.

Constraint: **Không thay đổi retry/policy/runtime behavior trong observability task.**
Không in/lưu credential, auth headers hoặc email payload thô trong diagnostics.
M1.2 có local implementation + offline validation PASS trên branch
`task/llm-observability`; evidence và progress log xem
[M1.2 implementation evidence](M1_2_provider_observability.md).
Provider observability và PII redaction đã hoàn tất; M1.3 verification/review DONE
theo trạng thái được coordinator xác nhận. Implementation report ở trên giữ log
lịch sử tại thời điểm triển khai.

### M1.3 — Offline verification + Code Review

Status: **DONE**.

Offline verification/review hoàn tất; targeted tests PASS, independent review
PASS theo evidence/trạng thái do coordinator cung cấp. Không đồng nghĩa M1 Gate PASS.

### M1.4 — Targeted LIVE diagnosis

Status: **DONE**.

Targeted LIVE ngày 05/10/2026 confirmed Gemini HTTP **503 / UNAVAILABLE / high
demand**. E01 và V01: R2 success, R4 nhận 503 ở cả hai attempts, final
TECHNICAL_ERROR. Stop rule kích hoạt sau V01; V02 không chạy trong M1.4.
Artifacts: `data/validation/m1_4_targeted_live_2026-10-05_*` và diagnostic DB
`data/validation/m1_4_targeted_live.db` (gitignored).

### M1.5 — Evidence-driven reliability fix

Status: **DONE**; không đồng nghĩa M1 Gate PASS.

#### Historical targeted backoff checkpoint

Tại thời điểm targeted backoff validation, local patch chưa commit: bounded **1-second backoff** trước existing
transient retry, kèm `retry_backoff_ms` evidence. Retry count, shared attempt budget,
model/prompt/schema unchanged. Targeted offline tests: **45 passed**;
independent review **PASS** theo xác nhận coordinator. Không chạy lại validation
trong docs checkpoint này.

Targeted LIVE after patch (mỗi case một lần):

| Case | Provider sequence | Final case result |
|---|---|---|
| E01 | R4: 503 → 1s → 503 | TECHNICAL_ERROR |
| V01 | R7: 503 → 1s → success | PASS / P05 |
| V02 | R4: 503 → 1s → 503 | TECHNICAL_ERROR |

Observed recovery không chứng minh backoff là nguyên nhân duy nhất của success.
Không generalize ba targeted cases thành provider-wide frequency claims.
V02 không tới R7; historical ClientError vẫn chưa exact-classified.
Artifacts: `data/validation/m1_5_targeted_live_2026-10-05_*` và diagnostic DB
`data/validation/m1_5_targeted_live.db` (gitignored).

#### Completed OpenAI checkpoint

- Targeted diagnosis confirmed Gemini **429 / RESOURCE_EXHAUSTED / quota exceeded**.
  Không dùng observation này để gán exact reason cho các historical ClientError.
- OpenAI được điều tra như alternate provider candidate. Direct compatibility probe
  R2/R4/R7: đều **HTTP 200**, existing validators **PASS**; schema normalization
  required. Probe không gửi temperature, chỉ chứng minh compatibility.
- Code commit: `c4d2f8d` — `feat(m1.5): add OpenAI provider path and production smoke`.
  Commit đã tồn tại khi đóng checkpoint; không amend, squash hoặc tạo commit rỗng
  để đổi message. Diagnostic scripts là công cụ tái lập evidence, không chứa khóa.
- Public production path vẫn `call_json(...) -> LLMResult`. Provider được chọn bằng
  config, không automatic cross-provider fallback. OpenAI SDK **max_retries=0**;
  wrapper giữ retry count, shared budget, timeout và bounded transient backoff.
- Schema normalization ở adapter OpenAI: deep-copy rồi recursively đặt
  additionalProperties=false trên object; không sửa core schema/fields/enums.
- New cache/cassette identity bao gồm provider/model; legacy Gemini reads giữ tương
  thích. OPENAI_API_KEY được redact, OpenAI exception logs chỉ giữ safe metadata.
- OPENAI_REASONING_EFFORT mặc định **none**. Khi none, giữ temperature=0.0 trên
  production path; effort khác bỏ temperature. Gemini/business semantics không đổi.
- Canonical runtime: `.venv-bootstrap`, Python **3.11.9**, openai **3.24.0**,
  google-genai **2.25.0**, pytest **8.3.3**.
- Targeted offline command đã chạy trong implementation session:

  ```powershell
  .venv-bootstrap/Scripts/python.exe -B -m pytest -q --basetemp=.pytest_cache/m15f-fix tests/test_openai_provider.py tests/test_llm_budget.py tests/test_provider_observability.py
  ```

  **77 PASS / 0 FAIL**. Không chạy lại tests hoặc LIVE trong docs checkpoint.
- Production adapter smoke theo evidence coordinator cung cấp: provider=openai,
  model=gpt-6-luna, reasoning_effort=none, temperature=0.0; ok=true,
  provider_attempts=**1**, latency_ms=**4007**, extraction_validator=**PASS**,
  result=**PASS**. Không có standalone raw smoke artifact được thêm vào repo;
  không suy diễn HTTP success status không được smoke ghi nhận.
- Compatibility và một smoke PASS **không chứng minh full reliability**; không
  khẳng định OpenAI categorically more reliable than Gemini.
- Tại M1.5 checkpoint, **full15 M1 Gate chưa chạy sau fix**; M1.6 khi đó là bước
  tiếp theo và chưa bắt đầu. Subsequent M1.6 evidence dưới đây đóng Gate; không
  gán ngược evidence đó cho thời điểm M1.5.

### M1.6 — Full15 Gate + Sprint Review

Status: **DONE — M1 PASS / CLOSED** (06/10/2026, Asia/Saigon).

Exit giữ nguyên: **TECHNICAL_FAILURE <= 1/15** trên full15 LIVE. Final actual:
**0/15 TECHNICAL_ERROR**, Gate **PASS**. Coordinator xác nhận final Code Review
PASS (no blocker/high/medium) và final independent Anti **PASS WITH DOCUMENTED
DEBT**, cho phép documentation sync và sprint closure. Đây là review decisions
do coordinator cung cấp; không rerun review/evaluation trong docs task này.

#### Failure diagnosis and bounded fixes

First verify4 (`data/validation/m1_6a_verify4_20261005_230950/`) có V02/V03
TECHNICAL_ERROR dù provider calls thành công trên attempt 1:

- V02: clock grounding false positive, draft `5:00 p.m.` so với evidence `17 giờ 00`.
  Narrow clock normalization chỉ chấp nhận equivalent time được evidence hỗ trợ;
  không nới generic number/article/form checks.
- V03: strict basis provenance failure, quote nối các câu và bỏ nhãn `Điểm a)`.
  Giữ strict continuous-substring validation; thêm tối đa một bounded basis repair
  qua public `call_json`, cùng evidence/schema và shared budget/deadline.
- `a2ed369` — harden grounding and basis repair; `d1b4e2a` — preserve primary
  summary/facts/question/options, chỉ nhận basis đã strict-validate từ repair.
  Không đổi policy, labels, Gate, retry/budget/timeout hoặc TECHNICAL_ERROR mapping.
- Offline fix validation: 111 targeted tests PASS và 10 existing regressions PASS
  ở M1.6b; field-preservation follow-up 35 semantic-validator tests + 10 existing
  regressions PASS (46 ngoài scope deselected); Ruff/diff check PASS.
  Không chạy lại test suite trong docs-only closure.

#### Final existing LIVE evidence

| Suite | Semantic labels | TECHNICAL_ERROR | Elapsed | Outcome |
|---|---|---|---|---|
| Final verify4 | 4/4 PASS | 0/4 | 35.28s | PASS |
| escalation5 | 4/5 PASS | 0/5 | 44.48s <=90s | within_time_limit=True; E04 mismatch |
| Final full15 | 14/15 PASS; 15/15 executed | 0/15 | 93.19s | M1 Gate PASS |

All three JSONs record provider=openai, model=gpt-6-luna, llm_mode=live,
cache_enabled=false. Console metadata records 12/17/42 provider attempts respectively,
all successful, all attempt 1, no retries or provider failures. Full15's
within_time_limit=True is the harness flag; <=90s applies only to escalation5.
These are synthetic DEV/REGRESSION runs, not independent held-out evaluation or
proof of general OpenAI superiority.

Harness exit code **1** on full15 (also escalation5) is due to E04 semantic
expected-label mismatch, **not TECHNICAL_ERROR**. This follows the unchanged harness
return condition and coordinator run record; exit status is not a JSON field.

#### Known M2 correctness issue and documented debt

E04 remains expected **ESCALATE / FACT_UNRESOLVED / P03**, actual **ESCALATE /
AUTHORITY_REQUIRED / P01** in escalation5 and full15. **Known M2 issue**:
provider/model-sensitive correctness issue; exact non-regression against the old
Gemini/dev path has not been proven. Không khẳng định M1 chắc chắn gây ra hoặc
không gây ra hành vi này. Expected label giữ nguyên; investigate trong M2.

Final review carries **six LOW debts**, plus pre-existing tracked bytecode hygiene:

| ID | Debt | Follow-up |
|---|---|---|
| LOW-01 | Cache identity omits OPENAI_REASONING_EFFORT and schema-normalizer version | Include both when tightening cache provenance; final runs used cache=false. |
| LOW-02 | OpenAI timeout is not a strict wall-clock total | Document/test transport timeout ceiling before promising strict total cancellation. |
| LOW-03 | reasoning_effort != none omits caller temperature | Document/test model-compatible temperature semantics; final path uses none. |
| LOW-04 | Thinner diagnostics for non-status OpenAI errors | Add safe error-class diagnostics without raw payloads or credentials. |
| LOW-05 | Harness imports private _provider_config | Expose shared public config helper when next touching config API. |
| LOW-06 | Clock grounding is evidence-wide / timezone-text limitation | Revisit locality/timezone handling with focused semantic cases. |
| HYGIENE-01 | Pre-existing tracked __pycache__/*.pyc (4 files) | Remove tracked bytecode in a separate hygiene task; ignore rules already exist. |

None of these carried LOW debts or hygiene debt invalidates M1 Gate. E04 is
correctness debt to M2, not a technical-failure count. M2 is NEXT, not started.

#### Curated archive and integrity

Six final JSON/log files are tracked under `reports/evidence/m1/`; **no DB/WAL/SHM**.
Archive-local `.gitattributes` prevents Git newline conversion of JSON/log bytes,
so archive SHA-256 also matches committed blobs across checkout platforms.
JSONs are byte-identical to source. Logs are curated UTF-8 safe-metadata/table
derivatives, retaining all provider events and result rows while removing only
PowerShell stderr wrapping/decorations. Originals remain untouched. Synthetic
subject/question artifacts remain in JSON. No secret/unsafe raw payload was found;
no credential or raw provider payload is archived.

The [immutable evidence manifest](../evidence/m1/README.md) records the original
absolute local source path, archived path, archive SHA-256 and source SHA-256 for
all six files, together with provider/model/cache and result summaries. These
files are immutable M1 closure evidence; future runs require separate artifacts.

| Archived evidence | Original local source | Archive SHA-256 |
|---|---|---|
| `reports/evidence/m1/verify4_final.json` | `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_verify4_rerun2_20261006_000228\verify4.json` | `351b9573f35d7953b075c6d96cadf7abd8d6665fbc861d5f5ada523e2142e6e2` |
| `reports/evidence/m1/verify4_final_console.log` | `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_verify4_rerun2_20261006_000228\console.log` | `a6dfaa17a70288abd994cdeb8002feb015549795faf064189cdaf314402f9b7b` |
| `reports/evidence/m1/escalation5_final.json` | `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_escalation5_20261006_004954\escalation5.json` | `07869713037ca86aa59b9456a7bb2a55e66c8609cbbf04fe17d0fe3241787fa8` |
| `reports/evidence/m1/escalation5_final_console.log` | `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_escalation5_20261006_004954\console.log` | `ec2bbba6e4d4ba2e5c0ed7af464ef8326452daacc612a29664aeb8e248d5f6a1` |
| `reports/evidence/m1/full15_gate_final.json` | `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_full15_gate_20261006_005305\full15.json` | `81203a4a50eb01c68595555a7f7ce8c3b0060d8e8451ed5e81c9138cc705ddaf` |
| `reports/evidence/m1/full15_gate_final_console.log` | `D:\LT\AIO\2026\Cuoc thi\Hackathon AIML\MLAi_VNG_A\data\validation\m1_6_full15_gate_20261006_005305\console.log` | `89a380edf71d05e764e95767c3bcf51ac48d4cbee564c24483364a61f26ff3df` |

## Historical Git Hygiene Note

Documentation bootstrap trước đây ghi nhận:

- Tracked `.env.example` đang deleted.
- Untracked `.env.example.txt` tồn tại.

Đây là historical note, không phải current working-tree state. Ở docs checkpoint
trước (`0e5770f`), ba file M1.5 code/test còn modified, unstaged và uncommitted.
Code checkpoint hiện tại `c4d2f8d` đã lưu chín implementation/test/evidence files;
checkpoint đóng M1.5 chỉ bổ sung documentation sync, không viết lại lịch sử.
