# M1 — Runtime & LLM Reliability

## Goal

**TECHNICAL_FAILURE <= 1/15 on full15 LIVE.**

Làm pipeline ổn định về mặt kỹ thuật trước khi đánh giá decision correctness.
Không tuning P01/P02/P03 correctness trong M1.

## Gate

Status: **NOT PASS YET**.

M1.5 có local patch chưa commit và targeted validation; full15 LIVE Gate sau fix
chưa chạy, M1.6 **NOT STARTED**. Starting POST-AUTH evidence có
TECHNICAL_FAILURE = 11/15, chưa đạt ngưỡng M1. Không coi credential replacement
hoặc R2 probe PASS là M1 Gate PASS. Chỉ Sprint Gate Review được phép đóng sprint;
agent không tự đánh dấu sprint PASS hoặc đổi gate.

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

Current Sprint: **M1 — Runtime & LLM Reliability**.
Current Micro-task: **M1.5 — Evidence-driven reliability fix**.

| Micro-task | Progress |
|---|---|
| M1.1 | DONE |
| M1.2 | DONE — provider observability |
| M1.3 | DONE — offline verification/review |
| M1.4 | DONE — targeted LIVE diagnosis |
| M1.5 | IN PROGRESS — evidence-driven reliability fix |
| M1.6 | NOT STARTED |

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

Status: **IN PROGRESS**.

Current local, uncommitted patch: bounded **1-second backoff** trước existing
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

Remaining work:

- Classify historical ClientError nếu reproducible.
- Xác định limiter thực sự chạm trước: per-call retry limit / shared case budget /
  case deadline / non-retryable error.
- Analyze attempt/time headroom, gồm unseen-input topology.
- Evaluate minimal reliability fix dựa trên evidence.
- Không mặc định backoff 3s, budget 6 hoặc fallback provider.

### M1.6 — Full15 Gate + Sprint Review

Status: **NOT STARTED**.

Exit: **TECHNICAL_FAILURE <= 1/15** trên full15 LIVE.
Cuối sprint phải có tests, Code Review, Review Agent, Anti review và Sprint Gate
Review theo roadmap. Chỉ Gate PASS mới chuyển M2.

## Historical Git Hygiene Note

Documentation bootstrap trước đây ghi nhận:

- Tracked `.env.example` đang deleted.
- Untracked `.env.example.txt` tồn tại.

Đây là historical note, không phải current working-tree state. Docs checkpoint
hiện tại chỉ stage STATUS, roadmap và living report; ba file M1.5 code/test vẫn
modified, unstaged và uncommitted.
