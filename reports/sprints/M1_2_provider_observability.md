# M1.2 — Provider observability: local implementation evidence

Date: 2026-10-05 (Asia/Saigon). Environment: Local; worktree OFF; Ponytail OFF.
Base: `dev @ f638e8ae4d7df15f5d09d6b2a91ddf266a57c023`.
Branch: `task/llm-observability`.

Local validation: **PASS**. Coordinator/reviewer acceptance: **PENDING**.
This is implementation evidence, not micro-task DONE or M1 Gate PASS.
M1.3 is not opened. The latest user instruction authorizes commit and push of
this task branch only after local validation PASS, overriding the attachment's
initial Commit/Push NO. No merge is authorized.

## Progress log

1. Read roadmap, STATUS, then living M1 report in the required order.
2. Verified dev, exact base HEAD, upstream origin/dev, clean working tree.
   Created task branch locally; no separate worktree.
3. Inspected wrapper, settings, shared budget, audit/DB helpers, existing tests,
   and installed google-genai 2.25.0 error definitions. No LIVE calls.
4. Added attempt evidence using the existing infra.llm logger and a small
   sanitizer module. Propagated case_id/step only inside the wrapper.
5. Initial tests: 37 passed. Ruff passed; Black requested formatting, applied.
6. Reviewed identity handling; added canonical UUID preservation and regression
   coverage. Subsequent tests: 38 passed. Compared checkpoint/current behavior
   across 160 offline scenarios: identical results, request arguments and budget.
7. Mypy found object/list narrowing issue in sanitizer; fixed it. Added tests
   for escaped Unicode prompts, sanitizer internal errors and status-only response
   access. Final wrapper/sanitizer/budget tests: **40 passed**.
8. Additional existing guard regression selection initially had **6 passed,
   10 setup errors, 23 deselected** due to WinError 5 on pytest's default temp
   directory. Classified ENVIRONMENT, used a newly allocated dedicated test temp
   without changing application files: **16 passed, 23 deselected**. Sockets
   blocked; LLM_MODE=replay; temporary fixture DBs only.
9. Final Black, Ruff, targeted mypy and git diff --check passed.
   Task changes are limited to wrapper instrumentation, sanitizer, offline tests
   and this evidence/living-report update. Coordinator review remains required.

## Capture and fields

Capture surrounds `_request_gemini` inside the existing `_call_live` attempt loop.
One `llm_provider_attempt` event per request-wrapper invocation; failures and
successes use the same generated call_id and 1-based attempt_index. Every wrapper
call gets its own call_id. Attempts rejected by `_attempt_timeout` use the
distinct event `llm_provider_attempt_skipped` and are not counted as SDK calls.

Both events are JSON in existing log messages and a `provider_attempt` LogRecord
extra field. WARNING level retains success evidence with the existing default
logging threshold; no new logging framework, handler, file sink or DB table.

Fields:

- Identity: case_id, trace_id (null), call_id, step, attempt_index.
- Timing/budget: elapsed_ms, effective_timeout_s, attempts_remaining_before,
  attempts_remaining_after, remaining_case_time_s (at attempt entry).
- Request metadata: model, prompt_chars, prompt_hash12 (SHA-256 of prompt alone).
- Result: success, retryable, will_retry, stop_reason.
- Error metadata when available: exception_class, http_status, provider_code,
  provider_status, provider_reason, sanitized_message, sanitized_details.

No HTTP success code is invented. SDK `code` exposes the HTTP error code; a
response object's status_code is a fallback. ErrorInfo reason may be retained
from sanitized nested details. No response text, body, headers or request object
is accessed or serialized.

## Sanitization

- Replace actual GOOGLE_API_KEY/GEMINI_API_KEY and raw/JSON-escaped prompt before
  truncation. Keys and prompts are only used in memory for redaction.
- Redact AIza key patterns, Bearer/Authorization/Cookie, email addresses,
  12-digit IDs, labeled password/token/secret/credential/API-key values and long
  opaque token strings.
- Remove embedded JSON/HTML payload tails and body/prompt/output labels.
- Keep only error/code/status/reason/message/details/domain/@type in diagnostic
  containers. Unknown fields, metadata, request/response/header/output fields and
  arbitrary objects are omitted/redacted; no repr/str of arbitrary objects.
- Bound strings to 512 chars, lists to 8 entries and nesting to depth 4;
  serialized diagnostic values above 4096 chars are redacted entirely.
- Sanitizer failures redact the value. Diagnostic/logging failures cannot mask
  original exceptions or change retry, budget, result or request semantics.

## Offline validation

Runtime: `.venv-bootstrap/Scripts/python.exe`, Python 3.11.9.

```text
python -m pytest -q tests/test_provider_observability.py tests/test_llm_budget.py
40 passed (37 new parameterized cases + 3 existing budget tests)

python -m black --check --line-length 100 infra/llm.py infra/provider_observability.py tests/test_provider_observability.py
3 files unchanged

python -m ruff check infra/llm.py infra/provider_observability.py tests/test_provider_observability.py
All checks passed

python -m mypy --ignore-missing-imports --follow-imports=silent infra/llm.py infra/provider_observability.py
Success: no issues found in 2 source files

git diff --check
PASS
```

Existing guard selection: `tests/test_guards.py -k "extract or generate_reply or
generate_escalation or retrieval or question_guard or multi_intent or prepolicy"`.
Executed via in-memory Python with socket.socket.connect/create_connection
raising AssertionError, LLM_MODE=replay, HF_HUB_OFFLINE=1,
TRANSFORMERS_OFFLINE=1, and --basetemp from tempfile.mkdtemp:
**16 passed, 23 deselected**. No application DB is used by these selected tests;
their DB fixtures point to isolated temporary paths.

Before/after check: loaded `git show f638e8a:infra/llm.py` into an in-memory module
and compared it with current wrapper, using mocked requests and fixed clock.
Matrix: success / ClientError 400 / ClientError 429 / ServerError 500 /
ServerError 503 then success / TimeoutError / ConnectionError / ValueError;
retries -1/0/1/10; no budget or budget/deadline (4,160)/(1,107.9)/(0,160)/(4,100)
at perf_counter=100. All **160** combinations matched in LLMResult, request
arguments, invocation count, remaining attempts/deadline; constants also matched.

## Behavior preservation and limits

Retry list/clamp, ClientError/ServerError behavior, shared case budget, timeout
algorithm/constants, request model/prompt/schema/temperature, exception
propagation from `_request_gemini`, and LLMResult values are unchanged. Settings,
policy, retrieval, routing, prompts and schemas are not edited.

- trace_id is not propagated to call_json; it remains null. case_id links to the
  existing case record. No diagnostic DB lookup/write was added.
- Capture covers SDK setup, request and local JSON parsing as one request-wrapper
  invocation. elapsed_ms is not pure HTTP latency; a parse/setup error does not
  establish a provider HTTP failure. Internal SDK HTTP retries are not observed.
- will_retry records the existing wrapper decision to continue; a subsequent
  retry can still be blocked by the shared budget/deadline and logged as skipped.
- No key, cache hit or replay means no provider attempt event.
- Sanitization is deliberately conservative and can drop useful free text or
  unknown provider details. Error code/status/reason remain when safely exposed.
- Logs require the existing logger's output to be retained by the diagnostic run;
  no persistent evidence sink was added. A failed logger can drop evidence.
- LIVE behavior was not tested. No Gemini, targeted LIVE, full15 or evaluation.
- No sprint/micro-task completion or next-sprint authorization is claimed.
