# C2-C — offline token-accounting simulation

Owner: Acer. Status: READY_FOR_REVIEW; Coordinator acceptance pending.
Authorization: **C2-C — CONDITIONAL GO: OFFLINE SIMULATION**, following
**GO-C2C OFFLINE (CONDITIONAL)**. Approved totals: 24,000 input / 6,000 output
tokens per case, at most three processing attempts, existing deadline, replay-only.

Baseline and remote dev verified before edits:
`ac5184ee5f1568827df321b7c737f218885f293f`, containing PR #70 and #71.
Branch: `codex/judge-input-c2c`. Final commit/PR identity is supplied in the handoff
and can be verified from this branch's PR HEAD; no runtime validation is inferred
from historical Mac or Lenovo results.

## Scope and behavior

- `infra/llm.py`: private `_c2c_simulation(case_id, directory)` scope, bound to an
  active judge reservation. No gateway route, environment feature flag or public
  signature change. The scope must enclose the complete case pipeline.
- One ContextVar budget spans steps, retry and repair. Nested simulation scopes
  are rejected; entering fresh `case_call_budget()` frames does not reset its
  counters, three-attempt limit or independent 60-second deadline.
- Separate fixtures declare synthetic request input tokens and output allocation.
  Before consuming a simulated response, validate provenance/model/prompt identity,
  nonnegative integer input, positive integer output allocation and both remaining
  case balances. Consume an attempt and debit allocation before response decoding.
- Missing/malformed/mismatched/over-limit usage poisons the scope and retains
  unreconciled allocation. Valid simulated usage can reconcile unused output
  allocation in RAM only. Durable C2-A quota/nonce/budget/revocation are not refunded.
- Kill/revoke/HOLD and deadline are checked before each replay step. The real SDK
  request entry rejects an active simulation scope before constructing a client.
- Legacy replay is unchanged: historical missing usage remains permitted there.
  Strict successful results carry `usage.source = synthetic`. No pricing invented.

New files: `tests/test_judge_input_c2c.py` and
`tests/fixtures/c2c_simulation/usage_case.json`. This is the only report changed.
No changes to gateway, Core #71, shared contracts, schema, audit semantics,
reservation constants, existing tests or historical cassettes.

## Validation / AC

Windows AMD64, Python 3.11.9, pytest 8.3.3, SQLite 3.45.1; fresh temporary SQLite
DBs and basetemp outside repo. Existing conftest traps network/DNS/OpenAI SDK;
provider tests use doubles. UTF-8 mode is inherited by subprocesses.

Test-first: new test initially errors because `_c2c_simulation` does not exist
(1 setup error, 2.28s). Initial implementation: 21 PASS, 14.63s. Then four additional
cases cover missing usage key, validated in-memory reconciliation, SDK denial and
real pipeline R2 retry/Core #71 fallback; final suite below includes all 25 C2-C cases.

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:PYTHONUTF8='1'
$env:PYTHONIOENCODING='utf-8'
# $temp is a fresh writable directory outside repo; exact executed base below.
.venv/Scripts/python.exe -B -m pytest -x -q -rs -p no:cacheprovider --basetemp="$temp/regression" tests/test_judge_input_c2c.py tests/test_judge_input_c1.py tests/test_judge_input_c2a.py tests/test_core_reliability.py tests/test_llm_budget.py tests/test_openai_provider.py tests/test_provider_observability.py tests/test_runtime_replay_audit.py tests/test_guards.py tests/test_restricted_demo.py tests/test_judge_new_input_offline.py --tb=short
.venv/Scripts/python.exe -B -m black --check --line-length 100 infra/llm.py tests/test_judge_input_c2c.py
.venv/Scripts/python.exe -B -m ruff check --no-cache infra/llm.py tests/test_judge_input_c2c.py
git diff --check
```

Exact temp root: `C:/Users/admin/AppData/Local/Temp/exodia-c2c-bec5deba028f403d80bc967986775b74`.
Final regression: **363 PASS, 0 FAIL, 0 SKIP in 158.80s**, exit 0.
Black/Ruff/diff checks PASS. Full repository suite and mypy NOT RUN.

| Acceptance | Result |
|---|---|
| Cumulative input/output bounds | PASS simulation: 3 x 8,000/2,000; preflight over-budget rejection before response decoding |
| Attempts/retry/repair | PASS: fourth attempt denied despite new common-budget frames; real R2 retry + Core #71 fallback uses three attempts |
| Missing/malformed/oversized usage | PASS: failure, scope poisoned, allocation retained; numeric booleans/strings/negative/mismatch rejected |
| Kill/revoke/HOLD/deadline | PASS: next step denied without ledger change from that denied call |
| No refund/no-send | PASS: C2-A invariance assertions; full pipeline persists PREVIEW or P01 escalation; no jobs or SEND events |
| Legacy/Core #71/C1/C2-A/replay/Audit | PASS in final 363-test suite; old fixtures/expectations unchanged |

## Self-review / remaining risks

Read the complete adapter diff and callers. Inactive simulation takes the original
paths; active simulation cannot enter SDK calls. No new database writes beyond the
existing latency path. C2-A atomic reservation and terminal readability guards stay
unchanged. Pre-existing untracked `.codex_tmp/` and `outputs/` are not staged.

The earlier measurement blocker is deliberately bounded: all 24 historical replay
cassettes lack usage, so strict simulation reads only its explicitly selected new
fixtures. Declared synthetic counts are NOT measured provider usage. There is no
model tokenizer/full-input accounting proof, real output-cap enforcement, durable
usage settlement, real retry billing proof, cost reconciliation or hard USD cap.
The private scope is a trusted offline harness lifecycle, not a production gateway
or restart-safe token ledger. Legacy replay is not evidence of provider hard bounds.

Provider LIVE/API calls: **0**. Merge/deploy: **NOT RUN**. PR targets dev and requires
independent review and Coordinator acceptance; this report does not declare DONE.
